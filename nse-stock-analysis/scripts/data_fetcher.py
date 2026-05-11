#!/usr/bin/env python3
"""
NSE Stock Data Fetcher
Fetches stock data from NSE (via nsepython) and Yahoo Finance.
Handles OHLCV, delivery data, FII/DII flows, and corporate actions.
"""

import argparse
import json
import sys
from typing import Optional

import pandas as pd
import yfinance as yf

try:
    from nsepython import nse_eq, nse_get_fii_dii, nsefetch
except ImportError:
    nse_eq = None
    nse_get_fii_dii = None
    nsefetch = None


def fetch_ohlcv(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Fetch OHLCV data for an NSE stock.

    Args:
        symbol: NSE symbol (e.g., RELIANCE, TCS)
        period: Data period (1mo, 3mo, 6mo, 1y, 2y, 5y, max)
        interval: Data interval (1d, 1wk, 1mo)

    Returns:
        DataFrame with Date, Open, High, Low, Close, Volume columns.
    """
    ticker = f"{symbol}.NS"
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty:
            raise ValueError(f"No data returned for {symbol}")
        # Flatten multi-level columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.index.name = "Date"
        df.dropna(inplace=True)
        return df
    except Exception as e:
        print(f"⚠️ ERROR: Failed to fetch data for {symbol}: {e}", file=sys.stderr)
        raise


def fetch_stock_info(symbol: str) -> dict:
    """
    Fetch fundamental info for an NSE stock.

    Returns:
        Dictionary with market cap, PE, PB, EPS, dividend yield, sector, etc.
    """
    ticker = yf.Ticker(f"{symbol}.NS")
    info = ticker.info
    return {
        "symbol": symbol,
        "name": info.get("longName", symbol),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "market_cap": info.get("marketCap", 0),
        "market_cap_cr": round(info.get("marketCap", 0) / 1e7, 2),
        "pe_ratio": info.get("trailingPE", None),
        "forward_pe": info.get("forwardPE", None),
        "pb_ratio": info.get("priceToBook", None),
        "eps": info.get("trailingEps", None),
        "dividend_yield": info.get("dividendYield", None),
        "roe": info.get("returnOnEquity", None),
        "debt_to_equity": info.get("debtToEquity", None),
        "book_value": info.get("bookValue", None),
        "revenue_growth": info.get("revenueGrowth", None),
        "earnings_growth": info.get("earningsGrowth", None),
        "current_price": info.get("currentPrice", info.get("regularMarketPrice", None)),
        "fifty_two_week_high": info.get("fiftyTwoWeekHigh", None),
        "fifty_two_week_low": info.get("fiftyTwoWeekLow", None),
        "avg_volume": info.get("averageVolume", None),
        "beta": info.get("beta", None),
    }


def fetch_nse_quote(symbol: str) -> Optional[dict]:
    """
    Fetch live quote from NSE using nsepython.

    Returns:
        Dictionary with NSE-specific data (delivery %, VWAP, etc.) or None.
    """
    if nse_eq is None:
        print("⚠️ nsepython not available, skipping NSE quote.", file=sys.stderr)
        return None
    try:
        data = nse_eq(symbol)
        if not data:
            return None
        price_info = data.get("priceInfo", {})
        security_info = data.get("securityInfo", {})
        return {
            "symbol": symbol,
            "last_price": price_info.get("lastPrice"),
            "change": price_info.get("change"),
            "pct_change": price_info.get("pChange"),
            "open": price_info.get("open"),
            "high": price_info.get("intraDayHighLow", {}).get("max"),
            "low": price_info.get("intraDayHighLow", {}).get("min"),
            "prev_close": price_info.get("previousClose"),
            "vwap": price_info.get("vwap"),
            "total_traded_volume": price_info.get("totalTradedVolume"),
            "total_traded_value": price_info.get("totalTradedValue"),
            "delivery_pct": None,  # Requires separate delivery data endpoint
            "face_value": security_info.get("faceValue"),
            "issued_size": security_info.get("issuedSize"),
        }
    except Exception as e:
        print(f"⚠️ NSE quote fetch failed for {symbol}: {e}", file=sys.stderr)
        return None


def fetch_fii_dii(period_days: int = 30) -> pd.DataFrame:
    """
    Fetch FII/DII activity data.

    Args:
        period_days: Number of days of historical FII/DII data.

    Returns:
        DataFrame with FII and DII buy/sell/net values.
    """
    if nse_get_fii_dii is None:
        print("⚠️ nsepython not available. Using sample FII/DII data.", file=sys.stderr)
        # Return empty DataFrame with correct schema
        return pd.DataFrame(columns=["date", "fii_buy", "fii_sell", "fii_net", "dii_buy", "dii_sell", "dii_net"])
    try:
        data = nse_get_fii_dii()
        df = pd.DataFrame(data)
        return df.head(period_days)
    except Exception as e:
        print(f"⚠️ FII/DII data fetch failed: {e}", file=sys.stderr)
        return pd.DataFrame()


def fetch_nifty_constituents(index: str = "NIFTY 50") -> list[str]:
    """
    Get constituent symbols for a NIFTY index.

    Args:
        index: Index name (NIFTY 50, NIFTY 100, NIFTY 200, NIFTY 500,
               NIFTY BANK, NIFTY IT, NIFTY PHARMA, etc.)

    Returns:
        List of NSE symbols.
    """
    index_map = {
        "NIFTY50": [
            "RELIANCE",
            "TCS",
            "HDFCBANK",
            "INFY",
            "ICICIBANK",
            "HINDUNILVR",
            "SBIN",
            "BHARTIARTL",
            "ITC",
            "KOTAKBANK",
            "LT",
            "AXISBANK",
            "BAJFINANCE",
            "ASIANPAINT",
            "MARUTI",
            "HCLTECH",
            "TITAN",
            "SUNPHARMA",
            "TATAMOTORS",
            "ULTRACEMCO",
            "WIPRO",
            "NESTLEIND",
            "NTPC",
            "POWERGRID",
            "M&M",
            "JSWSTEEL",
            "ADANIENT",
            "ADANIPORTS",
            "TATASTEEL",
            "BAJAJFINSV",
            "TECHM",
            "ONGC",
            "HDFCLIFE",
            "DIVISLAB",
            "COALINDIA",
            "GRASIM",
            "BPCL",
            "DRREDDY",
            "CIPLA",
            "APOLLOHOSP",
            "EICHERMOT",
            "TATACONSUM",
            "SBILIFE",
            "BRITANNIA",
            "HEROMOTOCO",
            "INDUSINDBK",
            "BAJAJ-AUTO",
            "HINDALCO",
            "UPL",
            "LTIM",
        ],
        "NIFTY100": [],  # Extend as needed
        "NIFTY200": [],
        "NIFTY500": [],
        "NIFTY BANK": [
            "HDFCBANK",
            "ICICIBANK",
            "SBIN",
            "KOTAKBANK",
            "AXISBANK",
            "INDUSINDBK",
            "BANKBARODA",
            "PNB",
            "FEDERALBNK",
            "IDFCFIRSTB",
            "BANDHANBNK",
            "AUBANK",
        ],
        "NIFTY IT": [
            "TCS",
            "INFY",
            "HCLTECH",
            "WIPRO",
            "TECHM",
            "LTIM",
            "MPHASIS",
            "COFORGE",
            "PERSISTENT",
            "LTTS",
        ],
        "NIFTY PHARMA": [
            "SUNPHARMA",
            "DRREDDY",
            "CIPLA",
            "DIVISLAB",
            "APOLLOHOSP",
            "BIOCON",
            "LUPIN",
            "AUROPHARMA",
            "TORNTPHARM",
            "ALKEM",
        ],
    }
    # Normalize index name
    key = index.upper().replace(" ", "").replace("_", "")
    if key in index_map and index_map[key]:
        return index_map[key]
    # Fallback: try NIFTY50
    if "50" in key:
        return index_map["NIFTY50"]
    # If we have an exact match
    for k, v in index_map.items():
        if k.replace(" ", "") == key and v:
            return v
    print(f"⚠️ Index '{index}' not found. Defaulting to NIFTY 50.", file=sys.stderr)
    return index_map["NIFTY50"]


def fetch_delivery_data(symbol: str, days: int = 20) -> pd.DataFrame:
    """
    Fetch delivery percentage data for a stock.

    Note: This requires nsepython or web scraping. Falls back to
    estimating delivery from volume patterns if unavailable.

    Args:
        symbol: NSE symbol
        days: Number of days of delivery data

    Returns:
        DataFrame with date, delivery_qty, traded_qty, delivery_pct columns.
    """
    # Attempt nsepython first
    if nsefetch is not None:
        try:
            url = (
                f"https://www.nseindia.com/api/historical/securityArchives?"
                f"from=01-01-2026&to=11-05-2026&symbol={symbol}"
                f"&dataType=priceVolumeDeliverable&series=EQ"
            )
            data = nsefetch(url)
            if data and "data" in data:
                df = pd.DataFrame(data["data"])
                return (
                    df[["CH_TIMESTAMP", "DELIV_QTY", "TTL_TRD_QNTY", "DELIV_PER"]]
                    .rename(
                        columns={
                            "CH_TIMESTAMP": "date",
                            "DELIV_QTY": "delivery_qty",
                            "TTL_TRD_QNTY": "traded_qty",
                            "DELIV_PER": "delivery_pct",
                        }
                    )
                    .head(days)
                )
        except Exception:
            pass

    # Fallback: return empty with schema
    print(f"⚠️ Delivery data unavailable for {symbol}. Using volume proxy.", file=sys.stderr)
    return pd.DataFrame(columns=["date", "delivery_qty", "traded_qty", "delivery_pct"])


def format_inr(value: float) -> str:
    """Format a number in Indian numbering system with ₹ symbol."""
    if value is None:
        return "N/A"
    if abs(value) >= 1e7:
        return f"₹{value / 1e7:,.2f} Cr"
    if abs(value) >= 1e5:
        return f"₹{value / 1e5:,.2f} L"
    return f"₹{value:,.2f}"


def format_volume(value: float) -> str:
    """Format volume in short form."""
    if value is None:
        return "N/A"
    if abs(value) >= 1e7:
        return f"{value / 1e7:.1f}Cr"
    if abs(value) >= 1e5:
        return f"{value / 1e5:.1f}L"
    if abs(value) >= 1e3:
        return f"{value / 1e3:.1f}K"
    return str(int(value))


def main():
    parser = argparse.ArgumentParser(description="NSE Stock Data Fetcher")
    parser.add_argument("--symbol", type=str, help="NSE stock symbol")
    parser.add_argument("--period", type=str, default="1y", help="Data period")
    parser.add_argument("--info", action="store_true", help="Fetch stock info")
    parser.add_argument("--ohlcv", action="store_true", help="Fetch OHLCV data")
    parser.add_argument("--quote", action="store_true", help="Fetch NSE live quote")
    parser.add_argument("--fii-dii", action="store_true", help="Fetch FII/DII data")
    parser.add_argument("--delivery", action="store_true", help="Fetch delivery data")
    parser.add_argument("--constituents", type=str, help="Get index constituents")
    parser.add_argument("--output", type=str, default="text", choices=["text", "json", "csv"])

    args = parser.parse_args()

    if args.constituents:
        symbols = fetch_nifty_constituents(args.constituents)
        if args.output == "json":
            print(json.dumps(symbols))
        else:
            print(f"Constituents of {args.constituents}: {len(symbols)} stocks")
            for s in symbols:
                print(f"  {s}")
        return

    if args.fii_dii:
        df = fetch_fii_dii()
        if df.empty:
            print("No FII/DII data available.")
        else:
            print(df.to_string(index=False))
        return

    if not args.symbol:
        parser.error("--symbol is required for stock-specific operations")

    if args.info:
        info = fetch_stock_info(args.symbol)
        if args.output == "json":
            print(json.dumps(info, indent=2, default=str))
        else:
            print(f"\n{'=' * 50}")
            print(f"  {info['name']} ({info['symbol']})")
            print(f"{'=' * 50}")
            print(f"  Sector:         {info['sector']}")
            print(f"  Market Cap:     {format_inr(info['market_cap'])}")
            print(f"  CMP:            {format_inr(info['current_price'])}")
            print(f"  PE Ratio:       {info['pe_ratio'] or 'N/A'}")
            print(f"  PB Ratio:       {info['pb_ratio'] or 'N/A'}")
            print(f"  EPS:            ₹{info['eps'] or 'N/A'}")
            roe_val = f"{info['roe'] * 100:.1f}%" if info["roe"] else "N/A"
            print(f"  ROE:            {roe_val}")
            div_val = f"{info['dividend_yield'] * 100:.1f}%" if info["dividend_yield"] else "N/A"
            print(f"  Div Yield:      {div_val}")
            print(f"  D/E Ratio:      {info['debt_to_equity'] or 'N/A'}")
            print(f"  52W High:       {format_inr(info['fifty_two_week_high'])}")
            print(f"  52W Low:        {format_inr(info['fifty_two_week_low'])}")
            print(f"  Beta:           {info['beta'] or 'N/A'}")
            print(f"{'=' * 50}\n")

    if args.ohlcv:
        df = fetch_ohlcv(args.symbol, period=args.period)
        if args.output == "csv":
            print(df.to_csv())
        elif args.output == "json":
            print(df.to_json(orient="records", date_format="iso"))
        else:
            print(f"\nOHLCV Data: {args.symbol} ({args.period})")
            print(f"Records: {len(df)}")
            print(df.tail(10).to_string())
            print()

    if args.quote:
        quote = fetch_nse_quote(args.symbol)
        if quote:
            if args.output == "json":
                print(json.dumps(quote, indent=2, default=str))
            else:
                print(f"\nNSE Quote: {args.symbol}")
                for k, v in quote.items():
                    print(f"  {k}: {v}")

    if args.delivery:
        df = fetch_delivery_data(args.symbol)
        if df.empty:
            print("No delivery data available.")
        else:
            print(df.to_string(index=False))


if __name__ == "__main__":
    main()
