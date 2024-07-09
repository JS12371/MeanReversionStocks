import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import streamlit as st
import time

# Function to fetch historical data
def get_stock_data(symbol, start_date, end_date):
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(start=start_date, end=end_date)
        if data.empty:
            raise ValueError(f"No data found for {symbol}")
        return data
    except Exception as e:
        return pd.DataFrame()  # Return an empty DataFrame on failure

# Read CSV file
stocks_df = pd.read_csv('tickers.csv')

# Extract stock symbols
symbols = stocks_df['Symbol'].tolist()

# Fetch data for SPY
end_date = datetime.now()
start_date_6m = end_date - timedelta(days=180)
start_date_1y = end_date - timedelta(days=365)

st.set_page_config(page_title="Mean Reversion Dashboard", layout="wide")

st.title('Mean Reversion Dashboard')

with st.spinner('Loading data for SPY...'):
    spy_data = get_stock_data('SPY', start_date_1y, end_date)

if not spy_data.empty:
    
    # Calculate SPY returns
    spy_return_6m = (spy_data['Close'].iloc[-1] - spy_data['Close'].iloc[-1 - 126]) / spy_data['Close'].iloc[-1 - 126]
    spy_return_1y = (spy_data['Close'].iloc[-1] - spy_data['Close'].iloc[0]) / spy_data['Close'].iloc[0]

    # Define market condition
    market_condition = (spy_return_6m > -0.05) or (spy_return_1y > 0)
    
    st.metric(label="Market Condition", value=market_condition)
else:
    st.error("Failed to fetch SPY data. Exiting...")
    st.stop()

# Function to calculate moving averages and std deviation
def calculate_indicators(data):
    data['3d_ma'] = data['Close'].rolling(window=3).mean()
    data['126d_ma'] = data['Close'].rolling(window=126).mean()
    data['3d_std'] = data['Close'].rolling(window=3).std()
    return data

# Function to calculate 1-year momentum
def calculate_momentum(data):
    if len(data) >= 252:  # Ensure enough data for 1 year
        momentum = (data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]
        return momentum
    return None

# Fetch and process stock data
stock_data = {}
momentum_data = {}
with st.spinner('Fetching and processing stock data...'):
    for symbol in symbols:
        data = get_stock_data(symbol, start_date_1y, end_date)
        if not data.empty:
            stock_data[symbol] = calculate_indicators(data)
            momentum = calculate_momentum(data)
            if momentum is not None:
                momentum_data[symbol] = momentum
        else:
            pass

# Initialize positions and entry dates
positions = []
entry_dates = {}
ledger = []

# Screening function
def screen_stock(symbol, data):
    if len(data) >= 126 and data['Close'].iloc[-1] >= 5:  # Ensure enough data for 126-day moving average and price >= $5
        condition = data['Close'].iloc[-1] > data['126d_ma'].iloc[-1] and data['Close'].iloc[-1] < (data['3d_ma'].iloc[-1] - data['3d_std'].iloc[-1]) and market_condition
        return condition
    return False

# Function to update positions
def update_positions():
    global positions, entry_dates, ledger
    for symbol in positions[:]:
        data = stock_data[symbol]
        if data['Close'].iloc[-1] > data['3d_ma'].iloc[-1] or not market_condition:
            positions.remove(symbol)
            exit_date = datetime.now()
            ledger.append({
                'Symbol': symbol,
                'Purchased On': entry_dates.pop(symbol, 'Unknown'),
                'Exited On': exit_date.strftime('%Y-%m-%d')
            })
    
    # Filter and sort stocks by 1-year momentum
    eligible_stocks = [symbol for symbol in symbols if symbol not in positions and symbol in stock_data and screen_stock(symbol, stock_data[symbol])]
    sorted_stocks = sorted([symbol for symbol in eligible_stocks if symbol in momentum_data], key=lambda x: momentum_data[x], reverse=True)
    
    # Add new positions if below cap
    for symbol in sorted_stocks:
        if len(positions) < 10:
            positions.append(symbol)
            entry_dates[symbol] = datetime.now()
        else:
            break
    
    display_positions()
    display_ledger()

# Function to display positions with entry dates
def display_positions():
    st.subheader("Current Positions")
    if positions:
        current_positions_df = pd.DataFrame({
            'Symbol': positions,
            'Entry Date': [entry_dates[symbol].strftime('%Y-%m-%d') for symbol in positions]
        })
        st.dataframe(current_positions_df)
    else:
        st.write("No current positions.")

# Function to display ledger
def display_ledger():
    st.subheader("Transaction Ledger")
    if ledger:
        ledger_df = pd.DataFrame(ledger)
        st.dataframe(ledger_df)
    else:
        st.write("No transactions yet.")

st.write("---")
st.info("Positions will be updated every 24 hours.")

# Periodic updates with Streamlit
while True:
    update_positions()
    time.sleep(3600 * 24)
    st.write("Positions updated.")
