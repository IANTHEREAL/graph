# PoC Application Process (for Global Business)​

Draft by: Business Enabling & Operation

Last Update: 24/7/2024


## Background​
In order to record PoC application and track PoC status, we optimize PoC application function in Salesforce and Lark/Feishu. Now all PoC requests shall go through Salesforce and be approved as below instructions. PoC status shall be updated by the PoC owner (Sales/Presales) in a timely manner. ​


## TiDBCloud PoC​

There are 2 ways to request TiDB Cloud PoC: requested directly by the Cloud User in the TiDB Cloud UI by clicking "Apply for a PoC Trial"; OR requested by Sales in Salesforce. The approvals flow as below:​

### 1. Requested byUser in TiDBCloud UI​

Non Presales Auto-approval will go to GPE (SLA = 24 hours);​ Otherwise, the approval process is within regional teams and final approval by regional GM.​

### 2. Requested by Sales in Salesforce​

Non Presales Auto-approval will go to GPE (SLA = 24 hours);​ Otherwise, the approval process is within regional teams and final approval by regional GM.​

### 3. Credits adding during PoC​

If the credits have been used up but PoC is still ongoing, pls request more credits in Salesforce "Cloud User Request" object, create one "Adding Credits Request" and submit for approval.​

Credits adding approval process is: ​
- If Credits Needed <=3,000 AND Accumulated Credits <=10,000, Sales Trigger > Sales Manager (for APAC) > Regional Leader > RDG Product Readiness > Finance > End
- If Credits Needed >3,000OR Accumulated Credits >10,000, Sales Trigger > Sales Manager (for APAC) > Regional Leader > RDG Product Readiness > Finance > End


## Role, Responsibility and SLA (1st Response) for Each Approval Steps​

| No. | Role                                                                 | Responsibility                                              | SLA (Cloud PoC Requested by User) | SLA (Cloud PoC Requested by Sales) | SLA for Enterprise PoC     |
|-----|----------------------------------------------------------------------|-------------------------------------------------------------|-----------------------------------|------------------------------------|-----------------------------|
| 1   | SDR                                                                  | Lead Qualification (SQL Criteria)                          | Per Regional Arrangement          | N/A                                | N/A                         |
| 2   | Sales                                                                | Customer Validation (Sales Stage "Qualification" criteria) | Per Regional Arrangement          | N/A                                | N/A                         |
| 3   | Presales                                                             | Technical Evaluation (Region level)                        | Per Regional Arrangement          | Per Regional Arrangement           | Per Regional Arrangement    |
| 4   | GPE (@Xiaole Fang for APAC; @Sidney Chen for NA/EMEA/JP)            | Technical Evaluation (HQ level)                            | 24 Hours                          | 24 Hours                           | 72 Hours                    |
| 5   | Regional Leader                                                      | Regional Approval on:<br>1. PoC Customer Validation;<br>2. PoC Budget | Per Regional Arrangement          | Per Regional Arrangement           | Per Regional Arrangement    |
| 6   | RDG - Product Readiness (@Nicole Sun)                                | Review adding credit necessity                             | 4 Hours                           | 4 Hours                            | N/A                         |
| 7   | Finance - FP&A (@Yanice Zhang for APAC/JP; @Ellen Wang for NA/EMEA) | PoC Budget                                                  | 8 Hours                           | 8 Hours                            | N/A                         |
| 8   | CEG - BE&O (@Vince Yao for APAC; @Kevin Lu for NA/EMEA; @Dexter Deng for JP) | Add Credits into the Tenant                                | 4 Hours                           | 4 Hours                            | N/A                         |


## Salesforce​

1. If the PoC request was submitted by the Cloud User in TiDB Cloud UI, pls go to step 3. If you want to create a PoC application in Salesforce for this customer, pls go to PoC tab to create a new one, or go to your Opprotunity to create a new PoC.​

2. After the PoC is created, pls fill in the required information as mentioned in below steps and click "Submit for Approval".​

