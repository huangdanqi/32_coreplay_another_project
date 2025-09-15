import mysql.connector

def get_emotion_data(
    host="127.0.0.1",
    port=3306,
    user="root",
    password="h05010501",
    database="page_test"
):
    """
    Connects to the MySQL database and fetches all rows from the emotion table.
    Returns a list of dictionaries.
    """
    conn = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM emotion;")
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows
