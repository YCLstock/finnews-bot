import time
import requests
from typing import List, Dict, Any, Tuple
import openai
from core.config import settings

# Initialize OpenAI
openai.api_key = settings.OPENAI_API_KEY

def generate_summary_optimized(content: str) -> str:
    """使用 OpenAI API 生成金融新聞摘要 (優化版)"""
    print("🧠 正在生成摘要 (使用 gpt-3.5-turbo)...")
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
        print(f"❌ 摘要失敗: {e}")
        return "[摘要生成失敗]"

def send_to_discord(webhook: str, articles: List[Dict[str, Any]], subscription: Dict[str, Any] = None) -> bool:
    """將格式化後的新聞摘要發送到 Discord Webhook（舊版，保持向後兼容）"""
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
    """發送推送總結消息"""
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
    """標準化語言代碼格式 - 將不同格式轉換為統一的下劃線格式"""
    if not language:
        return "zh_tw"  # 預設值
    
    # 建立轉換映射表
    language_mappings = {
        # 中文繁體
        "zh-TW": "zh_tw",
        "zh-tw": "zh_tw", 
        "zh_TW": "zh_tw",
        "zh_tw": "zh_tw",
        "zh-hant": "zh_tw",
        "zh_hant": "zh_tw",
        
        # 中文簡體
        "zh-CN": "zh_cn",
        "zh-cn": "zh_cn",
        "zh_CN": "zh_cn", 
        "zh_cn": "zh_cn",
        "zh-hans": "zh_cn",
        "zh_hans": "zh_cn",
        
        # 英文美式
        "en-US": "en_us",
        "en-us": "en_us",
        "en_US": "en_us",
        "en_us": "en_us",
        
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