import mysql.connector
from mysql.connector import Error

def create_database(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS crypto_data")
        connection.commit()  # Ensure database creation is committed
        print("Database created successfully")
    except Error as e:
        print(f"Error creating database: {e}")

def create_table(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()  # Ensure table creation is committed
        print("Table created successfully")
    except Error as e:
        print(f"Error creating table: {e}")

def delete_table(connection, table_name):
    cursor = connection.cursor()
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        connection.commit()  # Ensure table deletion is committed
        print(f"Table {table_name} deleted successfully")
    except Error as e:
        print(f"Error deleting table {table_name}: {e}")

def main():
    db_connection = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="admin0000",
        use_pure=True  # Sometimes necessary to avoid bugs in certain MySQL connector versions
    )
    create_database(db_connection)

    # Reconnect to the specific database to ensure all operations are targeting the correct DB
    db_connection = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="admin0000",
        database="crypto_data",
        use_pure=True
    )

    # Create tables
    raw_data_table = """
    CREATE TABLE IF NOT EXISTS raw_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        data_identifier VARCHAR(255),
        ticker VARCHAR(255),
        frequency VARCHAR(50),
        period VARCHAR(255),
        time_interval VARCHAR(255),  # Renamed to avoid conflict with SQL reserved keywords
        fetch_date DATETIME,
        data_start_date DATETIME,
        data_end_date DATETIME,
        data_duration VARCHAR(255),
        data_size_mb FLOAT
    );
    """

    prices_table = """
    CREATE TABLE IF NOT EXISTS prices (
        id INT AUTO_INCREMENT PRIMARY KEY,
        raw_data_id INT,
        data_identifier VARCHAR(255),
        date DATETIME,
        open FLOAT,
        high FLOAT,
        low FLOAT,
        close FLOAT,
        adj_close FLOAT,
        volume BIGINT,
        FOREIGN KEY (raw_data_id) REFERENCES raw_data (id)
    );
    """

    analytics_table = """
    CREATE TABLE IF NOT EXISTS analytics (
        id INT AUTO_INCREMENT PRIMARY KEY,
        raw_data_id INT,
        data_identifier VARCHAR(255),
        ticker VARCHAR(255),
        period VARCHAR(255),
        frequency VARCHAR(50),
        metric VARCHAR(255),
        value_type VARCHAR(255),
        value FLOAT,
        calculation_date DATETIME,
        FOREIGN KEY (raw_data_id) REFERENCES raw_data (id)
    );
    """

    logs_table = """
    CREATE TABLE IF NOT EXISTS logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        raw_data_id INT,
        log_date DATETIME,
        log_class VARCHAR(255),
        log_method VARCHAR(255),
        log_level VARCHAR(50),
        message TEXT,
        FOREIGN KEY (raw_data_id) REFERENCES raw_data (id)
    );
    """
    
    # Create tables
    #create_table(db_connection, raw_data_table)
    #create_table(db_connection, prices_table)
    #create_table(db_connection, logs_table)
    create_table(db_connection, analytics_table)

    

    # Interactive deletion
    while True:
        table_to_delete = input("Enter table name to delete or type 'exit' to finish: ")
        if table_to_delete.lower() == 'exit':
            break
        delete_table(db_connection, table_to_delete)

    db_connection.close()

if __name__ == "__main__":
    main()


