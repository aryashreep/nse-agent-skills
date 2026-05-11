#!/usr/bin/env python3
"""
NSE Swing Trading Analyzer
Comprehensive swing analysis with EMA alignment, breakout detection,
ICT concepts, volume analysis, and structured trade setup generation.
"""

import argparse
import sys
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
import pandas_ta as ta

from data_fetcher import fetch_ohlcv, fetch_stock_info, format_inr


def compute_swing_indicators(df: pd.DataFrame, ema_fast: int = 9, ema_mid: int = 21, ema_slow: int = 55) -> pd.DataFrame:
    """Compute all indicators needed for swing analysis."""
    df = df.copy()

    # EMAs
    df["EMA_FAST"] = ta.ema(df["Close"], length=ema_fast)
    df["EMA_MID"] = ta.ema(df["Close"], length=ema_mid)
    df["EMA_SLOW"] = ta.ema(df["Close"], length=ema_slow)
    df["EMA200"] = ta.ema(df["Close"], length=200)

    # Momentum
    df["RSI"] = ta.rsi(df["Close"], length=14)
    macd = ta.macd(df["Close"])
    if macd is not None:
        df["MACD"] = macd.iloc[:, 0]
        df["MACD_SIGNAL"] = macd.iloc[:, 1]
        df["MACD_HIST"] = macd.iloc[:, 2]

    # Trend strength
    adx_data = ta.adx(df["High"], df["Low"], df["Close"], length=14)
    if adx_data is not None:
        df["ADX"] = adx_data["ADX_14"]
        df["DI_PLUS"] = adx_data["DMP_14"]
        df["DI_MINUS"] = adx_data["DMN_14"]

    # Volatility
    df["ATR"] = ta.atr(df["High"], df["Low"], df["Close"], length=14)
    df["ATR_PCT"] = (df["ATR"] / df["Close"]) * 100
    df["ATR_SMA20"] = df["ATR"].rolling(20).mean()
    df["ATR_EXPANSION"] = df["ATR"] / df["ATR_SMA20"]

    # Volume
    df["VOL_SMA20"] = df["Volume"].rolling(20).mean()
    df["VOL_RATIO"] = df["Volume"] / df["VOL_SMA20"]

    # Swing points
    df["SWING_HIGH"] = df["High"].rolling(5, center=True).max()
    df["SWING_LOW"] = df["Low"].rolling(5, center=True).min()

    # Bollinger Bands
    bbands = ta.bbands(df["Close"], length=20, std=2)
    if bbands is not None:
        df["BB_UPPER"] = bbands.iloc[:, 0]
        df["BB_MID"] = bbands.iloc[:, 1]
        df["BB_LOWER"] = bbands.iloc[:, 2]
        df["BB_WIDTH"] = (df["BB_UPPER"] - df["BB_LOWER"]) / df["BB_MID"] * 100

    return df


def assess_trend(df: pd.DataFrame) -> dict:
    """Assess overall trend based on EMA alignment and ADX."""
    latest = df.iloc[-1]

    ema_fast = latest["EMA_FAST"]
    ema_mid = latest["EMA_MID"]
    ema_slow = latest["EMA_SLOW"]
    price = latest["Close"]
    adx = latest.get("ADX", 0)

    # EMA alignment
    if ema_fast > ema_mid > ema_slow:
        alignment = "BULLISH"
        alignment_emoji = "🟢"
    elif ema_fast < ema_mid < ema_slow:
        alignment = "BEARISH"
        alignment_emoji = "🔴"
    else:
        alignment = "MIXED"
        alignment_emoji = "🟡"

    # Price vs EMAs
    above_fast = price > ema_fast if not pd.isna(ema_fast) else None
    above_mid = price > ema_mid if not pd.isna(ema_mid) else None
    above_slow = price > ema_slow if not pd.isna(ema_slow) else None

    # Trend strength via ADX
    if pd.isna(adx):
        trend_strength = "Unknown"
    elif adx > 40:
        trend_strength = "Strong Trend"
    elif adx > 25:
        trend_strength = "Trending"
    elif adx > 20:
        trend_strength = "Weak Trend"
    else:
        trend_strength = "No Trend (Ranging)"

    return {
        "alignment": alignment,
        "alignment_emoji": alignment_emoji,
        "ema_fast": ema_fast,
        "ema_mid": ema_mid,
        "ema_slow": ema_slow,
        "price": price,
        "above_fast": above_fast,
        "above_mid": above_mid,
        "above_slow": above_slow,
        "adx": adx if not pd.isna(adx) else 0,
        "trend_strength": trend_strength,
        "rsi": latest["RSI"] if not pd.isna(latest["RSI"]) else 0,
    }


