# NSE & Nifty Agent Skills

Production-grade [SKILLS.sh](https://skills.sh) skill for Indian equity market analysis, including **NSE and Nifty** screening, valuation, swing trading, sector rotation, backtesting, and risk management.

## Skills

| Skill | Description |
|---|---|
| [nse-stock-analysis](./nse-stock-analysis/) | Comprehensive NSE stock analysis with technical indicators, ICT concepts, PPA scanning, swing trading, backtesting, FII/DII tracking, and institutional-grade reporting |

## Quick Start

### Install via SKILLS.sh

```bash
skills install aryashree-p/nse-agent-skills/nse-stock-analysis
```

### Install Dependencies

```bash
pip install nsepython yfinance pandas pandas_ta numpy vectorbt backtesting
```

### Use with Claude Code

After installation, use natural language prompts:

```
Analyze RELIANCE for swing trading opportunities
Screen NSE stocks with RSI < 30 and above 200 EMA
Compare INFY vs TCS vs WIPRO sector performance
Backtest triple EMA crossover on HDFCBANK for 1 year
Show FII/DII activity for NIFTY 50 stocks
```

## Repository Structure

```
nse-agent-skills/
├── README.md
└── nse-stock-analysis/
     ├── SKILL.md
     ├── scripts/
     │    ├── data_fetcher.py      # NSE/yfinance data retrieval
     │    ├── screener.py          # Multi-factor stock screening
     │    ├── swing_analyzer.py    # Swing trading + ICT analysis
     │    ├── valuation.py         # Fundamental valuation models
     │    ├── sector_compare.py    # Sector rotation & relative strength
     │    ├── risk_score.py        # Portfolio risk scoring
     │    └── backtest.py          # Strategy backtesting engine
     ├── templates/
     │    ├── swing_report.md      # Swing trade report template
     │    ├── valuation_report.md  # Valuation analysis template
     │    └── backtest_report.md   # Backtest results template
     └── references/
          ├── ict.md               # ICT concepts reference
          ├── ppa.md               # Price-Price Action scanner logic
          ├── risk-management.md   # Risk management framework
          └── indian-market-rules.md # NSE/SEBI rules & market hours
```

## Supported Workflows

1. **Swing Trading Analysis** - EMA alignment, breakout detection, volume confirmation
2. **ICT Setup Analysis** - Order blocks, fair value gaps, liquidity sweeps
3. **Triple EMA Crossover Scanner** - 9/21/55 EMA crossover signals
4. **Breakout Detection** - Volume breakout, ATR expansion, retest logic
5. **Backtesting** - Historical strategy testing with vectorbt/backtesting.py
6. **Sector Comparison** - Relative strength ranking across NIFTY sectors
7. **Valuation** - DCF, PE/PB multiples, Graham number, PEG ratio
8. **Risk Scoring** - Portfolio-level beta, VaR, max drawdown, Sharpe ratio
9. **FII/DII Tracking** - Institutional flow analysis
10. **Delivery Breakout** - Delivery % spike detection for accumulation signals

## Disclaimer

This tool is for **educational and analytical purposes only**. It does not constitute financial advice. Always consult a SEBI-registered investment advisor before making trading or investment decisions. Past performance does not guarantee future results.

## License

MIT
