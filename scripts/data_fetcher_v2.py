import os
import logging
import pandas as pd
from datetime import datetime
import yfinance as yf
from IPython.display import display, HTML

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CryptoDataFetcher:
    """
    A class to fetch and manage cryptocurrency data using the Yahoo Finance API.

    Attributes:
        config (dict): Configuration dictionary with tickers, periods, and intervals.

    Methods:
        fetch_data(ticker, period, interval): Fetches historical data for a given ticker.
        save_data(df, ticker, period, interval): Saves the fetched data to a CSV file.
        fetch_and_save(ticker, period, interval): Fetches and saves data if not fresh.
        ensure_directory(directory): Ensures the specified directory exists.
        build_filename(ticker, period, interval, date_str): Builds a filename for saving data.
        is_data_fresh(file_path): Checks if the data in the specified file is fresh.
        run_data_fetcher(): Manages the fetching process based on configuration and data freshness.
    """
    def __init__(self, config):
        self.config = config
        logging.info(f"Initializing CryptoDataFetcher with config: {config}")

    def fetch_data(self, ticker, period, interval):
        """Fetch historical data for a given cryptocurrency ticker."""
        logging.info(f"Starting data retrieval for {ticker} for period {period} and interval {interval}.")
        try:
            data = yf.download(ticker, period=period, interval=interval)
            if data.empty:
                logging.warning(f"No data retrieved for {ticker}")
            else:
                logging.info(f"Retrieved {len(data)} rows for {ticker}")
                # Ensure the date column is standardized
                if 'Datetime' in data.columns:
                    data.rename(columns={'Datetime': 'Date'}, inplace=True)
                data.index.name = 'Date'
            return data
        except Exception as e:
            logging.error(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()

    def save_data(self, df, ticker, period, interval):
        """Save the fetched data to a CSV file after removing timezone information."""
        # Remove timezone info
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        frequency = 'Hourly' if '1h' in interval else 'Daily'
        date_str = datetime.now().strftime("%Y%m%d")
        directory = os.path.join('data', ticker.replace('-USD', ''), frequency)
        self.ensure_directory(directory)
        filename = self.build_filename(ticker, period, interval, date_str)
        file_path = os.path.join(directory, filename)
        df.to_csv(file_path, index=True)
        logging.info(f"Data saved successfully to {file_path} with filename {os.path.basename(file_path)}.")
        return file_path

    def fetch_and_save(self, ticker, period, interval):
        """Combines fetching and saving into a single operation."""
        data = self.fetch_data(ticker, period, interval)
        if not data.empty:
            return self.save_data(data, ticker, period, interval)
        return None

    def ensure_directory(self, directory):
        """Ensure the directory exists."""
        os.makedirs(directory, exist_ok=True)
        logging.info(f"Directory ensured: {directory}")

    def build_filename(self, ticker, period, interval, date_str):
        """Build a consistent filename for data files."""
        return f"{ticker.replace('-USD', '')}_{period}_{interval}_{date_str}.csv"

    def is_data_fresh(self, file_path):
        """Check if the existing data file is fresh based on the current date."""
        filename = os.path.basename(file_path)
        date_str = filename.split('_')[-1].split('.')[0]
        file_date = datetime.strptime(date_str, "%Y%m%d").date()
        if file_date == datetime.now().date():
            logging.info(f"Data file {os.path.basename(file_path)} is fresh.")
            return True
        else:
            logging.info(f"Data file {os.path.basename(file_path)} is not fresh.")
            return False

    def run_data_fetcher(self):
        """Updated method to check freshness of data before fetching."""
        logging.info("Starting the data fetching process...")
        data_frames = {}
        for ticker in self.config['tickers']:
            for period, interval in self.config['combinations']:
                filename = self.build_filename(ticker, period, interval, datetime.now().strftime("%Y%m%d"))
                frequency = 'Hourly' if '1h' in interval else 'Daily'
                directory = os.path.join('data', ticker.replace('-USD', ''), frequency)
                file_path = os.path.join(directory, filename)
                self.ensure_directory(directory)

                if os.path.exists(file_path) and self.is_data_fresh(file_path):
                    logging.info(f"Loading data from existing file: {file_path}")
                    data = pd.read_csv(file_path, index_col='Date', parse_dates=['Date'])
                else:
                    logging.info(f"Fetching new data because the file is missing or not fresh. Fetching new data for {ticker}")
                    data = self.fetch_and_save(ticker, period, interval)
                    if data is not None:
                        data = pd.read_csv(file_path, index_col='Date', parse_dates=['Date'])

                data_frames[(ticker, period, interval)] = data
                logging.info(f"Data fetching process completed for {ticker} for period {period} and interval {interval}.")
        return data_frames

# Configuration dictionary
config_fetcher = {
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
    fetcher = CryptoDataFetcher(config_fetcher)
    all_data = fetcher.run_data_fetcher()
    # Example of displaying the first DataFrame from the configuration
    first_config = ('BTC-USD', '1y', '1d')
    if first_config in all_data:
        print(f"Displaying data for {first_config[0]} for period {first_config[1]} and interval {first_config[2]}:")
        display(all_data[first_config])
    else:
        print("Data for the specified configuration is not available.")
