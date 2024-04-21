import os
import pytest
import yfinance as yf
import pandas as pd
from datetime import datetime
import logging
from IPython.display import display, HTML


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CryptoDataFetcher:
    """
    A class to fetch and manage cryptocurrency data using the Yahoo Finance API.

    Attributes:
        tickers (list of str): List of cryptocurrency ticker symbols.
        period (str): The time period over which to fetch data (e.g., '1y' for one year).
        interval (str): The data retrieval interval (e.g., '1d' for one day).

    Methods:
        fetch_data(ticker): Fetches historical data for a given cryptocurrency ticker.
        save_data(df, ticker): Saves the fetched data to a CSV file.
        run_data_fetcher(): Fetches data for all tickers, saves it, and returns a dictionary of DataFrames.
        download_bulk_data(): Bulk downloads data across various timeframes and tickers for all specified tickers.
    """
    def __init__(self, tickers, period="1y", interval="1d"):
        self.tickers = tickers
        self.period = period
        self.interval = interval

    def fetch_data(self, ticker):
        """Fetch historical data for a given cryptocurrency ticker."""
        logging.info(f"Fetching data for {ticker}, Timeframe: {self.period}, Interval: {self.interval}")
        try:
            data = yf.download(ticker, period=self.period, interval=self.interval)
            if data.empty:
                logging.warning(f"No data retrieved for {ticker}")
            else:
                logging.info(f"Retrieved {len(data)} rows for {ticker}")
            return data
        except Exception as e:
            logging.error(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()

    def save_data(self, df, ticker):
        """Save the fetched data to a CSV file."""
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{ticker}_{self.period}_{self.interval}_{date_str}.csv"
        directory = os.path.join('data', ticker.replace('-USD', ''), self.period, self.interval)
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, filename)
        df.to_csv(file_path, index=True)
        logging.info(f"Data saved to {file_path}")
        return file_path

    def run_data_fetcher(self):
        """Fetch data for all tickers, save it, and return a dictionary of DataFrames."""
        data_frames = {}
        for ticker in self.tickers:
            date_str = datetime.now().strftime("%Y%m%d")
            filename = f"{ticker}_{self.period}_{self.interval}_{date_str}.csv"
            directory = os.path.join('data', ticker.replace('-USD', ''), self.period, self.interval)
            file_path = os.path.join(directory, filename)
            
            if os.path.exists(file_path):
                logging.info(f"File already exists: {file_path}. Loading data from file.")
                data = pd.read_csv(file_path, index_col=0, parse_dates=True)
            else:
                data = self.fetch_data(ticker)
                if not data.empty:
                    self.save_data(data, ticker)
            
            data_frames[ticker] = data
        return data_frames
    
    def download_bulk_data(self):
        """Bulk download data across various timeframes and tickers."""
        timeframes = [('max', '1d'), ('10y', '1d'), ('5y', '1d'), ('1y', '1d'), ('1y', '1h'), ('6mo', '1h'), ('3mo', '1h')]
        all_data = {}
        for period, interval in timeframes:
            fetcher = CryptoDataFetcher(self.tickers, period, interval)
            data_frames = fetcher.run_data_fetcher()
            for key, value in data_frames.items():
                all_data[(key, period, interval)] = value
        return all_data

# Example usage
if __name__ == '__main__':
    fetcher = CryptoDataFetcher(['BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD', 'BNB-USD'], '1y', '1d')
    choice = input("Enter 'bulk' to run bulk downloader or any key for specific fetch: ").strip().lower()
    if choice == 'bulk':
        all_crypto_data = fetcher.download_bulk_data()
        display(all_crypto_data)
    else:
        data = fetcher.run_data_fetcher()
        display(data)
