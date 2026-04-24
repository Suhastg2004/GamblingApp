import mysql.connector
from config.settings import settings

def create_database():
    conn = mysql.connector.connect(
        host=settings.db_host,
        user=settings.db_user,
        password=settings.db_password
    )
    cursor = conn.cursor()

    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.db_name}")
    conn.close()

def create_tables():
    conn = mysql.connector.connect(
        host=settings.db_host,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name
    )
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gambler_profile (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100),
        initial_stake DOUBLE,
        current_stake DOUBLE,
        win_threshold DOUBLE,
        loss_threshold DOUBLE,
        is_active BOOLEAN
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS betting_preferences (
        id INT AUTO_INCREMENT PRIMARY KEY,
        gambler_id INT,
        min_bet DOUBLE,
        max_bet DOUBLE,
        strategy VARCHAR(50),
        session_limit INT,
        FOREIGN KEY (gambler_id) REFERENCES gambler_profile(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gambler_statistics (
        id INT AUTO_INCREMENT PRIMARY KEY,
        gambler_id INT,
        total_bets INT,
        wins INT,
        losses INT,
        net_profit DOUBLE,
        FOREIGN KEY (gambler_id) REFERENCES gambler_profile(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stake_transactions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        gambler_id INT NOT NULL,
        transaction_type VARCHAR(30) NOT NULL,
        amount DOUBLE NOT NULL,
        balance_before DOUBLE NOT NULL,
        balance_after DOUBLE NOT NULL,
        bet_id VARCHAR(64),
        note VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (gambler_id) REFERENCES gambler_profile(id)
    )
    """)

    cursor.execute(
        "SHOW INDEX FROM stake_transactions WHERE Key_name='idx_stake_transactions_gambler_id'"
    )
    if not cursor.fetchone():
        cursor.execute(
            "CREATE INDEX idx_stake_transactions_gambler_id ON stake_transactions(gambler_id)"
        )

    cursor.execute(
        "SHOW INDEX FROM stake_transactions WHERE Key_name='idx_stake_transactions_created_at'"
    )
    if not cursor.fetchone():
        cursor.execute(
            "CREATE INDEX idx_stake_transactions_created_at ON stake_transactions(created_at)"
        )

    conn.commit()
    conn.close()    