"""Smoke test: verify IBKR Gateway connectivity and fetch sample bars."""

import asyncio
import sys

sys.path.insert(0, "src")

from stockpredict.data.ibkr_client import IBKRClient
from config.settings import get_settings


async def main():
    settings = get_settings()
    client = IBKRClient(settings.ibkr)

    print(f"Connecting to IBKR at {settings.ibkr.host}:{settings.ibkr.port}...")
    try:
        await client.connect()
        print("Connected!")

        ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
        print(f"\nFetching 30 days of daily bars for {ticker}...")
        df = await client.historical_bars(ticker, duration="30 D", bar_size="1 day")

        if df.empty:
            print("No data returned. Check your market data subscriptions.")
        else:
            print(f"\nGot {len(df)} bars:")
            print(df.tail(10).to_string())

        print(f"\nFetching quote for {ticker}...")
        q = await client.quote(ticker)
        print(f"Quote: {q}")

    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        await client.disconnect()
        print("\nDisconnected.")


if __name__ == "__main__":
    asyncio.run(main())
