#!/usr/bin/env python3
import requests
import json
from datetime import datetime

class Stocks:
    """Fetch stock market data using yfinance-compatible API"""

    def __init__(self):
        # No API key needed for Yahoo Finance
        pass

    def get_quote(self, symbol):
        """Get real-time quote for a single stock symbol using Yahoo Finance API"""
        try:
            # Use Yahoo Finance query API (no API key needed)
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                'interval': '1d',
                'range': '1d'
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'chart' not in data or 'result' not in data['chart']:
                return None

            result = data['chart']['result'][0]
            meta = result['meta']

            current_price = meta.get('regularMarketPrice', 0)
            previous_close = meta.get('chartPreviousClose', meta.get('previousClose', 0))
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close > 0 else 0

            return {
                'symbol': symbol,
                'price': float(current_price),
                'change': float(change),
                'change_percent': f"{change_percent:.2f}",
                'volume': int(meta.get('regularMarketVolume', 0)),
                'latest_trading_day': datetime.fromtimestamp(meta.get('regularMarketTime', 0)).strftime('%Y-%m-%d')
            }
        except Exception as e:
            print(f"Error fetching quote for {symbol}: {e}")
            return None

    def get_multiple_quotes(self, symbols):
        """Get quotes for multiple symbols"""
        quotes = {}
        for symbol in symbols:
            quote = self.get_quote(symbol)
            if quote:
                quotes[symbol] = quote
        return quotes

    def format_quote(self, quote):
        """Format a single quote for display"""
        if not quote:
            return "No data available"

        change = quote['change']
        change_pct = float(quote['change_percent'])

        # Determine emoji based on change
        if change > 0:
            emoji = '📈'
            sign = '+'
        elif change < 0:
            emoji = '📉'
            sign = ''
        else:
            emoji = '➡️'
            sign = ''

        return (
            f"{emoji} **{quote['symbol']}**: ${quote['price']:.2f} "
            f"({sign}{change:.2f}, {sign}{change_pct:.2f}%)"
        )

    def format_summary(self, symbols=None):
        """
        Format stock summary for email display
        Default symbols: MSFT, NVDA, ^DJI (Dow), ^GSPC (S&P 500)
        """
        if symbols is None:
            symbols = ['MSFT', 'NVDA', '^DJI', '^GSPC']

        quotes = self.get_multiple_quotes(symbols)

        if not quotes:
            return "❌ Unable to fetch stock data"

        output = []
        for symbol in symbols:
            if symbol in quotes:
                output.append(f"- {self.format_quote(quotes[symbol])}")

        # Add timestamp
        now = datetime.now().strftime('%I:%M %p %Z')
        output.append(f"\n*Market data as of {now}*")

        return "\n".join(output)


if __name__ == "__main__":
    # Test the module
    stocks = Stocks()
    print(stocks.format_summary())
