# Backtest Report: {{SYMBOL}}

**Strategy:** {{STRATEGY}} | **Period:** {{START_DATE}} to {{END_DATE}}

---

## Executive Summary

The **{{STRATEGY}}** strategy on {{SYMBOL}} over {{PERIOD}} produced a total return of **{{TOTAL_RETURN}}%** (CAGR: {{CAGR}}%) with a maximum drawdown of {{MAX_DRAWDOWN}}% and a Sharpe ratio of {{SHARPE}}.

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Starting Capital | ₹{{START_CAPITAL}} |
| Ending Capital | ₹{{END_CAPITAL}} |
| Total Return | {{TOTAL_RETURN}}% |
| CAGR | {{CAGR}}% |
| Max Drawdown | {{MAX_DRAWDOWN}}% |
| Sharpe Ratio | {{SHARPE}} |
| Win Rate | {{WIN_RATE}}% |
| Profit Factor | {{PROFIT_FACTOR}} |
| Total Trades | {{TOTAL_TRADES}} |
| Avg Holding Period | {{AVG_HOLDING}} days |
| Risk-Reward Ratio | {{RISK_REWARD}} |
| Avg Win | ₹{{AVG_WIN}} |
| Avg Loss | ₹{{AVG_LOSS}} |

---

## Trade Log

| # | Entry Date | Exit Date | Entry Price | Exit Price | Qty | P&L | Return % |
|---|-----------|-----------|------------|------------|-----|-----|----------|
{{TRADE_LOG}}

---

## Strategy Rules

### Entry Conditions
{{ENTRY_RULES}}

### Exit Conditions
{{EXIT_RULES}}

### Risk Management
- Risk per trade: {{RISK_PER_TRADE}}%
- Stop loss: ATR-based (2x ATR from entry)
- Commission: {{COMMISSION}}% per trade
- Max position size: {{MAX_POSITION}}% of capital

---

## Key Observations

{{OBSERVATIONS}}

---

## Disclaimer

⚠️ **IMPORTANT:**
- Backtesting uses historical data and assumes perfect execution at closing prices.
- Real-world results will differ due to slippage, liquidity, and execution timing.
- Past performance does NOT guarantee future results.
- This is NOT financial advice. Use at your own risk.

---

*Generated: {{TIMESTAMP}} IST*
