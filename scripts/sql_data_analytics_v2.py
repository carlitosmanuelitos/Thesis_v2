
import os
import logging
import pandas as pd
from datetime import datetime
import mysql.connector
from mysql.connector import Error

def mysql_connect():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="admin0000",
        database="crypto_data"
    )

class MySQLLogHandler(logging.Handler):
    def __init__(self, db_connection):
        super().__init__()
        self.db_connection = db_connection
    def emit(self, record):
        log_message = self.format(record)
        cursor = self.db_connection.cursor()
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

class CryptoAnalytics:
    def __init__(self, config):
        self.config = config
        self.connection = mysql_connect()
        logging.info("CryptoAnalytics class initialized with configuration.")
    
    def load_data(self, ticker, period, interval):
        """ Load data from SQL based on provided ticker, period, and interval. """
        frequency = 'Hourly' if '1h' in interval else 'Daily'
        cursor = self.connection.cursor()
        query = """
        SELECT date, open, high, low, close, adj_close, volume FROM prices
        INNER JOIN raw_data ON prices.raw_data_id = raw_data.id
        WHERE raw_data.ticker = %s AND raw_data.period = %s AND raw_data.frequency = %s
        ORDER BY date
        """
        cursor.execute(query, (ticker, period, frequency))
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume'])
        df.set_index('date', inplace=True)
        cursor.close()
        return df if not df.empty else None
    
    def calculate_analytics(self, df):
        """ Calculate weekly, monthly, and yearly analytics. """
        if df is None:
            return None, None, None
        df.index = pd.to_datetime(df.index)
        weekly = df.resample('W').agg({
            'close': ['mean', 'max', 'min', 'last'],
            'open': 'first',
            'volume': 'sum'
        })
        monthly = df.resample('M').agg({
            'close': ['mean', 'max', 'min', 'last'],
            'open': 'first',
            'volume': 'sum'
        })
        yearly = df.resample('Y').agg({
            'close': ['mean', 'max', 'min', 'last'],
            'open': 'first',
            'volume': 'sum'
        })
        return self.flatten_columns(weekly), self.flatten_columns(monthly), self.flatten_columns(yearly)
    
    def flatten_columns(self, resampled_df):
        """ Flatten the multi-level columns after resampling. """
        resampled_df.columns = ['_'.join(col).strip() for col in resampled_df.columns.values]
        print("Flattened columns:", resampled_df.columns)  # Debug print to check column names
        return resampled_df
    
    def save_analytics(self, weekly, monthly, yearly, ticker, period, interval):
        """ Save analytics data to SQL. """
        data_identifier = f"{ticker.replace('-USD', '')}_{period}_{interval}_{datetime.now().strftime('%Y%m%d')}"
        self.store_results(weekly, 'Weekly', ticker, period, interval, data_identifier)
        self.store_results(monthly, 'Monthly', ticker, period, interval, data_identifier)
        self.store_results(yearly, 'Yearly', ticker, period, interval, data_identifier)
    
    def store_results(self, results_df, metric, ticker, period, interval, data_identifier):
        """ Store analytics results into the SQL database. """
        cursor = self.connection.cursor()
        calculation_date = datetime.now()
        if results_df is not None:
            for column_name in results_df.columns:
                series = results_df[column_name]
                for index, value in series.items():  # Correctly use .items() for Series
                    cursor.execute(
                        "INSERT INTO analytics (data_identifier, ticker, period, frequency, metric, value_type, value, calculation_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (data_identifier, ticker, period, 'Hourly' if '1h' in interval else 'Daily', metric, column_name, float(value), calculation_date)
                    )
                    self.connection.commit()
        cursor.close()

    def run_analytics(self):
        logging.info("Starting the analytics process for all configured tickers and timeframes.")
        for ticker in self.config['tickers']:
            for period, interval in self.config['combinations']:
                df = self.load_data(ticker, period, interval)
                if df is not None:
                    weekly, monthly, yearly = self.calculate_analytics(df)
                    self.save_analytics(weekly, monthly, yearly, ticker, period, interval)
                else:
                    logging.warning(f"No data available for analysis for {ticker}, {period}, {interval}.")
    def close(self):
        if self.connection.is_connected():
            self.connection.close()
            logging.info("Database connection closed.")


# Configuration for data fetching
config_analytics = {
  "tickers": ["BTC-USD", "ETH-USD", "ADA-USD", "BNB-USD", "SOL-USD"],
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
    analytics = CryptoAnalytics(config_analytics)
    analytics.run_analytics()
    analytics.close()