3. The Salesforce PoC page layout is as below:

    - Account: to be linked to the Account after SQL conversion by Sales/SDR.
    - Contact: to be linked to the Contact after SQL conversion by Sales/SDR.
    - Lead: It's linked to the Cloud User Lead who requested this PoC.
    - Opportunity: to be linked to the Opportunity after SQL conversion by Sales/SDR.
    - Application Link: a link to the application form submitted in Cloud UI if this request is submitted by Cloud User in TiDB Cloud UI.
    - Credits Needed: to be updated by Sales.
    - Credits Expiry Date: to be updated by Sales.
    - PoC Customer Payment: No Payment or Partial Payment. To be updated by Sales.
    - Justification to Credits Needed: to be updated by Sales. Pls include the details of Presales Auto approved metrics in your justification.
    - Approval Status: it'll show the status of this PoC approval (In Progress OR Approved).
    - Region Leader: updated automatically; pls double check.
    - Regional GPE: updated automatically; pls double check.
    - Regional SDR: updated automatically; pls double check.
    - Presales: to be updated by Sales before Sales approval.
    - PoC Status: to be updated by Sales/Presales after the PoC is approved.
    - TiDB Cloud Account ID to run this PoC: updated automatically; pls double check.
    - Presales Auto-approve: to be updated by Presales before Presales approval.
    - Internal User: updated automatically; pls ignore.
    - Approve or Reject: pls click here when it's pending for your approval.


## TiDB Cloud OPS Portal​

If you want to check the status, remaining credits or bills of any TiDB Cloud User, pls log into ht tps://ops.tidbcloud.com/orgs to check. 


Any questions pls contact ​ ​. Thanks!​ @Vince Yao


## Reference​
​[PoC Auto Approved metric](https://pingcap.feishu.cn/wiki/wikcnGSMrbxpSh0E7oqYFRngOAx) ​​
[PoC Auto Approved Guideline](https://pingcap.feishu.cn/wiki/wikcnldz7pJPGSBeO3ShrFXg7F7)


## FAQ:
1. What if the credits are used up but the PoC is still ongoing?
1. Pls raise a new "Adding Credits Request" in Salesforce; details pls refer to "3. Credits adding during PoC" PoC Application Process..
2. How can I request PoC credits for a customer?
Alternatives: How to apply PoC credits?
1. Step 1: confirm with your customer if they have signed up TiDB Cloud and ask for their Cloud Org ID.
2. Step 2: claim the Lead with the Cloud Org ID from your SDR or Sales Ops, and convert it into your Account.
3. Step 3: submit the credits request in Salesforce; details pls refer to PoC Application Process (for Global Business). After the request is approved, the credits will be added.
3. Can I request PoC credits for my own TiDB Cloud account?
1. Yes, pls submit the internal credits request in TiDB Cloud Ops Portal. Details pls refer to TiDB Cloud Credits Request for Internal Users.
4. What will happen after my request is approved?
1. If this is a request in TiDB Cloud Ops Portal for internal users, the credits will be added automatically after the request is approved. If this is a request in Salesforce for external users, the credits will be added by your BE&O partner and the SLA is 4 hours.
5. How can I check what the approval process is now?
1. If this is an external PoC credits request in Salesforce, please go to Salesforce and check the "Approval History" on the PoC page. If it is blank, pls click "Submit for approval".
2. If this is an internal PoC credits request in Cloud Ops Portal, please go to Cloud Ops Portal and check the Approval Info on the Operation History page.
6. The TiDB Cloud Organization ID is blank in my PoC request in Salesforce. How can I get it filled in?
1. Step 1: confirm with your customer what is their Cloud Org ID for this PoC.
2. Step 2: claim the Lead associated with this Cloud Org ID in Salesforce from the SDR or your BE&O partner.
3. Step 3: convert the Lead into your Account.
4. Step 4: fill in the Org on the PoC page and the TiDB Cloud Org ID will display.
[Poc Auto Approved Guidance.pptx](https://pingcap.feishu.cn/wiki/wikcnldz7pJPGSBeO3ShrFXg7F7)
