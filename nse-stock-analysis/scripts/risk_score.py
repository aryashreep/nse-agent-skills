#!/usr/bin/env python3
"""
NSE Risk Scoring & Portfolio Analytics
Computes risk metrics for individual stocks and portfolios:
Beta, VaR, Max Drawdown, Sharpe/Sortino ratios, concentration risk.
"""

import argparse
import sys
from datetime import datetime

import numpy as np
import pandas as pd

from data_fetcher import fetch_ohlcv, fetch_stock_info, format_inr


def compute_risk_metrics(
    symbol: str,
    period: str = "1y",
    risk_free_rate: float = 0.065,
) -> dict:
    """
    Compute risk metrics for a single stock.

    Args:
        symbol: NSE symbol
        period: Analysis period
        risk_free_rate: Annual risk-free rate (default: 6.5% - India 10Y govt bond)

    Returns:
        Dictionary of risk metrics.
    """
    df = fetch_ohlcv(symbol, period=period)
    if len(df) < 20:
        raise ValueError(f"Insufficient data for {symbol}")

    close = df["Close"]
    returns = close.pct_change().dropna()
    daily_rf = risk_free_rate / 252

    # Basic stats
    total_return = (close.iloc[-1] / close.iloc[0] - 1) * 100
    annual_return = total_return * (252 / len(returns))
    volatility = returns.std() * np.sqrt(252) * 100

    # Beta (vs NIFTY 50)
    try:
        import yfinance as yf

        nifty = yf.download("^NSEI", period=period, progress=False)
        if isinstance(nifty.columns, pd.MultiIndex):
            nifty.columns = nifty.columns.get_level_values(0)
        nifty_returns = nifty["Close"].pct_change().dropna()
        # Align dates
        common_idx = returns.index.intersection(nifty_returns.index)
        if len(common_idx) > 20:
            s_ret = returns.loc[common_idx]
            n_ret = nifty_returns.loc[common_idx]
            cov = np.cov(s_ret, n_ret)
            beta = cov[0][1] / cov[1][1] if cov[1][1] != 0 else 1.0
        else:
            beta = 1.0
    except Exception:
        beta = 1.0

    # Value at Risk (Historical, 95%)
    var_95 = np.percentile(returns, 5) * 100
    var_99 = np.percentile(returns, 1) * 100

    # Max Drawdown
    cum_max = close.cummax()
    drawdown = (close - cum_max) / cum_max * 100
    max_drawdown = drawdown.min()

    # Sharpe Ratio
    excess_return = returns.mean() - daily_rf
    sharpe = (excess_return / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0

    # Sortino Ratio
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std()
    sortino = (excess_return / downside_std) * np.sqrt(252) if downside_std > 0 else 0

    # Risk score (0-100, higher = riskier)
    risk_score = 0
    risk_score += min(30, volatility * 0.5)  # Volatility component (max 30)
    risk_score += min(20, abs(max_drawdown) * 0.8)  # Drawdown component (max 20)
    risk_score += min(15, max(0, (beta - 1) * 30))  # Beta component (max 15)
    risk_score += min(15, abs(var_95) * 3)  # VaR component (max 15)
    if sharpe < 0.5:
        risk_score += 10  # Low Sharpe penalty
    elif sharpe < 1.0:
        risk_score += 5
    risk_score += min(10, max(0, 50 - total_return) * 0.2)  # Poor return penalty

    risk_score = min(100, max(0, round(risk_score)))

    return {
        "symbol": symbol,
        "total_return": round(total_return, 2),
        "annual_return": round(annual_return, 2),
        "volatility": round(volatility, 2),
        "beta": round(beta, 2),
        "var_95_daily": round(var_95, 2),
        "var_99_daily": round(var_99, 2),
        "max_drawdown": round(max_drawdown, 2),
        "sharpe_ratio": round(sharpe, 2),
        "sortino_ratio": round(sortino, 2),
        "risk_score": risk_score,
    }


def risk_rating(score: int) -> tuple[str, str]:
    """Convert risk score to emoji and label."""
    if score <= 40:
        return "🟢", "Low Risk"
    elif score <= 70:
        return "🟡", "Moderate Risk"
    else:
        return "🔴", "High Risk"


def metric_rating(metric: str, value: float) -> str:
    """Get rating for individual metrics."""
    ratings = {
        "beta": [(0.8, "🟢 Low"), (1.2, "🟡 Moderate"), (999, "🔴 High")],
        "sharpe": [(0.5, "🔴 Poor"), (1.0, "🟡 Average"), (999, "🟢 Good")],
        "sortino": [(0.7, "🔴 Poor"), (1.5, "🟡 Average"), (999, "🟢 Good")],
        "max_drawdown": [(-20, "🟢 Low"), (-10, "🟡 Moderate"), (999, "🔴 High")],
        "volatility": [(20, "🟢 Low"), (35, "🟡 Moderate"), (999, "🔴 High")],
    }
    thresholds = ratings.get(metric, [])
    for threshold, label in thresholds:
        if metric == "max_drawdown":
            if value >= threshold:
                return label
        elif metric in ("sharpe", "sortino"):
            if value <= threshold:
                return label
        else:
            if value <= threshold:
                return label
    return "N/A"


def analyze_portfolio(
    portfolio: dict[str, float],
    capital: float = 1000000,
    period: str = "1y",
) -> str:
    """
    Analyze portfolio risk.

    Args:
        portfolio: Dict of {symbol: weight_pct}
        capital: Total portfolio value in INR
        period: Analysis period

    Returns:
        Formatted portfolio risk report.
    """
    stock_data = {}
    stock_returns = {}
    sectors = {}

    for symbol, weight in portfolio.items():
        try:
            metrics = compute_risk_metrics(symbol, period=period)
            stock_data[symbol] = metrics

            df = fetch_ohlcv(symbol, period=period)
            stock_returns[symbol] = df["Close"].pct_change().dropna()

            info = fetch_stock_info(symbol)
            sector = info.get("sector", "Unknown")
            sectors[sector] = sectors.get(sector, 0) + weight

        except Exception as e:
            print(f"  ⚠️ Error analyzing {symbol}: {e}", file=sys.stderr)
            continue

    if not stock_data:
        return "⚠️ ERROR: Could not analyze any portfolio stocks."

    # Portfolio-level beta
    port_beta = sum(stock_data[s]["beta"] * (portfolio[s] / 100) for s in stock_data)

    # Portfolio VaR (simplified - weighted average)
    port_var = sum(stock_data[s]["var_95_daily"] * (portfolio[s] / 100) for s in stock_data)
    var_amount = abs(port_var / 100) * capital

    # Portfolio max drawdown (weighted)
    port_dd = sum(stock_data[s]["max_drawdown"] * (portfolio[s] / 100) for s in stock_data)

    # Portfolio Sharpe (weighted)
    port_sharpe = sum(stock_data[s]["sharpe_ratio"] * (portfolio[s] / 100) for s in stock_data)

    # Portfolio Sortino (weighted)
    port_sortino = sum(stock_data[s]["sortino_ratio"] * (portfolio[s] / 100) for s in stock_data)

    # Concentration risk
    max_sector = max(sectors.items(), key=lambda x: x[1]) if sectors else ("N/A", 0)
    max_stock = max(portfolio.items(), key=lambda x: x[1])

    # Portfolio risk score
    port_risk = 0
    port_risk += min(25, abs(port_dd) * 0.8)
    port_risk += min(15, max(0, (port_beta - 1) * 30))
    port_risk += min(15, abs(port_var) * 3)
    if port_sharpe < 0.5:
        port_risk += 10
    elif port_sharpe < 1.0:
        port_risk += 5
    # Concentration penalties
    if max_stock[1] > 40:
        port_risk += 15
    elif max_stock[1] > 25:
        port_risk += 8
    if max_sector[1] > 60:
        port_risk += 15
    elif max_sector[1] > 40:
        port_risk += 8
    # Single stock count
    if len(portfolio) < 5:
        port_risk += 10
    port_risk = min(100, max(0, round(port_risk)))

    emoji, rating = risk_rating(port_risk)
    now = datetime.now().strftime("%Y-%m-%d %H:%M IST")

    report = []
    report.append("═" * 55)
    report.append("  PORTFOLIO RISK ANALYSIS")
    report.append(f"  Capital: {format_inr(capital)} | Date: {datetime.now().strftime('%Y-%m-%d')}")
    report.append("═" * 55)
    report.append("")

    report.append("📊 PORTFOLIO COMPOSITION")
    for symbol, weight in sorted(portfolio.items(), key=lambda x: -x[1]):
        value = capital * weight / 100
        report.append(f"  {symbol:12s}  {weight:5.1f}%  {format_inr(value)}")
    report.append("")

    report.append("📈 INDIVIDUAL STOCK METRICS")
    report.append(f"  {'Stock':<12} {'Beta':>6} {'Vol':>7} {'Sharpe':>7} {'MaxDD':>7} {'Risk':>6}")
    report.append(f"  {'─' * 12} {'─' * 6} {'─' * 7} {'─' * 7} {'─' * 7} {'─' * 6}")
    for symbol in stock_data:
        d = stock_data[symbol]
        e, _ = risk_rating(d["risk_score"])
        report.append(
            f"  {symbol:<12} {d['beta']:>6.2f} {d['volatility']:>6.1f}% {d['sharpe_ratio']:>7.2f} "
            f"{d['max_drawdown']:>6.1f}% {e}{d['risk_score']:>3}"
        )
    report.append("")

    report.append("⚖️  PORTFOLIO RISK METRICS")
    report.append(f"  {'Metric':<25} {'Value':>15} {'Rating':>15}")
    report.append(f"  {'─' * 25} {'─' * 15} {'─' * 15}")
    report.append(f"  {'Portfolio Beta':<25} {port_beta:>15.2f} {metric_rating('beta', port_beta):>15}")
    report.append(f"  {'Value at Risk (95%)':<25} {format_inr(var_amount):>15} {'🟡 Moderate':>15}")
    report.append(f"  {'Max Drawdown':<25} {port_dd:>14.1f}% {metric_rating('max_drawdown', port_dd):>15}")
    report.append(f"  {'Sharpe Ratio':<25} {port_sharpe:>15.2f} {metric_rating('sharpe', port_sharpe):>15}")
    report.append(f"  {'Sortino Ratio':<25} {port_sortino:>15.2f} {metric_rating('sortino', port_sortino):>15}")
    report.append(
        f"  {'Top Sector Exposure':<25} {f'{max_sector[1]:.0f}% {max_sector[0]}':>15} "
        f"{'🔴 High' if max_sector[1] > 40 else '🟢 OK':>15}"
    )
    report.append(
        f"  {'Largest Position':<25} {f'{max_stock[1]:.0f}% {max_stock[0]}':>15} "
        f"{'🔴 High' if max_stock[1] > 30 else '🟢 OK':>15}"
    )
    report.append("")
    report.append(f"  {'OVERALL RISK SCORE':<25} {f'{port_risk}/100':>15} {emoji} {rating:>12}")
    report.append("")

    # Recommendations
    report.append("💡 RECOMMENDATIONS")
    if max_stock[1] > 30:
        report.append(f"  • Reduce {max_stock[0]} position (currently {max_stock[1]:.0f}%, recommend < 25%)")
    if max_sector[1] > 40:
        report.append(f"  • Diversify sector exposure ({max_sector[0]} at {max_sector[1]:.0f}%, recommend < 40%)")
    if len(portfolio) < 8:
        report.append(f"  • Consider adding more stocks (currently {len(portfolio)}, recommend 8-15)")
    if port_sharpe < 1.0:
        report.append(f"  • Portfolio Sharpe ({port_sharpe:.2f}) is below 1.0 - review weaker positions")
    if abs(port_dd) > 15:
        report.append(f"  • Max drawdown of {port_dd:.1f}% is significant - consider hedging")
    if not any([max_stock[1] > 30, max_sector[1] > 40, len(portfolio) < 8, port_sharpe < 1.0]):
        report.append("  • Portfolio is well-balanced. Continue monitoring.")
    report.append("")

    report.append("⚠️  Risk metrics are based on historical data and do not predict future risk.")
    report.append(f"  Generated: {now}")
    report.append("═" * 55)

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="NSE Risk Scoring & Portfolio Analytics")
    parser.add_argument("--symbol", type=str, help="Single stock risk analysis")
    parser.add_argument("--portfolio", type=str, help="Portfolio: SYMBOL:weight,... (e.g., RELIANCE:30,TCS:25)")
    parser.add_argument("--capital", type=float, default=1000000, help="Capital in INR")
    parser.add_argument("--period", type=str, default="1y", help="Analysis period")
    parser.add_argument("--output", type=str, default="text", choices=["text", "json"])

    args = parser.parse_args()

    if args.symbol:
        print(f"\n📊 Computing risk metrics for {args.symbol}...\n", file=sys.stderr)
        metrics = compute_risk_metrics(args.symbol, period=args.period)
        emoji, rating = risk_rating(metrics["risk_score"])

        print("═" * 45)
        print(f"  RISK ANALYSIS: {args.symbol}")
        print("═" * 45)
        print(f"  Total Return:    {metrics['total_return']:+.1f}%")
        print(f"  Volatility:      {metrics['volatility']:.1f}%  {metric_rating('volatility', metrics['volatility'])}")
        print(f"  Beta:            {metrics['beta']:.2f}  {metric_rating('beta', metrics['beta'])}")
        print(f"  VaR (95%):       {metrics['var_95_daily']:.2f}%/day")
        print(
            f"  Max Drawdown:    {metrics['max_drawdown']:.1f}%  {metric_rating('max_drawdown', metrics['max_drawdown'])}"
        )
        print(f"  Sharpe Ratio:    {metrics['sharpe_ratio']:.2f}  {metric_rating('sharpe', metrics['sharpe_ratio'])}")
        print(
            f"  Sortino Ratio:   {metrics['sortino_ratio']:.2f}  {metric_rating('sortino', metrics['sortino_ratio'])}"
        )
        print(f"  Risk Score:      {metrics['risk_score']}/100  {emoji} {rating}")
        print("═" * 45)
        return

    if args.portfolio:
        # Parse portfolio string: SYMBOL:weight,SYMBOL:weight
        portfolio = {}
        for item in args.portfolio.split(","):
            parts = item.strip().split(":")
            if len(parts) == 2:
                portfolio[parts[0].strip().upper()] = float(parts[1].strip())

        total_weight = sum(portfolio.values())
        if abs(total_weight - 100) > 1:
            print(f"⚠️ Portfolio weights sum to {total_weight}%, expected 100%", file=sys.stderr)

        print(f"\n📊 Analyzing portfolio ({len(portfolio)} stocks)...\n", file=sys.stderr)
        report = analyze_portfolio(portfolio, capital=args.capital, period=args.period)
        print(report)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
