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
| File | Ticker | Description | Start Date |
|------|--------|-------------|------------|
| XLC_Communication_Services.csv | XLC | Communication Services | 2018-06-19 |
| XLY_Consumer_Discretionary.csv | XLY | Consumer Discretionary | 1998-12-22 |
| XLP_Consumer_Staples.csv | XLP | Consumer Staples | 1998-12-22 |
| XLE_Energy.csv | XLE | Energy | 1998-12-22 |
| XLF_Financials.csv | XLF | Financials | 1998-12-22 |
| XLV_Health_Care.csv | XLV | Health Care | 1998-12-22 |
| XLI_Industrials.csv | XLI | Industrials | 1998-12-22 |
| XLRE_Real_Estate.csv | XLRE | Real Estate | 2015-10-08 |
| XLB_Materials.csv | XLB | Materials | 1998-12-22 |
| XLK_Technology.csv | XLK | Technology | 1998-12-22 |
| XLU_Utilities.csv | XLU | Utilities | 1998-12-22 |

### bonds/
| File | Ticker | Description | Start Date |
|------|--------|-------------|------------|
| AGG_US_Aggregate_Bonds.csv | AGG | iShares Core U.S. Aggregate Bond ETF | 2003-09-29 |
| TIP_TIPS.csv | TIP | iShares TIPS Bond ETF | 2003-12-05 |

### commodities/
| File | Ticker | Description | Start Date |
|------|--------|-------------|------------|
| DBC_Commodities_Broad.csv | DBC | Invesco DB Commodity Index Tracking Fund | 2006-02-06 |
| GLD_Gold.csv | GLD | SPDR Gold Shares | 2004-11-18 |

### rates/
| File | Ticker | Description | Start Date |
|------|--------|-------------|------------|
| BIL_Risk_Free_Rate_1_3M_TBill.csv | BIL | SPDR Bloomberg 1-3 Month T-Bill ETF | 2007-05-30 |
| SHV_Risk_Free_Rate_Short_Term.csv | SHV | iShares Short Treasury Bond ETF | 2007-01-11 |

### volatility/
| File | Ticker | Description | Start Date |
|------|--------|-------------|------------|
| VIX_VIX_Index.csv | ^VIX | CBOE Volatility Index (spot) | 1990-01-02 |
| VIXY_Equity_Volatility_VIX_Futures.csv | VIXY | ProShares VIX Short-Term Futures ETF | 2011-01-04 |

### macro/
| File | Source | Description | Frequency | Start Date |
|------|--------|-------------|-----------|------------|
| CPI_Monthly_CPIAUCSL.csv | FRED | Consumer Price Index for All Urban Consumers | Monthly | 1970-01-01 |

## Coverage
- **Start date:** Earliest available (1970-01-01 requested; ETFs start from their inception date)
- **End date:** Latest available
- **Frequency:** Daily (except CPI which is monthly)
