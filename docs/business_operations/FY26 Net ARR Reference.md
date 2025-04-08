# FY26 Net ARR Reference

This article focuses on FY26 Net ARR reference for business enabling and operation, including the definition, formula, calculation scenarios of Net ARR for different customer cases in TiDB Cloud, TiDB Self Host (Consumption Base) and TiDB Self Host (Subscription Base), along with a special case. Key points include: ​

1. Net ARR definition ：Net ARR (Net Annual Recurring Revenue) is a key metric for SaaS companies, reflecting annual recurring revenue after considering customer churn, expansions, etc., showing the health of recurring revenue.​
2. Net ARR formula ：Net ARR = Ending ARR - Baseline ARR (Standard Calculation). The baseline for customers is set in different ways based on prior quarter ending ARR, commitment amounts, etc.​
3. Net ARR scenarios for different customer cases ：For customers with new commitment plans in FY26 with or without prior quarter Ending ARR, and those with different relationships between FY25 commitment and FY25 Ending ARR, Net ARR is calculated according to the standard formula with specific baselines.​
4. Net ARR for TiDB Self Host (Subscription Base) ：Baseline = Prior Quarter Ending ARR, Net ARR = Ending ARR - Baseline ARR. Also, ARR = MRR * 12, MRR = Total Contract Value (from recurring revenue)/Total Contract Months.​
5. Special case ：Cloud CP shortfall true-up revenue is not counted in ARR. For example, if the commitment plan is 100K but only 90K is spent, the 10K is not included in ARR. 

## Net ARR Definition

### Explain on Net ARR

Net ARR (Net Annual Recurring Revenue) is a key metric for SaaS companies, reflecting the total recurring revenue generated on an annual basis, after accounting for factors such as customer churn, expansions, downgrades, and renewals. It provides a comprehensive view of the recurring revenue health of a SaaS business, considering both losses and gains in the customer base.

### Net ARR Formula and Calculation

Net ARR = Ending ARR - Baseline ARR (Standard Calculation)

The baseline for the customer will be set as:

- Prior Quarter Ending ARR
- FY25 Commitment, if it is greater than the FY25 Ending ARR entering FY26. FY25 Commitment will be the baseline until the Ending ARR exceeds the Commitment or the opportunity is renewed.

For multiple year commitment contracts, baseline equals current year/half year(x2) commitment value.

### Net ARR Scenarios

#### Apply to TiDB Cloud and TiDB Self Host (Consumption Base), examples with values of K$USD

##### Case 1: Customers with new commitment plan in FY26 without Ending ARR from prior quarter

|                      | FY25Q4 | FY26Q1 | FY26Q2 | FY26Q3 | FY26Q4 |
|----------------------|--------|--------|--------|--------|--------|
| **Baseline - greater of ending ARR or commitment amount** | 0      | 0      | 150    | 250    | 200    |
| **Ending ARR**       | 0      | 150    | 250    | 200    | 250    |
| **Commit**           |        |        |        | 250    |        |
| **Net ARR (for quota credit and commissions)** |        | **150** | 100    | -50    | 50     |

**Explain** : Customers with new commitment plan in FY26 Net ARR follows standard calculation **Ending ARR - Baseline ARR**

##### Case 2: Customers with new commitment plan in FY26 with Ending ARR from prior quarter

|                                      | FY25Q4 | FY26Q1 | FY26Q2 | FY26Q3 | FY26Q4 |
|--------------------------------------|--------|--------|--------|--------|--------|
| **Baseline - greater of ending ARR or commitment amount** | 0      | 50     | 150    | 250    | 200    |
| **Ending ARR**                       | 50     | 150    | 250    | 200    | 250    |
| **Commit**                           |        | 200    |        |        |        |
| **Net ARR (for quota credit and commissions)** |        | 100    | 100    | -50    | 50     |


**Explain** : Customers with new commitment plan in FY26 Net ARR follows standard calculation **Ending ARR - Baseline ARR**

##### Case 3: Customers with FY25 commitment higher than FY25 Ending ARR

