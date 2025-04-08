# Financial Metrics Definition/Calculation 

## Basic Information 基本信息

- Type｜ Policy
- Policy Name｜ Financial Metrics Definition/Calculation
- Applicable Scope｜All Employees in PingCAP
- Effective Date （YYYY/MM/DD）| 2025/1/1
- Review Cycle｜1 Year
- Next Review Time｜2026/1/1

## Metrics Definition

### ACV 
- ACV is the average value of a contract across 1 year. Therefore ACV remains the same each year throughout contract duration.
    - ACV is recognized based on contract date, not service start date
    - ACV is after tax amount （China with tax)
- Calculation - 
    - License： ACV = TCV
    - Subscription，Professional Servce，MA：ACV = TCV / # of years in contract (minimum 1 year)
        - For contracts with less than 1 year duration：ACV = TCV
    - Pay-as-you-go contracts: 
        - ACV = actual revenue
    - Contracts with free service period: 
        - ACV is to be recognized over both paid and free service periods
        - e.g. Contract Term: 2021.9.5-2022.9.4，Free service period: 2022.9.5-2022.12.4，TCV 900k ---> ACV = 900k / (12+3)*12 = 720k
- Back Dated contracts：
    - Recognize TCV & ACV in the same period of contract signature date (not when service started)
    - ACV is only recognized at the contract signature date (i.e. No ACV will be recorded for prior fiscal year or quarter)

### ARR

ARR stands for Annual Recurring Revenue. It is a key metric often used by subscription-based businesses or companies with recurring revenue models to measure the predictable and recurring revenue generated over a 12-month period.

Types of Product Family Included: Subscription, TiDB Cloud, MA of Perpetual License (China Only)

#### How to Calculate ARR:

- Subscription and MA (Unit Discount Model and Average Pricing Model)
    - ARR = (Subscription/MA Amount ) / (Term Length in Months) × 12 (to annualize)
    - When a quote contains multiple line items with different start and end dates, the Annual Recurring Revenue (ARR) should be calculated separately for each line item, taking into account the specific term length and the respective value for each item. The individual ARR values for all line items are then aggregated to determine the total order ARR."
- Subscription  (Consumption Model - least recommended)
    - ARR = Average 3 months' revenue x 12 (to annualize)
- TiDB Cloud
    - ARR = Average 3 months' revenue x 12 (to annualize)

#### ARR Recognition Time: 
- It usually begins to be recognized starting from the first revenue recognition month—which is generally aligned with the start date of the subscription or contract.
- Backdated contract: ARR begins to be recognized from first revenue recognition month and ends with service end month;
- Future start contract: No ARR until revenue starts;
- Early termination contract: ARR ends if contract terminated earlier than service end date;

Example for recognition:
1. Backdated Contract: Subscription Amount: $2400/Year, Term: 12 months, Service Start Date: April 1 (Contract signed on June 30)

|       | Apr-24 | May-24 | Jun-24 | Jul-24 | Aug-24 | Sep-24 | Oct-24 | Nov-24 | Dec-24 | Jan-25 | Feb-25 | Mar-25 | Total  |
|---------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| Revenue |        |        |  $598  | $204   | $204   | $197   | $204   | $197   | $204   | $204   | $184   | $204   | $2,400 |
| ARR     |        |        | $2,400 | $2,400 | $2,400 | $2,400 | $2,400 | $2,400 | $2,400 | $2,400 | $2,400 | $2,400 | $2,400 |

#### Revenue

1. Revenue is calculated after taxes. It's prorated by # of days in the contract starting with service start date.
2. For backdated contracts, revenue catchup for prior periods will be calculated at contract signature date.
3. Revenue should be prorated across both paid and free service periods.

#### RPO/Backlog

1. Remaining Performance Obligation (RPO) represents the total future performance obligations arising from contractual relationships 
2. RPO = TCV minus revenue recognition to-date

#### NRR 

1. Net Revenue Retention (NRR), aka net dollar retention, meansures how successful a company is at renewing or sustaining customer contracts and how well it is doing at generating additional revenue from this existing customer base.
2. Applicable contracts: Subscription, pay-as-you-go and MA
3. Calculation -  For example, in order to calculate NRR @ Jul 2021：For any customers that had non-zero MRR in Jul 2020 , NRR = sum of their MRR in Jul 2021 / sum of their MRR in Jul 2020
4. Industry benchmark: 100%+; Preferably above 120%
