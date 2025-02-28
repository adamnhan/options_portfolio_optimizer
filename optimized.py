import requests
import time
import pandas as pd
import statsmodels.api as sm
from scipy.optimize import minimize
import scipy.stats as si
from datetime import datetime
import numpy as np
from pandas.core.common import SettingWithCopyWarning
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=SettingWithCopyWarning)
API_KEY = "your_api_key"

def load_portfolio(csv_path):
    portfolio_df = pd.read_csv(csv_path)
    option_tickers = portfolio_df["ticker"].unique().tolist()
    underlying_tickers = portfolio_df["underlying"].unique().tolist()
    quantities = dict(zip(portfolio_df["ticker"], portfolio_df["quantity"]))
    return portfolio_df, option_tickers, underlying_tickers, quantities

def fetch_stock_prices(ticker, start_date, end_date):
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}?apiKey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        df = pd.DataFrame(results)
        df['date'] = pd.to_datetime(df['t'], unit='ms')
        df = df[['date', 'c']]
        df.rename(columns={'c': 'close_price'}, inplace=True)
        return df
    else:
        print(f"Error fetching stock prices for {ticker}: {response.status_code}")
        return None

def fetch_all_stock_prices(underlying_tickers, start_date, end_date):
    stock_data = {}
    for ticker in underlying_tickers:
        df = fetch_stock_prices(ticker, start_date, end_date)
        if df is not None and not df.empty:
            stock_data[ticker] = df
        else:
            print(f"⚠️ No stock data found for {ticker}, skipping...")
        time.sleep(12)  # Avoid hitting rate limits
    return stock_data

def fetch_multiple_option_prices(option_tickers, start_date, end_date):
    all_option_data = []
    for i, option_ticker in enumerate(option_tickers):
        url = f"https://api.polygon.io/v2/aggs/ticker/{option_ticker}/range/1/day/{start_date}/{end_date}?apiKey={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if "results" not in data or not data["results"]:
                print(f"Warning: No price data found for {option_ticker}")
                continue
            results = data["results"]
            df = pd.DataFrame(results)
            if "t" not in df.columns:
                print(f"Error: No 't' column in data for {option_ticker}. Full response: {data}")
                continue
            df['date'] = pd.to_datetime(df['t'], unit='ms')
            df = df[['date', 'c']]
            df.rename(columns={'c': 'option_price'}, inplace=True)
            df['option_ticker'] = option_ticker
            all_option_data.append(df)
        else:
            print(f"Error fetching option {option_ticker}: {response.status_code}, Response: {response.text}")
        if (i + 1) % 5 == 0:
            time.sleep(60)
    return pd.concat(all_option_data, ignore_index=True) if all_option_data else None

def fetch_option_greeks(option_tickers, underlying_prices, risk_free_rate=0.05, volatility=0.2):
    greeks_data = []
    for option_ticker in option_tickers:
        try:
            parts = option_ticker.split(":")[-1]
            underlying = ''.join(filter(str.isalpha, parts[:-9]))
            exp_year = int(parts[-15:-13]) + 2000
            exp_month = int(parts[-13:-11])
            exp_day = int(parts[-11:-9])
            option_type = "call" if parts[-9] == "C" else "put"
            strike_price = int(parts[-8:]) / 1000
            spot_price = underlying_prices.get(underlying, None)
            if spot_price is None or spot_price == 0:
                print(f"⚠️ Skipping {option_ticker} due to missing spot price: {spot_price}")
                continue
            time_to_expiry = (datetime(exp_year, exp_month, exp_day) - datetime.today()).days / 365
            if time_to_expiry <= 0:
                print(f"⚠️ Skipping {option_ticker} due to zero/negative expiration time: {time_to_expiry}")
                continue
            d1 = (np.log(spot_price / strike_price) + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry) / (volatility * np.sqrt(time_to_expiry))
            d2 = d1 - volatility * np.sqrt(time_to_expiry)
            delta = si.norm.cdf(d1) if option_type == "call" else si.norm.cdf(d1) - 1
            gamma = si.norm.pdf(d1) / (spot_price * volatility * np.sqrt(time_to_expiry))
            vega = spot_price * si.norm.pdf(d1) * np.sqrt(time_to_expiry)
            theta = (-spot_price * si.norm.pdf(d1) * volatility) / (2 * np.sqrt(time_to_expiry))
            greeks_data.append({
                "option_ticker": option_ticker,
                "underlying": underlying,
                "expiration": f"{exp_year}-{exp_month:02d}-{exp_day:02d}",
                "strike_price": strike_price,
                "option_type": option_type,
                "delta": delta,
                "gamma": gamma,
                "vega": vega,
                "theta": theta
            })
        except Exception as e:
            print(f"❌ Error processing {option_ticker}: {e}")
    greeks_df = pd.DataFrame(greeks_data)
    print("DEBUG: Completed Greeks calculation. Sample output:")
    print(greeks_df.head())
    return greeks_df

