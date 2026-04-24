import random

from config.db import get_connection
from models.win_loss_models import (
    GameResult,
    OddsConfiguration,
    OddsType,
    OutcomeStrategyType,
    RunningTotals,
    WinLossAnalysis,
    WinLossStatistics,
)
from utils.validator import validate_positive_amount, validate_probability


class WinLossCalculator:
    def determine_outcome(self, win_probability, strategy=OutcomeStrategyType.RANDOM, house_edge=0.0):
        validate_probability(win_probability)

        if isinstance(strategy, str):
            strategy = OutcomeStrategyType[strategy.upper()]

        probability = win_probability
        if strategy == OutcomeStrategyType.WEIGHTED:
            probability = max(0.0, min(1.0, win_probability - house_edge))

        return random.random() <= probability

    def calculate_odds_multiplier(self, odds_config, win_probability):
        validate_probability(win_probability)

        if odds_config.odds_type == OddsType.FIXED:
            return odds_config.value

        if odds_config.odds_type == OddsType.PROBABILITY_BASED:
            return max(1.01, round(1.0 / max(win_probability, 0.01), 4))

        if odds_config.odds_type == OddsType.DECIMAL:
            return max(1.01, odds_config.value)

        if odds_config.odds_type == OddsType.AMERICAN:
            american = odds_config.value
            if american >= 100:
                return 1.0 + (american / 100.0)
            if american <= -100:
                return 1.0 + (100.0 / abs(american))
            raise ValueError("American odds must be >= 100 or <= -100")

        raise ValueError("Unsupported odds type")

    def calculate_winnings(self, amount, odds_config, win_probability):
        validate_positive_amount(amount, "amount")
        multiplier = self.calculate_odds_multiplier(odds_config, win_probability)
        return amount * multiplier, multiplier

    def create_game_result(self, bet_row):
        amount = float(bet_row["amount"])
        multiplier = float(bet_row["odds_multiplier"])
        is_win = bool(bet_row["is_win"])

        winnings = amount * multiplier if is_win else 0.0
        losses = amount if not is_win else 0.0

        return GameResult(
            bet_id=bet_row["bet_id"],
            amount=amount,
            is_win=is_win,
            stake_before=float(bet_row["stake_before"]),
            stake_after=float(bet_row["stake_after"]),
            odds_multiplier=multiplier,
            winnings=winnings,
            losses=losses,
        )

    def analyze_results(self, game_results):
        if not game_results:
            running = RunningTotals(0, 0, 0, 0, 0.0, 0.0, 0.0, [], [])
            stats = WinLossStatistics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0)
            return WinLossAnalysis(running, stats, [])

        wins = sum(1 for r in game_results if r.is_win)
        losses = sum(1 for r in game_results if not r.is_win)
        pushes = 0

        total_winnings = sum(r.winnings for r in game_results)
        total_losses = sum(r.losses for r in game_results)
        net_profit = sum(r.net_change for r in game_results)
        total_staked = sum(r.amount for r in game_results)

        balance_history = [r.stake_after for r in game_results]
        progression = []
        running_profit = 0.0
        for r in game_results:
            running_profit += r.net_change
            progression.append(running_profit)

        running_totals = RunningTotals(
            total_games=len(game_results),
            wins=wins,
            losses=losses,
            pushes=pushes,
            total_winnings=total_winnings,
            total_losses=total_losses,
            net_profit=net_profit,
            balance_history=balance_history,
            profit_progression=progression,
        )

        current_win, current_loss, longest_win, longest_loss = self._streaks(game_results)

        avg_win = (total_winnings / wins) if wins else 0.0
        avg_loss = (total_losses / losses) if losses else 0.0

        stats = WinLossStatistics(
            win_rate=wins / len(game_results),
            loss_rate=losses / len(game_results),
            win_loss_ratio=(wins / losses) if losses else float(wins),
            average_win=avg_win,
            average_loss=avg_loss,
            largest_win=max((r.winnings for r in game_results), default=0.0),
            largest_loss=max((r.losses for r in game_results), default=0.0),
            profit_factor=(total_winnings / total_losses) if total_losses else float(total_winnings),
            roi=(net_profit / total_staked) if total_staked else 0.0,
            return_on_risk=(net_profit / total_losses) if total_losses else float(net_profit),
            current_win_streak=current_win,
            current_loss_streak=current_loss,
            longest_win_streak=longest_win,
            longest_loss_streak=longest_loss,
        )

        return WinLossAnalysis(running_totals, stats, game_results)

    def analyze_history(self, gambler_id, session_id=None, limit=500):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            query = """
                SELECT bet_id, amount, odds_multiplier, is_win, stake_before, stake_after
                FROM bets
                WHERE gambler_id=%s
            """
            params = [gambler_id]

            if session_id:
                query += " AND session_id=%s"
                params.append(session_id)

            query += " ORDER BY created_at, bet_id LIMIT %s"
            params.append(limit)

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            results = [self.create_game_result(r) for r in rows]
            return self.analyze_results(results)
        finally:
            conn.close()

    @staticmethod
    def _streaks(game_results):
        longest_win = 0
        longest_loss = 0
        current_run = 0
        current_type = None

        for r in game_results:
            r_type = "WIN" if r.is_win else "LOSS"
            if r_type == current_type:
                current_run += 1
            else:
                current_type = r_type
                current_run = 1

            if r_type == "WIN":
                longest_win = max(longest_win, current_run)
            else:
                longest_loss = max(longest_loss, current_run)

        current_win = current_run if current_type == "WIN" else 0
        current_loss = current_run if current_type == "LOSS" else 0
        return current_win, current_loss, longest_win, longest_loss


def build_odds_configuration(odds_type=None, odds_value=None, fallback_multiplier=None):
    if fallback_multiplier is not None:
        return OddsConfiguration(OddsType.FIXED, float(fallback_multiplier))

    if not odds_type:
        return OddsConfiguration(OddsType.PROBABILITY_BASED, 0.0)

    normalized = odds_type.upper()
    if normalized not in OddsType.__members__:
        raise ValueError("Invalid odds type")

    selected = OddsType[normalized]
    value = float(odds_value) if odds_value is not None else 0.0

    if selected in {OddsType.FIXED, OddsType.DECIMAL} and value <= 0:
        raise ValueError("Odds value must be positive for selected odds type")
    if selected == OddsType.AMERICAN and value == 0:
        raise ValueError("American odds value must be non-zero")

    return OddsConfiguration(selected, value)
