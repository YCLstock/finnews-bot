import time
import requests
import logging
import sys
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
import openai
from core.config import settings

# --- Logger Setup ---
def setup_logger(name: str, log_file: str = None, level=logging.INFO):
    """設定一個可複用的 logger"""
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger # 如果已經設定過，直接返回

    logger.setLevel(level)
    
    # 設定格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 設定控制台 handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    # (可選) 設定檔案 handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

# --- End of Logger Setup ---


# 台灣時區常數
TAIWAN_TIMEZONE = timezone(timedelta(hours=8))

# Initialize OpenAI
openai.api_key = settings.OPENAI_API_KEY

# 建立一個 logger 實例供 utils.py 內部使用
logger = setup_logger(__name__)

def generate_summary_optimized(content: str) -> str:
    """使用 OpenAI API 生成金融新聞摘要 (優化版)"""
    logger.info("🧠 正在生成摘要 (使用 gpt-3.5-turbo)...")
    if not openai.api_key:
        return "[摘要生成失敗：API Key 未設定]"

    # 優化後的 Prompt，更具體地指導模型
    system_prompt = """
    你是一位專業的財經新聞編輯。你的任務是為以下文章生成一段專業、客觀且精簡的摘要。

    請遵循以下指示：
    1.  **風格**：語氣必須中立、客觀，專注於事實陳述，避免任何猜測或情緒性用語。
    2.  **核心要素**：摘要內容應涵蓋新聞的幾個關鍵要素：
        -   **事件主角**：涉及的主要公司、人物或機構。
        -   **核心事件**：發生了什麼關鍵決策、發布或變化。
        -   **關鍵數據**：提及任何重要的財務數據、百分比或市場指標。
        -   **市場影響**：簡述此事件對相關產業、股價或市場的潛在影響。
    3.  **格式要求**：
        -   使用繁體中文。
        -   摘要長度嚴格控制在 50 到 150 字之間。
        -   摘要應是一段完整的段落，語意連貫。
    4.  **目標讀者**：此摘要是為了讓沒有時間閱讀全文的投資人能快速掌握新聞重點。
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            temperature=0.3,  # 對於摘要任務，較低的溫度可以讓輸出更穩定、更專注於事實
            max_tokens=600  # 稍微增加 token 限制以確保摘要能完整生成
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"❌ 摘要失敗: {e}")
        return "[摘要生成失敗]"

def send_to_discord(webhook: str, articles: List[Dict[str, Any]], subscription: Dict[str, Any] = None) -> bool:
    """
    將格式化後的新聞摘要發送到 Discord Webhook
    
    ⚠️ DEPRECATED: 此函數已棄用，請使用 core.delivery_manager.DeliveryManager
    保持此函數僅為向後兼容性，建議遷移到新的多平台推送系統
    """
    if not webhook.startswith("https://discord.com/api/webhooks/"):
        print(f"❌ Webhook 不正確：{webhook}")
        return False
    
    fields = [{
        "name": f"**{i+1}. {article['title']}**",
        "value": f"{article['summary']}\n[點此閱讀原文]({article['original_url']})",
        "inline": False
    } for i, article in enumerate(articles)]
    
    payload = {
        "embeds": [{
            "title": f"您訂閱的新聞",
            "color": 3447003,  # Discord 藍色
            "fields": fields,
            "footer": {"text": f"發送時間: {time.strftime('%Y-%m-%d %H:%M:%S')}"}
        }]
    }
    
    try:
        response = requests.post(webhook, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ 成功推送到 Discord")
        return True
    except Exception as e:
        print(f"❌ 推送失敗: {e}")
        return False

def send_batch_to_discord(webhook: str, articles: List[Dict[str, Any]], subscription: Dict[str, Any] = None) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    批量發送新聞到 Discord - 每則新聞單獨發送
    
    ⚠️ DEPRECATED: 此函數已棄用，請使用 core.delivery_manager.DeliveryManager
    保持此函數僅為向後兼容性，建議遷移到新的多平台推送系統
    
    Returns:
        Tuple[bool, List[Dict]]: (整體是否成功, 失敗的文章列表)
    """
    if not webhook.startswith("https://discord.com/api/webhooks/"):
        print(f"❌ Webhook 不正確：{webhook}")
        return False, articles
    
    if not articles:
        print("⚠️ 沒有文章需要推送")
        return False, []
    
    print(f"📤 開始批量推送 {len(articles)} 則新聞到 Discord...")
    
    successful_articles = []
    failed_articles = []
    
    # 獲取用戶推送頻率類型
    frequency_type = subscription.get('push_frequency_type', 'daily') if subscription else 'daily'
    
    for i, article in enumerate(articles):
        try:
            # 創建單則新聞的 Discord embed
            payload = {
                "embeds": [{
                    "title": f"📰 {article['title']}",
                    "description": article['summary'],
                    "color": 3447003,  # Discord 藍色
                    "fields": [
                        {
                            "name": "🔗 原文連結",
                            "value": f"[點此閱讀完整內容]({article['original_url']})",
                            "inline": False
                        }
                    ],
                    "footer": {
                        "text": f"第 {i+1}/{len(articles)} 則 • {frequency_type.upper()} 推送 • {time.strftime('%Y-%m-%d %H:%M:%S')}"
                    },
                    "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                }]
            }
            
            # 發送請求
            response = requests.post(webhook, json=payload, timeout=15)
            response.raise_for_status()
            
            successful_articles.append(article)
            print(f"✅ 成功推送第 {i+1} 則: {article['title'][:50]}...")
            
            # 推送間隔 - 避免 Discord API 限制和用戶體驗考量
            if i < len(articles) - 1:  # 最後一則不需要延遲
                delay = 1.5  # 1.5秒間隔
                print(f"⏳ 等待 {delay} 秒後推送下一則...")
                time.sleep(delay)
                
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP錯誤 {e.response.status_code}: {e.response.text}"
            print(f"❌ 推送第 {i+1} 則失敗: {error_msg}")
            failed_articles.append({
                **article, 
                "error": error_msg,
                "error_type": "http_error"
            })
            
        except requests.exceptions.Timeout:
            error_msg = "請求超時"
            print(f"❌ 推送第 {i+1} 則失敗: {error_msg}")
            failed_articles.append({
                **article, 
                "error": error_msg,
                "error_type": "timeout"
            })
            
        except requests.exceptions.RequestException as e:
            error_msg = f"網絡錯誤: {str(e)}"
            print(f"❌ 推送第 {i+1} 則失敗: {error_msg}")
            failed_articles.append({
                **article, 
                "error": error_msg,
                "error_type": "network_error"
            })
            
        except Exception as e:
            error_msg = f"未知錯誤: {str(e)}"
            print(f"❌ 推送第 {i+1} 則失敗: {error_msg}")
            failed_articles.append({
                **article, 
                "error": error_msg,
                "error_type": "unknown_error"
            })
    
    # 推送結果總結
    success_count = len(successful_articles)
    fail_count = len(failed_articles)
    
    if success_count > 0:
        print(f"🎉 批量推送完成: {success_count} 成功, {fail_count} 失敗")
    else:
        print(f"❌ 批量推送完全失敗: {fail_count} 則新聞都未能推送")
    
    # 如果成功推送了至少一則，就算整體成功
    overall_success = success_count > 0
    
    return overall_success, failed_articles

def create_push_summary_message(webhook: str, success_count: int, total_count: int, frequency_type: str) -> bool:
    """
    發送推送總結消息
    
    ⚠️ DEPRECATED: 此函數已棄用，請使用 core.delivery_manager.DeliveryManager.send_summary_message
    保持此函數僅為向後兼容性，建議遷移到新的多平台推送系統
    """
    if success_count == 0:
        return False
    
    try:
        summary_payload = {
            "embeds": [{
                "title": "📊 推送完成總結",
                "description": f"本次 **{frequency_type.upper()}** 推送已完成",
                "color": 5763719,  # 綠色
                "fields": [
                    {
                        "name": "✅ 成功推送",
                        "value": f"{success_count} 則新聞",
                        "inline": True
                    },
                    {
                        "name": "📅 推送類型", 
                        "value": {
                            "daily": "每日一次",
                            "twice": "每日兩次", 
                            "thrice": "每日三次"
                        }.get(frequency_type, frequency_type),
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"下次推送時間請參考您的訂閱設定 • FinNews-Bot"
                },
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            }]
        }
        
        response = requests.post(webhook, json=summary_payload, timeout=10)
        response.raise_for_status()
        print("📋 推送總結消息發送成功")
        return True
        
    except Exception as e:
        print(f"⚠️ 推送總結消息發送失敗: {e}")
        return False

def validate_discord_webhook(webhook: str) -> bool:
    """驗證 Discord Webhook URL 格式"""
    return webhook.startswith("https://discord.com/api/webhooks/")

def normalize_language_code(language: str) -> str:
    """標準化語言代碼格式 - 將不同格式轉換為資料庫 enum 支援的連字號格式"""
    if not language:
        return "zh-tw"  # 預設值（符合資料庫 enum）
    
    # 建立轉換映射表 - 統一轉換為連字號格式（符合資料庫 enum）
    language_mappings = {
        # 中文繁體 - 統一轉為 zh-tw
        "zh-TW": "zh-tw",
        "zh-tw": "zh-tw", 
        "zh_TW": "zh-tw",
        "zh_tw": "zh-tw",
        "zh-hant": "zh-tw",
        "zh_hant": "zh-tw",
        
        # 中文簡體 - 統一轉為 zh-cn
        "zh-CN": "zh-cn",
        "zh-cn": "zh-cn",
        "zh_CN": "zh-cn", 
        "zh_cn": "zh-cn",
        "zh-hans": "zh-cn",
        "zh_hans": "zh-cn",
        
        # 英文美式 - 統一轉為 en-us
        "en-US": "en-us",
        "en-us": "en-us",
        "en_US": "en-us",
        "en_us": "en-us",
        
        # 通用英文
        "en": "en",
        "EN": "en",
        
        # 通用中文
        "zh": "zh",
        "ZH": "zh"
    }
    
    # 直接查找映射
    normalized = language_mappings.get(language)
    if normalized:
        print(f"🔄 語言代碼轉換: {language} -> {normalized}")
        return normalized
    
    # 如果沒有找到映射，返回原值（讓驗證器處理）
    print(f"⚠️ 未知的語言代碼格式: {language}")
    return language

def validate_keywords(keywords: List[str]) -> bool:
    """驗證關鍵字列表"""
    if not isinstance(keywords, list):
        return False
    if len(keywords) > 10:  # 限制最多10個關鍵字
        return False
    # 空列表是有效的
    if len(keywords) == 0:
        return True
    # 檢查每個關鍵字都是非空字符串
    return all(isinstance(keyword, str) and len(keyword.strip()) > 0 for keyword in keywords)

def get_current_utc_time() -> datetime:
    """獲取當前 UTC 時間"""
    return datetime.now(timezone.utc)

def get_current_taiwan_time() -> datetime:
    """獲取當前台灣時間 (UTC+8)"""
    return datetime.now(TAIWAN_TIMEZONE)

def utc_to_taiwan_time(utc_time: datetime) -> datetime:
    """將 UTC 時間轉換為台灣時間"""
    if utc_time.tzinfo is None:
        # 如果沒有時區信息，假設是 UTC
        utc_time = utc_time.replace(tzinfo=timezone.utc)
    return utc_time.astimezone(TAIWAN_TIMEZONE)

def taiwan_to_utc_time(taiwan_time: datetime) -> datetime:
    """將台灣時間轉換為 UTC 時間"""
    if taiwan_time.tzinfo is None:
        # 如果沒有時區信息，假設是台灣時間
        taiwan_time = taiwan_time.replace(tzinfo=TAIWAN_TIMEZONE)
    return taiwan_time.astimezone(timezone.utc)

def format_taiwan_datetime(dt: datetime) -> str:
    """將時間格式化為台灣時間字符串"""
    taiwan_time = utc_to_taiwan_time(dt) if dt.tzinfo == timezone.utc else dt
    return taiwan_time.strftime('%Y-%m-%d %H:%M:%S (UTC+8)')

def parse_article_publish_time(article_html: str = None) -> datetime:
    """
    從文章 HTML 中提取發布時間，如果無法提取則使用當前時間
    
    Args:
        article_html: 文章的 HTML 內容（可選）
        
    Returns:
        datetime: UTC 時間戳
    """
    # 目前先返回當前 UTC 時間，後續可以擴展解析邏輯
    # TODO: 添加從 Yahoo Finance 文章中解析時間的邏輯
    current_utc = get_current_utc_time()
    print(f"📅 設定文章發布時間為當前時間: {format_taiwan_datetime(current_utc)}")
    return current_utc 