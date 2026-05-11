#!/usr/bin/env python3
"""
NSE Strategy Backtesting Engine
Backtests trading strategies on NSE stocks using historical data.
Strategies: Triple EMA Crossover, RSI Mean Reversion, Breakout Retest, EMA Pullback.
"""

import argparse
import sys
from datetime import datetime

import numpy as np
import pandas as pd
import pandas_ta as ta

from data_fetcher import fetch_ohlcv, format_inr


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add all indicators needed for strategies."""
    df = df.copy()
    df["EMA9"] = ta.ema(df["Close"], length=9)
    df["EMA21"] = ta.ema(df["Close"], length=21)
    df["EMA55"] = ta.ema(df["Close"], length=55)
    df["EMA200"] = ta.ema(df["Close"], length=200)
    df["RSI"] = ta.rsi(df["Close"], length=14)
    df["ATR"] = ta.atr(df["High"], df["Low"], df["Close"], length=14)
    df["VOL_SMA20"] = df["Volume"].rolling(20).mean()
    df["VOL_RATIO"] = df["Volume"] / df["VOL_SMA20"]

    # Swing highs/lows for breakout
    df["HIGHEST_20"] = df["High"].rolling(20).max()
    df["LOWEST_20"] = df["Low"].rolling(20).min()

    # Bollinger Bands
    bbands = ta.bbands(df["Close"], length=20, std=2)
    if bbands is not None:
        df["BB_UPPER"] = bbands.iloc[:, 0]
        df["BB_LOWER"] = bbands.iloc[:, 2]

    return df


def strategy_triple_ema_crossover(df: pd.DataFrame) -> pd.DataFrame:
    """
    Triple EMA Crossover Strategy:
    BUY: 9 EMA crosses above 21 EMA, both above 55 EMA, volume > 1.5x avg
    SELL: 9 EMA crosses below 21 EMA, or price closes below 55 EMA
    """
    df = df.copy()
    df["signal"] = 0

    for i in range(1, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i - 1]

        if pd.isna(curr["EMA9"]) or pd.isna(curr["EMA21"]) or pd.isna(curr["EMA55"]):
            continue

        # Buy signal
        if (
            prev["EMA9"] <= prev["EMA21"]
            and curr["EMA9"] > curr["EMA21"]
            and curr["EMA9"] > curr["EMA55"]
            and curr["EMA21"] > curr["EMA55"]
        ):
            vol_ok = curr["VOL_RATIO"] > 1.3 if not pd.isna(curr["VOL_RATIO"]) else True
            if vol_ok:
                df.iloc[i, df.columns.get_loc("signal")] = 1

        # Sell signal
        elif prev["EMA9"] >= prev["EMA21"] and curr["EMA9"] < curr["EMA21"]:
            df.iloc[i, df.columns.get_loc("signal")] = -1
        elif curr["Close"] < curr["EMA55"]:
            df.iloc[i, df.columns.get_loc("signal")] = -1

    return df


def strategy_rsi_mean_reversion(df: pd.DataFrame) -> pd.DataFrame:
    """
    RSI Mean Reversion Strategy:
    BUY: RSI < 30 and price above 200 EMA
    SELL: RSI > 70 or price drops below entry by 2x ATR
    """
    df = df.copy()
    df["signal"] = 0

    for i in range(1, len(df)):
        curr = df.iloc[i]
        if pd.isna(curr["RSI"]) or pd.isna(curr["EMA200"]):
            continue

        # Buy on oversold with trend filter
        if curr["RSI"] < 30 and curr["Close"] > curr["EMA200"]:
            df.iloc[i, df.columns.get_loc("signal")] = 1

        # Sell on overbought
        elif curr["RSI"] > 70:
            df.iloc[i, df.columns.get_loc("signal")] = -1

    return df


def strategy_breakout_retest(df: pd.DataFrame) -> pd.DataFrame:
    """
    Breakout Retest Strategy:
    BUY: Price breaks 20-day high, then retests and holds, with volume
    SELL: Price closes below 20-day low or 2x ATR stop
    """
    df = df.copy()
    df["signal"] = 0
    broke_out = False
    breakout_level = 0

    for i in range(2, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i - 1]

        if pd.isna(curr["HIGHEST_20"]):
            continue

        # Detect breakout
        if not broke_out and curr["Close"] > prev["HIGHEST_20"]:
            broke_out = True
            breakout_level = prev["HIGHEST_20"]

        # Detect retest (price comes back near breakout level and holds)
        elif broke_out:
            if curr["Low"] <= breakout_level * 1.01 and curr["Close"] > breakout_level:
                vol_ok = curr["VOL_RATIO"] > 1.2 if not pd.isna(curr["VOL_RATIO"]) else True
                if vol_ok:
                    df.iloc[i, df.columns.get_loc("signal")] = 1
                    broke_out = False
            elif curr["Close"] < breakout_level * 0.98:
                broke_out = False  # Failed retest

        # Sell on breakdown
        if not pd.isna(curr["LOWEST_20"]) and curr["Close"] < curr["LOWEST_20"]:
            df.iloc[i, df.columns.get_loc("signal")] = -1

    return df


def strategy_ema_pullback(df: pd.DataFrame) -> pd.DataFrame:
    """
    EMA Pullback Strategy:
    BUY: In uptrend (EMA9 > EMA21 > EMA55), price pulls back to 21 EMA and bounces
    SELL: Price closes below 55 EMA
    """
    df = df.copy()
    df["signal"] = 0

    for i in range(2, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i - 1]

        if pd.isna(curr["EMA9"]) or pd.isna(curr["EMA21"]) or pd.isna(curr["EMA55"]):
            continue

        # Uptrend check
        in_uptrend = curr["EMA9"] > curr["EMA21"] > curr["EMA55"]

        if in_uptrend:
            # Pullback to 21 EMA: previous bar touched/crossed 21 EMA, current bar closes above
            if prev["Low"] <= prev["EMA21"] * 1.005 and curr["Close"] > curr["EMA21"]:
                df.iloc[i, df.columns.get_loc("signal")] = 1

        # Sell: close below 55 EMA
        if curr["Close"] < curr["EMA55"]:
            df.iloc[i, df.columns.get_loc("signal")] = -1

    return df


STRATEGIES = {
    "triple-ema-crossover": strategy_triple_ema_crossover,
    "rsi-mean-reversion": strategy_rsi_mean_reversion,
    "breakout-retest": strategy_breakout_retest,
    "ema-pullback": strategy_ema_pullback,
}


def run_backtest(
    df: pd.DataFrame,
    strategy_name: str,
    capital: float = 1000000,
    risk_per_trade: float = 1.0,
    commission_pct: float = 0.1,
) -> dict:
    """
    Execute a backtest.

    Args:
        df: OHLCV DataFrame with indicators
        strategy_name: Strategy to test
        capital: Starting capital in INR
        risk_per_trade: Risk per trade as % of capital
        commission_pct: Total transaction cost per trade (%)

    Returns:
        Dictionary with backtest results.
    """
    strategy_fn = STRATEGIES.get(strategy_name)
    if not strategy_fn:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    df = strategy_fn(df)

    # Simulate trades
    trades = []
    position = None
    current_capital = capital

    for i in range(len(df)):
        row = df.iloc[i]
        date = df.index[i]

        if row["signal"] == 1 and position is None:
            # Enter long
            entry_price = row["Close"]
            atr = row["ATR"] if not pd.isna(row["ATR"]) else entry_price * 0.02
            stop_loss = entry_price - 2 * atr

            risk_amount = current_capital * (risk_per_trade / 100)
            risk_per_share = entry_price - stop_loss
            if risk_per_share <= 0:
                continue

            qty = int(risk_amount / risk_per_share)
            if qty <= 0:
                continue

            commission = entry_price * qty * (commission_pct / 100)
            position = {
                "entry_date": date,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "qty": qty,
                "entry_commission": commission,
            }

        elif row["signal"] == -1 and position is not None:
            # Exit long
            exit_price = row["Close"]
            commission = exit_price * position["qty"] * (commission_pct / 100)
            pnl = (exit_price - position["entry_price"]) * position["qty"]
            pnl -= position["entry_commission"] + commission

            current_capital += pnl
            holding_days = (date - position["entry_date"]).days

            trades.append(
                {
                    "entry_date": position["entry_date"].strftime("%Y-%m-%d"),
                    "exit_date": date.strftime("%Y-%m-%d"),
                    "entry_price": round(position["entry_price"], 2),
                    "exit_price": round(exit_price, 2),
                    "qty": position["qty"],
                    "pnl": round(pnl, 2),
                    "return_pct": round((exit_price / position["entry_price"] - 1) * 100, 2),
                    "holding_days": holding_days,
                }
            )
            position = None

        elif position is not None:
            # Check stop loss
            if row["Low"] <= position["stop_loss"]:
                exit_price = position["stop_loss"]
                commission = exit_price * position["qty"] * (commission_pct / 100)
                pnl = (exit_price - position["entry_price"]) * position["qty"]
                pnl -= position["entry_commission"] + commission

                current_capital += pnl
                holding_days = (date - position["entry_date"]).days

                trades.append(
                    {
                        "entry_date": position["entry_date"].strftime("%Y-%m-%d"),
                        "exit_date": date.strftime("%Y-%m-%d"),
                        "entry_price": round(position["entry_price"], 2),
                        "exit_price": round(exit_price, 2),
                        "qty": position["qty"],
                        "pnl": round(pnl, 2),
                        "return_pct": round((exit_price / position["entry_price"] - 1) * 100, 2),
                        "holding_days": holding_days,
                        "stopped_out": True,
                    }
                )
                position = None

    # Close any open position at last close
    if position is not None:
        exit_price = df.iloc[-1]["Close"]
        commission = exit_price * position["qty"] * (commission_pct / 100)
        pnl = (exit_price - position["entry_price"]) * position["qty"]
        pnl -= position["entry_commission"] + commission
        current_capital += pnl
        trades.append(
            {
                "entry_date": position["entry_date"].strftime("%Y-%m-%d"),
                "exit_date": df.index[-1].strftime("%Y-%m-%d"),
                "entry_price": round(position["entry_price"], 2),
                "exit_price": round(exit_price, 2),
                "qty": position["qty"],
                "pnl": round(pnl, 2),
                "return_pct": round((exit_price / position["entry_price"] - 1) * 100, 2),
                "holding_days": (df.index[-1] - position["entry_date"]).days,
                "open_trade": True,
            }
        )

    # Compute metrics
    total_trades = len(trades)
    if total_trades == 0:
        return {
            "total_trades": 0,
            "message": "No trades generated. Strategy did not trigger on this data.",
        }

    winning_trades = [t for t in trades if t["pnl"] > 0]
    losing_trades = [t for t in trades if t["pnl"] <= 0]
    win_rate = len(winning_trades) / total_trades * 100

    total_pnl = sum(t["pnl"] for t in trades)
    total_return = (current_capital / capital - 1) * 100
    trading_days = (df.index[-1] - df.index[0]).days
    years = trading_days / 365.25
    cagr = ((current_capital / capital) ** (1 / years) - 1) * 100 if years > 0 else 0

    avg_win = np.mean([t["pnl"] for t in winning_trades]) if winning_trades else 0
    avg_loss = abs(np.mean([t["pnl"] for t in losing_trades])) if losing_trades else 1
    profit_factor = (
        (sum(t["pnl"] for t in winning_trades) / abs(sum(t["pnl"] for t in losing_trades)))
        if losing_trades and sum(t["pnl"] for t in losing_trades) != 0
        else float("inf")
    )

    avg_holding = np.mean([t["holding_days"] for t in trades])

    # Max drawdown from equity curve
    equity = [capital]
    for t in trades:
        equity.append(equity[-1] + t["pnl"])
    equity = pd.Series(equity)
    peak = equity.cummax()
    drawdown = (equity - peak) / peak * 100
    max_drawdown = drawdown.min()

    # Sharpe (simplified)
    trade_returns = [t["return_pct"] for t in trades]
    if len(trade_returns) > 1:
        sharpe = (
            np.mean(trade_returns) / np.std(trade_returns) * np.sqrt(len(trade_returns) / years) if years > 0 else 0
        )
    else:
        sharpe = 0

    avg_rr = avg_win / avg_loss if avg_loss > 0 else 0

    return {
        "symbol": df.attrs.get("symbol", ""),
        "strategy": strategy_name,
        "period_start": df.index[0].strftime("%Y-%m-%d"),
        "period_end": df.index[-1].strftime("%Y-%m-%d"),
        "starting_capital": capital,
        "ending_capital": round(current_capital, 2),
        "total_return": round(total_return, 2),
        "cagr": round(cagr, 2),
        "max_drawdown": round(max_drawdown, 2),
        "sharpe_ratio": round(sharpe, 2),
        "total_trades": total_trades,
        "win_rate": round(win_rate, 1),
        "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else "∞",
        "avg_holding_days": round(avg_holding, 1),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "risk_reward": f"1:{avg_rr:.1f}",
        "total_pnl": round(total_pnl, 2),
        "trades": trades,
    }


def format_backtest_report(results: dict) -> str:
    """Format backtest results as a structured report."""
    if results.get("total_trades", 0) == 0:
        return f"⚠️ {results.get('message', 'No trades generated.')}"

    report = []
    report.append("╔" + "═" * 46 + "╗")
    report.append(f"║  BACKTEST RESULTS: {results['symbol']:<27}║")
    report.append(f"║  Strategy: {results['strategy']:<35}║")
    report.append(f"║  Period: {results['period_start']} to {results['period_end']:<14}║")
    report.append("╠" + "═" * 46 + "╣")
    report.append(f"║  Starting Capital:   {format_inr(results['starting_capital']):>23}║")
    report.append(f"║  Ending Capital:     {format_inr(results['ending_capital']):>23}║")
    report.append(f"║  Total Return:       {results['total_return']:>+22.1f}%║")
    report.append(f"║  CAGR:               {results['cagr']:>+22.1f}%║")
    report.append(f"║  Max Drawdown:       {results['max_drawdown']:>22.1f}%║")
    report.append(f"║  Sharpe Ratio:       {results['sharpe_ratio']:>23.2f}║")
    report.append(f"║  Win Rate:           {results['win_rate']:>22.1f}%║")
    report.append(f"║  Profit Factor:      {str(results['profit_factor']):>23}║")
    report.append(f"║  Total Trades:       {results['total_trades']:>23}║")
    report.append(f"║  Avg Holding Period: {results['avg_holding_days']:>20.1f} days║")
    report.append(f"║  Risk-Reward Ratio:  {results['risk_reward']:>23}║")
    report.append("╚" + "═" * 46 + "╝")
    report.append("")

    # Trade log (last 10)
    trades = results.get("trades", [])
    if trades:
        report.append("📋 RECENT TRADES (last 10):")
        report.append(f"  {'Entry Date':<12} {'Exit Date':<12} {'Entry':>8} {'Exit':>8} {'P&L':>10} {'Ret':>7}")
        report.append(f"  {'─' * 12} {'─' * 12} {'─' * 8} {'─' * 8} {'─' * 10} {'─' * 7}")
        for t in trades[-10:]:
            report.append(
                f"  {t['entry_date']:<12} {t['exit_date']:<12} "
                f"₹{t['entry_price']:>7,.0f} ₹{t['exit_price']:>7,.0f} "
                f"{format_inr(t['pnl']):>10} {t['return_pct']:>+6.1f}%"
            )
        report.append("")

    report.append("⚠️  Past backtest results do not guarantee future performance.")
    report.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="NSE Strategy Backtesting Engine")
    parser.add_argument("--symbol", type=str, required=True, help="NSE stock symbol")
    parser.add_argument(
        "--strategy", type=str, required=True, choices=list(STRATEGIES.keys()), help="Trading strategy to backtest"
    )
    parser.add_argument("--period", type=str, default="2y", help="Backtest period")
    parser.add_argument("--capital", type=float, default=1000000, help="Starting capital (INR)")
    parser.add_argument("--risk-per-trade", type=float, default=1.0, help="Risk per trade (%)")
    parser.add_argument("--commission", type=float, default=0.1, help="Commission per trade (%)")
    parser.add_argument("--report", action="store_true", help="Generate formatted report")
    parser.add_argument("--output", type=str, default="text", choices=["text", "json"])

    args = parser.parse_args()

    print(f"\n📊 Backtesting {args.strategy} on {args.symbol} ({args.period})...\n", file=sys.stderr)

    # Fetch and prepare data
    df = fetch_ohlcv(args.symbol, period=args.period)
    if len(df) < 60:
        print(f"⚠️ Insufficient data: {len(df)} bars (need at least 60)")
        sys.exit(1)

    df = add_indicators(df)
    df.attrs["symbol"] = args.symbol

    # Run backtest
    results = run_backtest(
        df,
        strategy_name=args.strategy,
        capital=args.capital,
        risk_per_trade=args.risk_per_trade,
        commission_pct=args.commission,
    )

    results["symbol"] = args.symbol

    if args.output == "json":
        import json

        # Remove trade list for cleaner JSON
        clean = {k: v for k, v in results.items() if k != "trades"}
        print(json.dumps(clean, indent=2))
    else:
        report = format_backtest_report(results)
        print(report)


if __name__ == "__main__":
    main()
