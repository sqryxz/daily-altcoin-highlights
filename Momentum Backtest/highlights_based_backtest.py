#!/usr/bin/env python3
"""
This script runs a backtest based on the top coins identified in the AI Altcoin Highlights
rather than using the momentum-based selection strategy.
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json
import requests
import time
import random

# Add parent directory to path so we can import from ai_highlights
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_highlights import get_market_data, generate_summary, COINGECKO_API_URL

# Constants for the backtest
HOLDING_PERIOD_DAYS = 1  # How often to rebalance (daily)
TOP_N_COINS = 3  # Number of top coins to use from the AI Highlights
HISTORY_DAYS = 90  # How many days of historical data to backtest
BENCHMARK_COIN = "bitcoin"  # Benchmark to compare against
INITIAL_CAPITAL = 10000  # Starting capital in USD
CACHE_DIR = "Momentum Backtest/cache"  # Cache directory path
MAX_RETRIES = 5  # Maximum number of retries for API requests
MIN_COINS_FOR_BACKTEST = 10  # Minimum number of coins needed for backtest

def ensure_cache_dir():
    """Ensure cache directory exists"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_historical_prices(coin_id, days=HISTORY_DAYS, vs_currency="usd"):
    """Get historical price data for a specific coin with exponential backoff for rate limits"""
    cache_file = f"{CACHE_DIR}/{coin_id}_history_{days}d.json"
    
    # Try to load from cache
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            cache_time = cache_data.get('timestamp', 0)
            # Cache valid for 12 hours
            if time.time() - cache_time < 12 * 3600:
                print(f"Loading {coin_id} history from cache...")
                return cache_data.get('data')
        except Exception as e:
            print(f"Error reading cache: {e}")
    
    # Fetch from API if cache not available
    print(f"Fetching {days} days of history for {coin_id}...")
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': vs_currency,
        'days': days,
        'interval': 'daily'
    }
    
    # Implement exponential backoff
    for retry in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params)
            
            # Handle rate limiting
            if response.status_code == 429:
                wait_time = 2 ** retry + random.random()
                print(f"Rate limited. Waiting {wait_time:.2f} seconds before retry {retry+1}/{MAX_RETRIES}...")
                time.sleep(wait_time)
                continue
                
            response.raise_for_status()
            data = response.json()
            
            # Cache the results
            try:
                ensure_cache_dir()
                with open(cache_file, 'w') as f:
                    cache_content = {
                        'timestamp': time.time(),
                        'data': data
                    }
                    json.dump(cache_content, f)
            except Exception as e:
                print(f"Error caching data: {e}")
                
            return data
        except requests.exceptions.RequestException as e:
            if response.status_code == 429 and retry < MAX_RETRIES - 1:
                # Already handled above, just continue the loop
                continue
            elif retry < MAX_RETRIES - 1:
                wait_time = 2 ** retry + random.random()
                print(f"Error: {e}. Retrying in {wait_time:.2f} seconds... ({retry+1}/{MAX_RETRIES})")
                time.sleep(wait_time)
            else:
                print(f"Error fetching historical data for {coin_id} after {MAX_RETRIES} retries: {e}")
                return None
        except Exception as e:
            print(f"Unexpected error for {coin_id}: {e}")
            return None
    
    return None

def prepare_historical_dataframe(coin_ids, max_coins=50):
    """Prepare a DataFrame with historical prices for all coins"""
    all_prices = {}
    all_volumes = {}
    
    # Add benchmark to the list if not already there
    if BENCHMARK_COIN not in coin_ids:
        coin_ids = [BENCHMARK_COIN] + coin_ids
    
    # Limit the number of coins to prevent excessive API calls
    if len(coin_ids) > max_coins:
        print(f"Limiting to top {max_coins} coins to prevent excessive API calls")
        coin_ids = coin_ids[:max_coins]
    
    for coin_id in coin_ids:
        history = get_historical_prices(coin_id)
        if not history:
            continue
            
        # Extract price and volume data
        prices = history.get('prices', [])
        volumes = history.get('total_volumes', [])
        
        # Convert to DataFrames
        if prices:
            df_prices = pd.DataFrame(prices, columns=['timestamp', coin_id])
            df_prices['timestamp'] = pd.to_datetime(df_prices['timestamp'], unit='ms')
            df_prices.set_index('timestamp', inplace=True)
            all_prices[coin_id] = df_prices
        
        if volumes:
            df_volumes = pd.DataFrame(volumes, columns=['timestamp', coin_id])
            df_volumes['timestamp'] = pd.to_datetime(df_volumes['timestamp'], unit='ms')
            df_volumes.set_index('timestamp', inplace=True)
            all_volumes[coin_id] = df_volumes
        
        # Add a small delay between API requests to avoid hitting rate limits
        time.sleep(0.5)
    
    # Combine all price DataFrames
    if all_prices:
        df_prices = pd.concat(all_prices.values(), axis=1)
        df_prices = df_prices.sort_index()
        
        # Forward fill missing values (if a coin doesn't have data for a day)
        df_prices = df_prices.ffill()
    else:
        df_prices = pd.DataFrame()
    
    # Combine all volume DataFrames
    if all_volumes:
        df_volumes = pd.concat(all_volumes.values(), axis=1)
        df_volumes = df_volumes.sort_index()
        df_volumes = df_volumes.ffill()
    else:
        df_volumes = pd.DataFrame()
    
    return df_prices, df_volumes