- 📅 FY25Q4
    - **Ending ARR**: 120
    - **Commitment**: 200
    - **Net ARR**: N/A
    - **Baseline for FY26Q1**: 200 (because commitment > ending ARR)
    - **Explanation**:  The customer had a FY25 commitment higher than the FY25 ending ARR. 👉 Therefore, the **prior commitment amount (200)** will serve as the **baseline for FY26Q1**.

- 📅 FY26Q1
    - **Baseline**: 200  
    - **Ending ARR**: 180  
    - **Commitment**: N/A  
    - **Net ARR**: **0**  
    - **Explanation**: Since the ending ARR (180) is **lower than the baseline (200)** and the customer did **not renew**, 👉 In this case, **Net ARR = 0** on all non-renewing quarters

- 📅 FY26Q2
    - **Baseline**: 200  
    - **Ending ARR**: 220  
    - **Commitment**: N/A  
    - **Net ARR**: **20**  
    - **Explanation**:  The ending ARR (220) **exceeds the baseline (200)**.  👉 **Net ARR = Ending ARR - Baseline = 220 - 200 = 20**

- 📅 FY26Q3
    - **Baseline**: 220  
    - **Ending ARR**: 250  
    - **Commitment**: N/A  
    - **Net ARR**: **30**  
    - **Explanation**:  
    The ending ARR (250) **exceeds the baseline (220)**.  👉 **Net ARR = 250 - 220 = 30**

- 📅 FY26Q4
    - **Baseline**: 250
    - **Ending ARR**: 270
    - **Commitment**: 300 (renewal)  
    - **Net ARR**: **20**  
    - **Explanation**:  The opportunity is **renewed** in this quarter.  👉 In renewal quarters, Net ARR follows the **standard calculation**:  **Net ARR = Ending ARR - Starting ARR = 270 - 250 = 20**

##### Case 4: Customers with FY25 commitment higher than FY25 Ending ARR, Churn is applied in the renewing quarter.

- 📅 FY25Q4
    - **Ending ARR**: 120  
    - **Commitment**: 200  
    - **Net ARR**: N/A  
    - **Baseline for FY26Q1**: 200 (greater of ending ARR or commitment)  
    - **Explanation**:  The customer had a FY25 commitment (200) higher than the FY25 ending ARR (120).  👉 Therefore, the **baseline for FY26Q1 is set to 200**.

- 📅 FY26Q1
    - **Baseline**: 200  
    - **Ending ARR**: 180  
    - **Commitment**: N/A  
    - **Net ARR**: **0**  
    - **Explanation**:   Since the ending ARR (180) is **lower than the baseline (200)** and the customer did **not renew**,  👉 **Net ARR = 0**

- ...

- 📅 FY26Q4
    - **Baseline**: 200  
    - **Ending ARR**: 190  
    - **Commitment**: 150 (renewal)  
    - **Net ARR**: **-10**  
    - **Explanation**: This is a **renewal quarter**, and churn is applied.  👉 **Net ARR = Ending ARR - Starting ARR = 190 - 200 = -10**

##### Case 5. Customers with FY25 commitment smaller than FY25 Ending ARR, and with a Q1 Ending ARR decline compared to FY25 Commitment, churn is applied. （Standard Calculation）

- 📅 FY25Q4
    - **Ending ARR**: 280  
    - **Commitment**: 200  
    - **Net ARR**: N/A  
    - **Baseline for FY26Q1**: 280 (greater of ending ARR or commitment)  
    - **Explanation**: The customer had a FY25 commitment (200) smaller than the FY25 ending ARR (280).  👉 Therefore, the **baseline for FY26Q1 is set to 280**.

- 📅 FY26Q1
    - **Baseline**: 280  
    - **Ending ARR**: 180  
    - **Commitment**: N/A  
    - **Net ARR**: **-100**  
    - **Explanation**: The ending ARR (180) is **lower than the baseline (280)**.  👉 **Net ARR = 180 - 280 = -100**

