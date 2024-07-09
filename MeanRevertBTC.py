import pandas as pd
import yfinance as yf
import numpy as np
from scipy.stats import percentileofscore

# Step 1: Import Bitcoin price data from Yahoo Finance
def import_bitcoin_data():
    btc_data = yf.download('BTC-USD', start='2010-01-01', interval='1d')
    return btc_data

# Step 2: Calculate the 4-year moving average
def calculate_moving_average(data, window=4*365):
    data['4yr_MA'] = data['Close'].rolling(window=window).mean()
    data['240d_MA'] = data['Close'].rolling(window=240).mean()
    return data.dropna()

# Step 3: Calculate the day-to-day percent change in the moving average
def calculate_pct_change(data):
    data['MA_pct_change'] = data['4yr_MA'].pct_change() * 100
    data['240d_MA_pct_change'] = data['240d_MA'].pct_change() * 100
    return data.dropna()

# Step 4: Compare the most recent percent change with the past 4 years of percent changes
def calculate_percentile(data):
    recent_pct_change = data['MA_pct_change'].iloc[-1]
    past_pct_changes = data['MA_pct_change'][:-1]  # Exclude the most recent data point for comparison
    shortMA_pct_changes = data['240d_MA_pct_change'][:-1]
    percentile = percentileofscore(past_pct_changes, recent_pct_change)
    return recent_pct_change, percentile, shortMA_pct_changes

# Step 5: Output a percent that is equal to 100 - percentile
def calculate_inverse_percentile(percentile):
    return 100 - percentile

# Main function to run the analysis
def main():
    while True:
        btc_data = import_bitcoin_data()
        btc_data_ma = calculate_moving_average(btc_data)
        btc_data_pct_change = calculate_pct_change(btc_data_ma)
        recent_pct_change, percentile, shortMApctChanges = calculate_percentile(btc_data_pct_change)
        inverse_percentile = calculate_inverse_percentile(percentile)

        if shortMApctChanges.iloc[-1] > 0:
            print("Short-term trend is up")
        else:
            print("Short-term trend is down, therefore no position is taken.")
            inverse_percentile = 0


        print(f"Recent Percent Change in 4-Year Moving Average: {recent_pct_change:.2f}%")
        print(f"Percentile of Recent Change: {percentile:.2f}%")
        print(f"Most Recent 240d MA Change: {btc_data_pct_change['240d_MA_pct_change'].iloc[-1]:.2f}%")
        print(f"Inverse Percentile (Percent Capital into Bitcoin): {inverse_percentile:.2f}%")
        ##sleep for a day
        import time
        time.sleep(86400)

if __name__ == "__main__":
    main()
