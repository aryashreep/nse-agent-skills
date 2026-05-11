#!/usr/bin/env python3
"""
NSE Sector Comparison & Relative Strength Analyzer
Compares sector performance, ranks stocks by relative strength,
and provides sector rotation quadrant analysis.
"""

import argparse
import sys
from datetime import datetime

import numpy as np
import pandas as pd
import pandas_ta as ta

from data_fetcher import fetch_nifty_constituents, fetch_ohlcv, format_inr


def compute_returns(symbol: str, period: str = "3mo") -> dict:
    """Compute returns and relative strength metrics for a symbol."""
    try:
        df = fetch_ohlcv(symbol, period=period)
        if len(df) < 10:
            return {}

        close = df["Close"]
        returns = {
            "symbol": symbol,
            "current_price": round(close.iloc[-1], 2),
            "period_return": round(((close.iloc[-1] / close.iloc[0]) - 1) * 100, 2),
            "volatility": round(close.pct_change().std() * np.sqrt(252) * 100, 2),
        }

        # Rolling returns
        if len(close) >= 5:
            returns["1w_return"] = round(((close.iloc[-1] / close.iloc[-5]) - 1) * 100, 2)
        if len(close) >= 20:
            returns["1m_return"] = round(((close.iloc[-1] / close.iloc[-20]) - 1) * 100, 2)

        # RSI
        rsi = ta.rsi(close, length=14)
        if rsi is not None and len(rsi) > 0:
            returns["rsi"] = round(rsi.iloc[-1], 1) if not pd.isna(rsi.iloc[-1]) else 0

        # Momentum score: rate of change
        if len(close) >= 63:
            roc = ((close.iloc[-1] / close.iloc[-63]) - 1) * 100
            returns["momentum"] = round(roc, 2)
        else:
            returns["momentum"] = returns["period_return"]

        return returns
    except Exception as e:
        print(f"  ⚠️ Error computing returns for {symbol}: {e}", file=sys.stderr)
        return {}


def compute_relative_strength(
    symbol: str,
    benchmark_symbol: str = "^NSEI",
    period: str = "3mo",
) -> float:
    """
    Compute relative strength of a stock vs benchmark.
    RS = (Stock Return / Benchmark Return) * 100
    """
    try:
        stock_df = fetch_ohlcv(symbol, period=period)
        bench_df = fetch_ohlcv(benchmark_symbol.replace("^", ""), period=period)

        if len(stock_df) < 10 or len(bench_df) < 10:
            return 0

        stock_return = (stock_df["Close"].iloc[-1] / stock_df["Close"].iloc[0]) - 1
        bench_return = (bench_df["Close"].iloc[-1] / bench_df["Close"].iloc[0]) - 1

        if bench_return == 0:
            return 0

        rs = (stock_return / abs(bench_return)) * 100
        return round(rs, 2)
    except Exception:
        return 0


