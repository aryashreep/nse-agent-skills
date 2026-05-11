# Indian Market Rules & Structure

## Overview

This reference covers NSE/BSE market structure, trading hours, regulatory framework, and key institutional details relevant to systematic stock analysis.

---

## Market Hours (IST)

| Session | Timing | Notes |
|---------|--------|-------|
| Pre-Open | 9:00 AM - 9:15 AM | Order collection, price discovery |
| Normal Trading | 9:15 AM - 3:30 PM | Continuous trading |
| Closing Session | 3:40 PM - 4:00 PM | Closing price determination |
| Post-Close | 4:00 PM - 4:15 PM | Trade modification |
| AMO (After Market) | 4:00 PM - 9:00 AM | Order placement for next day |

**Key Timing Notes:**
- NSE is closed on Saturdays, Sundays, and declared holidays
- Muhurat Trading: Special 1-hour session on Diwali day
- No after-hours continuous trading (unlike US markets)

---

## Market Indices

### Broad Market
| Index | Description | Constituents |
|-------|-------------|-------------|
| NIFTY 50 | Large cap benchmark | 50 stocks |
| NIFTY Next 50 | Junior large caps | 50 stocks |
| NIFTY 100 | Top 100 by market cap | 100 stocks |
| NIFTY 200 | Broad large + mid cap | 200 stocks |
| NIFTY 500 | Broad market | 500 stocks |
| NIFTY Midcap 50 | Mid cap index | 50 stocks |
| NIFTY Smallcap 50 | Small cap index | 50 stocks |

### Sectoral Indices
| Index | Sector |
|-------|--------|
| NIFTY Bank | Banking |
| NIFTY IT | Information Technology |
| NIFTY Pharma | Pharmaceuticals |
| NIFTY FMCG | Fast Moving Consumer Goods |
| NIFTY Auto | Automobiles |
| NIFTY Metal | Metals & Mining |
| NIFTY Realty | Real Estate |
| NIFTY Energy | Energy |
| NIFTY Infra | Infrastructure |
| NIFTY PSE | Public Sector Enterprises |
| NIFTY Financial Services | Financial Services (broader) |
| NIFTY Media | Media & Entertainment |

---

## Settlement & Clearing

| Parameter | Detail |
|-----------|--------|
| Settlement Cycle | T+1 (from Jan 27, 2023) |
| Clearing Corporation | NSE Clearing Limited (NCL) |
| Depository | CDSL, NSDL |
| STT on Delivery | 0.1% (both buy and sell) |
| STT on Intraday | 0.025% (sell side only) |

---

## Circuit Limits

### Index-Level Circuit Breakers

| Trigger Level | Before 1:00 PM | 1:00 PM - 2:30 PM | After 2:30 PM |
|--------------|---------------|-------------------|---------------|
| 10% movement | 45 min halt | 15 min halt | No halt |
| 15% movement | 1 hr 45 min halt | 45 min halt | Remainder of day |
| 20% movement | Remainder of day | Remainder of day | Remainder of day |

### Stock-Level Circuit Limits

- **Price Bands:** 2%, 5%, 10%, or 20% based on exchange classification
- **No Circuit:** Stocks in F&O segment have no circuit limits
- **Dynamic Price Bands:** Applied to F&O stocks to prevent erratic moves

---

## Regulatory Framework

### SEBI (Securities and Exchange Board of India)

- Primary regulator for securities markets
- Regulates mutual funds, FIIs, portfolio managers
- Enforces insider trading regulations
- Mandates disclosure requirements

### Key SEBI Regulations for Traders

1. **Insider Trading:** Trading based on unpublished price-sensitive information is prohibited
2. **Front Running:** Prohibited — executing orders ahead of large client orders
3. **Market Manipulation:** Creating artificial volume or price is prohibited
4. **Disclosure:** Promoters must disclose stake changes > 2%
5. **Short Selling:** Allowed for institutional investors with disclosure

---

## FII/DII Framework

### Foreign Institutional Investors (FII) / Foreign Portfolio Investors (FPI)

- Registered with SEBI under FPI regulations
- Categories: Category I (sovereign), II (regulated), III (others)
- Investment limits: Sector-wise and company-wise caps
- Daily FII buy/sell data published by NSDL/CDSL

### Domestic Institutional Investors (DII)

- Mutual Funds, Insurance Companies, Banks
- DII flows often counterbalance FII flows
- Mutual fund SIP flows provide steady DII buying (~₹15,000-20,000 Cr/month)

### How to Use FII/DII Data

| Pattern | Implication |
|---------|-------------|
| FII buying + DII buying | Strong bullish signal |
| FII buying + DII selling | FII-driven rally (may reverse) |
| FII selling + DII buying | Potential bottom formation |
| FII selling + DII selling | Strong bearish signal |

---

## Delivery Data

### What It Tells You

- **Delivery %** = (Delivered Quantity / Total Traded Quantity) × 100
- High delivery % suggests genuine buying/selling (not speculative)
- Average delivery % varies by stock — compare to its own average

### Interpretation

| Delivery % | Interpretation |
|-----------|---------------|
| > 70% | Strong institutional interest |
| 50-70% | Moderate — mixed retail/institutional |
| 30-50% | Speculative activity dominates |
| < 30% | Highly speculative — mostly intraday traders |

### Delivery Breakout Signal

```
IF Today's Delivery % > 1.5 × 20-day Average Delivery %
AND Price Change > +1%
AND Volume > 1.5 × Average Volume
THEN → Institutional accumulation signal
```

---

## Corporate Actions Calendar

| Action | Impact | Data Source |
|--------|--------|------------|
| Quarterly Results | High volatility around results date | BSE/NSE announcements |
| Dividends | Price adjusts on ex-date | Company announcements |
| Bonus Issues | Price adjusts, shares increase | Board meeting outcomes |
| Stock Splits | Price adjusts proportionally | Company announcements |
| Rights Issues | Dilution risk | SEBI filings |
| Buybacks | Generally positive for price | Board approvals |

---

## Market Microstructure Notes

1. **Lot Size:** F&O lot sizes set by exchange (varies by stock)
2. **Tick Size:** ₹0.05 for stocks > ₹1, ₹0.01 for stocks ≤ ₹1
3. **Order Types:** Market, Limit, Stop-Loss, Stop-Loss Market, AMO
4. **Auction:** Special call auction for illiquid stocks
5. **Block Deals:** Minimum ₹10 Cr, executed in separate window (8:45-9:00 AM)
6. **Bulk Deals:** > 0.5% of equity shares — must be disclosed to exchange

---

## Tax Implications (for reference only)

| Type | Holding Period | Tax Rate |
|------|---------------|----------|
| STCG (Short Term Capital Gains) | < 12 months | 20% (Budget 2024) |
| LTCG (Long Term Capital Gains) | > 12 months | 12.5% (above ₹1.25 lakh) |
| Intraday Trading | N/A | Taxed as business income |
| F&O Trading | N/A | Taxed as business income |

*Tax rates are subject to change. Consult a CA for personalized tax advice.*

---

## Data Sources

| Data | Source | Update Frequency |
|------|--------|-----------------|
| Price/Volume | NSE, Yahoo Finance | Real-time / EOD |
| Delivery Data | NSE Bhavcopy | EOD |
| FII/DII Flows | NSDL, NSE | Daily |
| Corporate Actions | BSE, NSE | As announced |
| Index Constituents | NSE | Quarterly review |
| Financial Statements | BSE, Screener.in | Quarterly |
