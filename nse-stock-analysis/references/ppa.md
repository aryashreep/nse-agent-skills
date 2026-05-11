# PPA (Price-Price Action) Scanner Logic

## Overview

The PPA scanner identifies stocks emerging from tight consolidation (compression) with volume expansion. It is designed to catch early-stage breakouts before they become widely visible on conventional scanners.

---

## Core Concept

**Price Compression → Expansion:** Stocks that trade in a narrow range for an extended period build energy. When they break out of this compression with volume, the subsequent move tends to be powerful and directional.

---

## PPA Scanner Algorithm

### Step 1: Identify Consolidation

A stock is in consolidation when:

```
Consolidation Range = High(N days) - Low(N days)
Average ATR = mean(ATR(14)) over N days
Range Ratio = Consolidation Range / Average ATR

IF Range Ratio < (N * 0.5):
    → Stock is in TIGHT consolidation
```

**Parameters:**
- `N` (consolidation_days): Minimum days in consolidation (default: 10)
- Range Ratio threshold: `N * 0.5` — tighter ranges get higher scores

### Step 2: Detect Breakout

A breakout occurs when:

```
Today's Range = High - Low
Breakout Ratio = Today's Range / Average ATR

IF Breakout Ratio > breakout_threshold (default: 1.5):
    → BREAKOUT detected
```

### Step 3: Confirm Direction

```
IF Close > Consolidation High:
    → BULLISH breakout (🟢)
ELIF Close < Consolidation Low:
    → BEARISH breakout (🔴)
ELSE:
    → FALSE breakout (skip)
```

### Step 4: Volume Confirmation

```
Volume Ratio = Today's Volume / 20-day Average Volume

IF Volume Ratio > 1.5:
    → Volume CONFIRMED ✅
    IF Volume Ratio > 2.5:
        → Strong institutional interest
```

### Step 5: Quality Scoring

```
PPA Score = 0

IF Range Ratio < N * 0.3:    PPA Score += 30  (very tight consolidation)
ELIF Range Ratio < N * 0.5:  PPA Score += 20  (tight consolidation)

IF Breakout Ratio > 2.0:     PPA Score += 25  (strong breakout)
ELIF Breakout Ratio > 1.5:   PPA Score += 15

IF Volume Ratio > 2.5:       PPA Score += 25  (strong volume)
ELIF Volume Ratio > 1.5:     PPA Score += 15

IF Close > EMA(21):          PPA Score += 10  (trend alignment)
IF RSI(14) between 40-70:    PPA Score += 10  (not overbought/oversold)

TOTAL: 0-100
```

---

## PPA Categories

| PPA Score | Category | Action |
|-----------|----------|--------|
| 80-100 | A+ Setup | Strong conviction entry |
| 60-79 | A Setup | Entry with standard position size |
| 40-59 | B Setup | Watch list — wait for confirmation |
| < 40 | C Setup | Skip — insufficient conviction |

---

## Best Practices

### Ideal PPA Setup Characteristics
1. **Consolidation:** 10-30 days of tight range (< 5% total range)
2. **Volume:** Declining volume during consolidation, surge on breakout
3. **Trend Alignment:** Stock above 200 EMA (higher timeframe trend intact)
4. **Sector Alignment:** Sector index also trending or breaking out
5. **Delivery %:** Above-average delivery on breakout day

### Filters to Avoid False Breakouts
- Avoid breakouts into resistance (prior swing highs)
- Skip if RSI > 80 on breakout (already extended)
- Require at least 1.5x average volume
- Avoid penny stocks (CMP < ₹50) or very low liquidity stocks
- Check if results day or corporate action is imminent (avoid event risk)

### Stop-Loss Placement
- **Below consolidation low:** For bullish breakouts
- **ATR-based:** 1.5x ATR below breakout candle low
- **Use tighter stop:** If consolidation is very tight (high compression)

### Target Setting
- **Target 1:** Width of consolidation range projected from breakout level
- **Target 2:** 2x consolidation range
- **Target 3:** Next major resistance level

---

## NSE-Specific Considerations

1. **Circuit Limits:** Some stocks may hit upper circuit on breakout — consider partial entry before breakout
2. **T+1 Settlement:** Be aware of settlement cycle for position sizing
3. **NIFTY Index:** Check if NIFTY itself is in compression — sector rotation often follows
4. **Delivery Data:** High delivery % on breakout day is a strong confirmation for NSE stocks
5. **FII/DII Data:** Cross-reference with institutional buying for additional conviction

---

## Example PPA Scan Output

```
Symbol   | Consol Range        | Days | Breakout ATR | Vol Surge | PPA Score | Direction
---------|---------------------|------|-------------|-----------|-----------|----------
BAJFIN   | ₹7,100 - ₹7,250    | 12   | 2.3x        | 2.8x      | 85        | 🟢 UP
TATAMTR  | ₹620 - ₹645        | 15   | 1.8x        | 2.1x      | 72        | 🟢 UP
MARUTI   | ₹10,800 - ₹11,200  | 8    | 1.6x        | 1.7x      | 58        | 🟡 WATCH
```