def calculate_returns(df_prices):
    """Calculate daily returns"""
    # Daily returns
    daily_returns = df_prices.pct_change().dropna()
    return daily_returns

def extract_top_coins_from_highlights(market_data, top_n=TOP_N_COINS):
    """Extract the top N coins from the daily AI highlights summary"""
    # Sort the market data by 24h price change (descending)
    sorted_data = sorted(
        market_data, 
        key=lambda x: x.get('price_change_percentage_24h', 0), 
        reverse=True
    )
    
    # Take the top N coins
    top_coins = [coin['id'] for coin in sorted_data[:top_n] if 'id' in coin]
    
    if not top_coins:
        print("Warning: No valid coins found in the highlights data")
        return []
    
    print(f"Top {top_n} coins from daily highlights:")
    for i, coin_id in enumerate(top_coins):
        coin_info = next((c for c in sorted_data if c.get('id') == coin_id), None)
        if coin_info:
            change = coin_info.get('price_change_percentage_24h', 0)
            symbol = coin_info.get('symbol', '').upper()
            print(f"  {i+1}. {symbol} ({coin_id}): {change:.2f}% 24h change")
    
    return top_coins

def run_highlights_based_backtest(df_prices, daily_returns, market_data_by_day):
    """Run a backtest based on the top coins from the daily AI highlights summary"""
    # Initialize portfolio and benchmark tracking
    portfolio_value = [INITIAL_CAPITAL]
    benchmark_value = [INITIAL_CAPITAL]
    rebalance_dates = []
    positions = {}
    win_count = 0
    total_rebalances = 0
    spike_captures = 0  # Count of ≥10% daily moves caught
    
    # Find the closest trading day to start with
    trading_days = daily_returns.index
    
    # Make sure we have at least one day of data
    if len(trading_days) < 2:
        print("Error: Not enough trading days in the data")
        return None
    
    current_day = trading_days[0]
    last_rebalance = current_day - timedelta(days=HOLDING_PERIOD_DAYS + 1)  # Force initial rebalance
    
    for i, current_day in enumerate(trading_days):
        # Get the day's market data (or use the most recent if not available for this day)
        day_key = current_day.strftime('%Y-%m-%d')
        if day_key in market_data_by_day:
            day_market_data = market_data_by_day[day_key]
        else:
            # Find the most recent day
            available_days = [d for d in market_data_by_day.keys() if d < day_key]
            if available_days:
                latest_day = max(available_days)
                day_market_data = market_data_by_day[latest_day]
            else:
                # Use the first available day
                first_day = min(market_data_by_day.keys())
                day_market_data = market_data_by_day[first_day]
        
        # Check if it's time to rebalance
        if (current_day - last_rebalance).days >= HOLDING_PERIOD_DAYS:
            # Get top coins from the highlights
            top_coins = extract_top_coins_from_highlights(day_market_data, TOP_N_COINS)
            
            # Store rebalance decision for later analysis
            rebalance_info = {
                'date': current_day,
                'selected_coins': top_coins,
                'daily_changes': {
                    coin: next(
                        (c.get('price_change_percentage_24h', 0) for c in day_market_data if c.get('id') == coin), 
                        0
                    ) for coin in top_coins
                }
            }
            rebalance_dates.append(rebalance_info)
            
            # Close old positions and calculate P&L
            prior_portfolio_value = portfolio_value[-1]
            
            # Record if this rebalance was a win compared to benchmark
            if len(positions) > 0 and i > 0:
                portfolio_return = (portfolio_value[-1] / portfolio_value[-2]) - 1
                benchmark_return = (benchmark_value[-1] / benchmark_value[-2]) - 1
                if portfolio_return > benchmark_return:
                    win_count += 1
                total_rebalances += 1
            
            # Create new equal-weighted positions
            if top_coins:
                # Filter to only coins we have price data for
                investable_coins = [coin for coin in top_coins if coin in df_prices.columns]
                if investable_coins:
                    positions = {coin: prior_portfolio_value / len(investable_coins) for coin in investable_coins}
                else:
                    # If no coins have price data, maintain cash position
                    positions = {}
            else:
                positions = {}
            
            last_rebalance = current_day
        
        # Update portfolio value for today
        if positions:
            # Only consider coins that have data for today
            valid_positions = {coin: amount for coin, amount in positions.items() 
                             if coin in daily_returns.columns and current_day in daily_returns.index}
            
            if valid_positions:
                daily_pnl = sum(valid_positions[coin] * daily_returns.loc[current_day, coin]
                                for coin in valid_positions)
                new_portfolio_value = portfolio_value[-1] + daily_pnl
                
                # Check for spike captures (≥10% daily moves)
                for coin in valid_positions:
                    if daily_returns.loc[current_day, coin] >= 0.10:  # 10% or more
                        spike_captures += 1
            else:
                # No valid positions, maintain current value
                new_portfolio_value = portfolio_value[-1]
        else:
            # No positions, maintain current value
            new_portfolio_value = portfolio_value[-1]
        
        portfolio_value.append(new_portfolio_value)
        
        # Update benchmark value
        if BENCHMARK_COIN in daily_returns.columns and current_day in daily_returns.index:
            benchmark_daily_return = daily_returns.loc[current_day, BENCHMARK_COIN]
            new_benchmark_value = benchmark_value[-1] * (1 + benchmark_daily_return)
            benchmark_value.append(new_benchmark_value)
        else:
            benchmark_value.append(benchmark_value[-1])
    
    # Compile results
    performance = {
        'portfolio_values': portfolio_value[1:],  # Drop the initial value
        'benchmark_values': benchmark_value[1:],  # Drop the initial value
        'dates': trading_days,
        'rebalance_dates': rebalance_dates,
        'win_rate': win_count / total_rebalances if total_rebalances > 0 else 0,
        'spike_captures': spike_captures
    }
    
    return performance

