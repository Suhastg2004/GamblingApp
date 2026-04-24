from config.db import get_connection
from models.stake_transaction import TransactionType
from services.stake_management_service import StakeManagementService
from utils.validator import validate_stake, validate_thresholds, validate_bets
from utils.logger import logger

class GamblerProfileService:
    def __init__(self):
        self.stake_service = StakeManagementService()
    
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