def rank_by_relative_strength(
    symbols: list[str],
    period: str = "3mo",
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Rank stocks by relative strength.

    Args:
        symbols: List of NSE symbols
        period: Analysis period
        top_n: Number of top stocks to return

    Returns:
        DataFrame ranked by relative strength score.
    """
    results = []
    total = len(symbols)

    # First get benchmark return
    try:
        nifty_df = fetch_ohlcv("NIFTY 50", period=period)
        if nifty_df.empty:
            # Fallback: use ^NSEI
            import yfinance as yf
            nifty_df = yf.download("^NSEI", period=period, progress=False)
            if isinstance(nifty_df.columns, pd.MultiIndex):
                nifty_df.columns = nifty_df.columns.get_level_values(0)
        nifty_return = ((nifty_df["Close"].iloc[-1] / nifty_df["Close"].iloc[0]) - 1) * 100
    except Exception:
        nifty_return = 0

    for i, symbol in enumerate(symbols):
        try:
            print(f"  Ranking {symbol} ({i+1}/{total})...", end="\r", file=sys.stderr)
            data = compute_returns(symbol, period=period)
            if not data:
                continue

            period_ret = data.get("period_return", 0)
            vs_nifty = period_ret - nifty_return

            # RS Score: normalized 0-100 (will be adjusted after all stocks computed)
            results.append({
                "Symbol": symbol,
                "CMP": f"₹{data['current_price']:,.2f}",
                "Period Return": f"{period_ret:+.1f}%",
                "vs NIFTY 50": f"{vs_nifty:+.1f}%",
                "Momentum": data.get("momentum", 0),
                "RSI": data.get("rsi", 0),
                "Volatility": f"{data.get('volatility', 0):.1f}%",
                "_return": period_ret,
                "_momentum": data.get("momentum", 0),
            })
        except Exception as e:
            print(f"  ⚠️ Skipping {symbol}: {e}", file=sys.stderr)
            continue

    print(" " * 60, end="\r", file=sys.stderr)

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)

    # Compute RS Score (percentile rank based on return + momentum)
    df["_composite"] = df["_return"] * 0.6 + df["_momentum"] * 0.4
    df["RS Score"] = df["_composite"].rank(pct=True) * 100
    df["RS Score"] = df["RS Score"].round(1)

    # Trend emoji
    df["Trend"] = df["_return"].apply(
        lambda x: "🟢 Strong" if x > 10 else "🟡 Moderate" if x > 0 else "🔴 Weak"
    )

    # Sort and select top N
    df = df.sort_values("RS Score", ascending=False).head(top_n)

    # Add rank
    df.insert(0, "Rank", range(1, len(df) + 1))

    # Drop internal columns
    df = df.drop(columns=["_return", "_momentum", "_composite"])

    return df


def compare_sectors(
    sectors: list[str],
    period: str = "3mo",
    benchmark: str = "NIFTY 50",
) -> pd.DataFrame:
    """
    Compare sector index performance.

    Args:
        sectors: List of sector index names
        period: Comparison period
        benchmark: Benchmark index

    Returns:
        DataFrame comparing sector performance.
    """
    sector_tickers = {
        "NIFTY IT": "^CNXIT",
        "NIFTY BANK": "^NSEBANK",
        "NIFTY PHARMA": "^CNXPHARMA",
        "NIFTY 50": "^NSEI",
        "NIFTY FMCG": "^CNXFMCG",
        "NIFTY AUTO": "^CNXAUTO",
        "NIFTY METAL": "^CNXMETAL",
        "NIFTY REALTY": "^CNXREALTY",
        "NIFTY ENERGY": "^CNXENERGY",
        "NIFTY INFRA": "^CNXINFRA",
        "NIFTY PSE": "^CNXPSE",
    }

    results = []
    for sector in sectors:
        sector_upper = sector.upper().strip()
        ticker = sector_tickers.get(sector_upper)
        if not ticker:
            print(f"  ⚠️ Unknown sector index: {sector}", file=sys.stderr)
            continue

        try:
            import yfinance as yf
            df = yf.download(ticker, period=period, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if df.empty:
                continue

            close = df["Close"]
            period_ret = ((close.iloc[-1] / close.iloc[0]) - 1) * 100

            results.append({
                "Sector": sector_upper,
                "Current": f"{close.iloc[-1]:,.0f}",
                "Return": f"{period_ret:+.1f}%",
                "_return": period_ret,
            })
        except Exception as e:
            print(f"  ⚠️ Error fetching {sector}: {e}", file=sys.stderr)

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)
    df = df.sort_values("_return", ascending=False)
    df["Rank"] = range(1, len(df) + 1)
    df["Trend"] = df["_return"].apply(
        lambda x: "🟢 Leading" if x > 5 else "🟡 Neutral" if x > -5 else "🔴 Lagging"
    )
    df = df.drop(columns=["_return"])
    return df[["Rank", "Sector", "Current", "Return", "Trend"]]


def sector_rotation_quadrant(period: str = "6mo") -> str:
    """
    Sector rotation quadrant analysis.
    Classifies sectors into: Leading, Weakening, Lagging, Improving.
    Based on momentum and relative strength change.
    """
    sectors = [
        "NIFTY IT", "NIFTY BANK", "NIFTY PHARMA", "NIFTY FMCG",
        "NIFTY AUTO", "NIFTY METAL", "NIFTY ENERGY", "NIFTY REALTY",
    ]

    sector_tickers = {
        "NIFTY IT": "^CNXIT",
        "NIFTY BANK": "^NSEBANK",
        "NIFTY PHARMA": "^CNXPHARMA",
        "NIFTY FMCG": "^CNXFMCG",
        "NIFTY AUTO": "^CNXAUTO",
        "NIFTY METAL": "^CNXMETAL",
        "NIFTY ENERGY": "^CNXENERGY",
        "NIFTY REALTY": "^CNXREALTY",
    }

    results = {"Leading": [], "Weakening": [], "Lagging": [], "Improving": []}

    for sector in sectors:
        ticker = sector_tickers.get(sector)
        if not ticker:
            continue
        try:
            import yfinance as yf
            df = yf.download(ticker, period=period, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if len(df) < 40:
                continue

            close = df["Close"]
            # Momentum: current return
            full_return = ((close.iloc[-1] / close.iloc[0]) - 1) * 100
            # RS change: compare first half vs second half return
            mid = len(close) // 2
            first_half = ((close.iloc[mid] / close.iloc[0]) - 1) * 100
            second_half = ((close.iloc[-1] / close.iloc[mid]) - 1) * 100
            rs_improving = second_half > first_half

            if full_return > 0 and rs_improving:
                results["Leading"].append(f"  {sector} ({full_return:+.1f}%)")
            elif full_return > 0 and not rs_improving:
                results["Weakening"].append(f"  {sector} ({full_return:+.1f}%)")
            elif full_return <= 0 and not rs_improving:
                results["Lagging"].append(f"  {sector} ({full_return:+.1f}%)")
            else:
                results["Improving"].append(f"  {sector} ({full_return:+.1f}%)")

        except Exception:
            continue

    report = []
    report.append("═" * 55)
    report.append("  SECTOR ROTATION QUADRANT ANALYSIS")
    report.append(f"  Period: {period} | Date: {datetime.now().strftime('%Y-%m-%d')}")
    report.append("═" * 55)
    report.append("")

    report.append("🟢 LEADING (Strong momentum + Improving RS)")
    report.extend(results.get("Leading", ["  None"]))
    report.append("")

    report.append("🟡 WEAKENING (Strong momentum + Declining RS)")
    report.extend(results.get("Weakening", ["  None"]))
    report.append("")

    report.append("🔴 LAGGING (Weak momentum + Declining RS)")
    report.extend(results.get("Lagging", ["  None"]))
    report.append("")

    report.append("🔵 IMPROVING (Weak momentum + Improving RS)")
    report.extend(results.get("Improving", ["  None"]))
    report.append("")
    report.append("═" * 55)

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="NSE Sector Comparison & Relative Strength")
    parser.add_argument("--sectors", type=str, help="Comma-separated sector indices")
    parser.add_argument("--universe", type=str, help="Stock universe for RS ranking")
    parser.add_argument("--rank-by", type=str, choices=["relative-strength"],
                        help="Ranking method")
    parser.add_argument("--period", type=str, default="3mo", help="Analysis period")
    parser.add_argument("--benchmark", type=str, default="NIFTY 50", help="Benchmark index")
    parser.add_argument("--top", type=int, default=10, help="Top N stocks to show")
    parser.add_argument("--rotation", action="store_true", help="Sector rotation quadrant")
    parser.add_argument("--output", type=str, default="text", choices=["text", "json", "csv"])

    args = parser.parse_args()

    if args.rotation:
        print(sector_rotation_quadrant(period=args.period))
        return

    if args.sectors:
        sector_list = [s.strip() for s in args.sectors.split(",")]
        print(f"\n📊 Sector Comparison ({args.period}):\n", file=sys.stderr)
        result = compare_sectors(sector_list, period=args.period, benchmark=args.benchmark)
        if result.empty:
            print("No sector data available.")
        else:
            print(result.to_string(index=False))
        return

    if args.universe and args.rank_by:
        symbols = fetch_nifty_constituents(args.universe)
        print(f"\n📊 Relative Strength Ranking — {args.universe} ({args.period}):\n", file=sys.stderr)
        result = rank_by_relative_strength(symbols, period=args.period, top_n=args.top)
        if result.empty:
            print("No data available for ranking.")
        else:
            if args.output == "json":
                print(result.to_json(orient="records", indent=2))
            elif args.output == "csv":
                print(result.to_csv(index=False))
            else:
                print(f"\n✅ Top {args.top} by Relative Strength:\n")
                print(result.to_string(index=False))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
