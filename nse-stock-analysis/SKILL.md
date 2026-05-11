---
name: nse-stock-analysis
version: 1.0.0
description: Professional NSE stock analysis with screening, swing trading, ICT concepts, backtesting, sector rotation, valuation, and risk management for Indian equity markets.
author: aryashree-p
tags:
  - nse
  - indian-stocks
  - swing-trading
  - technical-analysis
  - backtesting
  - valuation
  - sector-rotation
  - risk-management
  - ict
  - screening
language: python
requirements:
  - python>=3.9
  - nsepython>=0.5
  - yfinance>=0.2.18
  - pandas>=2.0
  - pandas_ta>=0.3.14
  - numpy>=1.24
  - vectorbt>=0.26
  - backtesting>=0.3.3
---

# NSE Stock Analysis

A production-grade Indian equity market analysis tool for NSE-listed stocks. Provides institutional-quality screening, swing trading analysis, ICT-based setups, backtesting, valuation, sector rotation, and risk management - all powered by public market data.

**Target users:** Swing traders, positional traders, value investors, and systematic analysts operating in Indian equity markets (NSE/BSE).

---

## When to Use This Skill

Activate this skill when the user:

- Asks to **analyze an NSE stock** (e.g., "Analyze RELIANCE", "What's the setup on HDFCBANK?")
- Requests **stock screening** (e.g., "Find oversold large caps", "Screen for breakout candidates")
- Wants **swing trading analysis** (e.g., "Swing trade setup for TCS", "Is INFY in a trend?")
- Asks about **ICT concepts** on a stock (e.g., "Show order blocks on SBIN", "Find fair value gaps on NIFTY")
- Needs **backtesting** (e.g., "Backtest EMA crossover on RELIANCE for 2 years")
- Requests **sector comparison** (e.g., "Compare IT vs Banking sector", "Rank NIFTY 50 by relative strength")
- Wants **valuation analysis** (e.g., "Is INFY undervalued?", "Calculate intrinsic value of TCS")
- Needs **risk assessment** (e.g., "Risk score my portfolio", "What's the max drawdown on this strategy?")
- Asks about **FII/DII flows** (e.g., "Show institutional activity", "Are FIIs buying banking stocks?")
- Wants **delivery breakout** analysis (e.g., "Find delivery % spikes", "Accumulation signals in NIFTY 500")

**Do NOT use this skill for:** Cryptocurrency, forex, US/global stocks, options Greeks computation, or real-time intraday scalping.

---

## Important Disclaimers

> **⚠️ NOT FINANCIAL ADVICE**: All analysis is for educational and informational purposes only. This tool does not constitute investment advice. Consult a SEBI-registered investment advisor before trading.
>
> **⚠️ DATA LIMITATIONS**: Data is sourced from public APIs (NSE, Yahoo Finance). There may be delays, gaps, or inaccuracies. Always verify critical data points independently.
>
> **⚠️ PAST PERFORMANCE**: Historical backtesting results do not guarantee future returns. Markets are inherently uncertain.

---

## Supported Workflows

### Workflow 1: Stock Screening

Screen NSE stocks across multiple technical and fundamental factors.

#### Step 1: Define Screening Criteria

```bash
python scripts/screener.py \
  --universe "NIFTY500" \
  --rsi-below 35 \
  --above-ema 200 \
  --min-volume 500000 \
  --min-delivery-pct 50 \
  --sector "IT"
```

**Parameters:**
- `--universe`: Stock universe - `NIFTY50`, `NIFTY100`, `NIFTY200`, `NIFTY500`, or comma-separated symbols
- `--rsi-below` / `--rsi-above`: RSI(14) filter (0-100)
- `--above-ema` / `--below-ema`: Price relative to EMA (9, 21, 50, 100, 200)
- `--min-volume`: Minimum average daily volume
- `--min-delivery-pct`: Minimum delivery percentage
- `--sector`: Filter by NIFTY sector index
- `--min-market-cap`: Minimum market cap in crores

#### Step 2: Review Screening Results

