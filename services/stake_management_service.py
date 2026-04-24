from collections import Counter

from config.db import get_connection
from models.stake_boundary import StakeBoundary
from models.stake_history_report import StakeHistoryReport
from models.stake_manager import StakeManager
from models.stake_monitor import StakeMonitor
from models.stake_transaction import TransactionType
from utils.logger import logger
from utils.validator import (
    validate_balance_transition,
    validate_boundaries,
    validate_positive_amount,
)


class StakeManagementService:
    def initialize_stake(self, gambler_id, initial_stake, lower_limit, upper_limit):
        validate_positive_amount(initial_stake, "initial_stake")
        validate_boundaries(lower_limit, upper_limit)

        boundary = StakeBoundary(lower_limit, upper_limit)
        if boundary.status_for(initial_stake) in {"OUT_LOW", "OUT_HIGH"}:
            raise ValueError("Initial stake must be within boundary limits")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT current_stake FROM gambler_profile WHERE id=%s FOR UPDATE",
                (gambler_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("Gambler not found")

            cursor.execute(
                "UPDATE gambler_profile SET current_stake=%s WHERE id=%s",
                (initial_stake, gambler_id),
            )
            self._record_transaction(
                cursor,
                gambler_id,
                TransactionType.INITIAL_STAKE,
                initial_stake,
                0.0,
                initial_stake,
                note="Stake initialized",
            )

            conn.commit()
            logger.info(f"Stake initialized for gambler: {gambler_id}")
            return {
                "gambler_id": gambler_id,
                "current_stake": initial_stake,
                "boundary_status": boundary.status_for(initial_stake),
            }
        except Exception as e:
            conn.rollback()
            logger.error(f"Stake initialization failed: {e}")
            raise
        finally:
            conn.close()

    def track_current_stake(self, gambler_id):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT current_stake, loss_threshold, win_threshold FROM gambler_profile WHERE id=%s",
                (gambler_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("Gambler not found")

            boundary = StakeBoundary(row["loss_threshold"], row["win_threshold"])
            manager = StakeManager(row["loss_threshold"], row["win_threshold"])
            boundary_state = manager.validate(row["current_stake"])
            return {
                "gambler_id": gambler_id,
                "current_stake": row["current_stake"],
                "boundary_status": boundary.status_for(row["current_stake"]),
                "boundary_details": boundary_state,
            }
        finally:
            conn.close()

    def process_bet_outcome(self, gambler_id, bet_amount, is_win, payout_multiplier=2.0, bet_id=None):
        validate_positive_amount(bet_amount, "bet_amount")
        validate_positive_amount(payout_multiplier, "payout_multiplier")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT current_stake, loss_threshold, win_threshold FROM gambler_profile WHERE id=%s FOR UPDATE",
                (gambler_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("Gambler not found")

            balance_before = float(row["current_stake"])
            if bet_amount > balance_before:
                raise ValueError("Bet amount cannot exceed current stake")

            after_bet = validate_balance_transition(balance_before, -bet_amount)
            self._record_transaction(
                cursor,
                gambler_id,
                TransactionType.BET_PLACED,
                -bet_amount,
                balance_before,
                after_bet,
                bet_id=bet_id,
                note="Bet placed",
            )

            balance_after = after_bet
            outcome_type = TransactionType.BET_LOSS
            if is_win:
                winnings = bet_amount * payout_multiplier
                balance_after = validate_balance_transition(after_bet, winnings)
                outcome_type = TransactionType.BET_WIN
                self._record_transaction(
                    cursor,
                    gambler_id,
                    outcome_type,
                    winnings,
                    after_bet,
                    balance_after,
                    bet_id=bet_id,
                    note="Bet settled as win",
                )
            else:
                self._record_transaction(
                    cursor,
                    gambler_id,
                    outcome_type,
                    0.0,
                    after_bet,
                    balance_after,
                    bet_id=bet_id,
                    note="Bet settled as loss",
                )

            cursor.execute(
                "UPDATE gambler_profile SET current_stake=%s WHERE id=%s",
                (balance_after, gambler_id),
            )

            boundary = StakeBoundary(row["loss_threshold"], row["win_threshold"])
            status = boundary.status_for(balance_after)

            conn.commit()
            logger.info(f"Bet processed for gambler: {gambler_id}")
            return {
                "gambler_id": gambler_id,
                "balance_before": balance_before,
                "balance_after": balance_after,
                "result": "WIN" if is_win else "LOSS",
                "boundary_status": status,
            }
        except Exception as e:
            conn.rollback()
            logger.error(f"Bet processing failed: {e}")
            raise
        finally:
            conn.close()

    def apply_funds_change(self, gambler_id, amount, change_type, note=None):
        if change_type not in {TransactionType.DEPOSIT, TransactionType.WITHDRAWAL, TransactionType.ADJUSTMENT}:
            raise ValueError("Invalid funds change type")

        if change_type in {TransactionType.DEPOSIT, TransactionType.WITHDRAWAL}:
            validate_positive_amount(amount, "amount")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT current_stake, loss_threshold, win_threshold FROM gambler_profile WHERE id=%s FOR UPDATE",
                (gambler_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("Gambler not found")

            balance_before = float(row["current_stake"])
            amount_delta = amount
            if change_type == TransactionType.WITHDRAWAL:
                amount_delta = -amount

            balance_after = validate_balance_transition(balance_before, amount_delta)
            cursor.execute(
                "UPDATE gambler_profile SET current_stake=%s WHERE id=%s",
                (balance_after, gambler_id),
            )
            self._record_transaction(
                cursor,
                gambler_id,
                change_type,
                amount_delta,
                balance_before,
                balance_after,
                note=note,
            )

            boundary = StakeBoundary(row["loss_threshold"], row["win_threshold"])

            conn.commit()
            logger.info(f"Funds updated for gambler: {gambler_id}")
            return {
                "gambler_id": gambler_id,
                "balance_before": balance_before,
                "balance_after": balance_after,
                "boundary_status": boundary.status_for(balance_after),
            }
        except Exception as e:
            conn.rollback()
            logger.error(f"Funds update failed: {e}")
            raise
        finally:
            conn.close()

    def monitor_stake_fluctuations(self, gambler_id):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT balance_after FROM stake_transactions WHERE gambler_id=%s ORDER BY created_at, id",
                (gambler_id,),
            )
            balances = [float(r["balance_after"]) for r in cursor.fetchall()]

            if not balances:
                cursor.execute(
                    "SELECT current_stake FROM gambler_profile WHERE id=%s",
                    (gambler_id,),
                )
                row = cursor.fetchone()
                if not row:
                    raise ValueError("Gambler not found")
                balances = [float(row["current_stake"])]

            cursor.execute(
                "SELECT loss_threshold, win_threshold FROM gambler_profile WHERE id=%s",
                (gambler_id,),
            )
            boundary_row = cursor.fetchone()
            if not boundary_row:
                raise ValueError("Gambler not found")

            manager = StakeManager(boundary_row["loss_threshold"], boundary_row["win_threshold"])
            monitor = manager.track(gambler_id, balances)
            return monitor.to_dict()
        finally:
            conn.close()

    def validate_stake_boundaries(self, gambler_id):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT current_stake, loss_threshold, win_threshold FROM gambler_profile WHERE id=%s",
                (gambler_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("Gambler not found")

            manager = StakeManager(row["loss_threshold"], row["win_threshold"])
            boundary = manager.validate(row["current_stake"])
            return {
                "gambler_id": gambler_id,
                "current_stake": row["current_stake"],
                **boundary,
            }
        finally:
            conn.close()

    def generate_stake_history_report(self, gambler_id, transaction_type=None, limit=200):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            query = """
                SELECT id, gambler_id, transaction_type, amount, balance_before, balance_after,
                       bet_id, note, created_at
                FROM stake_transactions
                WHERE gambler_id=%s
            """
            params = [gambler_id]

            if transaction_type:
                query += " AND transaction_type=%s"
                params.append(transaction_type)

            query += " ORDER BY created_at, id LIMIT %s"
            params.append(limit)

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            txns = [self._serialize_txn(row) for row in rows]

            if not txns:
                report = StakeHistoryReport(
                    gambler_id=gambler_id,
                    total_transactions=0,
                    opening_balance=0.0,
                    closing_balance=0.0,
                    net_change=0.0,
                    by_type={},
                    transactions=[],
                )
                return report.to_dict()

            type_counts = Counter(t["transaction_type"] for t in txns)
            report = StakeHistoryReport(
                gambler_id=gambler_id,
                total_transactions=len(txns),
                opening_balance=float(txns[0]["balance_before"]),
                closing_balance=float(txns[-1]["balance_after"]),
                net_change=float(txns[-1]["balance_after"] - txns[0]["balance_before"]),
                by_type=dict(type_counts),
                transactions=txns,
            )
            return report.to_dict()
        finally:
            conn.close()

    def reset_stake(self, gambler_id, initial_stake):
        validate_positive_amount(initial_stake, "initial_stake")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT current_stake FROM gambler_profile WHERE id=%s FOR UPDATE",
                (gambler_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("Gambler not found")

            before = float(row["current_stake"])
            cursor.execute(
                "UPDATE gambler_profile SET current_stake=%s WHERE id=%s",
                (initial_stake, gambler_id),
            )
            self._record_transaction(
                cursor,
                gambler_id,
                TransactionType.RESET,
                initial_stake - before,
                before,
                initial_stake,
                note="Stake reset to initial value",
            )

            conn.commit()
            logger.info(f"Stake reset for gambler: {gambler_id}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Stake reset failed: {e}")
            raise
        finally:
            conn.close()

    def _record_transaction(
        self,
        cursor,
        gambler_id,
        tx_type,
        amount,
        balance_before,
        balance_after,
        bet_id=None,
        note=None,
    ):
        tx_value = tx_type.value if hasattr(tx_type, "value") else str(tx_type)
        cursor.execute(
            """
            INSERT INTO stake_transactions
            (gambler_id, transaction_type, amount, balance_before, balance_after, bet_id, note)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                gambler_id,
                tx_value,
                amount,
                balance_before,
                balance_after,
                bet_id,
                note,
            ),
        )

    @staticmethod
    def _serialize_txn(row):
        created_at = row["created_at"].isoformat() if row.get("created_at") else None
        return {
            "id": row["id"],
            "gambler_id": row["gambler_id"],
            "transaction_type": row["transaction_type"],
            "amount": float(row["amount"]),
            "balance_before": float(row["balance_before"]),
            "balance_after": float(row["balance_after"]),
            "bet_id": row["bet_id"],
            "note": row["note"],
            "created_at": created_at,
        }
