import mysql.connector
from config.settings import settings

def get_connection():
    return mysql.connector.connect(
        host = settings.db_host,
        user = settings.db_user,
        password = settings.db_password,
        database = settings.db_name
    )
    