| Symbol | CMP | RSI(14) | Above 200 EMA | Volume | Delivery % | Sector |
|--------|-----|---------|----------------|--------|------------|--------|
| INFY | ₹1,456 | 32.4 | ✅ Yes (+4.2%) | 8.2M | 62% | IT |
| TCS | ₹3,890 | 28.7 | ✅ Yes (+2.1%) | 3.1M | 58% | IT |
| WIPRO | ₹412 | 34.1 | ✅ Yes (+1.8%) | 12.4M | 55% | IT |

#### Step 3: Deep Dive

For any screened stock, proceed to Workflow 2 (Swing Analysis) or Workflow 6 (Valuation).

---

### Workflow 2: Swing Trading Analysis

Full swing trading setup analysis with entry, target, and stop-loss levels.

#### Step 1: Fetch Data and Compute Indicators

```bash
python scripts/swing_analyzer.py \
  --symbol "RELIANCE" \
  --period "6mo" \
  --ema-fast 9 \
  --ema-mid 21 \
  --ema-slow 55
```

**Parameters:**
- `--symbol`: NSE symbol (e.g., RELIANCE, TCS, HDFCBANK)
- `--period`: Analysis period - `1mo`, `3mo`, `6mo`, `1y`, `2y`
- `--ema-fast`: Fast EMA period (default: 9)
- `--ema-mid`: Mid EMA period (default: 21)
- `--ema-slow`: Slow EMA period (default: 55)

#### Step 2: Analyze Output

The script produces a structured swing analysis:

**Trend Assessment:**
- EMA alignment (bullish: 9 > 21 > 55, bearish: 9 < 21 < 55)
- Price position relative to EMAs
- ADX trend strength

**Signal Detection:**
- Triple EMA crossover signals
- Volume breakout (volume > 2x 20-day average)
- ATR expansion (ATR > 1.5x 20-day average ATR)
- Delivery breakout (delivery % > 1.5x 20-day average)
- Breakout retest confirmation

**Entry/Exit Levels:**
- Entry zone (price range)
- Stop-loss (ATR-based or swing low)
- Target 1 (1:1.5 R:R)
- Target 2 (1:2.5 R:R)
- Target 3 (1:4 R:R)

#### Step 3: Generate Report

```bash
python scripts/swing_analyzer.py --symbol "RELIANCE" --report
```

Outputs a structured markdown report using `templates/swing_report.md`.

---

### Workflow 3: ICT Setup Analysis

Analyze stocks using Inner Circle Trader (ICT) concepts.

#### Step 1: Run ICT Analysis

```bash
python scripts/swing_analyzer.py \
  --symbol "HDFCBANK" \
  --ict \
  --timeframe "daily"
```

#### Step 2: ICT Output Includes

- **Order Blocks (OB):** Last bullish/bearish order blocks with price levels
- **Fair Value Gaps (FVG):** Unfilled gaps as potential entry zones
- **Liquidity Sweeps:** Recent sweep of highs/lows (stop hunts)
- **Market Structure:** Higher highs/higher lows or lower highs/lower lows
- **Optimal Trade Entry (OTE):** 62-79% Fibonacci retracement zones
- **Kill Zones:** Alignment with London/NY open mapped to IST

#### ICT Concepts Reference

See `references/ict.md` for detailed ICT terminology and application to Indian markets.

---

### Workflow 4: Scanner Workflows

#### Triple EMA Crossover Scanner

```bash
python scripts/screener.py \
  --universe "NIFTY200" \
  --scan "triple-ema-crossover" \
  --lookback 5
```

Finds stocks where the 9 EMA crossed above 21 EMA while both are above 55 EMA within the last N days.

| Symbol | Crossover Date | 9 EMA | 21 EMA | 55 EMA | Volume Surge | Signal |
|--------|---------------|-------|--------|--------|-------------|--------|
| BAJFINANCE | 2026-05-08 | ₹7,245 | ₹7,198 | ₹7,012 | ✅ 2.3x | 🟢 BUY |
| TATAMOTORS | 2026-05-07 | ₹652 | ₹648 | ₹631 | ✅ 1.8x | 🟢 BUY |

