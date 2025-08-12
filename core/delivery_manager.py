#!/usr/bin/env python3
"""
推送平台管理器
支援多種推送平台的統一介面
"""

import smtplib
import asyncio
import requests
import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime

from core.config import settings

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeliveryProvider(ABC):
    """推送服務提供者抽象基類"""
    
    @abstractmethod
    async def send_articles(self, target: str, articles: List[Dict[str, Any]], subscription: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """發送新聞文章到指定目標
        
        Args:
            target: 推送目標 (email地址或webhook URL)
            articles: 新聞文章列表
            subscription: 用戶訂閱資訊
            
        Returns:
            Tuple[bool, List[Dict]]: (整體是否成功, 失敗的文章列表)
        """
        pass
    
    @abstractmethod
    def validate_target(self, target: str) -> bool:
        """驗證推送目標格式是否正確"""
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """獲取平台名稱"""
        pass


class DiscordProvider(DeliveryProvider):
    """Discord Webhook 推送服務"""
    
    def get_platform_name(self) -> str:
        return "Discord"
    
    def validate_target(self, target: str) -> bool:
        """驗證 Discord Webhook URL 格式"""
        return target.startswith("https://discord.com/api/webhooks/")
    
    async def validate_target_with_test(self, target: str) -> Tuple[bool, str]:
        """
        驗證 Discord Webhook URL 並測試連通性
        
        Returns:
            Tuple[bool, str]: (是否有效, 錯誤訊息)
        """
        import aiohttp
        import asyncio
        
        # 首先檢查格式
        if not self.validate_target(target):
            return False, "Discord Webhook URL 格式不正確，應以 https://discord.com/api/webhooks/ 開頭"
        
        try:
            # 發送測試請求到 Discord webhook
            timeout = aiohttp.ClientTimeout(total=10)  # 10秒超時
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # 發送一個測試的 embed 消息
                test_payload = {
                    "embeds": [{
                        "title": "🔍 驗證測試",
                        "description": "此為系統驗證消息，可忽略。",
                        "color": 3447003,
                        "footer": {
                            "text": "FinNews-Bot 驗證系統"
                        }
                    }]
                }
                
                async with session.post(target, json=test_payload) as response:
                    if response.status == 204:
                        # Discord webhook 成功回應 204 No Content
                        logger.info(f"✅ Discord webhook validation successful: {target[:50]}...")
                        return True, ""
                    elif response.status == 404:
                        return False, "Webhook 不存在或已被刪除"
                    elif response.status == 401:
                        return False, "Webhook 權限不足或無效"
                    elif response.status == 429:
                        return False, "請求過於頻繁，請稍後再試"
                    else:
                        error_text = await response.text()
                        logger.warning(f"⚠️ Discord webhook returned status {response.status}: {error_text}")
                        return False, f"Discord API 回應異常 (狀態碼: {response.status})"
                        
        except asyncio.TimeoutError:
            return False, "連接超時，請檢查網路連線或稍後重試"
        except aiohttp.ClientError as e:
            logger.error(f"❌ Discord webhook validation network error: {e}")
            return False, "網路連接錯誤，請檢查網路連線"
        except Exception as e:
            logger.error(f"❌ Discord webhook validation error: {e}")
            return False, f"驗證時發生錯誤: {str(e)}"
    
    async def send_articles(self, webhook: str, articles: List[Dict[str, Any]], subscription: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        批量發送新聞到 Discord - 每則新聞單獨發送
        
        Returns:
            Tuple[bool, List[Dict]]: (整體是否成功, 失敗的文章列表)
        """
        if not self.validate_target(webhook):
            logger.error(f"❌ Invalid Discord webhook URL: {webhook}")
            return False, articles
        
        if not articles:
            logger.warning("⚠️ No articles to send")
            return False, []
        
        logger.info(f"📤 Starting batch send of {len(articles)} articles to Discord...")
        
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
                logger.info(f"✅ Successfully sent article {i+1}: {article['title'][:50]}...")
                
                # 推送間隔 - 避免 Discord API 限制
                if i < len(articles) - 1:  # 最後一則不需要延遲
                    delay = 1.5  # 1.5秒間隔
                    logger.info(f"⏳ Waiting {delay} seconds before next article...")
                    await asyncio.sleep(delay)
                    
            except requests.exceptions.HTTPError as e:
                error_msg = f"HTTP錯誤 {e.response.status_code}: {e.response.text}"
                logger.error(f"❌ Failed to send article {i+1}: {error_msg}")
                failed_articles.append({
                    **article, 
                    "error": error_msg,
                    "error_type": "http_error"
                })
                
            except requests.exceptions.RequestException as e:
                error_msg = f"網路錯誤: {str(e)}"
                logger.error(f"❌ Failed to send article {i+1}: {error_msg}")
                failed_articles.append({
                    **article,
                    "error": error_msg,
                    "error_type": "network_error"
                })
                
            except Exception as e:
                error_msg = f"未知錯誤: {str(e)}"
                logger.error(f"❌ Failed to send article {i+1}: {error_msg}")
                failed_articles.append({
                    **article,
                    "error": error_msg,
                    "error_type": "unknown_error"
                })
        
        success_count = len(successful_articles)
        total_count = len(articles)
        overall_success = success_count > 0 and len(failed_articles) == 0
        
        logger.info(f"📊 Discord batch sending completed: {success_count}/{total_count} successful")
        
        # 發送推送總結消息（如果有成功推送的文章）
        if success_count > 0:
            await self._send_summary_message(webhook, success_count, frequency_type)
        
        return overall_success, failed_articles
    
    async def _send_summary_message(self, webhook: str, success_count: int, frequency_type: str) -> bool:
        """發送推送總結消息到 Discord"""
        try:
            summary_payload = {
                "embeds": [{
                    "title": "📋 新聞推送完成",
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
            logger.info("📋 Push summary message sent successfully")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to send push summary message: {e}")
            return False


class EmailProvider(DeliveryProvider):
    """Email 推送服務"""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.from_name = "FinNews-Bot"
    
    def get_platform_name(self) -> str:
        return "Email"
    
    def validate_target(self, email: str) -> bool:
        """驗證 Email 地址格式"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    async def validate_target_with_test(self, email: str) -> Tuple[bool, str]:
        """
        驗證 Email 地址格式（不進行實際發送測試）
        
        Returns:
            Tuple[bool, str]: (是否有效, 錯誤訊息)
        """
        # 首先檢查格式
        if not self.validate_target(email):
            return False, "電子郵件地址格式不正確，請提供有效的電子郵件地址"
        
        # 對於 Email，我們不進行實際的發送測試，因為這會發送測試郵件
        # 只進行格式驗證和 SMTP 配置檢查
        if not all([self.smtp_server, self.smtp_user, self.smtp_password]):
            logger.warning("⚠️ SMTP configuration incomplete, but email format is valid")
            return True, "Email 格式正確，但 SMTP 配置未完成，可能無法發送郵件"
        
        # Email 格式正確且 SMTP 配置完整
        return True, ""
    
    async def send_articles(self, email: str, articles: List[Dict[str, Any]], subscription: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        批量發送新聞到 Email
        
        Returns:
            Tuple[bool, List[Dict]]: (整體是否成功, 失敗的文章列表)
        """
        if not self.validate_target(email):
            logger.error(f"❌ Invalid email address: {email}")
            return False, articles
        
        if not articles:
            logger.warning("⚠️ No articles to send")
            return False, []
        
        # 檢查 SMTP 配置
        if not all([self.smtp_server, self.smtp_user, self.smtp_password]):
            logger.error("❌ SMTP configuration missing")
            return False, articles
        
        logger.info(f"📧 Sending {len(articles)} articles to email: {email}")
        
        try:
            # 獲取用戶推送頻率類型
            frequency_type = subscription.get('push_frequency_type', 'daily')
            user_language = subscription.get('summary_language', 'zh-tw')
            
            # 生成 HTML 郵件內容
            html_content = self._generate_email_html(articles, frequency_type, user_language)
            
            # 創建郵件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = self._generate_email_subject(len(articles), frequency_type, user_language)
            msg['From'] = formataddr((self.from_name, self.from_email))
            msg['To'] = email
            
            # 添加 HTML 內容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 發送郵件
            await self._send_email(msg, email)
            
            logger.info(f"✅ Successfully sent email to: {email}")
            return True, []
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {email}: {str(e)}")
            return False, articles
    
    def _generate_email_subject(self, article_count: int, frequency_type: str, language: str) -> str:
        """生成郵件主旨"""
        frequency_labels = {
            'zh-tw': {'daily': '每日', 'twice': '上午/下午', 'thrice': '早午晚'},
            'zh-cn': {'daily': '每日', 'twice': '上午/下午', 'thrice': '早午晚'},
            'en': {'daily': 'Daily', 'twice': 'Bi-daily', 'thrice': 'Tri-daily'}
        }
        
        lang = 'en' if language.startswith('en') else 'zh-tw'
        freq_label = frequency_labels[lang].get(frequency_type, frequency_type)
        
        if lang == 'en':
            return f"FinNews-Bot {freq_label} Update - {article_count} Articles"
        else:
            return f"FinNews-Bot {freq_label}財經新聞 - {article_count}則更新"
    
    def _generate_email_html(self, articles: List[Dict[str, Any]], frequency_type: str, language: str) -> str:
        """生成 HTML 格式的郵件內容"""
        lang_is_en = language.startswith('en')
        
        # 郵件標題
        title = "FinNews-Bot Financial News Update" if lang_is_en else "FinNews-Bot 財經新聞推送"
        greeting = f"Here are your latest financial news updates:" if lang_is_en else f"以下是您的最新財經新聞："
        
        # 頻率標籤
        frequency_labels = {
            'daily': 'Daily Update' if lang_is_en else '每日推送',
            'twice': 'Bi-daily Update' if lang_is_en else '每日兩次推送', 
            'thrice': 'Tri-daily Update' if lang_is_en else '每日三次推送'
        }
        freq_label = frequency_labels.get(frequency_type, frequency_type)
        
        # 生成文章 HTML
        articles_html = ""
        for i, article in enumerate(articles, 1):
            articles_html += f"""
            <div style="margin-bottom: 24px; padding: 16px; border-left: 4px solid #3B82F6; background-color: #F8FAFC;">
                <h3 style="margin: 0 0 8px 0; color: #1E293B;">
                    <a href="{article['original_url']}" style="color: #1E293B; text-decoration: none;">
                        {i}. {article['title']}
                    </a>
                </h3>
                <p style="margin: 0 0 12px 0; color: #475569; line-height: 1.5;">
                    {article['summary']}
                </p>
                <a href="{article['original_url']}" 
                   style="display: inline-block; padding: 8px 16px; background-color: #3B82F6; color: white; text-decoration: none; border-radius: 4px; font-size: 14px;">
                    {'Read Full Article' if lang_is_en else '閱讀完整文章'} →
                </a>
            </div>
            """
        
        # 完整 HTML 模板
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            
            <!-- Header -->
            <div style="text-align: center; margin-bottom: 32px; padding: 24px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; color: white;">
                <h1 style="margin: 0 0 8px 0; font-size: 24px;">📰 {title}</h1>
                <p style="margin: 0; opacity: 0.9; font-size: 16px;">{freq_label}</p>
            </div>
            
            <!-- Greeting -->
            <p style="margin-bottom: 24px; font-size: 16px; color: #475569;">
                {greeting}
            </p>
            
            <!-- Articles -->
            {articles_html}
            
            <!-- Footer -->
            <div style="margin-top: 40px; padding-top: 24px; border-top: 2px solid #E2E8F0; text-align: center; color: #64748B; font-size: 14px;">
                <p style="margin: 0 0 8px 0;">
                    {'This email was sent by FinNews-Bot' if lang_is_en else '此郵件由 FinNews-Bot 發送'}
                </p>
                <p style="margin: 0; font-size: 12px;">
                    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • 
                    {'Personalized financial news delivery' if lang_is_en else '個人化財經新聞推送服務'}
                </p>
            </div>
            
        </body>
        </html>
        """
        
        return html_content
    
    async def _send_email(self, msg: MIMEMultipart, to_email: str):
        """發送郵件"""
        try:
            # 使用 asyncio 在線程池中執行 SMTP 操作
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_email_sync, msg, to_email)
            
        except Exception as e:
            logger.error(f"SMTP send error: {e}")
            raise
    
    def _send_email_sync(self, msg: MIMEMultipart, to_email: str):
        """同步發送郵件"""
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)


class DeliveryManager:
    """推送平台管理器"""
    
    def __init__(self):
        self.providers = {
            'discord': DiscordProvider(),
            'email': EmailProvider()
        }
        logger.info(f"Delivery manager initialized with platforms: {list(self.providers.keys())}")
    
    def get_provider(self, platform: str) -> Optional[DeliveryProvider]:
        """獲取指定平台的推送服務提供者"""
        return self.providers.get(platform.lower())
    
    def validate_target(self, platform: str, target: str) -> bool:
        """驗證推送目標格式"""
        provider = self.get_provider(platform)
        if not provider:
            logger.error(f"Unsupported platform: {platform}")
            return False
        
        return provider.validate_target(target)
    
    async def validate_target_with_test(self, platform: str, target: str) -> Tuple[bool, str]:
        """
        驗證推送目標並測試連通性（僅在用戶完成設置時調用）
        
        Returns:
            Tuple[bool, str]: (是否有效, 錯誤訊息)
        """
        provider = self.get_provider(platform)
        if not provider:
            return False, f"不支援的平台: {platform}"
        
        # 如果提供者有增強驗證方法，使用增強驗證
        if hasattr(provider, 'validate_target_with_test'):
            return await provider.validate_target_with_test(target)
        
        # 否則使用基本格式驗證
        is_valid = provider.validate_target(target)
        if is_valid:
            return True, "格式驗證通過"
        else:
            if platform.lower() == 'discord':
                return False, "Discord Webhook URL 格式不正確，應以 https://discord.com/api/webhooks/ 開頭"
            elif platform.lower() == 'email':
                return False, "Email 地址格式不正確"
            else:
                return False, f"無效的 {platform} 目標格式"
    
    async def send_to_platform(self, platform: str, target: str, articles: List[Dict[str, Any]], subscription: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """發送新聞到指定平台
        
        Args:
            platform: 推送平台 ('discord' 或 'email')
            target: 推送目標 (webhook URL 或 email 地址)
            articles: 新聞文章列表
            subscription: 用戶訂閱資訊
            
        Returns:
            Tuple[bool, List[Dict]]: (整體是否成功, 失敗的文章列表)
        """
        provider = self.get_provider(platform)
        if not provider:
            logger.error(f"❌ Unsupported delivery platform: {platform}")
            return False, articles
        
        logger.info(f"📤 Sending {len(articles)} articles via {provider.get_platform_name()} to user: {subscription.get('user_id', 'N/A')[:8]}...")
        
        try:
            return await provider.send_articles(target, articles, subscription)
        except Exception as e:
            logger.error(f"❌ Failed to send via {provider.get_platform_name()}: {str(e)}")
            return False, articles
    
    def get_supported_platforms(self) -> List[str]:
        """獲取支援的推送平台列表"""
        return list(self.providers.keys())
    
    async def send_summary_message(self, platform: str, target: str, success_count: int, total_count: int, frequency_type: str) -> bool:
        """發送推送總結消息"""
        provider = self.get_provider(platform)
        if not provider:
            logger.error(f"❌ Unsupported platform for summary: {platform}")
            return False
        
        # 目前只有 Discord 支援總結消息
        if platform.lower() == 'discord' and isinstance(provider, DiscordProvider):
            return await provider._send_summary_message(target, success_count, frequency_type)
        
        # 其他平台暫不支援總結消息
        logger.info(f"Summary messages not supported for platform: {platform}")
        return True


# 創建全域實例
delivery_manager = DeliveryManager()


def get_delivery_manager() -> DeliveryManager:
    """獲取全域推送管理器實例"""
    return delivery_manager


# 向後兼容的函數
async def send_batch_to_discord(webhook: str, articles: List[Dict[str, Any]], subscription: Dict[str, Any] = None) -> Tuple[bool, List[Dict[str, Any]]]:
    """向後兼容的 Discord 推送函數"""
    return await delivery_manager.send_to_platform('discord', webhook, articles, subscription or {})


def validate_discord_webhook(webhook: str) -> bool:
    """向後兼容的 Discord Webhook 驗證函數"""
    return delivery_manager.validate_target('discord', webhook)


def validate_email(email: str) -> bool:
    """Email 地址驗證函數"""
    return delivery_manager.validate_target('email', email)