def calculate_performance_metrics(performance):
    """Calculate key performance metrics"""
    portfolio_values = performance['portfolio_values']
    benchmark_values = performance['benchmark_values']
    dates = performance['dates']
    
    # Create DataFrames for strategy and benchmark returns
    strategy_returns = pd.Series(
        [portfolio_values[i] / portfolio_values[i-1] - 1 for i in range(1, len(portfolio_values))],
        index=dates[1:]
    )
    benchmark_returns = pd.Series(
        [benchmark_values[i] / benchmark_values[i-1] - 1 for i in range(1, len(benchmark_values))],
        index=dates[1:]
    )
    
    # Cumulative returns
    strategy_cumulative = (strategy_returns + 1).cumprod()
    benchmark_cumulative = (benchmark_returns + 1).cumprod()
    
    # Calculate metrics
    risk_free_rate = 0.02  # Assuming 2% annual risk-free rate
    daily_risk_free = (1 + risk_free_rate) ** (1/252) - 1
    
    # Strategy metrics
    strategy_annual_return = (strategy_cumulative.iloc[-1] ** (252 / len(strategy_cumulative))) - 1
    strategy_volatility = strategy_returns.std() * np.sqrt(252)
    strategy_sharpe = (strategy_annual_return - risk_free_rate) / strategy_volatility if strategy_volatility > 0 else 0
    
    # Calculate drawdowns
    strategy_drawdown = 1 - strategy_cumulative / strategy_cumulative.cummax()
    max_drawdown = strategy_drawdown.max()
    
    # Benchmark metrics
    benchmark_annual_return = (benchmark_cumulative.iloc[-1] ** (252 / len(benchmark_cumulative))) - 1
    benchmark_volatility = benchmark_returns.std() * np.sqrt(252)
    benchmark_sharpe = (benchmark_annual_return - risk_free_rate) / benchmark_volatility if benchmark_volatility > 0 else 0
    
    metrics = {
        'strategy_cumulative_return': strategy_cumulative.iloc[-1] - 1,
        'benchmark_cumulative_return': benchmark_cumulative.iloc[-1] - 1,
        'strategy_annual_return': strategy_annual_return,
        'benchmark_annual_return': benchmark_annual_return,
        'strategy_volatility': strategy_volatility,
        'benchmark_volatility': benchmark_volatility,
        'strategy_sharpe': strategy_sharpe,
        'benchmark_sharpe': benchmark_sharpe,
        'max_drawdown': max_drawdown,
        'win_rate': performance['win_rate'],
        'spike_captures': performance['spike_captures'],
        'strategy_returns': strategy_returns,
        'benchmark_returns': benchmark_returns,
        'strategy_cumulative': strategy_cumulative,
        'benchmark_cumulative': benchmark_cumulative,
        'rebalance_dates': performance['rebalance_dates']
    }
    
    return metrics

