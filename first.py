import pandas as pd
from IPython.display import display, HTML

# Define the file path
file_path = '/Users/strix/Documents/Thesis - DL/Thesis_v2/data/BTC/10y/BTC_10y_1d_20240421.csv'
df = pd.read_csv(file_path)
display(df.head())


df.info()