#### Volume Breakout Scanner

```bash
python scripts/screener.py \
  --universe "NIFTY500" \
  --scan "volume-breakout" \
  --volume-multiplier 2.0 \
  --price-change-pct 2.0
```

Detects stocks with unusual volume surge (>2x average) accompanied by significant price movement.

#### PPA Scanner (Price-Price Action)

```bash
python scripts/screener.py \
  --universe "NIFTY200" \
  --scan "ppa" \
  --consolidation-days 10 \
  --breakout-threshold 1.5
```

Identifies stocks breaking out of tight consolidation ranges with volume confirmation. See `references/ppa.md` for PPA logic details.

#### Delivery Breakout Scanner

```bash
python scripts/screener.py \
  --universe "NIFTY200" \
  --scan "delivery-breakout" \
  --delivery-pct-threshold 60 \
  --delivery-surge-multiplier 1.5
```

Finds stocks where delivery percentage has spiked significantly above average, indicating institutional accumulation.

---

### Workflow 5: Backtesting

Backtest trading strategies on NSE stocks using historical data.

#### Step 1: Run Backtest

```bash
python scripts/backtest.py \
  --symbol "TCS" \
  --strategy "triple-ema-crossover" \
  --period "2y" \
  --capital 1000000 \
  --risk-per-trade 1.0
```

**Parameters:**
- `--symbol`: NSE symbol
- `--strategy`: Strategy name - `triple-ema-crossover`, `rsi-mean-reversion`, `breakout-retest`, `ema-pullback`
- `--period`: Backtest period - `6mo`, `1y`, `2y`, `5y`
- `--capital`: Starting capital in INR (default: ₹10,00,000)
- `--risk-per-trade`: Risk per trade as % of capital (default: 1%)
- `--commission`: Brokerage + taxes per trade in % (default: 0.1%)

#### Step 2: Review Backtest Results

```
╔══════════════════════════════════════════╗
║     BACKTEST RESULTS: TCS                ║
║     Strategy: Triple EMA Crossover       ║
║     Period: 2024-05-01 to 2026-05-01     ║
╠══════════════════════════════════════════╣
║ Total Return:         +34.2%             ║
║ CAGR:                 +16.1%             ║
║ Max Drawdown:         -12.4%             ║
║ Sharpe Ratio:         1.42               ║
║ Win Rate:             58.3%              ║
║ Profit Factor:        1.87               ║
║ Total Trades:         24                  ║
║ Avg Holding Period:   12.3 days          ║
║ Risk-Reward Ratio:    1:2.1              ║
╚══════════════════════════════════════════╝
```

#### Step 3: Generate Report

```bash
python scripts/backtest.py --symbol "TCS" --strategy "triple-ema-crossover" --report
```

Outputs a detailed report using `templates/backtest_report.md`.

#### Available Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| `triple-ema-crossover` | 9/21/55 EMA crossover with volume filter | Trending markets |
| `rsi-mean-reversion` | Buy RSI < 30, sell RSI > 70 with EMA filter | Range-bound markets |
| `breakout-retest` | Buy on breakout retest with volume confirmation | Consolidation breakouts |
| `ema-pullback` | Buy on pullback to 21 EMA in uptrend | Trending pullbacks |

---

### Workflow 6: Valuation Analysis

Fundamental valuation for long-term investment analysis.

#### Step 1: Run Valuation

```bash
python scripts/valuation.py \
  --symbol "INFY" \
  --method "all"
```

**Parameters:**
- `--symbol`: NSE symbol
- `--method`: Valuation method - `dcf`, `pe-relative`, `pb-relative`, `graham`, `peg`, `all`

#### Step 2: Review Valuation Output

