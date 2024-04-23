import mysql.connector
from mysql.connector import Error
import pandas as pd
import yfinance as yf
from datetime import datetime
import logging

"""
This script, data_fetcher_v3.py, is designed to fetch and manage cryptocurrency data using the Yahoo Finance API.
It logs detailed operational data to a MySQL database, and stores both metadata and time-series data in structured formats.
Dependencies include yfinance, mysql-connector-python, and pandas.

Features:
- Fetches cryptocurrency data based on configuration settings.
- Normalizes and stores time-series data in a MySQL database.
- Logs all operations with detailed metadata linking logs to data entries.

Usage:
Configure the MySQL database parameters and run the script to start fetching data as configured in the `config_fetcher` dictionary.
"""

def mysql_connect():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="admin0000",
        database="crypto_data"
    )

class MySQLLogHandler(logging.Handler):
    """
    Fetches cryptocurrency data from Yahoo Finance and stores it in a MySQL database along with operational logs.

    Attributes:
        config (dict): Configuration dictionary specifying tickers and their respective fetch intervals and periods.

    Methods:
        fetch_data: Retrieves data from Yahoo Finance for a specified ticker, interval, and period.
        save_data: Stores fetched data in the MySQL database and logs operations.
        run: Executes the data fetching and saving process for all configured tickers and intervals.
        close: Closes the database connection.
    """
    def __init__(self, db_connection):
        super().__init__()
        self.db_connection = db_connection

    def emit(self, record):
        log_message = self.format(record)
        cursor = self.db_connection.cursor()
        # Properly handle record.args
        raw_data_id = None
        if record.args:
            if isinstance(record.args, (list, tuple)) and len(record.args) > 0:
                raw_data_id = record.args[0] if isinstance(record.args[0], int) else None
            elif isinstance(record.args, dict):
                raw_data_id = record.args.get('raw_data_id')

        try:
            cursor.execute(
                "INSERT INTO logs (raw_data_id, log_date, log_class, log_method, log_level, message) VALUES (%s, NOW(), %s, %s, %s, %s)",
                (raw_data_id, record.name, record.funcName, record.levelname, log_message)
            )
            self.db_connection.commit()
        except Error as e:
            print(f"Failed to log to database: {e}")
        finally:
            cursor.close()


# Custom logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
db_connection = mysql_connect()
logger.addHandler(MySQLLogHandler(db_connection))

class CryptoDataFetcher:
    def __init__(self, config):
        self.config = config
        self.connection = mysql_connect()
        logger.info("CryptoDataFetcher initialized with config: %s", config)

    def fetch_data(self, ticker, period, interval):
        logger.info("Starting data retrieval for %s, period %s, interval %s", ticker, period, interval)
        data = yf.download(ticker, period=period, interval=interval)
        data.reset_index(inplace=True)
        if 'Datetime' in data.columns:
            data.rename(columns={'Datetime': 'Date'}, inplace=True)
        return data

    def save_data(self, data, ticker, period, interval):
        if data.empty:
            logger.warning("No data retrieved for %s", ticker)
            return
        data_identifier = f"{ticker.replace('-USD', '')}_{period}_{interval}_{datetime.now().strftime('%Y%m%d')}"
        cursor = self.connection.cursor()

        # Check data freshness
        cursor.execute("SELECT id FROM raw_data WHERE data_identifier = %s", (data_identifier,))
        existing_entry = cursor.fetchone()
        if existing_entry:
            logger.info("Data already exists for identifier %s with ID %s", data_identifier, existing_entry[0])
            return

        # Data preparation
        fetch_date = datetime.now()
        data_start_date = data['Date'].min()
        data_end_date = data['Date'].max()
        data_duration = str(data_end_date - data_start_date)
        data_size_mb = (data.to_csv(index=False).encode('utf-8').__sizeof__() / 1024 ** 2)

        # Metadata insertion
        try:
            cursor.execute(
                "INSERT INTO raw_data (data_identifier, ticker, frequency, period, time_interval, fetch_date, data_start_date, data_end_date, data_duration, data_size_mb) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (data_identifier, ticker, 'Hourly' if '1h' in interval else 'Daily', period, interval, fetch_date, data_start_date, data_end_date, data_duration, data_size_mb)
            )
            raw_data_id = cursor.lastrowid
            self.connection.commit()
            logger.info("Metadata saved with ID %d", raw_data_id)
        except Error as e:
            logger.error("Failed to save metadata for %s: %s", ticker, e)
            return

        # Prices data insertion
        for _, row in data.iterrows():
            try:
                cursor.execute(
                    "INSERT INTO prices (raw_data_id, data_identifier, date, open, high, low, close, adj_close, volume) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (raw_data_id, data_identifier, row['Date'], row['Open'], row['High'], row['Low'], row['Close'], row['Adj Close'], row['Volume'])
                )
                self.connection.commit()
            except Error as e:
                logger.error("Failed to insert price data for %s: %s", ticker, e)

        cursor.close()

    def run(self):
        for ticker in self.config['tickers']:
            for period, interval in self.config['combinations']:
                data = self.fetch_data(ticker, period, interval)
                self.save_data(data, ticker, period, interval)

    def close(self):
        if self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed.")

# Configuration for data fetching
config_fetcher = {
  "tickers": ["XRP-USD"],
  "combinations": [
    ('max', '1d'), 
    ('10y', '1d'), 
    ('5y', '1d'), 
    ('1y', '1d'), 
    ('1y', '1h'), 
    ('6mo', '1h'), 
    ('3mo', '1h')
  ]
}

if __name__ == '__main__':
    fetcher = CryptoDataFetcher(config_fetcher)
    try:
        fetcher.run()
    finally:
        fetcher.close()
        db_connection.close()
