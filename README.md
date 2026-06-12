# AWS Cost Monitor Dashboard
 
A serverless AWS cost monitoring pipeline that automatically tracks daily spending, sends smart budget alerts, and displays an interactive dashboard — built entirely on AWS free/low-cost services.
 
## Live Dashboard
Hosted on S3 Static Website Hosting — accessible via browser, no login required.
 
## Architecture
 
```
EventBridge (daily trigger)
        ↓
    Lambda (Python)
        ↓
Cost Explorer API ──→ Service-wise breakdown
AWS Budgets API   ──→ Budget vs actual spend
Resource Explorer ──→ Active resources inventory
        ↓
DynamoDB ──→ Daily cost history (30+ days)
        ↓
S3 ──→ dashboard_data.json + history.json
        ↓
S3 Static Website ──→ index.html + history.html
        ↓
SNS ──→ Email alerts (50% / 80% / 100% thresholds)
```
 
## Features
 
- **Real-time cost tracking** — fetches actual AWS spend since start of month
- **Smart budget alerts** — email notifications at 50%, 80%, and 100% of budget limit (no spam — threshold-based)
- **Service-wise breakdown** — see exactly which AWS service is costing what
- **Active resource inventory** — view all running Lambda functions, S3 buckets, EC2 instances, DynamoDB tables and more
- **Historical data** — daily records stored in DynamoDB, visualized as monthly bar charts
- **Month-over-month comparison** — compare current vs previous month spending per service
- **Expandable resource view** — click any service type to see individual resource names
## AWS Services Used
 
| Service | Purpose |
|---------|---------|
| AWS Lambda | Core processing — fetches cost data, saves to DB, triggers alerts |
| Amazon S3 | Stores dashboard HTML + JSON data, hosts static website |
| Amazon DynamoDB | Stores daily cost history |
| Amazon SNS | Sends email alerts when budget thresholds are crossed |
| AWS EventBridge | Daily scheduled trigger for Lambda |
| AWS Cost Explorer API | Fetches service-wise cost breakdown |
| AWS Budgets API | Fetches budget limit and actual spend |
| AWS Resource Explorer | Fetches inventory of all active AWS resources |
| AWS IAM | Least-privilege role for Lambda permissions |

##Screenshots

##Dashboard
<img width="1882" height="826" alt="image" src="https://github.com/user-attachments/assets/8f6c8ff8-6d0e-4a53-a6a2-1e8a6bcf6585" />

<img width="1879" height="867" alt="image" src="https://github.com/user-attachments/assets/3c5f2bf4-b01f-42b3-9b7c-823fb8cae6b1" />

##Email
<img width="1404" height="478" alt="image" src="https://github.com/user-attachments/assets/66d990b7-dca9-421f-b92d-ff81be4a3179" />

