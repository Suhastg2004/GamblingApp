from config.db import get_connection
from services.betting_service import BettingService
from services.game_session_manager import GameSessionManager
from models.game_session import SessionEndReason
from models.stake_transaction import TransactionType
from services.stake_management_service import StakeManagementService
from utils.validator import validate_stake, validate_thresholds, validate_bets
from utils.logger import logger

class GamblerProfileService:
    def __init__(self):
        self.stake_service = StakeManagementService()
        self.betting_service = BettingService(self.stake_service)
        self.game_session_manager = GameSessionManager(self.betting_service, self.stake_service)
    
    def create_gambler(self, name, initial_stake, win_th, loss_th, min_bet, max_bet, strategy, session_limit):
        try:
            validate_stake(initial_stake)
            validate_thresholds(initial_stake, win_th, loss_th)
            validate_bets(min_bet, max_bet)

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
            INSERT INTO gambler_profile (name, initial_stake, current_stake, win_threshold, loss_threshold, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, initial_stake, initial_stake, win_th, loss_th, True))

            gid = cursor.lastrowid

            cursor.execute("""
            INSERT INTO betting_preferences (gambler_id, min_bet, max_bet, strategy, session_limit)
            VALUES (%s, %s, %s, %s, %s)
            """, (gid, min_bet, max_bet, strategy, session_limit))

            cursor.execute("""
            INSERT INTO gambler_statistics (gambler_id, total_bets, wins, losses, net_profit)
            VALUES (%s, 0, 0, 0, 0)
            """, (gid,))

            cursor.execute("""
            INSERT INTO stake_transactions
            (gambler_id, transaction_type, amount, balance_before, balance_after, note)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (gid, TransactionType.INITIAL_STAKE.value, initial_stake, 0.0, initial_stake, "Stake initialized"))

            conn.commit()
            conn.close()

            logger.info(f"Gambler created: {gid}")
            return gid

        except Exception as e:
            logger.error(f"Create failed: {e}")
            raise

    def get_gambler(self, gid):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM gambler_profile WHERE id=%s", (gid,))
            profile = cursor.fetchone()

            cursor.execute("SELECT * FROM betting_preferences WHERE gambler_id=%s", (gid,))
            pref = cursor.fetchone()

            cursor.execute("SELECT * FROM gambler_statistics WHERE gambler_id=%s", (gid,))
            stats = cursor.fetchone()

            conn.close()

            logger.info(f"Gambler retrieved: {gid}")

            return {
                "profile": profile,
                "preferences": pref,
                "statistics": stats
            }

        except Exception as e:
            logger.error(f"Retrieve failed: {e}")
            raise

    def update_gambler(self, gid, name=None, win_th=None, loss_th=None):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            if name:
                cursor.execute("UPDATE gambler_profile SET name=%s WHERE id=%s", (name, gid))

            if win_th and loss_th:
                cursor.execute("UPDATE gambler_profile SET win_threshold=%s, loss_threshold=%s WHERE id=%s",
                               (win_th, loss_th, gid))

            conn.commit()
            conn.close()

            logger.info(f"Gambler updated: {gid}")

        except Exception as e:
            logger.error(f"Update failed: {e}")
            raise

    def validate_gambler(self, gid):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM gambler_profile WHERE id=%s", (gid,))
            g = cursor.fetchone()
            conn.close()

            if not g:
                return False

            if not g["is_active"]:
                return False

            if not (g["loss_threshold"] < g["current_stake"] < g["win_threshold"]):
                return False

            return True

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise

    def reset_gambler(self, gid):
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT initial_stake FROM gambler_profile WHERE id=%s", (gid,))
            row = cursor.fetchone()
            if not row:
                raise ValueError("Gambler not found")
            i = row["initial_stake"]

            cursor.execute("""
            UPDATE gambler_statistics 
            SET total_bets=0, wins=0, losses=0, net_profit=0 
            WHERE gambler_id=%s
            """, (gid,))

            conn.commit()
            conn.close()

            self.stake_service.reset_stake(gid, i)

            logger.info(f"Gambler reset: {gid}")

        except Exception as e:
            logger.error(f"Reset failed: {e}")
            raise

    def get_stake_status(self, gid):
        return self.stake_service.track_current_stake(gid)

    def process_bet(self, gid, bet_amount, is_win, payout_multiplier=2.0, bet_id=None):
        return self.stake_service.process_bet_outcome(gid, bet_amount, is_win, payout_multiplier, bet_id)

    def deposit(self, gid, amount, note=None):
        return self.stake_service.apply_funds_change(gid, amount, TransactionType.DEPOSIT, note)

    def withdraw(self, gid, amount, note=None):
        return self.stake_service.apply_funds_change(gid, amount, TransactionType.WITHDRAWAL, note)

    def adjust_stake(self, gid, amount_delta, note=None):
        return self.stake_service.apply_funds_change(gid, amount_delta, TransactionType.ADJUSTMENT, note)

    def get_stake_monitor(self, gid):
        return self.stake_service.monitor_stake_fluctuations(gid)

    def validate_stake_boundaries(self, gid):
        return self.stake_service.validate_stake_boundaries(gid)

    def get_stake_history_report(self, gid, transaction_type=None, limit=200):
        return self.stake_service.generate_stake_history_report(gid, transaction_type, limit)

    def place_single_bet(
        self,
        gid,
        amount,
        win_probability,
        odds_multiplier=None,
        outcome_strategy="RANDOM",
        house_edge=0.0,
        odds_type=None,
        odds_value=None,
    ):
        return self.betting_service.place_bet(
            gid,
            amount,
            win_probability,
            odds_multiplier=odds_multiplier,
            outcome_strategy=outcome_strategy,
            house_edge=house_edge,
            odds_type=odds_type,
            odds_value=odds_value,
        )

    def place_strategy_bets(
        self,
        gid,
        strategy_name,
        win_probability,
        rounds,
        base_bet,
        odds_multiplier=None,
        percentage=0.05,
        step=1.0,
        stop_on_boundary=True,
    ):
        return self.betting_service.place_consecutive_bets(
            gambler_id=gid,
            strategy_name=strategy_name,
            win_probability=win_probability,
            rounds=rounds,
            base_bet=base_bet,
            odds_multiplier=odds_multiplier,
            percentage=percentage,
            step=step,
            stop_on_boundary=stop_on_boundary,
        )

    def get_betting_session_summary(self, session_id):
        return self.betting_service.get_session_summary(session_id)

    def get_win_loss_analysis(self, gid, session_id=None, limit=500):
        return self.betting_service.get_win_loss_analysis(gid, session_id=session_id, limit=limit)

    def start_game_session(
        self,
        gid,
        lower_limit,
        upper_limit,
        min_bet,
        max_bet,
        max_games,
        max_duration_seconds,
        default_win_probability,
    ):
        return self.game_session_manager.start_new_session(
            gid,
            lower_limit,
            upper_limit,
            min_bet,
            max_bet,
            max_games,
            max_duration_seconds,
            default_win_probability,
        )

    def continue_game_session(self, session_id, rounds, bet_amount=None, win_probability=None, odds_multiplier=None):
        return self.game_session_manager.continue_session(
            session_id,
            rounds,
            bet_amount=bet_amount,
            win_probability=win_probability,
            odds_multiplier=odds_multiplier,
        )

    def pause_game_session(self, session_id, reason="User requested pause"):
        return self.game_session_manager.pause_session(session_id, reason)

    def resume_game_session(self, session_id):
        return self.game_session_manager.resume_session(session_id)

    def end_game_session(self, session_id, reason="MANUAL"):
        reason_map = {
            "MANUAL": SessionEndReason.MANUAL,
            "TIMEOUT": SessionEndReason.TIMEOUT,
            "UPPER_LIMIT_REACHED": SessionEndReason.UPPER_LIMIT_REACHED,
            "LOWER_LIMIT_REACHED": SessionEndReason.LOWER_LIMIT_REACHED,
            "MAX_GAMES_REACHED": SessionEndReason.MAX_GAMES_REACHED,
        }
        selected = reason_map.get(reason.upper())
        if not selected:
            raise ValueError("Invalid end reason")
        return self.game_session_manager.end_session(session_id, selected)

    def get_game_session(self, session_id):
        return self.game_session_manager.get_session(session_id)

    def list_active_game_sessions(self):
        return self.game_session_manager.list_active_sessions()