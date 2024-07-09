import pandas as pd
import yfinance as yf
import numpy as np
from scipy.stats import percentileofscore
import streamlit as st

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

# Streamlit app
def main():
    st.set_page_config(page_title="Bitcoin Moving Average Analysis", layout="wide")
    
    st.title('📈 Bitcoin Mean Reversion Model')
    st.markdown('This app calculates the recent percent change in the 4-year moving average of Bitcoin prices and determines the percent allocation based on the percentile of that change.')
    
    st.sidebar.header('Settings')
    window_4yr = st.sidebar.slider('4-Year Moving Average Window (days)', 365, 1825, 4*365)
    window_240d = st.sidebar.slider('240-Day Moving Average Window (days)', 120, 360, 240)
    
    btc_data = import_bitcoin_data()
    btc_data_ma = calculate_moving_average(btc_data, window_4yr)
    btc_data_pct_change = calculate_pct_change(btc_data_ma)

    recent_pct_change, percentile, shortMApctChanges = calculate_percentile(btc_data_pct_change)
    inverse_percentile = calculate_inverse_percentile(percentile)

    st.markdown("### Recent Analysis Results")
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Recent % Change in 4-Year MA", f"{recent_pct_change:.2f}%")
    col2.metric("Percentile of Recent Change", f"{percentile:.2f}%")
    col3.metric("Most Recent 240d MA Change", f"{btc_data_pct_change['240d_MA_pct_change'].iloc[-1]:.2f}%")
    col4.metric("Inverse Percentile (Capital in BTC)", f"{inverse_percentile:.2f}%")
    
    if shortMApctChanges.iloc[-1] > 0:
        st.success("Short-term trend is up")
    else:
        st.warning("Short-term trend is down, therefore no position is taken.")
        inverse_percentile = 0

    st.write("---")

    st.markdown("### Bitcoin Price and Moving Averages")
    st.line_chart(btc_data[['Close', '4yr_MA', '240d_MA']][1460:])
    
    st.markdown("### Moving Averages % Change")
    if 'MA_pct_change' in btc_data_ma.columns and '240d_MA_pct_change' in btc_data_ma.columns:
        st.line_chart(btc_data_ma[['MA_pct_change', '240d_MA_pct_change']])
    else:
        st.write("Percent change columns are not available for plotting.")

if __name__ == "__main__":
    main()