def detect_signals(df: pd.DataFrame, lookback: int = 5) -> dict:
    """Detect swing trading signals."""
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    recent = df.tail(lookback)

    signals = {}

    # Triple EMA crossover
    if not any(pd.isna(x) for x in [latest["EMA_FAST"], latest["EMA_MID"], prev["EMA_FAST"], prev["EMA_MID"]]):
        bullish_cross = prev["EMA_FAST"] <= prev["EMA_MID"] and latest["EMA_FAST"] > latest["EMA_MID"]
        bearish_cross = prev["EMA_FAST"] >= prev["EMA_MID"] and latest["EMA_FAST"] < latest["EMA_MID"]
        # Check if crossover happened in lookback period
        cross_detected = False
        for i in range(1, min(lookback, len(df))):
            r = df.iloc[-i]
            p = df.iloc[-i-1]
            if p["EMA_FAST"] <= p["EMA_MID"] and r["EMA_FAST"] > r["EMA_MID"]:
                signals["triple_ema_crossover"] = {"type": "BULLISH", "days_ago": i - 1}
                cross_detected = True
                break
            elif p["EMA_FAST"] >= p["EMA_MID"] and r["EMA_FAST"] < r["EMA_MID"]:
                signals["triple_ema_crossover"] = {"type": "BEARISH", "days_ago": i - 1}
                cross_detected = True
                break
        if not cross_detected:
            signals["triple_ema_crossover"] = None
    else:
        signals["triple_ema_crossover"] = None

    # Volume breakout
    vol_ratio = latest["VOL_RATIO"] if not pd.isna(latest["VOL_RATIO"]) else 0
    signals["volume_breakout"] = vol_ratio >= 2.0
    signals["vol_ratio"] = vol_ratio

    # ATR expansion
    atr_exp = latest["ATR_EXPANSION"] if not pd.isna(latest["ATR_EXPANSION"]) else 0
    signals["atr_expansion"] = atr_exp >= 1.5
    signals["atr_expansion_ratio"] = atr_exp

    # Breakout retest
    recent_high = recent["High"].max()
    recent_low = recent["Low"].min()
    prev_resistance = df.iloc[-lookback - 5:-lookback]["High"].max() if len(df) > lookback + 5 else None
    if prev_resistance and not pd.isna(prev_resistance):
        # Price broke above resistance and retested
        if latest["Close"] > prev_resistance and latest["Low"] <= prev_resistance * 1.01:
            signals["breakout_retest"] = True
            signals["retest_level"] = prev_resistance
        else:
            signals["breakout_retest"] = False
            signals["retest_level"] = prev_resistance
    else:
        signals["breakout_retest"] = False
        signals["retest_level"] = None

    # MACD signal
    if "MACD_HIST" in df.columns and not pd.isna(latest.get("MACD_HIST")):
        signals["macd_bullish"] = latest["MACD_HIST"] > 0
        signals["macd_hist"] = latest["MACD_HIST"]
    else:
        signals["macd_bullish"] = None
        signals["macd_hist"] = 0

    return signals


