# AWS Lambda 部署指南

## 📋 部署前準備

### 1. 安裝 AWS CLI
```bash
# Windows
curl "https://awscli.amazonaws.com/AWSCLIV2.msi" -o "AWSCLIV2.msi"
msiexec /i AWSCLIV2.msi

# macOS  
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### 2. 配置 AWS 憑證
```bash
aws configure
# AWS Access Key ID: [輸入您的Access Key]
# AWS Secret Access Key: [輸入您的Secret Key]  
# Default region name: ap-southeast-1
# Default output format: json
```

### 3. 創建 IAM 執行角色

在 AWS IAM 控制台創建角色，包含以下權限：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream", 
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

角色ARN格式：`arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role`

## 🚀 執行部署

### 1. 編輯部署腳本
```bash
# 編輯 deploy.sh，替換：
# - YOUR_ACCOUNT: 您的AWS帳號ID
# - lambda-execution-role: 您創建的IAM角色名稱
```

### 2. 設定環境變數
```bash
export SUPABASE_URL="your-supabase-url"
export SUPABASE_SERVICE_KEY="your-service-key"  
export OPENAI_API_KEY="your-openai-key"
```

### 3. 執行部署
```bash
# 給腳本執行權限
chmod +x deploy.sh

# 執行部署
./deploy.sh
```

## 📊 部署後驗證

### 1. 檢查函數
```bash
# 列出Lambda函數
aws lambda list-functions --region ap-southeast-1

# 檢查函數配置
aws lambda get-function --function-name finnews-bot-crawler --region ap-southeast-1
```

### 2. 測試執行
```bash
# 手動觸發爬蟲
aws lambda invoke \
  --function-name finnews-bot-crawler \
  --region ap-southeast-1 \
  response.json

# 檢查執行結果
cat response.json
```

### 3. 檢查定時觸發
```bash
# 列出EventBridge規則
aws events list-rules --region ap-southeast-1

# 檢查觸發目標
aws events list-targets-by-rule \
  --rule finnews-crawler-schedule \
  --region ap-southeast-1
```

## 🔧 故障排除

### 常見錯誤

#### 1. 權限錯誤
```
AccessDenied: User is not authorized to perform lambda:CreateFunction
```
**解決方案**: 檢查AWS用戶權限，確保有Lambda和EventBridge權限

#### 2. 角色不存在
```  
InvalidParameterValueException: The role defined for the function cannot be assumed by Lambda
```
**解決方案**: 確認IAM角色ARN正確，且角色信任政策包含Lambda服務

#### 3. 部署包太大
```
InvalidParameterValueException: Unzipped size must be smaller than 262144000 bytes
```
**解決方案**: 移除不必要檔案，或使用Lambda Layers

### 日誌檢查
```bash
# 檢查CloudWatch日誌
aws logs describe-log-groups --region ap-southeast-1

# 查看最新日誌
aws logs tail /aws/lambda/finnews-bot-crawler --follow --region ap-southeast-1
```

## 💰 成本估算

| 服務 | 免費額度 | 預估用量 | 月費用 |
|------|----------|----------|--------|
| Lambda 請求 | 100萬次 | ~5000次 | $0 |
| Lambda 運算時間 | 40萬GB-秒 | ~1000GB-秒 | $0 |
| EventBridge | 1400萬事件 | ~4500事件 | $0 |
| **總計** | | | **$0** |

## 📈 監控設置

### CloudWatch 警報
```bash
# 創建錯誤率警報
aws cloudwatch put-metric-alarm \
  --alarm-name "Lambda-Error-Rate" \
  --alarm-description "Lambda函數錯誤率過高" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --region ap-southeast-1
```

### 日誌保留設置
```bash
# 設定日誌保留期限（7天）
aws logs put-retention-policy \
  --log-group-name /aws/lambda/finnews-bot-crawler \
  --retention-in-days 7 \
  --region ap-southeast-1
```