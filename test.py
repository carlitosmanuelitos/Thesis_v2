import mysql.connector
from mysql.connector import Error

def test_mysql_connection(host_name, user_name, password, port_number):
    try:
        # Attempt to connect to the database
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            port=port_number,
            passwd=password
        )
        if connection.is_connected():
            db_Info = connection.get_server_info()
            print("Connected to MySQL Server version ", db_Info)
            cursor = connection.cursor()
            cursor.execute("SELECT database();")
            record = cursor.fetchone()
            print("You're connected to database: ", record)
        # Close the connection
        connection.close()
    except Error as e:
        print("Error while connecting to MySQL", e)

# Replace 'your_password' with your database password, if any
# Since we're testing the connection, no password is used in this example.
# Please ensure that you handle your database password securely.

hostname = '127.0.0.1'
username = 'root'
port = 3306
password = 'admin0000'

test_mysql_connection(hostname, username, password, port)
