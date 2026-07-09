# QWIM Team 5 — Cleaned Data

This folder contains cleaned versions of all raw data in `../data/`. The folder
structure mirrors the raw data exactly. Each file retains its original OHLCV
columns and has additional derived columns appended (e.g. `Log_Return`,
`Log_VIX`, `YoY_Inflation`).

---

## Folder Structure

```
cleaned_data/
├── sectors/        11 S&P 500 sector ETFs — Group 1 cleaning
├── bonds/          AGG, TIP — Group 1 cleaning
├── commodities/    DBC, GLD — Group 1 cleaning + commodity note
├── rates/          BIL, SHV — Group 1 cleaning
├── volatility/     VIXY (Group 1), VIX index (Group 2)
└── macro/          CPI — Group 3 cleaning
```

---

## Cleaning Methods by Group

---

### Group 1 — All ETFs
**Files:** all 11 sector ETFs · AGG · TIP · DBC · GLD · BIL · SHV · VIXY

These 18 files share the same 4-step pipeline applied in order.

#### Step 1 — Dividend & Split Adjustment *(pre-applied)*
Prices were downloaded with `auto_adjust=True` via yfinance, which corrects
for stock splits and dividend distributions using CRSP-style total return
methodology. No further adjustment is needed.

> Campbell, J. Y., Lo, A. W., & MacKinlay, A. C. (1997).
> *The Econometrics of Financial Markets*. Princeton University Press.

---

#### Step 2 — Stale Price / Zero-Volume Filter
Days where the closing price is identical to the prior day **and** trading
volume is zero are flagged as non-trading observations (data artefacts, not
genuine price stasis). These observations are set to `NaN` and then
forward-filled (see Step 4).

> Karolyi, G. A., Lee, K. H., & Van Dijk, M. A. (2012).
> "Understanding commonality in liquidity around the world."
> *Journal of Financial Economics*, 105(1), 82–112.

---

#### Step 3 — Extreme Return Filter (Ince & Porter)
Daily log returns are computed as `r_t = ln(Close_t / Close_{t-1})`.
Two filters are applied:

- **Reversal filter:** if `r_t > 300%` and `r_{t+1} < −50%`, the observation
  is treated as a data entry error and removed.
- **Rolling outlier filter:** returns more than ±5 rolling standard deviations
  from the 252-day rolling mean are set to `NaN`. A minimum of 60 observations
  is required before the rolling window activates.

Cleaned log returns are stored in the added column **`Log_Return`**.

> Ince, O. S., & Porter, R. B. (2006).
> "Individual Equity Return Data from Thomson Datastream: Handle with Care!"
> *Journal of Financial Research*, 29(4), 463–479.

---

#### Step 4 — Missing Value Handling
After steps 2–3, isolated `NaN` values are forward-filled (`ffill`) with a
maximum gap of **5 consecutive days**. Gaps longer than 5 days are left as
`NaN` and should be investigated before use in modelling.

> Stambaugh, R. F. (1999).
> "Predictive regressions."
> *Journal of Financial Economics*, 54(3), 375–421.

---

#### Additional Note — DBC (Commodity ETF, futures-based)
DBC holds commodity futures contracts, not physical commodities. When futures
contracts near expiration, DBC rolls into the next contract. In contango
markets this creates a **roll cost** embedded in the ETF price; in
backwardation markets it creates a **roll yield**. These effects are already
reflected in the adjusted price and require no additional cleaning step, but
should be acknowledged when interpreting returns.

> Gorton, G., & Rouwenhorst, K. G. (2006).
> "Facts and Fantasies about Commodity Futures."
> *Financial Analysts Journal*, 62(2), 47–68.

---

### Group 2 — ^VIX (CBOE Volatility Index)
**File:** `volatility/VIX_VIX_Index.csv`

The VIX is a model-free implied volatility index computed from S&P 500 option
prices. It is **not** a traded price series and requires different treatment
from ETF data.

| Rule | Reason |
|------|--------|
| **No outlier filter applied** | Spikes (e.g. 2008 GFC, March 2020) are genuine volatility events, not data errors |
| **No volume/stale-price filter** | VIX is a computed index with no trading volume |
| **Log transform applied** | Raw VIX is right-skewed; `log(VIX)` is closer to normally distributed |
| **First difference added** | `Δlog(VIX)` captures volatility shocks and is more suitable for regression inputs |

