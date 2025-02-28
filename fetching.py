import requests
import time
from datetime import datetime, timedelta


API_KEY = "ur api key"

def get_option_price_history(ticker):
    """Fetches the number of days of historical data available for an option."""
    print(f"[DEBUG] Fetching price history for {ticker}...")
    start_date = (datetime.today() - timedelta(days=180)).strftime("%Y-%m-%d")
    today_str = datetime.today().strftime("%Y-%m-%d")
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{today_str}?apiKey={API_KEY}"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        history_length = len(data.get("results", []))
        print(f"[DEBUG] {ticker} has {history_length} days of price history.")
        return history_length
    elif response.status_code == 429:
        print(f"[DEBUG] Rate limit hit for {ticker}. Waiting before retrying...")
        wait_time = int(response.headers.get("Retry-After", 12))
        time.sleep(wait_time)
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            history_length = len(data.get("results", []))
            print(f"[DEBUG] {ticker} has {history_length} days of price history after retry.")
            return history_length
        else:
            print(f"[WARN] Still failing for {ticker}: {response.status_code}")
            return 0
    else:
        print(f"[WARN] Error fetching price history for {ticker}: {response.status_code}")
        return 0

def get_current_options_with_history(underlying, min_days_of_data=5):
    """
    Fetches active (unexpired) option contracts for the given underlying
    and returns those with at least `min_days_of_data` days of historical price data.
    """
    url = "https://api.polygon.io/v3/reference/options/contracts"
    params = {
        "underlying_ticker": underlying,
        "expired": "false",  
        "limit": 100,
        "order": "desc",
        "apiKey": API_KEY
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"[ERROR] {response.status_code}: {response.text}")
        return []

    data = response.json().get("results", [])
    if not data:
        print(f"[WARN] No active option contracts found for {underlying}.")
        return []

    print(f"[DEBUG] Total active options fetched for {underlying}: {len(data)}")
    valid_options = []
    total = len(data)
    for i, contract in enumerate(data):
        ticker = contract["ticker"]
        print(f"[DEBUG] Processing contract {i+1}/{total}: {ticker}")
        history_length = get_option_price_history(ticker)
        if history_length >= min_days_of_data:
            valid_options.append((ticker, history_length))
        print("[DEBUG] Waiting for 12 seconds to comply with rate limit...")
        time.sleep(12) 

    print(f"[DEBUG] Finished processing. Valid options found: {len(valid_options)}")
    valid_options.sort(key=lambda x: x[1], reverse=True)
    return [t for t, _ in valid_options]

underlying = "GOOG"
current_tickers = get_current_options_with_history(underlying)
print("Valid tickers:", current_tickers)
