#!/usr/bin/env python3
"""
NSE Stock Screener
Multi-factor screening for NSE stocks: technical, fundamental, and volume-based filters.
Supports triple EMA crossover, volume breakout, PPA, and delivery breakout scans.
"""

import argparse
import sys
from typing import Optional

import numpy as np
import pandas as pd
import pandas_ta as ta

from data_fetcher import (
    fetch_nifty_constituents,
    fetch_ohlcv,
    fetch_stock_info,
    format_volume,
)


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute standard technical indicators on OHLCV data."""
    df = df.copy()
    df["EMA9"] = ta.ema(df["Close"], length=9)
    df["EMA21"] = ta.ema(df["Close"], length=21)
    df["EMA55"] = ta.ema(df["Close"], length=55)
    df["EMA200"] = ta.ema(df["Close"], length=200)
    df["RSI"] = ta.rsi(df["Close"], length=14)
    df["ADX"] = ta.adx(df["High"], df["Low"], df["Close"], length=14)["ADX_14"]
    atr = ta.atr(df["High"], df["Low"], df["Close"], length=14)
    df["ATR"] = atr
    df["ATR_PCT"] = (atr / df["Close"]) * 100
    df["VOL_SMA20"] = df["Volume"].rolling(20).mean()
    df["VOL_RATIO"] = df["Volume"] / df["VOL_SMA20"]
    # Bollinger Bands
    bbands = ta.bbands(df["Close"], length=20, std=2)
    if bbands is not None:
        df["BB_UPPER"] = bbands.iloc[:, 0]
        df["BB_MID"] = bbands.iloc[:, 1]
        df["BB_LOWER"] = bbands.iloc[:, 2]
    return df


def screen_basic(
    symbols: list[str],
    rsi_below: Optional[float] = None,
    rsi_above: Optional[float] = None,
    above_ema: Optional[int] = None,
    below_ema: Optional[int] = None,
    min_volume: Optional[int] = None,
    min_delivery_pct: Optional[float] = None,
    sector_filter: Optional[str] = None,
    min_market_cap: Optional[float] = None,
) -> pd.DataFrame:
    """
    Screen stocks based on technical and fundamental filters.

    Returns:
        DataFrame with matching stocks and their metrics.
    """
    results = []
    total = len(symbols)

    for i, symbol in enumerate(symbols):
        try:
            print(f"  Screening {symbol} ({i + 1}/{total})...", end="\r", file=sys.stderr)
            df = fetch_ohlcv(symbol, period="1y")
            if len(df) < 50:
                continue

            df = compute_indicators(df)
            latest = df.iloc[-1]
            cmp = latest["Close"]
            rsi = latest["RSI"]
            vol = latest["Volume"]
            vol_ratio = latest["VOL_RATIO"]

            # Apply filters
            if rsi_below is not None and (pd.isna(rsi) or rsi > rsi_below):
                continue
            if rsi_above is not None and (pd.isna(rsi) or rsi < rsi_above):
                continue
            if above_ema is not None:
                ema_col = f"EMA{above_ema}"
                if ema_col in df.columns and not pd.isna(latest.get(ema_col)):
                    if cmp <= latest[ema_col]:
                        continue
                    ema_dist = ((cmp - latest[ema_col]) / latest[ema_col]) * 100
                else:
                    continue
            if below_ema is not None:
                ema_col = f"EMA{below_ema}"
                if ema_col in df.columns and not pd.isna(latest.get(ema_col)):
                    if cmp >= latest[ema_col]:
                        continue
                else:
                    continue
            if min_volume is not None and vol < min_volume:
                continue
            if min_market_cap is not None:
                try:
                    info = fetch_stock_info(symbol)
                    if info["market_cap_cr"] < min_market_cap:
                        continue
                except Exception:
                    continue
            if sector_filter is not None:
                try:
                    info = fetch_stock_info(symbol)
                    if sector_filter.lower() not in info.get("sector", "").lower():
                        continue
                except Exception:
                    continue

            # EMA alignment
            ema9 = latest.get("EMA9", np.nan)
            ema21 = latest.get("EMA21", np.nan)
            ema55 = latest.get("EMA55", np.nan)
            if not any(pd.isna(x) for x in [ema9, ema21, ema55]):
                if ema9 > ema21 > ema55:
                    alignment = "🟢 Bullish"
                elif ema9 < ema21 < ema55:
                    alignment = "🔴 Bearish"
                else:
                    alignment = "🟡 Mixed"
            else:
                alignment = "N/A"

            result = {
                "Symbol": symbol,
                "CMP": round(cmp, 2),
                "RSI(14)": round(rsi, 1) if not pd.isna(rsi) else "N/A",
                "Vol Ratio": f"{vol_ratio:.1f}x" if not pd.isna(vol_ratio) else "N/A",
                "EMA Align": alignment,
            }
            if above_ema is not None:
                result[f"vs EMA{above_ema}"] = f"+{ema_dist:.1f}%"

            results.append(result)

        except Exception as e:
            print(f"  ⚠️ Skipping {symbol}: {e}", file=sys.stderr)
            continue

    print(" " * 60, end="\r", file=sys.stderr)  # Clear progress line
    return pd.DataFrame(results)


def scan_triple_ema_crossover(
    symbols: list[str],
    lookback: int = 5,
) -> pd.DataFrame:
    """
    Scan for stocks where 9 EMA crossed above 21 EMA while both above 55 EMA.

    Args:
        symbols: List of NSE symbols to scan
        lookback: Number of days to look back for crossover

    Returns:
        DataFrame with crossover signals.
    """
    results = []
    total = len(symbols)

    for i, symbol in enumerate(symbols):
        try:
            print(f"  Scanning {symbol} ({i + 1}/{total})...", end="\r", file=sys.stderr)
            df = fetch_ohlcv(symbol, period="6mo")
            if len(df) < 60:
                continue

            df = compute_indicators(df)
            recent = df.tail(lookback + 1)

            for j in range(1, len(recent)):
                row = recent.iloc[j]
                prev = recent.iloc[j - 1]

                ema9 = row.get("EMA9", np.nan)
                ema21 = row.get("EMA21", np.nan)
                ema55 = row.get("EMA55", np.nan)
                prev_ema9 = prev.get("EMA9", np.nan)
                prev_ema21 = prev.get("EMA21", np.nan)

                if any(pd.isna(x) for x in [ema9, ema21, ema55, prev_ema9, prev_ema21]):
                    continue

                # Bullish crossover: 9 EMA crosses above 21 EMA, both above 55 EMA
                if prev_ema9 <= prev_ema21 and ema9 > ema21 and ema9 > ema55 and ema21 > ema55:
                    vol_surge = row["VOL_RATIO"] if not pd.isna(row["VOL_RATIO"]) else 0
                    results.append(
                        {
                            "Symbol": symbol,
                            "Crossover Date": recent.index[j].strftime("%Y-%m-%d"),
                            "CMP": round(row["Close"], 2),
                            "EMA9": round(ema9, 2),
                            "EMA21": round(ema21, 2),
                            "EMA55": round(ema55, 2),
                            "Vol Surge": f"{vol_surge:.1f}x",
                            "Signal": "🟢 BUY" if vol_surge > 1.5 else "🟡 WATCH",
                        }
                    )
                    break  # Only latest crossover per stock

        except Exception as e:
            print(f"  ⚠️ Skipping {symbol}: {e}", file=sys.stderr)
            continue

    print(" " * 60, end="\r", file=sys.stderr)
    return pd.DataFrame(results)


def scan_volume_breakout(
    symbols: list[str],
    volume_multiplier: float = 2.0,
    price_change_pct: float = 2.0,
) -> pd.DataFrame:
    """
    Scan for stocks with unusual volume surge and price movement.

    Args:
        symbols: List of NSE symbols
        volume_multiplier: Minimum volume vs 20-day average
        price_change_pct: Minimum absolute price change percentage

    Returns:
        DataFrame with volume breakout signals.
    """
    results = []
    total = len(symbols)

    for i, symbol in enumerate(symbols):
        try:
            print(f"  Scanning {symbol} ({i + 1}/{total})...", end="\r", file=sys.stderr)
            df = fetch_ohlcv(symbol, period="3mo")
            if len(df) < 25:
                continue

            df = compute_indicators(df)
            latest = df.iloc[-1]

            vol_ratio = latest.get("VOL_RATIO", 0)
            if pd.isna(vol_ratio):
                continue

            pct_change = ((latest["Close"] - df.iloc[-2]["Close"]) / df.iloc[-2]["Close"]) * 100

            if vol_ratio >= volume_multiplier and abs(pct_change) >= price_change_pct:
                direction = "🟢 BULLISH" if pct_change > 0 else "🔴 BEARISH"
                results.append(
                    {
                        "Symbol": symbol,
                        "CMP": round(latest["Close"], 2),
                        "Change %": f"{pct_change:+.1f}%",
                        "Vol Ratio": f"{vol_ratio:.1f}x",
                        "Volume": format_volume(latest["Volume"]),
                        "RSI": round(latest["RSI"], 1) if not pd.isna(latest["RSI"]) else "N/A",
                        "Direction": direction,
                    }
                )

        except Exception as e:
            print(f"  ⚠️ Skipping {symbol}: {e}", file=sys.stderr)
            continue

    print(" " * 60, end="\r", file=sys.stderr)
    return pd.DataFrame(results)


def scan_ppa(
    symbols: list[str],
    consolidation_days: int = 10,
    breakout_threshold: float = 1.5,
) -> pd.DataFrame:
    """
    PPA (Price-Price Action) Scanner.
    Identifies stocks breaking out of tight consolidation with volume.

    Args:
        symbols: List of NSE symbols
        consolidation_days: Days of consolidation to detect
        breakout_threshold: ATR multiplier for breakout detection

    Returns:
        DataFrame with PPA breakout signals.
    """
    results = []
    total = len(symbols)

    for i, symbol in enumerate(symbols):
        try:
            print(f"  Scanning {symbol} ({i + 1}/{total})...", end="\r", file=sys.stderr)
            df = fetch_ohlcv(symbol, period="3mo")
            if len(df) < consolidation_days + 20:
                continue

            df = compute_indicators(df)
            latest = df.iloc[-1]

            # Check consolidation: range within ATR for N days
            consol_data = df.iloc[-(consolidation_days + 1) : -1]
            consol_range = consol_data["High"].max() - consol_data["Low"].min()
            avg_atr = consol_data["ATR"].mean()

            if pd.isna(avg_atr) or avg_atr == 0:
                continue

            range_ratio = consol_range / avg_atr

            # Tight consolidation: range < consolidation_days * 0.5 * ATR
            if range_ratio > consolidation_days * 0.5:
                continue

            # Check breakout: today's range > threshold * ATR
            today_range = latest["High"] - latest["Low"]
            if today_range > breakout_threshold * avg_atr:
                vol_surge = latest["VOL_RATIO"] if not pd.isna(latest["VOL_RATIO"]) else 0
                direction = "🟢 UP" if latest["Close"] > consol_data["High"].max() else "🔴 DOWN"

                results.append(
                    {
                        "Symbol": symbol,
                        "CMP": round(latest["Close"], 2),
                        "Consol Range": f"₹{consol_data['Low'].min():.0f}-₹{consol_data['High'].max():.0f}",
                        "Consol Days": consolidation_days,
                        "Breakout ATR": f"{today_range / avg_atr:.1f}x",
                        "Vol Surge": f"{vol_surge:.1f}x",
                        "Direction": direction,
                    }
                )

        except Exception as e:
            print(f"  ⚠️ Skipping {symbol}: {e}", file=sys.stderr)
            continue

    print(" " * 60, end="\r", file=sys.stderr)
    return pd.DataFrame(results)


def scan_delivery_breakout(
    symbols: list[str],
    delivery_pct_threshold: float = 60.0,
    delivery_surge_multiplier: float = 1.5,
) -> pd.DataFrame:
    """
    Scan for stocks with delivery percentage spikes (institutional accumulation signal).

    Note: Requires nsepython for delivery data. Falls back to volume analysis.

    Args:
        symbols: List of NSE symbols
        delivery_pct_threshold: Minimum delivery percentage
        delivery_surge_multiplier: Minimum delivery vs average

    Returns:
        DataFrame with delivery breakout signals.
    """
    results = []
    total = len(symbols)

    for i, symbol in enumerate(symbols):
        try:
            print(f"  Scanning {symbol} ({i + 1}/{total})...", end="\r", file=sys.stderr)
            # Using volume-based proxy when delivery data unavailable
            df = fetch_ohlcv(symbol, period="3mo")
            if len(df) < 25:
                continue

            df = compute_indicators(df)
            latest = df.iloc[-1]

            # Volume proxy for delivery analysis
            vol_ratio = latest.get("VOL_RATIO", 0)
            if pd.isna(vol_ratio) or vol_ratio < delivery_surge_multiplier:
                continue

            # Additional filter: price should be up on high volume
            pct_change = ((latest["Close"] - df.iloc[-2]["Close"]) / df.iloc[-2]["Close"]) * 100
            if pct_change <= 0:
                continue

            rsi = latest["RSI"] if not pd.isna(latest["RSI"]) else 0

            results.append(
                {
                    "Symbol": symbol,
                    "CMP": round(latest["Close"], 2),
                    "Change %": f"{pct_change:+.1f}%",
                    "Vol Surge": f"{vol_ratio:.1f}x",
                    "RSI": round(rsi, 1),
                    "Signal": "🟢 ACCUMULATION" if vol_ratio > 2.0 else "🟡 WATCH",
                }
            )

        except Exception as e:
            print(f"  ⚠️ Skipping {symbol}: {e}", file=sys.stderr)
            continue

    print(" " * 60, end="\r", file=sys.stderr)
    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser(description="NSE Stock Screener")
    parser.add_argument(
        "--universe",
        type=str,
        default="NIFTY50",
        help="Stock universe (NIFTY50, NIFTY100, NIFTY200, NIFTY500, NIFTY BANK, NIFTY IT, etc.)",
    )
    parser.add_argument("--symbols", type=str, help="Comma-separated symbols (overrides --universe)")
    parser.add_argument(
        "--scan",
        type=str,
        choices=["basic", "triple-ema-crossover", "volume-breakout", "ppa", "delivery-breakout"],
        default="basic",
        help="Scan type",
    )

    # Basic screen filters
    parser.add_argument("--rsi-below", type=float, help="RSI below threshold")
    parser.add_argument("--rsi-above", type=float, help="RSI above threshold")
    parser.add_argument("--above-ema", type=int, choices=[9, 21, 50, 55, 100, 200], help="Price above EMA")
    parser.add_argument("--below-ema", type=int, choices=[9, 21, 50, 55, 100, 200], help="Price below EMA")
    parser.add_argument("--min-volume", type=int, help="Minimum average daily volume")
    parser.add_argument("--min-delivery-pct", type=float, help="Minimum delivery percentage")
    parser.add_argument("--sector", type=str, help="Filter by sector")
    parser.add_argument("--min-market-cap", type=float, help="Min market cap in crores")

    # Scanner-specific params
    parser.add_argument("--lookback", type=int, default=5, help="Lookback days for crossover scan")
    parser.add_argument("--volume-multiplier", type=float, default=2.0, help="Volume surge multiplier")
    parser.add_argument("--price-change-pct", type=float, default=2.0, help="Min price change %")
    parser.add_argument("--consolidation-days", type=int, default=10, help="PPA consolidation days")
    parser.add_argument("--breakout-threshold", type=float, default=1.5, help="PPA breakout ATR multiplier")
    parser.add_argument("--delivery-pct-threshold", type=float, default=60.0)
    parser.add_argument("--delivery-surge-multiplier", type=float, default=1.5)

    parser.add_argument("--output", type=str, default="text", choices=["text", "json", "csv"])

    args = parser.parse_args()

    # Determine symbol list
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",")]
    else:
        symbols = fetch_nifty_constituents(args.universe)

    print(f"\n📊 NSE Screener — {args.scan.upper()} scan on {len(symbols)} stocks\n", file=sys.stderr)

    if args.scan == "basic":
        results = screen_basic(
            symbols,
            rsi_below=args.rsi_below,
            rsi_above=args.rsi_above,
            above_ema=args.above_ema,
            below_ema=args.below_ema,
            min_volume=args.min_volume,
            min_delivery_pct=args.min_delivery_pct,
            sector_filter=args.sector,
            min_market_cap=args.min_market_cap,
        )
    elif args.scan == "triple-ema-crossover":
        results = scan_triple_ema_crossover(symbols, lookback=args.lookback)
    elif args.scan == "volume-breakout":
        results = scan_volume_breakout(symbols, args.volume_multiplier, args.price_change_pct)
    elif args.scan == "ppa":
        results = scan_ppa(symbols, args.consolidation_days, args.breakout_threshold)
    elif args.scan == "delivery-breakout":
        results = scan_delivery_breakout(symbols, args.delivery_pct_threshold, args.delivery_surge_multiplier)
    else:
        print(f"Unknown scan type: {args.scan}", file=sys.stderr)
        sys.exit(1)

    if results.empty:
        print("No stocks matched the screening criteria.")
        return

    print(f"\n✅ Found {len(results)} matching stocks:\n")

    if args.output == "json":
        print(results.to_json(orient="records", indent=2))
    elif args.output == "csv":
        print(results.to_csv(index=False))
    else:
        print(results.to_string(index=False))

    print()


if __name__ == "__main__":
    main()