- 📅 FY26Q2
    - **Baseline**: 180  
    - **Ending ARR**: 200  
    - **Commitment**: N/A  
    - **Net ARR**: **20**  
    - **Explanation**:  Net ARR follows standard calculation.  👉 **Net ARR = 200 - 180 = 20**

- 📅 FY26Q3
    - **Baseline**: 200  
    - **Ending ARR**: 200  
    - **Commitment**: 250 (early renew)  
    - **Net ARR**: **0**  
    - **Explanation**:  Regardless of the renewal, Net ARR follows standard calculation.  👉 **Net ARR = 200 - 200 = 0**

- 📅 FY26Q4
    - **Baseline**: 200  
    - **Ending ARR**: 300  
    - **Commitment**: N/A  
    - **Net ARR**: **100**  
    - **Explanation**:  Net ARR follows standard calculation.  👉 **Net ARR = 300 - 200 = 100**

#### Apply to TiDB Self Host (Subscription Base)

- Baseline = Prior Quarter Ending ARR
- Net ARR = Ending ARR - Baseline ARR
- ARR = MRR * 12
- MRR = Total Contract Value(from recurring revenue)/Total Contract Months
- MRR recognized month equals order 1st revenue booked month. MRR Ending Month = Service Ending Month

##### Case 1: Ending ARR equals Booking ACV

- 📅 FY25Q4
    - **Baseline**: 0 
    - **Ending ARR**: 135  
    - **Booking ACV**: 135  
    - **Baseline for FY26Q1**: 135 (greater of Ending ARR or Booking ACV)  
    - **Net ARR**: N/A  
    - **Explanation**: Initial quarter, no Net ARR calculated.

- 📅 FY26Q1
    - **Baseline**: 135  
    - **Ending ARR**: 135  
    - **Booking ACV**: 135  
    - **Net ARR**: **0**  
    - **Explanation**: Ending ARR remains constant.  👉 **Net ARR = 135 - 135 = 0**

- 📅 ...

- 📅 FY26Q4
    - **Baseline**: 135  
    - **Ending ARR**: 135  
    - **Booking ACV**: 135  
    - **Net ARR**: **0**  
    - **Explanation**: Ending ARR remains constant.  👉 **Net ARR = 135 - 135 = 0**


**Explain**: Ending ARR remains constant throughout the quarter: **Net ARR = Ending ARR - Baseline ARR** 

##### Case 2: Booking ACV is greater than Ending ARR

For Booking ACV larger than Ending ARR, we use the Booking ACV as the baseline.

- 📅 FY25Q4
    - **Baseline**: 0 
    - **Ending ARR**: 135  
    - **Booking ACV**: 400  
    - **Baseline for FY26Q1**: 400 (greater of Ending ARR or Booking ACV)  
    - **Net ARR**: N/A  
    - **Explanation**: Booking ACV is higher than Ending ARR, so baseline is set to 400.

- 📅 FY26Q1
    - **Baseline**: 400  
    - **Ending ARR**: 400  
    - **Booking ACV**: 400  
    - **Net ARR**: **0**  
    - **Explanation**: Ending ARR equals baseline.  
      👉 **Net ARR = 400 - 400 = 0**

- 📅 ...

- 📅 FY26Q4
    - **Baseline**: 400  
    - **Ending ARR**: 400  
    - **Booking ACV**: 400  
    - **Net ARR**: **0**  
    - **Explanation**: Ending ARR remains constant.  
      👉 **Net ARR = 400 - 400 = 0**

**Explain**: Ending ARR remains constant throughout the quarter: **Net ARR = Ending ARR - Baseline ARR**

### Special Case

- For Cloud CP shortfall true-up revenue, it will not be counted in ARR. i.e. Commitment Plan 100K, but only with 90K spending, the 10K will not be counted in ARR.

## Reference

ARR Definition: [Financial Metrics Definition/Calculation](https://pingcap.feishu.cn/docx/M2eddodkGojkfKxkGaRcGkNqnxh) (Check metrics like ACV, ARR, Revenue and their calculation)