# Options Portfolio Optimizer

This project is a Python-based tool designed to optimize an options portfolio by fetching historical market data, calculating option Greeks, running regression analyses, and ultimately determining the optimal weights for each option in the portfolio.

## Overview

The script performs the following tasks:
- **Data Loading:** Reads portfolio information from a CSV file, including option tickers, underlying assets, and quantities.
- **Data Fetching:** Retrieves historical stock and option prices using the Polygon.io API.
- **Greek Calculation:** Computes key option Greeks such as delta, gamma, vega, and theta to assess option sensitivity.
- **Regression Analysis:** Performs regression analyses to relate option returns with market returns and Greeks.
- **Portfolio Optimization:** Uses optimization techniques to determine the optimal allocation (weights) for each option, subject to constraints based on market and risk factors.

## Features

- **CSV-Based Portfolio Input:** Easily manage your portfolio via a CSV file.
- **API Integration:** Fetches historical and current data from Polygon.io.
- **Statistical Analysis:** Leverages regression techniques to analyze market behavior.
- **Risk Management:** Incorporates option Greeks for effective risk assessment.

## Requirements

- Python 3.6 or higher
- Required libraries:
  - `requests`
  - `pandas`
  - `statsmodels`
  - `scipy`
  - `numpy`
- A valid API key from [Polygon.io](https://polygon.io/)

## Installation

1. **Clone the Repository:**
   ```bash
   git clone git@github.com:adamnhan/options_portfolio_optimizer.git
   ```
2. **Install the required dependencies:**

3. **Get polygon.io api**
  - They offer a free plan which provides data which suffices for the purposes of this project. You
    can get their greeks directly if you pay, but for this delta-based strategy, the necessary greeks are calculated.

4. **Portfolio**
  - I've provided an example portfolio in portfolio.csv, you can modify this to be your own portfolio. If you wish to extract
   different tickers from different underlying assets than the example portfolio, use the fetching.py file. This file will 
    fetch different contract tickers which have adequate price history and are not expired. This does take a while as the free plan limit is 5 calls/min. You 
    can adjust the amount of contracts to query via the "limit" parameter in the get_current_options_with_history function.

## How does it work? 
  After all data has been fetched, the underlying asset returns and option returns are calculated, giving percentage change of the day to day returns. The underlying returns are used later as an variabel in regression and the option returns are group by ticker.

The greeks are calculated via the black-scholes model. They're stored in a dataframe for regression later.

The data is then put through regression analysis. X variables include underlying asset return, delta, gamma, vega, and theta. The Y variable is option returns. The data is then fit with an Ordinary Least Squares model to estimate the coefficients (beta).

We extract the beta coefficients, which represent expected returns per unit exposure. We also extract the deltas to enforce a delta-neutral constraint, this is where the risk comes into play. The closer delta is to 0 (neutral) , the less it responds to small market movements, helping reduce risk if we allocate more resources towards an option with a neutral delta. 

An objective function is also defined. Portfolio Return = sum(weight * beta), we use minimize() from SciPy to negate this function as well. We define constraints, weight sum and delta-neutral. The weight sum constraint ensures all weights sum to 1, and the delta neutral constraint ensures overall delta is 0. In addition, the optimization also takes into account longs vs shorts, and allows short selling, which are represented by negative weights in the return dataframe. I defined a max cap to allow for diversification, where the max cap equals double a ticker's normal even allocation. So if there were 5 tickers in a portfolio, max cap is 40%, if there were 4 tickers, max cap is 50% etc etc. The tickers are then optimized with the minimize() func from scipy to find optimal weight distribution.

Final output is displayed in a dataframe in console.
