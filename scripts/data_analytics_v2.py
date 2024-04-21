import os
import logging
import pandas as pd
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CryptoAnalytics:
    """
    A class to perform and manage analytics on cryptocurrency data.

    Methods:
        load_data(ticker, period, interval): Loads data for a given ticker, period, and interval.
        calculate_analytics(df): Calculates various analytics on the data.
        save_analytics(df, ticker, period, interval): Saves the analytics data to a CSV file.
        run_analytics(): Runs the entire analytics pipeline for a specified configuration.
    """
    def __init__(self, config):
        self.config = config
        logging.info("CryptoAnalytics class initialized with configuration.")

    def load_data(self, ticker, period, interval):
        frequency = 'Hourly' if '1h' in interval else 'Daily'
        directory = os.path.join('data', ticker.replace('-USD', ''), frequency)
        filename = f"{ticker.replace('-USD', '')}_{period}_{interval}_{datetime.now().strftime('%Y%m%d')}.csv"
        file_path = os.path.join(directory, filename)
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, parse_dates=['Date'], index_col='Date')
            logging.info(f"Data loaded from {file_path}")
            return df
        else:
            logging.warning(f"Data file not found: {file_path}")
            return None

    def flatten_columns(self, resampled_df):
        resampled_df.columns = ['_'.join(col).strip() for col in resampled_df.columns.values]
        return resampled_df

    def calculate_analytics(self, df):
        weekly = df.resample('W').agg({
            'Close': ['mean', 'max', 'min', 'last'],
            'Open': 'first',
            'Volume': 'sum'
        })
        monthly = df.resample('M').agg({
            'Close': ['mean', 'max', 'min', 'last'],
            'Open': 'first',
            'Volume': 'sum'
        })
        yearly = df.resample('Y').agg({
            'Close': ['mean', 'max', 'min', 'last'],
            'Open': 'first',
            'Volume': 'sum'
        })

        weekly = self.flatten_columns(weekly)
        monthly = self.flatten_columns(monthly)
        yearly = self.flatten_columns(yearly)

        # Calculate variations
        for resampled in [weekly, monthly, yearly]:
            resampled['variation_$_abs'] = resampled['Close_last'] - resampled['Open_first']
            resampled['variation_%_rel'] = resampled['variation_$_abs'] / resampled['Open_first'] * 100

        return weekly, monthly, yearly

    def save_analytics(self, weekly, monthly, yearly, ticker, period, interval):
        frequency = 'Hourly' if '1h' in interval else 'Daily'
        directory = os.path.join('data_analytics', ticker.replace('-USD', ''), frequency)
        os.makedirs(directory, exist_ok=True)
        filename = f"Analytics_{ticker.replace('-USD', '')}_{period}_{interval}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        file_path = os.path.join(directory, filename)

        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            weekly.to_excel(writer, sheet_name='Weekly')
            monthly.to_excel(writer, sheet_name='Monthly')
            if not yearly.empty:  # Only save yearly data if it exists
                yearly.to_excel(writer, sheet_name='Yearly')
            logging.info(f"Analytics saved to {file_path}")
        return file_path  # Return the path to the saved file


    def run_analytics(self):
        for ticker in self.config['tickers']:
            for period, interval in self.config['combinations']:
                # Generate the expected file path
                frequency = 'Hourly' if '1h' in interval else 'Daily'
                analytics_directory = os.path.join('data_analytics', ticker.replace('-USD', ''), frequency)
                analytics_filename = f"Analytics_{ticker.replace('-USD', '')}_{period}_{interval}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                analytics_file_path = os.path.join(analytics_directory, analytics_filename)

                # Check if analytics already exist
                if os.path.exists(analytics_file_path):
                    logging.info(f"Analytics already performed for {ticker}, {period}, {interval} and saved at {analytics_file_path}")
                    continue  # Skip to the next iteration if analytics already exist

                df = self.load_data(ticker, period, interval)
                if df is not None and not df.empty:
                    weekly, monthly, yearly = self.calculate_analytics(df)
                    self.save_analytics(weekly, monthly, yearly, ticker, period, interval)
                else:
                    logging.info(f"No data available for analysis for {ticker}, {period}, {interval}")


# Configuration dictionary for analytics
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
