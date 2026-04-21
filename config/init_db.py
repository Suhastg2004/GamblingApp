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

    conn.commit()
    conn.close()