| Metric | Value |
|--------|-------|
| Current Market Price | ₹1,456 |
| PE Ratio (TTM) | 24.3x |
| Industry Avg PE | 28.1x |
| PB Ratio | 7.8x |
| ROE (TTM) | 32.1% |
| ROCE | 38.4% |
| Debt/Equity | 0.08 |
| Dividend Yield | 2.4% |
| Graham Number | ₹1,234 |
| DCF Fair Value | ₹1,612 |
| PEG Ratio | 1.1 |
| **Verdict** | **🟢 Fairly Valued to Slightly Undervalued** |

#### Valuation Verdicts

- 🟢 **Undervalued**: CMP < 80% of fair value - potential buying opportunity
- 🟡 **Fairly Valued**: CMP within 80-120% of fair value - hold/accumulate
- 🔴 **Overvalued**: CMP > 120% of fair value - avoid fresh entry

---

### Workflow 7: Sector Comparison & Relative Strength

Compare stocks within or across sectors and rank by relative strength.

#### Step 1: Sector Comparison

```bash
python scripts/sector_compare.py \
  --sectors "NIFTY IT,NIFTY BANK,NIFTY PHARMA" \
  --period "3mo" \
  --benchmark "NIFTY 50"
```

#### Step 2: Relative Strength Ranking

```bash
python scripts/sector_compare.py \
  --universe "NIFTY50" \
  --rank-by "relative-strength" \
  --period "3mo" \
  --top 10
```

| Rank | Symbol | RS Score | 3M Return | vs NIFTY 50 | Trend |
|------|--------|----------|-----------|-------------|-------|
| 1 | BAJFINANCE | 94.2 | +18.4% | +12.1% | 🟢 Strong |
| 2 | RELIANCE | 88.7 | +15.2% | +8.9% | 🟢 Strong |
| 3 | HDFCBANK | 82.1 | +12.8% | +6.5% | 🟢 Strong |
| ... | ... | ... | ... | ... | ... |

#### Step 3: Sector Rotation Analysis

```bash
python scripts/sector_compare.py \
  --rotation \
  --period "6mo"
```

Produces a sector rotation quadrant analysis:
- **Leading:** Strong momentum + improving relative strength
- **Weakening:** Strong momentum + declining relative strength
- **Lagging:** Weak momentum + declining relative strength
- **Improving:** Weak momentum + improving relative strength

---

### Workflow 8: Risk Scoring & Portfolio Analysis

#### Step 1: Score Individual Stock Risk

```bash
python scripts/risk_score.py \
  --symbol "RELIANCE" \
  --capital 500000
```

#### Step 2: Portfolio Risk Analysis

```bash
python scripts/risk_score.py \
  --portfolio "RELIANCE:30,TCS:25,HDFCBANK:20,INFY:15,SBIN:10" \
  --capital 1000000
```

**Portfolio allocation format:** `SYMBOL:weight_pct` (weights must sum to 100).

#### Risk Output

| Metric | Value | Rating |
|--------|-------|--------|
| Portfolio Beta | 0.92 | 🟢 Low |
| Value at Risk (95%) | ₹42,300 | 🟡 Moderate |
| Max Drawdown (1Y) | -14.2% | 🟡 Moderate |
| Sharpe Ratio | 1.24 | 🟢 Good |
| Sortino Ratio | 1.67 | 🟢 Good |
| Sector Concentration | 45% Financial | 🔴 High |
| **Overall Risk Score** | **62/100** | **🟡 Moderate Risk** |

#### Risk Ratings

- 🟢 **Low Risk (0-40):** Well-diversified, low volatility, strong fundamentals
- 🟡 **Moderate Risk (41-70):** Acceptable for swing/positional trading
- 🔴 **High Risk (71-100):** High concentration, volatility, or fundamental concerns

---

## Risk Management Framework

Every analysis output must include:

1. **Position Sizing:** Maximum 2% capital risk per trade
2. **Stop-Loss:** Always defined - ATR-based (1.5-2x ATR) or swing structure based
3. **Risk-Reward:** Minimum 1:1.5 R:R for entry consideration
4. **Portfolio Heat:** Maximum 6% total portfolio risk at any time
5. **Sector Exposure:** Maximum 40% in any single sector
6. **Single Stock:** Maximum 20% of portfolio in any single stock