**Added columns:**
- `Log_VIX` = `ln(Close)`
- `Delta_Log_VIX` = `Log_VIX_t − Log_VIX_{t−1}`

> Whaley, R. E. (2000).
> "The investor fear gauge."
> *Journal of Portfolio Management*, 26(3), 12–17.

> Carr, P., & Wu, L. (2006).
> "A tale of two indices."
> *Journal of Derivatives*, 13(3), 13–29.

---

### Group 3 — CPI (Monthly, FRED)
**File:** `macro/CPI_Monthly_CPIAUCSL.csv`  
**Source:** FRED series `CPIAUCSL` (seasonally adjusted, all urban consumers)

CPI is a macroeconomic level variable, not a price return series. It is
non-stationary (I(1)) and must be transformed before use in modelling.

| Rule | Reason |
|------|--------|
| **No outlier filter** | FRED data is already quality-controlled |
| **No stale-price filter** | CPI is reported monthly; unchanged values are valid |
| **YoY inflation rate computed** | Removes non-stationarity; standard in macro literature |
| **MoM inflation rate computed** | Higher-frequency signal; useful for shorter-horizon models |
| **Data revision caveat** | FRED shows the *latest revised* figure. For a realistic backtest with no look-ahead bias, use the ALFRED real-time vintage dataset instead |

**Added columns:**
- `YoY_Inflation` = `ln(CPI_t / CPI_{t−12})`
- `MoM_Inflation` = `ln(CPI_t / CPI_{t−1})`

> Croushore, D., & Stark, T. (2001).
> "A real-time data set for macroeconomists."
> *Journal of Econometrics*, 105(1), 111–130.

> Stock, J. H., & Watson, M. W. (2002).
> "Macroeconomic forecasting using diffusion indexes."
> *Journal of Business & Economic Statistics*, 20(2), 147–162.

---

## Summary Table

| File(s) | Group | Steps applied | Key reference |
|---------|-------|---------------|---------------|
| All 11 sector ETFs | 1 | Adj. ✓ · Stale filter · Ince & Porter · ffill | Ince & Porter (2006) |
| AGG, TIP | 1 | same as above | Ince & Porter (2006) |
| GLD | 1 | same as above | Ince & Porter (2006) |
| DBC | 1 + note | same + roll yield note | Gorton & Rouwenhorst (2006) |
| BIL, SHV | 1 | same as above | Ince & Porter (2006) |
| VIXY | 1 | same as above | Ince & Porter (2006) |
| VIX_VIX_Index.csv | 2 | log(VIX), Δlog(VIX), no outlier filter | Whaley (2000) |
| CPI_Monthly_CPIAUCSL.csv | 3 | YoY & MoM inflation rates | Croushore & Stark (2001) |

---

## Full Reference List

1. Campbell, J. Y., Lo, A. W., & MacKinlay, A. C. (1997). *The Econometrics of Financial Markets*. Princeton University Press.
2. Carr, P., & Wu, L. (2006). "A tale of two indices." *Journal of Derivatives*, 13(3), 13–29.
3. Croushore, D., & Stark, T. (2001). "A real-time data set for macroeconomists." *Journal of Econometrics*, 105(1), 111–130.
4. Gorton, G., & Rouwenhorst, K. G. (2006). "Facts and Fantasies about Commodity Futures." *Financial Analysts Journal*, 62(2), 47–68.
5. Ince, O. S., & Porter, R. B. (2006). "Individual Equity Return Data from Thomson Datastream: Handle with Care!" *Journal of Financial Research*, 29(4), 463–479.
6. Karolyi, G. A., Lee, K. H., & Van Dijk, M. A. (2012). "Understanding commonality in liquidity around the world." *Journal of Financial Economics*, 105(1), 82–112.
7. Stambaugh, R. F. (1999). "Predictive regressions." *Journal of Financial Economics*, 54(3), 375–421.
8. Stock, J. H., & Watson, M. W. (2002). "Macroeconomic forecasting using diffusion indexes." *Journal of Business & Economic Statistics*, 20(2), 147–162.
9. Whaley, R. E. (2000). "The investor fear gauge." *Journal of Portfolio Management*, 26(3), 12–17.
