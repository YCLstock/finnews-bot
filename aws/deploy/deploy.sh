#!/bin/bash
# AWS Lambda 部署腳本

echo "🚀 開始部署 FinNews-Bot AWS Lambda 函數"

# 設定變數
REGION="ap-southeast-1"
CRAWLER_FUNCTION="finnews-bot-crawler"
PUSHER_FUNCTION="finnews-bot-pusher"

# 檢查 AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ 請先安裝 AWS CLI"
    exit 1
fi

echo "📦 準備部署包..."

# 建立暫時目錄
mkdir -p temp/crawler temp/pusher

# 複製共用檔案到爬蟲包
cp -r ../core temp/crawler/
cp -r ../scraper temp/crawler/
cp ../aws/crawler/lambda_function.py temp/crawler/
cp ../requirements.txt temp/crawler/

# 複製共用檔案到推送包  
cp -r ../core temp/pusher/
cp ../aws/pusher/lambda_function.py temp/pusher/
cp ../requirements.txt temp/pusher/

# 建立部署包
echo "📦 建立爬蟲部署包..."
cd temp/crawler
zip -r ../../crawler-deployment.zip . -x "*.pyc" "*__pycache__*"
cd ../..

echo "📦 建立推送部署包..."
cd temp/pusher  
zip -r ../../pusher-deployment.zip . -x "*.pyc" "*__pycache__*"
cd ../..

# 部署爬蟲 Lambda
echo "🚀 部署爬蟲 Lambda 函數..."
aws lambda create-function \
    --function-name $CRAWLER_FUNCTION \
    --runtime python3.9 \
    --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://crawler-deployment.zip \
    --timeout 300 \
    --memory-size 512 \
    --region $REGION \
    --environment Variables='{
        "SUPABASE_URL":"'$SUPABASE_URL'",
        "SUPABASE_SERVICE_KEY":"'$SUPABASE_SERVICE_KEY'",
        "OPENAI_API_KEY":"'$OPENAI_API_KEY'",
        "CRAWLER_LIMIT":"10"
    }' \
    || aws lambda update-function-code \
    --function-name $CRAWLER_FUNCTION \
    --zip-file fileb://crawler-deployment.zip \
    --region $REGION

# 部署推送 Lambda
echo "🚀 部署推送 Lambda 函數..."
aws lambda create-function \
    --function-name $PUSHER_FUNCTION \
    --runtime python3.9 \
    --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://pusher-deployment.zip \
    --timeout 180 \
    --memory-size 256 \
    --region $REGION \
    --environment Variables='{
        "SUPABASE_URL":"'$SUPABASE_URL'",
        "SUPABASE_SERVICE_KEY":"'$SUPABASE_SERVICE_KEY'"
    }' \
    || aws lambda update-function-code \
    --function-name $PUSHER_FUNCTION \
    --zip-file fileb://pusher-deployment.zip \
    --region $REGION

# 設定定時觸發
echo "⏰ 設定 EventBridge 定時觸發..."

# 爬蟲：每4小時執行一次
aws events put-rule \
    --name finnews-crawler-schedule \
    --schedule-expression "cron(0 22,2,6,10 * * ? *)" \
    --region $REGION

aws lambda add-permission \
    --function-name $CRAWLER_FUNCTION \
    --statement-id crawler-schedule-permission \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:$REGION:YOUR_ACCOUNT:rule/finnews-crawler-schedule \
    --region $REGION \
    || echo "權限可能已存在"

aws events put-targets \
    --rule finnews-crawler-schedule \
    --targets "Id"="1","Arn"="arn:aws:lambda:$REGION:YOUR_ACCOUNT:function:$CRAWLER_FUNCTION" \
    --region $REGION

# 推送：每10分鐘檢查一次
aws events put-rule \
    --name finnews-pusher-schedule \
    --schedule-expression "rate(10 minutes)" \
    --region $REGION

aws lambda add-permission \
    --function-name $PUSHER_FUNCTION \
    --statement-id pusher-schedule-permission \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:$REGION:YOUR_ACCOUNT:rule/finnews-pusher-schedule \
    --region $REGION \
    || echo "權限可能已存在"

aws events put-targets \
    --rule finnews-pusher-schedule \
    --targets "Id"="1","Arn"="arn:aws:lambda:$REGION:YOUR_ACCOUNT:function:$PUSHER_FUNCTION" \
    --region $REGION

# 清理
echo "🧹 清理暫時檔案..."
rm -rf temp
rm crawler-deployment.zip
rm pusher-deployment.zip

echo "✅ AWS Lambda 部署完成！"
echo "📝 請記得："
echo "   1. 在AWS IAM中創建適當的執行角色"
echo "   2. 在腳本中替換 YOUR_ACCOUNT 為實際帳號ID"
echo "   3. 設定環境變數"
echo "   4. 測試 Lambda 函數執行"