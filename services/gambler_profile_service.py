from config.db import get_connection
from utils.validator import validate_stake, validate_thresholds, validate_bets
from utils.logger import logger

class GamblerProfileService:
    
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
            cursor = conn.cursor()

            cursor.execute("SELECT initial_stake FROM gambler_profile WHERE id=%s", (gid,))
            i = cursor.fetchone()[0]

            cursor.execute("""
            UPDATE gambler_profile 
            SET current_stake=%s 
            WHERE id=%s
            """, (i, gid))

            cursor.execute("""
            UPDATE gambler_statistics 
            SET total_bets=0, wins=0, losses=0, net_profit=0 
            WHERE gambler_id=%s
            """, (gid,))

            conn.commit()
            conn.close()

            logger.info(f"Gambler reset: {gid}")

        except Exception as e:
            logger.error(f"Reset failed: {e}")
            raise