### Position Size Formula

```
Position Size = (Capital × Risk%) / (Entry - Stop Loss)
```

### Risk Per Trade Categories

| Category | Max Risk/Trade | Max Open Risk | Suitable For |
|----------|---------------|---------------|-------------|
| Conservative | 0.5% | 3% | New traders, large capital |
| Moderate | 1.0% | 6% | Experienced swing traders |
| Aggressive | 2.0% | 10% | Professional traders |

---

## FII/DII Activity Analysis

Track institutional money flow:

```bash
python scripts/data_fetcher.py \
  --fii-dii \
  --period "1mo"
```

| Date | FII Buy (₹Cr) | FII Sell (₹Cr) | FII Net | DII Buy (₹Cr) | DII Sell (₹Cr) | DII Net |
|------|---------------|----------------|---------|---------------|----------------|---------|
| 2026-05-09 | 12,450 | 10,230 | +2,220 | 8,340 | 9,120 | -780 |
| 2026-05-08 | 11,890 | 13,450 | -1,560 | 10,230 | 8,670 | +1,560 |

---

## Output Formatting Standards

All outputs must follow these standards:

### Numeric Formatting
- **Prices:** ₹ symbol, comma-separated (₹1,23,456.78)
- **Percentages:** 1 decimal place with % sign (+12.4%, -3.2%)
- **Volumes:** Short format (12.4M, 3.2L, 1.8Cr)
- **Market Cap:** In crores (₹4,52,000 Cr)

### Status Indicators
- 🟢 Bullish / Positive / Low Risk / Buy Signal
- 🟡 Neutral / Moderate / Watch / Hold
- 🔴 Bearish / Negative / High Risk / Sell Signal

### Report Structure
Every report must include:
1. **Header:** Stock name, date, analysis type
2. **Summary:** 2-3 line executive summary with verdict
3. **Data Tables:** Structured metrics with clear labels
4. **Levels:** Entry, stop-loss, targets (where applicable)
5. **Risk Warning:** Standard disclaimer
6. **Timestamp:** IST timestamp of analysis

---

## Error Handling Standards

### Data Errors
- If NSE API is unavailable, fall back to yfinance data with a warning
- If a symbol is not found, suggest similar symbols (fuzzy match)
- If data is stale (>24 hours old), display warning with last update time

### Calculation Errors
- If insufficient data for an indicator (e.g., 200 EMA needs 200 data points), warn the user and use available data
- If a valuation metric cannot be computed (e.g., negative earnings for PE), skip with explanation
- Never output NaN/null - always replace with "N/A" and explain why

### User Input Errors
- Invalid symbol → suggest corrections
- Invalid date range → suggest valid range
- Conflicting parameters → explain conflict and use defaults

### Standard Error Response Format

```
⚠️ ERROR: [Error Type]
Cause: [Brief explanation]
Resolution: [What to do]
Fallback: [Alternative action taken, if any]
```

---

## Example Prompts and Expected Behavior

### Example 1: Quick Stock Check

**User:** "How does RELIANCE look?"

**Expected:** Run swing analysis with default parameters. Produce a concise summary with trend, key levels, and signal.

### Example 2: Screening Request

**User:** "Find NIFTY 200 stocks with RSI below 30 that are above their 200 EMA"

**Expected:** Run screener with `--universe NIFTY200 --rsi-below 30 --above-ema 200`. Present results in a table.

### Example 3: Backtest Request

**User:** "Backtest EMA crossover strategy on TCS for 2 years with 10 lakh capital"

**Expected:** Run backtest with `--symbol TCS --strategy triple-ema-crossover --period 2y --capital 1000000`. Show results and risk metrics.

### Example 4: Valuation Request

**User:** "Is HDFCBANK undervalued?"

**Expected:** Run valuation with `--symbol HDFCBANK --method all`. Compare current price to intrinsic values. Give a clear verdict.

### Example 5: Sector Comparison