def plot_results(metrics, coin_universe):
    """Plot the backtest results"""
    plt.figure(figsize=(12, 8))
    
    # Cumulative returns
    plt.subplot(2, 1, 1)
    plt.plot(metrics['strategy_cumulative'], label=f'Top {TOP_N_COINS} Daily AI Coins')
    plt.plot(metrics['benchmark_cumulative'], label=f'Benchmark ({BENCHMARK_COIN.capitalize()})')
    plt.title(f'Daily Top Performers Strategy: Top {TOP_N_COINS} AI Coins vs. {BENCHMARK_COIN.capitalize()}')
    plt.ylabel('Cumulative Return')
    plt.legend()
    plt.grid(True)
    
    # Drawdowns
    plt.subplot(2, 1, 2)
    drawdowns = 1 - metrics['strategy_cumulative'] / metrics['strategy_cumulative'].cummax()
    plt.fill_between(drawdowns.index, 0, drawdowns.values, color='red', alpha=0.3)
    plt.title('Drawdowns')
    plt.ylabel('Drawdown')
    plt.xlabel('Date')
    plt.grid(True)
    
    plt.tight_layout()
    
    # Save the figure
    plt.savefig("Momentum Backtest/highlights_backtest_results.png")
    
    # Show summary 
    print("\n" + "="*50)
    print(f"DAILY TOP PERFORMERS BACKTEST RESULTS ({datetime.now().strftime('%Y-%m-%d')})")
    print("="*50)
    print(f"Strategy: Top {TOP_N_COINS} Daily AI Coins (24h performance)")
    print(f"Universe: {len(coin_universe)} AI-related cryptocurrencies")
    print(f"Benchmark: {BENCHMARK_COIN.capitalize()}")
    period_start = metrics['strategy_returns'].index[0].strftime('%Y-%m-%d') if len(metrics['strategy_returns']) > 0 else "N/A"
    period_end = metrics['strategy_returns'].index[-1].strftime('%Y-%m-%d') if len(metrics['strategy_returns']) > 0 else "N/A"
    print(f"Period: {period_start} to {period_end}")
    print("="*50)
    print(f"Total Return: {metrics['strategy_cumulative_return']:.2%} vs. Benchmark: {metrics['benchmark_cumulative_return']:.2%}")
    print(f"Annualized Return: {metrics['strategy_annual_return']:.2%} vs. Benchmark: {metrics['benchmark_annual_return']:.2%}")
    print(f"Annualized Volatility: {metrics['strategy_volatility']:.2%}")
    print(f"Sharpe Ratio: {metrics['strategy_sharpe']:.2f}")
    print(f"Maximum Drawdown: {metrics['max_drawdown']:.2%}")
    print(f"Win Rate: {metrics['win_rate']:.2%} of rebalances")
    print(f"Spike Captures: {metrics['spike_captures']} instances of ≥10% daily moves")
    print("="*50)
    
    # Get most recent portfolio allocation
    if len(metrics.get('rebalance_dates', [])) > 0:
        latest_rebalance = metrics['rebalance_dates'][-1]
        latest_date = latest_rebalance['date']
        latest_coins = latest_rebalance['selected_coins']
        latest_changes = latest_rebalance['daily_changes']
        
        print("\nMost Recent Portfolio Allocation:")
        for coin in latest_coins:
            change = latest_changes.get(coin, 0)
            print(f"- {coin.upper()}: {change:.2f}% 24h change")
        print(f"(As of {latest_date.strftime('%Y-%m-%d')})")
    
    return

def get_coin_universe():
    """Get the universe of AI coins to backtest"""
    # Use the existing function from ai_highlights.py
    market_data = get_market_data()
    if not market_data:
        print("Failed to fetch AI coin data. Exiting.")
        return None
    
    # Extract coin IDs from market data
    coin_universe = [coin['id'] for coin in market_data]
    
    print(f"Identified {len(coin_universe)} AI-related coins for backtest universe.")
    return coin_universe, market_data

