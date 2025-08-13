import os
import time
import schedule
import pandas as pd
import pandas_ta as ta
from pybit.unified_trading import HTTP


# --- Configuration Section ---
#
# Bybit API Credentials - IMPORTANT: Set these as environment variables.
# The script will read them securely. NEVER hardcode keys in your script.
# [Source: 2]
api_key = os.getenv("BYBIT_API_KEY", "YOUR_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET", "YOUR_API_SECRET")


# Trading Parameters
# [Source: 1]
trading_config = {
    "symbol": "BTCUSDT",
    "category": "spot",
}


# Investment Strategy
# [Source: 1]
investment_config = {
    "daily_amount": 1.00
}


# Dynamic DCA Strategy Rules
# [Source: 3, 4, 5]
strategy_config = {
    "rsi_buy_threshold": 50,
    "use_ema_filter": True,
    "ema_period": 50, # Standard period for the EMA filter
}


# Scheduler
# [Source: 6]
scheduler_config = {
    "trade_time": "01:00",
}


# Market Data
# [Source: 7]
market_data_config = {
    "interval": "D", # 'D' for Daily
    "limit": 200,
}


# --- Trading Logic Section ---


def execute_trade_logic():
    """
    Fetches market data, evaluates the strategy, and places an order if conditions are met.
    """
    print("Running trading logic...")
    session = HTTP(api_key=api_key, api_secret=api_secret)


    try:
        # 1. Fetch historical market data (K-line)
        kline_response = session.get_kline(
            category=trading_config["category"],
            symbol=trading_config["symbol"],
            interval=market_data_config["interval"],
            limit=market_data_config["limit"],
        )


        if kline_response['retCode'] != 0:
            print(f"Error fetching kline data: {kline_response['retMsg']}")
            return


        # 2. Process data with Pandas
        klines = kline_response['result']['list']
        df = pd.DataFrame(klines, columns=["timestamp", "open", "high", "low", "close", "volume", "turnover"])
        df['close'] = df['close'].astype(float)
        df = df.iloc[::-1].reset_index(drop=True) # Bybit returns data newest first, so we reverse it


        # 3. Calculate technical indicators
        df.ta.rsi(append=True)
        if strategy_config["use_ema_filter"]:
            df.ta.ema(length=strategy_config["ema_period"], append=True)


        # 4. Get the latest values
        latest_close = df['close'].iloc[-1]
        latest_rsi = df['RSI_14'].iloc[-1]
        print(f"Latest Data for {trading_config['symbol']}: Close=${latest_close}, RSI={latest_rsi:.2f}")


        if strategy_config["use_ema_filter"]:
            latest_ema = df[f'EMA_{strategy_config["ema_period"]}'].iloc[-1]
            print(f"EMA({strategy_config['ema_period']}): ${latest_ema:.2f}")


        # 5. Evaluate strategy rules
        buy_conditions_met = True
        
        # Condition 1: RSI must be below the threshold
        if latest_rsi >= strategy_config["rsi_buy_threshold"]:
            print(f"Buy condition NOT met: RSI ({latest_rsi:.2f}) is not below threshold ({strategy_config['rsi_buy_threshold']}).")
            buy_conditions_met = False


        # Condition 2: If EMA filter is used, price must be below EMA
        if strategy_config["use_ema_filter"] and latest_close >= latest_ema:
            print(f"Buy condition NOT met: Price (${latest_close}) is not below EMA (${latest_ema:.2f}).")
            buy_conditions_met = False


        # 6. Place order if all conditions are met
        if buy_conditions_met:
            print("All buy conditions met. Preparing to place order.")
            
            # --- UNCOMMENT THE FOLLOWING BLOCK TO ENABLE LIVE TRADING ---
            #
            # print(f"Placing SPOT BUY order for {investment_config['daily_amount']} USDT of {trading_config['symbol']}.")
            # order_response = session.place_order(
            #     category=trading_config["category"],
            #     symbol=trading_config["symbol"],
            #     side="Buy",
            #     orderType="Market",
            #     qty=str(investment_config["daily_amount"]), # For spot, qty is the quote currency amount (USDT)
            # )
            #
            # if order_response['retCode'] == 0:
            #     print("Successfully placed buy order.")
            #     print(order_response['result'])
            # else:
            #     print(f"Error placing order: {order_response['retMsg']}")
            #
            # --- END OF LIVE TRADING BLOCK ---


            # For now, we will just simulate the action
            print("SIMULATION: Order for $1.00 of BTCUSDT would be placed.")


        else:
            print("Trade conditions not met. No action taken.")


    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# --- Scheduler Section ---


def main():
    """
    Main function to schedule and run the trading bot.
    """
    print("Trading bot started.")
    print(f"Trading will be attempted every day at {scheduler_config['trade_time']}.")
    
    # Schedule the job
    schedule.every().day.at(scheduler_config['trade_time']).do(execute_trade_logic)


    # Run the bot once immediately on startup for testing
    execute_trade_logic() 


    # Keep the script running to let the scheduler work
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()