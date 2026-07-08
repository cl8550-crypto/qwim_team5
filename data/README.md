# QWIM Team 5 — Market Data

Daily price data (adjusted close + OHLCV) downloaded from Yahoo Finance via `yfinance`.
CPI is monthly from FRED (`CPIAUCSL`). All files in CSV format with a `Date` index.

## Folder Structure

```
data/
├── sectors/        S&P 500 sector ETFs (SPDR Select Sector series)
├── bonds/          US fixed income ETFs
├── commodities/    Broad commodities and gold ETFs
├── rates/          Risk-free rate proxies (short-term T-bill ETFs)
├── volatility/     Equity volatility (VIX index + VIX futures ETF)
└── macro/          Macroeconomic indicators (monthly)
```

## Tickers

### sectors/
| File | Ticker | Description |
|------|--------|-------------|
| XLC_Communication_Services.csv | XLC | Communication Services |
| XLY_Consumer_Discretionary.csv | XLY | Consumer Discretionary |
| XLP_Consumer_Staples.csv | XLP | Consumer Staples |
| XLE_Energy.csv | XLE | Energy |
| XLF_Financials.csv | XLF | Financials |
| XLV_Health_Care.csv | XLV | Health Care |
| XLI_Industrials.csv | XLI | Industrials |
| XLRE_Real_Estate.csv | XLRE | Real Estate |
| XLB_Materials.csv | XLB | Materials |
| XLK_Technology.csv | XLK | Technology |
| XLU_Utilities.csv | XLU | Utilities |

### bonds/
| File | Ticker | Description |
|------|--------|-------------|
| AGG_US_Aggregate_Bonds.csv | AGG | iShares Core U.S. Aggregate Bond ETF |
| TIP_TIPS.csv | TIP | iShares TIPS Bond ETF |

### commodities/
| File | Ticker | Description |
|------|--------|-------------|
| DBC_Commodities_Broad.csv | DBC | Invesco DB Commodity Index Tracking Fund |
| GLD_Gold.csv | GLD | SPDR Gold Shares |

### rates/
| File | Ticker | Description |
|------|--------|-------------|
| BIL_Risk_Free_Rate_1_3M_TBill.csv | BIL | SPDR Bloomberg 1-3 Month T-Bill ETF |
| SHV_Risk_Free_Rate_Short_Term.csv | SHV | iShares Short Treasury Bond ETF |

### volatility/
| File | Ticker | Description |
|------|--------|-------------|
| VIX_Index.csv | ^VIX | CBOE Volatility Index (spot) |
| Equity_Volatility_VIX_Futures.csv | VIXY | ProShares VIX Short-Term Futures ETF |

### macro/
| File | Source | Description | Frequency |
|------|--------|-------------|-----------|
| CPI_Monthly_CPIAUCSL.csv | FRED | Consumer Price Index for All Urban Consumers | Monthly |

## Coverage
- **Start date:** 2000-01-01 (or ETF inception date if later)
- **End date:** Latest available
- **Frequency:** Daily (except CPI which is monthly)
