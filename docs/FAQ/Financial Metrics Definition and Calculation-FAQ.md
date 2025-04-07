source link - [Financial Metrics Definition and Calculation.md](https://pingcap.feishu.cn/docx/M2eddodkGojkfKxkGaRcGkNqnxh)

Below is the complete FAQ in markdown format that reorganizes the original document’s content into clear, stand‐alone question–answer pairs. Each section covers a key concept from the policy, and a glossary at the end defines important terms.

---

# Frequently Asked Questions (FAQ)  
## Financial Metrics Definition/Calculation Policy

This FAQ explains the key concepts, definitions, and processes from the Financial Metrics Definition/Calculation policy. It is intended for all employees in PingCAP and provides guidance on how various financial metrics are defined and calculated.

---

## 1. Policy Overview and Basic Information

### Q1: What is the name and type of this policy?
A1: The policy is named “Financial Metrics Definition/Calculation” and is classified as a Policy document.

### Q2: Who is the applicable audience for this policy?
A2: This policy applies to all employees in PingCAP.

### Q3: When does the policy take effect and how often is it reviewed?
A3:  
• Effective Date: January 1, 2025  
• Review Cycle: Every 1 year  
• Next Review Time: January 1, 2026

---

## 2. Annual Contract Value (ACV)

### Q4: What is ACV and what does it represent?
A4: ACV stands for Annual Contract Value. It represents the average value of a contract over one year. The ACV remains constant each year throughout the contract’s duration and is recognized using the contract date (not the service start date).

### Q5: How is ACV treated with regard to taxes and service start dates?
A5: The ACV listed in the policy is based on the after-tax amount (for China, with tax included), and its recognition is based solely on the contract signature date rather than when the service actually starts.

### Q6: How is ACV calculated for different types of contracts?
A6:  
• For License contracts:      ACV = Total Contract Value (TCV).  
• For Subscription, Professional Service, and Managed Agreements (MA):  
  – ACV = TCV divided by the number of years in the contract (with a minimum duration of 1 year).  
  – For contracts shorter than 1 year, ACV = TCV.  
• For Pay-as-you-go contracts:   ACV equals the actual revenue.  
• For contracts with a free service period:  
  – The ACV is recognized over both the paid and free service periods.  
  – Example: For a contract running from September 5, 2021, to September 4, 2022, with an additional free service period from September 5, 2022, to December 4, 2022, and a TCV of 900k, the ACV is calculated as 900k divided by (12+3) months, multiplied by 12, resulting in an ACV of 720k.

### Q7: How are backdated contracts handled in terms of ACV recognition?
A7: For backdated contracts, both TCV and ACV are recognized in the period when the contract is signed. ACV is only recorded at the contract signature date, meaning no ACV will be allocated to periods (fiscal year or quarter) that precede the signing date.

---

## 3. Annual Recurring Revenue (ARR)

### Q8: What is ARR and why is it important?
A8: ARR stands for Annual Recurring Revenue. It is a key metric used by subscription-based or recurring revenue businesses to measure predictable and recurring revenue earned over a 12‑month period.

### Q9: Which product families are included in the ARR calculation?
A9: The ARR calculation applies to the following product families:  
• Subscription products  
• TiDB Cloud  
• Managed Agreements (MA) for Perpetual Licenses (applicable for China only)

### Q10: How is ARR calculated for subscription and MA contracts under the Unit Discount Model or Average Pricing Model?
A10: For these contracts, ARR is calculated as:  
  ARR = (Subscription/MA Amount) divided by the term length in months, then multiplied by 12 (to annualize the revenue).  
If a quote contains multiple line items with different start and end dates, you must calculate the ARR for each line item separately considering its specific term, then aggregate the amounts to obtain the total ARR.

### Q11: What is the ARR calculation method for consumption-based subscription models and TiDB Cloud?
A11: For both the Subscription (Consumption Model, which is least recommended) and TiDB Cloud:  
  ARR = (Average revenue over 3 months) multiplied by 12, which annualizes the revenue.

### Q12: When is ARR recognized in a contract?
A12: ARR is typically recognized starting from the first month of revenue recognition, which usually coincides with the subscription’s or contract’s start date. Specific scenarios include:  
• Backdated Contracts: ARR begins from the first revenue recognition month and continues until the service end month.  
• Future Start Contracts: No ARR is recorded until revenue recognition begins.  
• Early Termination Contracts: ARR recognition stops if the contract is terminated before the service end date.

### Q13: Can you provide an example of ARR recognition for a backdated contract?
A13: Yes. For example, consider a backdated contract with a subscription amount of $2,400 per year, a term of 12 months, a service start date of April 1, and a contract signed on June 30. In this scenario, even though revenue might be recognized in different amounts month-to-month starting the service date, the ARR is recorded as $2,400 for each month from the point of revenue recognition (in this example, from June onward) for the duration of the contract.

---

## 4. Revenue Recognition

### Q14: How is revenue defined and calculated under this policy?
A14: Revenue under this policy is calculated as follows:  
• The amount is determined after taxes have been applied.  
• Revenue is prorated based on the number of days in the contract period, starting from the service start date.  
• For backdated contracts, any revenue catchup for prior periods is calculated at the contract signature date.  
• The revenue proration applies to both paid service periods and any free service periods.

---

## 5. Remaining Performance Obligation (RPO)

### Q15: What does RPO stand for, and how is it calculated?
A15: RPO stands for Remaining Performance Obligation. It represents the total future performance obligations that arise from existing contractual relationships. The calculation is:  
  RPO = Total Contract Value (TCV) minus the revenue recognized to date.

---

## 6. Net Revenue Retention (NRR)

### Q16: What is NRR and what does it measure?
A16: NRR, or Net Revenue Retention (also known as net dollar retention), measures how successfully a company renews or sustains customer contracts while generating additional revenue from its existing customer base. It reflects the overall health and growth potential of recurring revenue.

### Q17: Which types of contracts are considered when calculating NRR?
A17: NRR applies to Subscription contracts, Pay-as-you-go contracts, and Managed Agreements (MA).

### Q18: How is NRR calculated?
A18: NRR is calculated by comparing the monthly recurring revenue (MRR) of a set of customers between two periods. For example, to calculate NRR for July 2021 for customers who had non-zero MRR in July 2020:  
  NRR = (Sum of MRR in July 2021 for these customers) ÷ (Sum of MRR in July 2020 for these customers).

### Q19: What is the industry benchmark for NRR?
A19: The industry benchmark for NRR is generally 100% or higher, with a preferable target above 120%.

---

## 7. Glossary of Key Terms

• ACV (Annual Contract Value): The average value of a contract per year; calculated as noted by contract type and recognized at the signature date.  
• TCV (Total Contract Value): The total value of a contract over its entire duration.  
• ARR (Annual Recurring Revenue): The recurring revenue generated over a 12‑month period from subscription or similar revenue models.  
• RPO (Remaining Performance Obligation): The total future revenue potential remaining in contractual obligations (TCV minus recognized revenue).  
• NRR (Net Revenue Retention): A measure of revenue growth from existing customers, reflecting customer renewals and upsells.  
• MA: Managed Agreements (as referenced in the context of subscriptions or service contracts).  
• TiDB Cloud: A product family included in ARR calculations (specific to the company’s offerings).  
• MRR (Monthly Recurring Revenue): The recurring revenue measured on a monthly basis used often in calculating NRR.

---

This FAQ provides a comprehensive, user-friendly overview of the Financial Metrics Definition/Calculation policy, ensuring that anyone—even without prior familiarity with the original document—can understand the key financial metrics, their calculation methods, and their relevance to contractual obligations and revenue recognition.