def compute_returns(stock_df, option_df):
    stock_df['market_return'] = stock_df['close_price'].pct_change()
    option_df['option_return'] = option_df.groupby('option_ticker')['option_price'].pct_change()
    return stock_df.dropna(), option_df.dropna()

def run_regressions(option_df, stock_df, greeks_df):
    regression_results = {}
    for option_ticker in option_df['option_ticker'].unique():
        option_subset = option_df[option_df['option_ticker'] == option_ticker]
        option_subset.loc[:, 'date'] = pd.to_datetime(option_subset['date'])
        stock_df['date'] = pd.to_datetime(stock_df['date'])
        merged_df = option_subset.merge(stock_df, on='date', how='inner')
        merged_df = merged_df.merge(greeks_df, on='option_ticker', how='left')
        if merged_df.shape[0] < 5:
            print(f"Skipping {option_ticker}: Not enough data for regression.")
            continue
        X = merged_df[['market_return', 'delta', 'gamma', 'vega', 'theta']]
        X = sm.add_constant(X)
        y = merged_df['option_return']
        model = sm.OLS(y, X)
        results = model.fit()
        regression_results[option_ticker] = results
    return regression_results

def optimize_portfolio(regression_results, greeks_df, quantities):
    betas = np.array([
        regression_results[ticker].params[1] * quantities.get(ticker, 1)
        for ticker in regression_results
    ])
    deltas = np.array([
        greeks_df.loc[greeks_df['option_ticker'] == ticker, 'delta'].values[0] * quantities.get(ticker, 1)
        for ticker in regression_results
    ])
    num_options = len(betas)
    max_cap = 2 / num_options

    def objective(weights):
        return -np.dot(weights, betas)

    constraints = [
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
        {'type': 'eq', 'fun': lambda w: np.dot(w, deltas)}
    ]
    bounds = [(-1, max_cap)] * num_options
    init_weights = np.ones(num_options) / num_options
    result = minimize(objective, init_weights, bounds=bounds, constraints=constraints)
    return result.x

def main():
    csv_path = "portfolio.csv"
    start_date = "2023-02-01"
    end_date = "2025-02-20"

    portfolio_df, option_tickers, underlying_tickers, quantities = load_portfolio(csv_path)
    stock_data = fetch_all_stock_prices(underlying_tickers, start_date, end_date)
    underlying_prices = {
        ticker: stock_data[ticker]["close_price"].iloc[-1] if ticker in stock_data and not stock_data[ticker].empty else None
        for ticker in underlying_tickers
    }
    option_data = fetch_multiple_option_prices(option_tickers, start_date, end_date)
    greeks_df = fetch_option_greeks(option_tickers, underlying_prices)
    valid_stocks = {k: v for k, v in stock_data.items() if v is not None and not v.empty}
    if not valid_stocks:
        print("❌ Error: No valid stock data available.")
        return

    stock_df = list(valid_stocks.values())[0].rename(columns={'close_price': list(valid_stocks.keys())[0]})
    for i, (ticker, df) in enumerate(valid_stocks.items()):
        if i == 0:
            continue
        stock_df = stock_df.merge(df.rename(columns={'close_price': ticker}), on='date', how='inner')

    expected_columns = ['date'] + list(valid_stocks.keys())
    if stock_df.shape[1] == len(expected_columns):
        stock_df.columns = expected_columns
    else:
        print("⚠️ Mismatch detected: Column count does not match valid tickers.")
        print("❌ Skipping column renaming to prevent errors.")

    stock_df['market_return'] = stock_df.iloc[:, 1:].mean(axis=1).pct_change()
    stock_df.dropna(inplace=True)
    if 'option_price' in option_data.columns:
        option_data['option_return'] = option_data['option_price'].pct_change()
        option_data.dropna(inplace=True)

    regression_results = run_regressions(option_data, stock_df, greeks_df)
    optimal_weights = optimize_portfolio(regression_results, greeks_df, quantities)
    
    # Display optimal weights next to their respective tickers
    tickers_used = list(regression_results.keys())
    weight_df = pd.DataFrame({
        "Ticker": tickers_used,
        "Optimal Weight": optimal_weights
    })
    print("✅ Optimal Weights by Ticker:")
    print(weight_df)

if __name__ == "__main__":
    main()
