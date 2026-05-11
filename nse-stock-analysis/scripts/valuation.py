#!/usr/bin/env python3
"""
NSE Stock Valuation Analyzer
Fundamental valuation using DCF, PE/PB multiples, Graham Number, and PEG ratio.
"""

import argparse
import math
from datetime import datetime

from data_fetcher import fetch_stock_info, format_inr


def graham_number(eps: float, book_value: float) -> float:
    """
    Graham Number = sqrt(22.5 * EPS * Book Value)
    Conservative intrinsic value estimate.
    """
    if eps is None or book_value is None or eps <= 0 or book_value <= 0:
        return 0
    return round(math.sqrt(22.5 * eps * book_value), 2)


def pe_relative_value(eps: float, industry_pe: float) -> float:
    """
    PE Relative Value = EPS * Industry Average PE
    Fair value based on peer valuation.
    """
    if eps is None or industry_pe is None or eps <= 0:
        return 0
    return round(eps * industry_pe, 2)


def peg_ratio(pe: float, earnings_growth: float) -> float:
    """
    PEG Ratio = PE / Earnings Growth Rate
    < 1: Undervalued, 1-2: Fair, > 2: Overvalued
    """
    if pe is None or earnings_growth is None or earnings_growth <= 0:
        return 0
    return round(pe / (earnings_growth * 100), 2)


def simple_dcf(
    eps: float,
    growth_rate: float,
    discount_rate: float = 0.12,
    terminal_growth: float = 0.04,
    projection_years: int = 10,
) -> float:
    """
    Simplified DCF valuation using EPS growth.

    Args:
        eps: Current EPS (TTM)
        growth_rate: Expected earnings growth rate (decimal)
        discount_rate: Required rate of return (default 12%)
        terminal_growth: Long-term growth rate (default 4%)
        projection_years: Number of projection years (default 10)

    Returns:
        Intrinsic value per share.
    """
    if eps is None or eps <= 0 or growth_rate is None:
        return 0

    # Ensure growth_rate is reasonable
    growth_rate = min(growth_rate, 0.30)  # Cap at 30%
    growth_rate = max(growth_rate, 0.0)

    total_pv = 0
    projected_eps = eps

    for year in range(1, projection_years + 1):
        projected_eps *= 1 + growth_rate
        # Taper growth rate in later years
        if year > 5:
            growth_rate *= 0.9
        pv = projected_eps / ((1 + discount_rate) ** year)
        total_pv += pv

    # Terminal value
    terminal_eps = projected_eps * (1 + terminal_growth)
    terminal_value = terminal_eps / (discount_rate - terminal_growth)
    terminal_pv = terminal_value / ((1 + discount_rate) ** projection_years)

    intrinsic_value = total_pv + terminal_pv
    return round(intrinsic_value, 2)


def get_industry_pe(sector: str) -> float:
    """
    Get approximate industry average PE for Indian sectors.
    Based on typical NIFTY sectoral index PE ranges.
    """
    sector_pe = {
        "Technology": 28.0,
        "Information Technology": 28.0,
        "Financial Services": 18.0,
        "Financials": 18.0,
        "Consumer Defensive": 45.0,
        "Consumer Staples": 45.0,
        "Consumer Cyclical": 35.0,
        "Consumer Discretionary": 35.0,
        "Energy": 12.0,
        "Healthcare": 30.0,
        "Industrials": 25.0,
        "Basic Materials": 15.0,
        "Materials": 15.0,
        "Communication Services": 20.0,
        "Utilities": 15.0,
        "Real Estate": 25.0,
    }
    for key, pe in sector_pe.items():
        if key.lower() in sector.lower():
            return pe
    return 20.0  # Default


def valuation_verdict(cmp: float, fair_value: float) -> tuple[str, str]:
    """
    Determine valuation verdict.

    Returns:
        Tuple of (emoji, verdict text).
    """
    if fair_value <= 0:
        return "⚪", "Cannot Determine"
    ratio = cmp / fair_value
    if ratio < 0.8:
        return "🟢", "UNDERVALUED"
    elif ratio < 1.0:
        return "🟢", "SLIGHTLY UNDERVALUED"
    elif ratio < 1.2:
        return "🟡", "FAIRLY VALUED"
    else:
        return "🔴", "OVERVALUED"


