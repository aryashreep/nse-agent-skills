# Risk Management Framework

## Overview

This document defines the risk management rules applied to all trading and investment analysis produced by the NSE Stock Analysis skill. Risk management is non-negotiable — every trade setup must include defined risk parameters.

---

## Core Principles

1. **Capital Preservation First:** Protecting capital takes priority over generating returns
2. **Defined Risk:** Every trade must have a pre-defined stop-loss before entry
3. **Position Sizing:** Size positions based on risk, not conviction
4. **Portfolio Heat:** Monitor aggregate portfolio risk at all times
5. **Systematic Rules:** Follow rules consistently — no exceptions for "high conviction" trades

---

## Position Sizing Rules

### Formula

```
Position Size (shares) = Risk Amount / Risk Per Share
Risk Amount = Capital × Risk Per Trade (%)
Risk Per Share = Entry Price - Stop Loss Price
```

### Risk Per Trade Limits

| Trader Category | Max Risk/Trade | Max Open Risk | Max Positions |
|----------------|---------------|---------------|---------------|
| Conservative | 0.5% | 3% | 6 |
| Moderate | 1.0% | 6% | 6-8 |
| Aggressive | 2.0% | 10% | 5-10 |
| Professional | 2.0-3.0% | 12% | 8-15 |

### Example

```
Capital:        ₹10,00,000
Risk/Trade:     1% = ₹10,000
Entry Price:    ₹500
Stop Loss:      ₹480
Risk/Share:     ₹20
Position Size:  500 shares (₹2,50,000 = 25% of capital)
```

---

## Stop-Loss Methods

### 1. ATR-Based Stop (Recommended)

```
Stop Loss = Entry - (ATR(14) × Multiplier)
```

| Multiplier | Tightness | Best For |
|-----------|-----------|----------|
| 1.0x ATR | Very Tight | Scalping, intraday |
| 1.5x ATR | Tight | Short-term swing |
| 2.0x ATR | Standard | Swing trading (default) |
| 3.0x ATR | Wide | Positional trading |

### 2. Structure-Based Stop

Place stop below the nearest swing low (bullish) or above swing high (bearish).
Add 0.5% buffer below the structure level to avoid stop hunts.

### 3. EMA-Based Stop

- **Swing trades:** Stop below 21 EMA or 55 EMA
- **Positional trades:** Stop below 200 EMA

### 4. Percentage-Based Stop

Maximum 3% from entry for swing trades, 8% for positional.

---

## Risk-Reward Ratios

| Minimum R:R | Rating | Action |
|------------|--------|--------|
| < 1:1 | 🔴 Poor | Do NOT take this trade |
| 1:1 - 1:1.5 | 🟡 Marginal | Only if win rate > 60% |
| 1:1.5 - 1:2 | 🟢 Good | Standard swing trade |
| 1:2 - 1:3 | 🟢 Excellent | Strong setup |
| > 1:3 | 🟢 Outstanding | High-conviction setup |

### Target Setting

- **Target 1 (T1):** 1.5x risk (book 30-40% position)
- **Target 2 (T2):** 2.5x risk (book 30-40% position)
- **Target 3 (T3):** 4.0x risk or trail stop (remaining position)

Move stop to breakeven after T1 is hit.

---

## Portfolio Risk Rules

### Concentration Limits

| Parameter | Maximum | Reason |
|-----------|---------|--------|
| Single stock | 20% of portfolio | Avoid single-stock blow-up |
| Single sector | 40% of portfolio | Avoid sector risk |
| Total open risk | 6% of capital | Survive consecutive losses |
| Correlated positions | 3 max | Avoid hidden correlation |

### Portfolio Heat Calculation

```
Portfolio Heat = Sum of (Position Size × Distance to Stop) / Total Capital

IF Portfolio Heat > 6%:
    → Do NOT add new positions
    → Consider reducing weakest position
```

### Drawdown Rules

| Drawdown Level | Action |
|---------------|--------|
| 0-5% | Normal trading — continue |
| 5-10% | Reduce position sizes by 50% |
| 10-15% | Reduce to 1-2 positions only |
| > 15% | Stop trading, review strategy |
| > 20% | Full stop — take a break, analyze what went wrong |

---

## NSE-Specific Risk Considerations

### Transaction Costs

| Component | Typical Rate |
|-----------|-------------|
| Brokerage (discount) | ₹20/trade or 0.03% |
| STT (delivery) | 0.1% (buy + sell) |
| Exchange charges | 0.00345% |
| GST on brokerage | 18% of brokerage |
| SEBI charges | 0.0001% |
| Stamp duty | 0.015% (buy) |
| **Total approx.** | **~0.1-0.15% per side** |

### Circuit Limits

- **Upper/Lower Circuit:** Some stocks can be locked in circuit, preventing exit
- **Index Stocks:** NIFTY 50 stocks rarely hit circuits — prefer these for trading
- **Avoid:** Stocks with regular circuit hits unless specifically trading the pattern

### Settlement

- **T+1 Settlement:** Funds are available next trading day after selling
- **Pledged Shares:** Be aware of collateral requirements if using margin

### Corporate Actions

- **Earnings Season:** Reduce position sizes or exit before results
- **Ex-Dividend Dates:** Be aware of price adjustments
- **Bonus/Split:** Adjust stop-losses and targets post-corporate action

---

## Risk Checklist Before Every Trade

- [ ] Stop-loss is defined and placed
- [ ] Risk per trade ≤ 2% of capital
- [ ] Risk-reward ratio ≥ 1:1.5
- [ ] Portfolio heat ≤ 6%
- [ ] No sector over-concentration
- [ ] No earnings/events within holding period
- [ ] Sufficient liquidity (volume > 5L shares/day)
- [ ] Not trading against major trend (higher timeframe)

---

## Emotional Risk Rules

1. **No revenge trading:** After a loss, do NOT increase size to "make it back"
2. **No FOMO entries:** If you missed an entry, wait for the next setup
3. **Plan the trade, trade the plan:** Don't modify stops or targets mid-trade without new information
4. **Daily loss limit:** Stop trading if you lose 3% of capital in a single day
5. **Weekly review:** Review all trades weekly — look for pattern in losses
