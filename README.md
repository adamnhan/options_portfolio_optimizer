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
    fetch different contract tickers which have adequate price history and are not expired. This does take a while, and you
    can adjust the amount  
