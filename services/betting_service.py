import uuid

from config.db import get_connection
from models.bet import Bet
from models.betting_session import BettingSession
from models.betting_strategies import build_strategy
from models.win_loss_models import OutcomeStrategyType
from services.stake_management_service import StakeManagementService
from services.win_loss_calculator import WinLossCalculator, build_odds_configuration
from utils.logger import logger
from utils.validator import validate_positive_amount, validate_probability


class BettingService:
    def __init__(self, stake_service=None):
        self.stake_service = stake_service or StakeManagementService()
        self.win_loss_calculator = WinLossCalculator()

    def place_bet(
        self,
        gambler_id,
        amount,
        win_probability,
        odds_multiplier=None,
        strategy_name=None,
        session_id=None,
        outcome_strategy="RANDOM",
        house_edge=0.0,
        odds_type=None,
        odds_value=None,
    ):
        validate_positive_amount(amount, "amount")
        validate_probability(win_probability)

        context = self._get_bet_context(gambler_id)
        self._validate_bet_amount(amount, context)

        odds_config = build_odds_configuration(odds_type, odds_value, odds_multiplier)
        _, computed_multiplier = self.win_loss_calculator.calculate_winnings(amount, odds_config, win_probability)
        validate_positive_amount(computed_multiplier, "odds_multiplier")

        is_win = self.determine_bet_outcome(win_probability, outcome_strategy=outcome_strategy, house_edge=house_edge)
        bet_id = str(uuid.uuid4())

        settlement = self.stake_service.process_bet_outcome(
            gambler_id,
            amount,
            is_win,
            computed_multiplier,
            bet_id,
        )

        bet = Bet(
            bet_id=bet_id,
            gambler_id=gambler_id,
            amount=amount,
            win_probability=win_probability,
            odds_multiplier=computed_multiplier,
            stake_before=settlement["balance_before"],
            stake_after=settlement["balance_after"],
            is_win=is_win,
            strategy_name=strategy_name,
            session_id=session_id,
        )

        self._persist_bet(bet)
        self._update_statistics(gambler_id, bet)

        if session_id:
            self._update_session_totals(session_id, bet)

        analysis = self.win_loss_calculator.analyze_history(gambler_id, session_id=session_id, limit=500)

        logger.info(f"Bet placed for gambler {gambler_id}: {bet.bet_id}")
        return {
            "bet": bet.to_dict(),
            "settlement": settlement,
            "win_loss": analysis.to_dict(),
        }

    def determine_bet_outcome(self, win_probability, outcome_strategy="RANDOM", house_edge=0.0):
        validate_probability(win_probability)
        strategy = OutcomeStrategyType[outcome_strategy.upper()]
        return self.win_loss_calculator.determine_outcome(win_probability, strategy, house_edge=house_edge)

    def place_bet_with_strategy(
        self,
        gambler_id,
        strategy_name,
        win_probability,
        base_bet,
        odds_multiplier=None,
        percentage=0.05,
        step=1.0,
        session_id=None,
    ):
        context = self._get_bet_context(gambler_id)
        strategy = build_strategy(strategy_name, base_bet, percentage=percentage, step=step)
        amount = strategy.next_bet(context["current_stake"], context["min_bet"], context["max_bet"])
        return self.place_bet(
            gambler_id=gambler_id,
            amount=amount,
            win_probability=win_probability,
            odds_multiplier=odds_multiplier,
            strategy_name=strategy_name,
            session_id=session_id,
        )

    def place_consecutive_bets(
        self,
        gambler_id,
        strategy_name,
        win_probability,
        rounds,
        base_bet,
        odds_multiplier=None,
        percentage=0.05,
        step=1.0,
        stop_on_boundary=True,
    ):
        validate_positive_amount(rounds, "rounds")
        validate_positive_amount(base_bet, "base_bet")
        validate_probability(win_probability)

        strategy = build_strategy(strategy_name, base_bet, percentage=percentage, step=step)
        session = self.start_session(gambler_id, strategy_name, win_probability)
        session_id = session["session_id"]

        placed = []
        for _ in range(int(rounds)):
            context = self._get_bet_context(gambler_id)
            amount = strategy.next_bet(context["current_stake"], context["min_bet"], context["max_bet"])

            if amount <= 0:
                break

            result = self.place_bet(
                gambler_id=gambler_id,
                amount=amount,
                win_probability=win_probability,
                odds_multiplier=odds_multiplier,
                strategy_name=strategy_name,
                session_id=session_id,
            )
            placed.append(result["bet"])

            strategy.record_outcome(result["bet"]["is_win"])

            if stop_on_boundary and result["settlement"]["boundary_status"].startswith("OUT"):
                break

        ended = self.end_session(session_id)
        return {
            "session": ended,
            "bets": placed,
        }

    def start_session(self, gambler_id, strategy_name, win_probability):
        validate_probability(win_probability)

        session_id = str(uuid.uuid4())
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO betting_sessions
                (session_id, gambler_id, strategy_name, win_probability, status)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (session_id, gambler_id, strategy_name, win_probability, "ACTIVE"),
            )
            conn.commit()
            return self.get_session_summary(session_id)
        finally:
            conn.close()

    def end_session(self, session_id):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "UPDATE betting_sessions SET status=%s, ended_at=NOW() WHERE session_id=%s",
                ("ENDED", session_id),
            )
            conn.commit()
            return self.get_session_summary(session_id)
        finally:
            conn.close()

    def get_session_summary(self, session_id):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT session_id, gambler_id, strategy_name, win_probability,
                       started_at, ended_at, total_bets, wins, losses, profit
                FROM betting_sessions
                WHERE session_id=%s
                """,
                (session_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("Session not found")

            cursor.execute("SELECT bet_id FROM bets WHERE session_id=%s ORDER BY created_at", (session_id,))
            bet_rows = cursor.fetchall()
            bet_ids = [r["bet_id"] for r in bet_rows]

            session = BettingSession(
                session_id=row["session_id"],
                gambler_id=row["gambler_id"],
                strategy_name=row["strategy_name"],
                win_probability=row["win_probability"],
                started_at=row["started_at"],
                ended_at=row["ended_at"],
                total_bets=row["total_bets"],
                wins=row["wins"],
                losses=row["losses"],
                profit=float(row["profit"]),
                bet_ids=bet_ids,
            )
            return session.to_dict()
        finally:
            conn.close()

    def _get_bet_context(self, gambler_id):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT gp.current_stake, bp.min_bet, bp.max_bet
                FROM gambler_profile gp
                JOIN betting_preferences bp ON bp.gambler_id = gp.id
                WHERE gp.id=%s
                """,
                (gambler_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("Gambler or betting preferences not found")
            return {
                "current_stake": float(row["current_stake"]),
                "min_bet": float(row["min_bet"]),
                "max_bet": float(row["max_bet"]),
            }
        finally:
            conn.close()

    @staticmethod
    def _validate_bet_amount(amount, context):
        if amount < context["min_bet"]:
            raise ValueError("Bet amount is below configured minimum")
        if amount > context["max_bet"]:
            raise ValueError("Bet amount exceeds configured maximum")
        if amount > context["current_stake"]:
            raise ValueError("Bet amount cannot exceed current stake")

    @staticmethod
    def _default_odds_multiplier(win_probability):
        if win_probability == 0:
            return 2.0
        return max(1.01, round(1.0 / win_probability, 4))

    def get_win_loss_analysis(self, gambler_id, session_id=None, limit=500):
        return self.win_loss_calculator.analyze_history(gambler_id, session_id=session_id, limit=limit).to_dict()

    def _persist_bet(self, bet):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO bets
                (bet_id, gambler_id, session_id, strategy_name, amount, win_probability,
                 odds_multiplier, potential_win, stake_before, stake_after, is_win)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    bet.bet_id,
                    bet.gambler_id,
                    bet.session_id,
                    bet.strategy_name,
                    bet.amount,
                    bet.win_probability,
                    bet.odds_multiplier,
                    bet.potential_win,
                    bet.stake_before,
                    bet.stake_after,
                    bet.is_win,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def _update_statistics(self, gambler_id, bet):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE gambler_statistics
                SET total_bets = total_bets + 1,
                    wins = wins + %s,
                    losses = losses + %s,
                    net_profit = net_profit + %s
                WHERE gambler_id = %s
                """,
                (1 if bet.is_win else 0, 0 if bet.is_win else 1, bet.net_change, gambler_id),
            )
            conn.commit()
        finally:
            conn.close()

    def _update_session_totals(self, session_id, bet):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE betting_sessions
                SET total_bets = total_bets + 1,
                    wins = wins + %s,
                    losses = losses + %s,
                    profit = profit + %s
                WHERE session_id = %s
                """,
                (1 if bet.is_win else 0, 0 if bet.is_win else 1, bet.net_change, session_id),
            )
            conn.commit()
        finally:
            conn.close()
