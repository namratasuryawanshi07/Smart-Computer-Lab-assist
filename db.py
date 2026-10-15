import mysql.connector

def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="smart_lab_asset"
    )
    return connection