**User:** "Compare IT stocks performance this quarter"

**Expected:** Run sector comparison for NIFTY IT constituents over 3 months. Rank by relative strength.

### Example 6: Portfolio Risk Check

**User:** "Check risk for my portfolio: 40% RELIANCE, 30% TCS, 20% HDFCBANK, 10% SBIN"

**Expected:** Run portfolio risk scoring. Highlight concentration risk, compute VaR, suggest rebalancing if needed.

---

## Example Analysis: RELIANCE Swing Trading

```
═══════════════════════════════════════════════════════
  SWING ANALYSIS: RELIANCE INDUSTRIES LIMITED (NSE)
  Date: 2026-05-11 | Timeframe: Daily
═══════════════════════════════════════════════════════

📊 TREND ASSESSMENT
  EMA 9:   ₹2,945.30  (Price above ✅)
  EMA 21:  ₹2,912.45  (Price above ✅)
  EMA 55:  ₹2,867.80  (Price above ✅)
  Alignment: 🟢 BULLISH (9 > 21 > 55)
  ADX:      28.4 (Trending)
  RSI(14):  58.2 (Neutral)

📈 SIGNAL DETECTION
  Triple EMA Crossover:    ✅ Active (crossed 3 days ago)
  Volume Breakout:         ✅ 2.1x average volume
  ATR Expansion:           🟡 1.3x (moderate)
  Delivery Breakout:       ✅ 68% vs 52% avg
  Breakout Retest:         ✅ Retested ₹2,920 and held

🎯 TRADE SETUP
  Signal:      🟢 BUY
  Entry Zone:  ₹2,930 – ₹2,950
  Stop Loss:   ₹2,867 (below 55 EMA, 2.8% risk)
  Target 1:    ₹3,030 (R:R 1:1.5)
  Target 2:    ₹3,130 (R:R 1:2.5)
  Target 3:    ₹3,280 (R:R 1:4.0)

📐 POSITION SIZING (₹10,00,000 capital, 1% risk)
  Risk Amount:    ₹10,000
  Position Size:  120 shares (₹3,54,000)
  % of Capital:   35.4%

⚠️  RISK WARNING
  • This is a TRADE setup, not an investment recommendation
  • Always use a stop-loss
  • Past patterns do not guarantee future results
  • Consult a SEBI-registered advisor for personalized advice

  Generated: 2026-05-11 15:30 IST
═══════════════════════════════════════════════════════
```

---

## Example Analysis: INFY Valuation

```
═══════════════════════════════════════════════════════
  VALUATION ANALYSIS: INFOSYS LIMITED (NSE)
  Date: 2026-05-11
═══════════════════════════════════════════════════════

📊 KEY FUNDAMENTALS
  Market Cap:       ₹6,04,320 Cr
  PE Ratio (TTM):   24.3x (Industry: 28.1x)
  PB Ratio:         7.8x
  EV/EBITDA:        18.2x
  ROE:              32.1%
  ROCE:             38.4%
  Debt/Equity:      0.08
  Dividend Yield:   2.4%
  EPS (TTM):        ₹59.92

💰 VALUATION MODELS
  Graham Number:        ₹1,234 (CMP: ₹1,456 → 🔴 Above)
  PE Relative Value:    ₹1,682 (CMP: ₹1,456 → 🟢 Below)
  PEG Ratio:            1.1   (→ 🟢 Fairly Valued)
  DCF Fair Value:       ₹1,612 (CMP: ₹1,456 → 🟢 Below)

📋 VERDICT: 🟢 FAIRLY VALUED TO SLIGHTLY UNDERVALUED
  Average Fair Value:   ₹1,510
  Current Price:        ₹1,456 (3.6% below fair value)
  Margin of Safety:     3.6% (Thin - wait for dips for better entry)

  Recommendation: ACCUMULATE on dips below ₹1,400
  Investment Horizon: 12-24 months

⚠️  This is NOT financial advice. Verify data independently.
  Generated: 2026-05-11 15:30 IST
═══════════════════════════════════════════════════════
```