def run_valuation(symbol: str, method: str = "all") -> str:
    """
    Run full valuation analysis on a stock.

    Args:
        symbol: NSE symbol
        method: Valuation method(s) - dcf, pe-relative, pb-relative, graham, peg, all

    Returns:
        Formatted valuation report string.
    """
    info = fetch_stock_info(symbol)

    cmp = info.get("current_price", 0)
    eps = info.get("eps", 0)
    pe = info.get("pe_ratio", 0)
    pb = info.get("pb_ratio", 0)
    book_value = info.get("book_value", 0)
    roe = info.get("roe", 0)
    de = info.get("debt_to_equity", 0)
    div_yield = info.get("dividend_yield", 0)
    sector = info.get("sector", "Unknown")
    earnings_growth = info.get("earnings_growth", 0)
    revenue_growth = info.get("revenue_growth", 0)

    industry_pe = get_industry_pe(sector)

    # Compute valuations
    graham = graham_number(eps, book_value) if method in ("all", "graham") else None
    pe_rel = pe_relative_value(eps, industry_pe) if method in ("all", "pe-relative") else None
    peg = peg_ratio(pe, earnings_growth) if method in ("all", "peg") else None

    # DCF
    growth_for_dcf = earnings_growth if earnings_growth and earnings_growth > 0 else (revenue_growth or 0.10)
    dcf_value = simple_dcf(eps, growth_for_dcf) if method in ("all", "dcf") else None

    # Average fair value
    fair_values = [v for v in [graham, pe_rel, dcf_value] if v and v > 0]
    avg_fair_value = round(sum(fair_values) / len(fair_values), 2) if fair_values else 0

    # Verdict
    emoji, verdict = valuation_verdict(cmp, avg_fair_value) if avg_fair_value > 0 else ("⚪", "Insufficient Data")

    # Generate report
    now = datetime.now().strftime("%Y-%m-%d %H:%M IST")
    report = []
    report.append("═" * 55)
    report.append(f"  VALUATION ANALYSIS: {info['name']} (NSE)")
    report.append(f"  Date: {datetime.now().strftime('%Y-%m-%d')}")
    report.append("═" * 55)
    report.append("")

    report.append("📊 KEY FUNDAMENTALS")
    report.append(f"  Market Cap:       {format_inr(info['market_cap'])}")
    report.append(f"  PE Ratio (TTM):   {f'{pe:.1f}x' if pe else 'N/A'} (Industry: {industry_pe:.1f}x)")
    report.append(f"  PB Ratio:         {f'{pb:.1f}x' if pb else 'N/A'}")
    report.append(f"  ROE:              {f'{roe * 100:.1f}%' if roe else 'N/A'}")
    report.append(f"  Debt/Equity:      {f'{de:.2f}' if de else 'N/A'}")
    report.append(f"  Dividend Yield:   {f'{div_yield * 100:.1f}%' if div_yield else 'N/A'}")
    report.append(f"  EPS (TTM):        {f'₹{eps:.2f}' if eps else 'N/A'}")
    report.append(f"  Revenue Growth:   {f'{revenue_growth * 100:.1f}%' if revenue_growth else 'N/A'}")
    report.append(f"  Earnings Growth:  {f'{earnings_growth * 100:.1f}%' if earnings_growth else 'N/A'}")
    report.append("")

    report.append("💰 VALUATION MODELS")
    if graham:
        g_emoji, _ = valuation_verdict(cmp, graham)
        report.append(
            f"  Graham Number:        ₹{graham:,.2f} (CMP: ₹{cmp:,.2f} → {g_emoji} {'Below' if cmp < graham else 'Above'})"
        )
    if pe_rel:
        p_emoji, _ = valuation_verdict(cmp, pe_rel)
        report.append(
            f"  PE Relative Value:    ₹{pe_rel:,.2f} (CMP: ₹{cmp:,.2f} → {p_emoji} {'Below' if cmp < pe_rel else 'Above'})"
        )
    if peg:
        peg_status = "🟢 Undervalued" if peg < 1 else "🟡 Fair" if peg < 2 else "🔴 Overvalued"
        report.append(f"  PEG Ratio:            {peg:.2f} → {peg_status}")
    if dcf_value:
        d_emoji, _ = valuation_verdict(cmp, dcf_value)
        report.append(
            f"  DCF Fair Value:       ₹{dcf_value:,.2f} (CMP: ₹{cmp:,.2f} → {d_emoji} {'Below' if cmp < dcf_value else 'Above'})"
        )
    report.append("")

    report.append(f"📋 VERDICT: {emoji} {verdict}")
    if avg_fair_value > 0:
        margin = ((avg_fair_value - cmp) / avg_fair_value) * 100
        report.append(f"  Average Fair Value:   ₹{avg_fair_value:,.2f}")
        report.append(
            f"  Current Price:        ₹{cmp:,.2f} ({margin:+.1f}% {'below' if margin > 0 else 'above'} fair value)"
        )
        report.append(f"  Margin of Safety:     {abs(margin):.1f}%")

        if margin > 20:
            report.append("\n  Recommendation: 🟢 BUY - significant margin of safety")
        elif margin > 0:
            report.append("\n  Recommendation: 🟡 ACCUMULATE on dips")
        elif margin > -20:
            report.append("\n  Recommendation: 🟡 HOLD - fairly valued")
        else:
            report.append("\n  Recommendation: 🔴 AVOID - expensive relative to fundamentals")
    report.append("")

    report.append("⚠️  This is NOT financial advice. Verify data independently.")
    report.append(f"  Generated: {now}")
    report.append("═" * 55)

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="NSE Stock Valuation Analyzer")
    parser.add_argument("--symbol", type=str, required=True, help="NSE stock symbol")
    parser.add_argument(
        "--method",
        type=str,
        default="all",
        choices=["all", "dcf", "pe-relative", "pb-relative", "graham", "peg"],
        help="Valuation method",
    )
    parser.add_argument("--discount-rate", type=float, default=0.12, help="Discount rate for DCF")
    parser.add_argument("--growth-rate", type=float, help="Override growth rate for DCF")

    args = parser.parse_args()
    report = run_valuation(args.symbol, method=args.method)
    print(report)


if __name__ == "__main__":
    main()