def compute_trade_levels(df: pd.DataFrame, trend: dict, risk_pct: float = 1.0, capital: float = 1000000) -> dict:
    """Compute entry, stop-loss, and target levels."""
    latest = df.iloc[-1]
    atr = latest["ATR"] if not pd.isna(latest["ATR"]) else 0
    price = latest["Close"]

    if trend["alignment"] == "BULLISH":
        # Long setup
        entry_low = round(price * 0.995, 2)
        entry_high = round(price * 1.005, 2)

        # Stop loss: below slow EMA or 2x ATR, whichever is tighter
        sl_ema = trend["ema_slow"] if not pd.isna(trend["ema_slow"]) else price - 2 * atr
        sl_atr = price - 2 * atr
        stop_loss = round(max(sl_ema, sl_atr), 2)

        risk_per_share = price - stop_loss
        if risk_per_share <= 0:
            risk_per_share = atr * 2

        target1 = round(price + risk_per_share * 1.5, 2)
        target2 = round(price + risk_per_share * 2.5, 2)
        target3 = round(price + risk_per_share * 4.0, 2)
        signal = "🟢 BUY"

    elif trend["alignment"] == "BEARISH":
        entry_low = round(price * 0.995, 2)
        entry_high = round(price * 1.005, 2)
        stop_loss = round(price + 2 * atr, 2)
        risk_per_share = stop_loss - price
        if risk_per_share <= 0:
            risk_per_share = atr * 2
        target1 = round(price - risk_per_share * 1.5, 2)
        target2 = round(price - risk_per_share * 2.5, 2)
        target3 = round(price - risk_per_share * 4.0, 2)
        signal = "🔴 SHORT/AVOID"
    else:
        entry_low = round(price * 0.99, 2)
        entry_high = round(price * 1.01, 2)
        stop_loss = round(price - 2 * atr, 2)
        risk_per_share = price - stop_loss
        if risk_per_share <= 0:
            risk_per_share = atr * 2
        target1 = round(price + risk_per_share * 1.5, 2)
        target2 = round(price + risk_per_share * 2.5, 2)
        target3 = round(price + risk_per_share * 4.0, 2)
        signal = "🟡 WAIT/NEUTRAL"

    # Position sizing
    risk_amount = capital * (risk_pct / 100)
    position_size = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
    position_value = position_size * price
    pct_of_capital = (position_value / capital) * 100 if capital > 0 else 0
    risk_pct_actual = ((price - stop_loss) / price) * 100

    return {
        "signal": signal,
        "entry_low": entry_low,
        "entry_high": entry_high,
        "stop_loss": stop_loss,
        "risk_pct": round(abs(risk_pct_actual), 1),
        "target1": target1,
        "target2": target2,
        "target3": target3,
        "risk_per_share": round(risk_per_share, 2),
        "position_size": position_size,
        "position_value": round(position_value, 2),
        "pct_of_capital": round(pct_of_capital, 1),
        "risk_amount": round(risk_amount, 2),
        "rr_t1": "1:1.5",
        "rr_t2": "1:2.5",
        "rr_t3": "1:4.0",
    }


