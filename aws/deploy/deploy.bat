@echo off
chcp 65001 >nul
echo 🚀 開始部署 FinNews-Bot AWS Lambda 函數

REM 設定變數
set REGION=ap-southeast-1
set CRAWLER_FUNCTION=finnews-bot-crawler
set PUSHER_FUNCTION=finnews-bot-pusher
set ACCOUNT_ID=121424776979
set ROLE_NAME=finnews-lambda-role

echo.
echo ⚠️  請先確認以下設定：
echo    1. AWS CLI 已安裝並配置
echo    2. 已創建 IAM 角色: %ROLE_NAME%
echo    3. 已設定環境變數
echo.
set /p CONTINUE="繼續部署嗎？(y/n): "
if /i not "%CONTINUE%"=="y" goto :end

REM 檢查 AWS CLI
aws --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 請先安裝 AWS CLI
    goto :end
)

echo 📦 準備部署包...

REM 建立暫時目錄
if exist temp rmdir /s /q temp
mkdir temp\crawler temp\pusher

REM 複製共用檔案到爬蟲包
xcopy /e /i ..\core temp\crawler\core\ >nul
xcopy /e /i ..\scraper temp\crawler\scraper\ >nul
copy ..\aws\crawler\lambda_function.py temp\crawler\ >nul
copy ..\requirements.txt temp\crawler\ >nul

REM 複製共用檔案到推送包  
xcopy /e /i ..\core temp\pusher\core\ >nul
copy ..\aws\pusher\lambda_function.py temp\pusher\ >nul
copy ..\requirements.txt temp\pusher\ >nul

echo 📦 建立爬蟲部署包...
cd temp\crawler
powershell -Command "Compress-Archive -Path * -DestinationPath ..\..\crawler-deployment.zip -Force"
cd ..\..

echo 📦 建立推送部署包...
cd temp\pusher  
powershell -Command "Compress-Archive -Path * -DestinationPath ..\..\pusher-deployment.zip -Force"
cd ..\..

echo 🚀 部署爬蟲 Lambda 函數...
aws lambda create-function ^
    --function-name %CRAWLER_FUNCTION% ^
    --runtime python3.9 ^
    --role arn:aws:iam::%ACCOUNT_ID%:role/%ROLE_NAME% ^
    --handler lambda_function.lambda_handler ^
    --zip-file fileb://crawler-deployment.zip ^
    --timeout 300 ^
    --memory-size 512 ^
    --region %REGION% ^
    --environment Variables="{\"SUPABASE_URL\":\"%SUPABASE_URL%\",\"SUPABASE_SERVICE_KEY\":\"%SUPABASE_SERVICE_KEY%\",\"OPENAI_API_KEY\":\"%OPENAI_API_KEY%\",\"CRAWLER_LIMIT\":\"10\"}"

if errorlevel 1 (
    echo 📝 函數可能已存在，嘗試更新代碼...
    aws lambda update-function-code ^
        --function-name %CRAWLER_FUNCTION% ^
        --zip-file fileb://crawler-deployment.zip ^
        --region %REGION%
)

echo 🚀 部署推送 Lambda 函數...
aws lambda create-function ^
    --function-name %PUSHER_FUNCTION% ^
    --runtime python3.9 ^
    --role arn:aws:iam::%ACCOUNT_ID%:role/%ROLE_NAME% ^
    --handler lambda_function.lambda_handler ^
    --zip-file fileb://pusher-deployment.zip ^
    --timeout 180 ^
    --memory-size 256 ^
    --region %REGION% ^
    --environment Variables="{\"SUPABASE_URL\":\"%SUPABASE_URL%\",\"SUPABASE_SERVICE_KEY\":\"%SUPABASE_SERVICE_KEY%\"}"

if errorlevel 1 (
    echo 📝 函數可能已存在，嘗試更新代碼...
    aws lambda update-function-code ^
        --function-name %PUSHER_FUNCTION% ^
        --zip-file fileb://pusher-deployment.zip ^
        --region %REGION%
)

echo ⏰ 設定 EventBridge 定時觸發...

REM 爬蟲：每4小時執行一次
aws events put-rule ^
    --name finnews-crawler-schedule ^
    --schedule-expression "cron(0 22,2,6,10 * * ? *)" ^
    --region %REGION%

aws lambda add-permission ^
    --function-name %CRAWLER_FUNCTION% ^
    --statement-id crawler-schedule-permission ^
    --action lambda:InvokeFunction ^
    --principal events.amazonaws.com ^
    --source-arn arn:aws:events:%REGION%:%ACCOUNT_ID%:rule/finnews-crawler-schedule ^
    --region %REGION% 2>nul

aws events put-targets ^
    --rule finnews-crawler-schedule ^
    --targets "Id"="1","Arn"="arn:aws:lambda:%REGION%:%ACCOUNT_ID%:function:%CRAWLER_FUNCTION%" ^
    --region %REGION%

REM 推送：每10分鐘檢查一次
aws events put-rule ^
    --name finnews-pusher-schedule ^
    --schedule-expression "rate(10 minutes)" ^
    --region %REGION%

aws lambda add-permission ^
    --function-name %PUSHER_FUNCTION% ^
    --statement-id pusher-schedule-permission ^
    --action lambda:InvokeFunction ^
    --principal events.amazonaws.com ^
    --source-arn arn:aws:events:%REGION%:%ACCOUNT_ID%:rule/finnews-pusher-schedule ^
    --region %REGION% 2>nul

aws events put-targets ^
    --rule finnews-pusher-schedule ^
    --targets "Id"="1","Arn"="arn:aws:lambda:%REGION%:%ACCOUNT_ID%:function:%PUSHER_FUNCTION%" ^
    --region %REGION%

echo 🧹 清理暫時檔案...
rmdir /s /q temp
del crawler-deployment.zip pusher-deployment.zip

echo.
echo ✅ AWS Lambda 部署完成！
echo 📝 請記得：
echo    1. 在腳本中設定正確的 ACCOUNT_ID
echo    2. 設定環境變數 SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY
echo    3. 在 AWS Console 測試 Lambda 函數
echo    4. 檢查 CloudWatch 日誌

:end
pause