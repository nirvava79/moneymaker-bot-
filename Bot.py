"""
Autonomous $10 BTC Trading Bot with Self-Termination Safety
- Starts with a $10 investment allocation.
- Automatically trades based on market trends.
- Automatically terminates execution (kills itself) if it loses money or fails to grow equity.
"""
import os
import sys
import time
import ccxt

# ---------------- Settings ----------------
EXCHANGE = "kraken"        # Exchange ID
SYMBOL = "BTC/USD"         # Trading pair
TIMEFRAME = "1h"           # Candle timeframe
FAST, SLOW = 20, 50        # Moving average parameters
START_CASH = 10.0          # Exact $10 starting investment
POSITION_FRACTION = 1.0    # Use the full $10 budget for the trade
STOP_LOSS = 0.02           # 2% tight stop loss to protect the $10
FEE = 0.001                # Fee estimation
# ------------------------------------------

def make_exchange(authed=False):
    cfg = {"enableRateLimit": True}
    if authed:
        cfg["apiKey"] = os.environ.get("EXCHANGE_API_KEY", "")
        cfg["secret"] = os.environ.get("EXCHANGE_API_SECRET", "")
    return getattr(ccxt, EXCHANGE)(cfg)

def sma(vals, n, i):
    return sum(vals[i - n + 1 : i + 1]) / n

def run_bot():
    ex = make_exchange(authed=False) # Change to True if using live keys
    print(f"Initializing $10 Autonomous BTC Bot on {EXCHANGE}...")
    
    initial_capital = START_CASH
    entry_price = 0.0
    position_open = False

    while True:
        try:
            # Fetch current market price
            ticker = ex.fetch_ticker(SYMBOL)
            px = ticker["last"]
            
            # Simulate or fetch current equity based on our $10 starting point
            # (Using Paper balance simulation for safety)
            current_equity = initial_capital if not position_open else (initial_capital / entry_price) * px

            print(f"Current Price: {px} | Equity: ${current_equity:.2f}")

            # SELF-TERMINATION CONDITION: 
            # If equity drops below the initial $10 investment, "kill" the bot immediately.
            if current_equity < initial_capital:
                print(f"[CRITICAL] Bot failed to make money or experienced a loss. Current equity: ${current_equity:.2f}.")
                print("[SHUTDOWN] Terminating bot process to protect capital.")
                sys.exit(0)

            # Fetch candles for trend analysis
            candles = ex.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=SLOW + 5)
            closes = [c[4] for c in candles]
            
            if len(closes) >= SLOW:
                f = sma(closes, FAST, len(closes) - 1)
                s = sma(closes, SLOW, len(closes) - 1)
                is_uptrend = f > s

                # Execution Logic
                if is_uptrend and not position_open:
                    entry_price = px
                    position_open = True
                    print(f"[BUY] Uptrend detected. Invested ${initial_capital} at {px}")

                elif position_open:
                    # Check stop-loss
                    if px <= entry_price * (1 - STOP_LOSS):
                        position_open = False
                        print(f"[STOP LOSS] Price dropped. Position closed at {px}")
                    elif not is_uptrend:
                        position_open = False
                        print(f"[SELL] Trend reversed. Position closed at {px}")

        except ccxt.NetworkError as e:
            print(f"Network error (retrying): {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            sys.exit(1)

        # Pause before the next check cycle
        time.sleep(60)

if __name__ == "__main__":
    run_bot()