def detect_ict_setups(df: pd.DataFrame) -> dict:
    """
    Detect ICT (Inner Circle Trader) setups.
    - Order Blocks
    - Fair Value Gaps
    - Liquidity Sweeps
    - Market Structure shifts
    """
    results = {
        "order_blocks": [],
        "fair_value_gaps": [],
        "liquidity_sweeps": [],
        "market_structure": "",
        "ote_zone": None,
    }

    if len(df) < 20:
        return results

    # Market Structure: Higher highs/higher lows vs lower highs/lower lows
    highs = []
    lows = []
    for i in range(2, len(df) - 2):
        if df.iloc[i]["High"] > df.iloc[i-1]["High"] and df.iloc[i]["High"] > df.iloc[i+1]["High"]:
            highs.append((i, df.iloc[i]["High"]))
        if df.iloc[i]["Low"] < df.iloc[i-1]["Low"] and df.iloc[i]["Low"] < df.iloc[i+1]["Low"]:
            lows.append((i, df.iloc[i]["Low"]))

    if len(highs) >= 2 and len(lows) >= 2:
        if highs[-1][1] > highs[-2][1] and lows[-1][1] > lows[-2][1]:
            results["market_structure"] = "🟢 BULLISH (HH + HL)"
        elif highs[-1][1] < highs[-2][1] and lows[-1][1] < lows[-2][1]:
            results["market_structure"] = "🔴 BEARISH (LH + LL)"
        else:
            results["market_structure"] = "🟡 TRANSITIONAL"
    else:
        results["market_structure"] = "Insufficient data"

    # Order Blocks: Last bearish candle before a strong bullish move (bullish OB)
    for i in range(len(df) - 20, len(df) - 1):
        if i < 1:
            continue
        curr = df.iloc[i]
        nxt = df.iloc[i + 1] if i + 1 < len(df) else None
        if nxt is None:
            continue

        # Bullish Order Block: bearish candle followed by strong bullish move
        if curr["Close"] < curr["Open"]:  # Bearish candle
            move_pct = ((nxt["Close"] - curr["Close"]) / curr["Close"]) * 100
            if move_pct > 1.5:  # Strong bullish move
                results["order_blocks"].append({
                    "type": "BULLISH OB",
                    "date": df.index[i].strftime("%Y-%m-%d"),
                    "high": round(curr["High"], 2),
                    "low": round(curr["Low"], 2),
                    "strength": f"+{move_pct:.1f}%",
                })

        # Bearish Order Block: bullish candle followed by strong bearish move
        if curr["Close"] > curr["Open"]:  # Bullish candle
            move_pct = ((curr["Close"] - nxt["Close"]) / curr["Close"]) * 100
            if move_pct > 1.5:
                results["order_blocks"].append({
                    "type": "BEARISH OB",
                    "date": df.index[i].strftime("%Y-%m-%d"),
                    "high": round(curr["High"], 2),
                    "low": round(curr["Low"], 2),
                    "strength": f"-{move_pct:.1f}%",
                })

    # Keep only last 3 order blocks
    results["order_blocks"] = results["order_blocks"][-3:]

    # Fair Value Gaps: 3-candle pattern where candle 1 high < candle 3 low (bullish FVG)
    for i in range(len(df) - 15, len(df) - 2):
        if i < 0:
            continue
        c1 = df.iloc[i]
        c3 = df.iloc[i + 2]

        # Bullish FVG
        if c1["High"] < c3["Low"]:
            results["fair_value_gaps"].append({
                "type": "BULLISH FVG",
                "date": df.index[i + 1].strftime("%Y-%m-%d"),
                "top": round(c3["Low"], 2),
                "bottom": round(c1["High"], 2),
                "filled": df.iloc[-1]["Low"] <= c3["Low"],
            })

        # Bearish FVG
        if c1["Low"] > c3["High"]:
            results["fair_value_gaps"].append({
                "type": "BEARISH FVG",
                "date": df.index[i + 1].strftime("%Y-%m-%d"),
                "top": round(c1["Low"], 2),
                "bottom": round(c3["High"], 2),
                "filled": df.iloc[-1]["High"] >= c3["High"],
            })

    results["fair_value_gaps"] = results["fair_value_gaps"][-3:]

    # Liquidity Sweeps: price takes out a recent swing high/low then reverses
    if len(highs) >= 1 and len(lows) >= 1:
        latest = df.iloc[-1]
        # Check if latest bar swept a swing high and closed below it
        for _, high_val in highs[-3:]:
            if latest["High"] > high_val and latest["Close"] < high_val:
                results["liquidity_sweeps"].append({
                    "type": "SWEEP OF HIGHS",
                    "level": round(high_val, 2),
                    "implication": "🔴 Bearish (sell-side liquidity taken)",
                })
        for _, low_val in lows[-3:]:
            if latest["Low"] < low_val and latest["Close"] > low_val:
                results["liquidity_sweeps"].append({
                    "type": "SWEEP OF LOWS",
                    "level": round(low_val, 2),
                    "implication": "🟢 Bullish (buy-side liquidity taken)",
                })

    # OTE Zone (Optimal Trade Entry): 62-79% Fibonacci retracement
    if len(highs) >= 1 and len(lows) >= 1:
        recent_high = max(h[1] for h in highs[-3:])
        recent_low = min(l[1] for l in lows[-3:])
        fib_range = recent_high - recent_low
        results["ote_zone"] = {
            "top": round(recent_high - fib_range * 0.618, 2),
            "bottom": round(recent_high - fib_range * 0.79, 2),
            "swing_high": round(recent_high, 2),
            "swing_low": round(recent_low, 2),
        }

    return results