def simulate_historical_market_data(coin_universe, days=HISTORY_DAYS):
    """
    Simulate historical market data by creating snapshots for each day
    This is needed because we don't have access to historical rankings from the highlights
    """
    print(f"Simulating {days} days of historical market data...")
    
    # Get current market data
    current_market_data = get_market_data()
    if not current_market_data:
        print("Failed to fetch current market data. Exiting.")
        return None
    
    # Get historical price data for all coins
    df_prices, _ = prepare_historical_dataframe(coin_universe)
    
    if df_prices.empty:
        print("No price data available. Exiting.")
        return None
    
    # Calculate daily returns
    daily_returns = calculate_returns(df_prices)
    
    # Create a simulated market data snapshot for each day
    market_data_by_day = {}
    
    # Start from the most recent day and work backward
    for day in reversed(daily_returns.index):
        day_str = day.strftime('%Y-%m-%d')
        
        # Create a copy of the current market data
        day_market_data = []
        
        for coin in current_market_data:
            coin_id = coin.get('id')
            if coin_id and coin_id in daily_returns.columns:
                # Get the actual 24h return for this day if available
                if day in daily_returns.index:
                    # Use yesterday's close to today's close as the 24h change
                    day_idx = daily_returns.index.get_loc(day)
                    if day_idx > 0:
                        yesterday = daily_returns.index[day_idx - 1]
                        if yesterday in daily_returns.index and coin_id in daily_returns.columns:
                            price_change = df_prices.loc[day, coin_id] / df_prices.loc[yesterday, coin_id] - 1
                            day_coin = coin.copy()
                            day_coin['price_change_percentage_24h'] = price_change * 100  # Convert to percentage
                            day_market_data.append(day_coin)
            
        # Only add days with enough data
        if len(day_market_data) >= MIN_COINS_FOR_BACKTEST:
            market_data_by_day[day_str] = day_market_data
    
    print(f"Created simulated market data for {len(market_data_by_day)} days")
    return market_data_by_day, df_prices, daily_returns

def main():
    """Main function to run the highlights-based backtest"""
    print("Starting Daily AI Coin Highlights Backtest...")
    
    # Ensure cache directory exists
    ensure_cache_dir()
    
    # Get universe of AI coins
    coin_universe_result = get_coin_universe()
    if not coin_universe_result:
        return
    
    coin_universe, current_market_data = coin_universe_result
    
    # Simulate historical market data
    simulation_result = simulate_historical_market_data(coin_universe)
    if not simulation_result:
        return
    
    market_data_by_day, df_prices, daily_returns = simulation_result
    
    # Ensure we have enough coins for a meaningful backtest
    if len(df_prices.columns) < MIN_COINS_FOR_BACKTEST:
        print(f"Not enough coins with historical data. Need at least {MIN_COINS_FOR_BACKTEST}, got {len(df_prices.columns)}.")
        return
    
    print(f"Historical data prepared for {len(df_prices.columns)} coins.")
    
    # Run highlights-based backtest
    print(f"Running highlights-based backtest...")
    performance = run_highlights_based_backtest(df_prices, daily_returns, market_data_by_day)
    
    if not performance:
        print("Failed to run backtest. Exiting.")
        return
    
    # Calculate performance metrics
    metrics = calculate_performance_metrics(performance)
    
    # Plot and display results
    plot_results(metrics, coin_universe)
    
    # Save results to CSV
    results_df = pd.DataFrame({
        'Date': metrics['strategy_returns'].index,
        'Strategy_Return': metrics['strategy_returns'].values,
        'Benchmark_Return': metrics['benchmark_returns'].values,
        'Strategy_Cumulative': metrics['strategy_cumulative'].values,
        'Benchmark_Cumulative': metrics['benchmark_cumulative'].values
    })
    results_df.to_csv("Momentum Backtest/highlights_backtest_results.csv", index=False)
    
    # Save portfolio allocations history
    allocations_data = []
    for rebalance in performance['rebalance_dates']:
        for coin in rebalance['selected_coins']:
            allocations_data.append({
                'Date': rebalance['date'],
                'Coin': coin,
                'Daily_Change': rebalance['daily_changes'].get(coin, 0)
            })
    
    if allocations_data:
        allocations_df = pd.DataFrame(allocations_data)
        allocations_df.to_csv("Momentum Backtest/highlights_portfolio_allocations.csv", index=False)
    
    print("Backtest complete! Results saved to 'Momentum Backtest' folder.")

if __name__ == "__main__":
    main() 