def generate_report(symbol: str, df: pd.DataFrame, trend: dict, signals: dict,
                    levels: dict, ict: Optional[dict] = None,
                    ema_fast: int = 9, ema_mid: int = 21, ema_slow: int = 55) -> str:
    """Generate a structured swing analysis report."""
    latest = df.iloc[-1]
    now = datetime.now().strftime("%Y-%m-%d %H:%M IST")

    report = []
    report.append("═" * 55)
    report.append(f"  SWING ANALYSIS: {symbol} (NSE)")
    report.append(f"  Date: {datetime.now().strftime('%Y-%m-%d')} | Timeframe: Daily")
    report.append("═" * 55)
    report.append("")

    # Trend Assessment
    report.append("📊 TREND ASSESSMENT")
    report.append(f"  EMA {ema_fast}:   {format_inr(trend['ema_fast'])}  (Price {'above ✅' if trend['above_fast'] else 'below ❌'})")
    report.append(f"  EMA {ema_mid}:  {format_inr(trend['ema_mid'])}  (Price {'above ✅' if trend['above_mid'] else 'below ❌'})")
    report.append(f"  EMA {ema_slow}:  {format_inr(trend['ema_slow'])}  (Price {'above ✅' if trend['above_slow'] else 'below ❌'})")
    report.append(f"  Alignment: {trend['alignment_emoji']} {trend['alignment']} ({ema_fast} {'>' if trend['alignment'] == 'BULLISH' else '<'} {ema_mid} {'>' if trend['alignment'] == 'BULLISH' else '<'} {ema_slow})")
    report.append(f"  ADX:      {trend['adx']:.1f} ({trend['trend_strength']})")
    report.append(f"  RSI(14):  {trend['rsi']:.1f} ({'Overbought ⚠️' if trend['rsi'] > 70 else 'Oversold ⚠️' if trend['rsi'] < 30 else 'Neutral'})")
    report.append("")

    # Signal Detection
    report.append("📈 SIGNAL DETECTION")
    cross = signals.get("triple_ema_crossover")
    if cross:
        report.append(f"  Triple EMA Crossover:    ✅ {cross['type']} ({cross['days_ago']} days ago)")
    else:
        report.append(f"  Triple EMA Crossover:    ❌ None detected")

    report.append(f"  Volume Breakout:         {'✅' if signals['volume_breakout'] else '❌'} {signals['vol_ratio']:.1f}x average volume")
    report.append(f"  ATR Expansion:           {'✅' if signals['atr_expansion'] else '🟡'} {signals['atr_expansion_ratio']:.1f}x")
    retest_status = '✅' if signals['breakout_retest'] else '❌'
    retest_detail = f" at {format_inr(signals['retest_level'])}" if signals['retest_level'] else ""
    report.append(f"  Breakout Retest:         {retest_status}{retest_detail}")

    if signals.get("macd_bullish") is not None:
        report.append(f"  MACD:                    {'✅ Bullish' if signals['macd_bullish'] else '❌ Bearish'}")
    report.append("")

    # Trade Setup
    report.append("🎯 TRADE SETUP")
    report.append(f"  Signal:      {levels['signal']}")
    report.append(f"  Entry Zone:  {format_inr(levels['entry_low'])} – {format_inr(levels['entry_high'])}")
    report.append(f"  Stop Loss:   {format_inr(levels['stop_loss'])} ({levels['risk_pct']}% risk)")
    report.append(f"  Target 1:    {format_inr(levels['target1'])} (R:R {levels['rr_t1']})")
    report.append(f"  Target 2:    {format_inr(levels['target2'])} (R:R {levels['rr_t2']})")
    report.append(f"  Target 3:    {format_inr(levels['target3'])} (R:R {levels['rr_t3']})")
    report.append("")

    # Position Sizing
    report.append(f"📐 POSITION SIZING ({format_inr(levels['risk_amount']/levels['risk_pct']*100 if levels['risk_pct'] > 0 else 1000000)} capital, {levels['risk_pct']}% risk)")
    report.append(f"  Risk Amount:    {format_inr(levels['risk_amount'])}")
    report.append(f"  Position Size:  {levels['position_size']} shares ({format_inr(levels['position_value'])})")
    report.append(f"  % of Capital:   {levels['pct_of_capital']}%")
    report.append("")

    # ICT Section (if requested)
    if ict:
        report.append("🔮 ICT ANALYSIS")
        report.append(f"  Market Structure: {ict['market_structure']}")

        if ict["order_blocks"]:
            report.append("  Order Blocks:")
            for ob in ict["order_blocks"]:
                report.append(f"    • {ob['type']}: ₹{ob['low']}-₹{ob['high']} ({ob['date']}) [{ob['strength']}]")

        if ict["fair_value_gaps"]:
            report.append("  Fair Value Gaps:")
            for fvg in ict["fair_value_gaps"]:
                filled = "FILLED" if fvg["filled"] else "UNFILLED"
                report.append(f"    • {fvg['type']}: ₹{fvg['bottom']}-₹{fvg['top']} ({fvg['date']}) [{filled}]")

        if ict["liquidity_sweeps"]:
            report.append("  Liquidity Sweeps:")
            for ls in ict["liquidity_sweeps"]:
                report.append(f"    • {ls['type']} at ₹{ls['level']} → {ls['implication']}")

        if ict["ote_zone"]:
            ote = ict["ote_zone"]
            report.append(f"  OTE Zone (62-79% Fib): ₹{ote['bottom']}-₹{ote['top']}")
            report.append(f"    Swing Range: ₹{ote['swing_low']}-₹{ote['swing_high']}")

        report.append("")

    # Risk Warning
    report.append("⚠️  RISK WARNING")
    report.append("  • This is a TRADE setup, not an investment recommendation")
    report.append("  • Always use a stop-loss")
    report.append("  • Past patterns do not guarantee future results")
    report.append("  • Consult a SEBI-registered advisor for personalized advice")
    report.append("")
    report.append(f"  Generated: {now}")
    report.append("═" * 55)

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="NSE Swing Trading Analyzer")
    parser.add_argument("--symbol", type=str, required=True, help="NSE stock symbol")
    parser.add_argument("--period", type=str, default="6mo", help="Analysis period")
    parser.add_argument("--ema-fast", type=int, default=9, help="Fast EMA period")
    parser.add_argument("--ema-mid", type=int, default=21, help="Mid EMA period")
    parser.add_argument("--ema-slow", type=int, default=55, help="Slow EMA period")
    parser.add_argument("--ict", action="store_true", help="Include ICT analysis")
    parser.add_argument("--capital", type=float, default=1000000, help="Trading capital in INR")
    parser.add_argument("--risk", type=float, default=1.0, help="Risk per trade (%)")
    parser.add_argument("--report", action="store_true", help="Generate full report")
    parser.add_argument("--output", type=str, default="text", choices=["text", "json"])

    args = parser.parse_args()

    print(f"\n📊 Analyzing {args.symbol}...\n", file=sys.stderr)

    # Fetch data
    df = fetch_ohlcv(args.symbol, period=args.period)
    if len(df) < 60:
        print(f"⚠️ Insufficient data for {args.symbol} (need at least 60 bars, got {len(df)})")
        sys.exit(1)

    # Compute indicators
    df = compute_swing_indicators(df, args.ema_fast, args.ema_mid, args.ema_slow)

    # Assess trend
    trend = assess_trend(df)

    # Detect signals
    signals = detect_signals(df)

    # Compute levels
    levels = compute_trade_levels(df, trend, risk_pct=args.risk, capital=args.capital)

    # ICT analysis
    ict = detect_ict_setups(df) if args.ict else None

    # Generate report
    report = generate_report(
        args.symbol, df, trend, signals, levels, ict,
        args.ema_fast, args.ema_mid, args.ema_slow,
    )
    print(report)


if __name__ == "__main__":
    main()
