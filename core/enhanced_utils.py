#!/usr/bin/env python3
"""
增強版工具函數 - 支援透明度和標籤管理
"""

import time
import requests
from typing import List, Dict, Any, Tuple
from datetime import datetime

from core.utils import get_current_taiwan_time
from core.tag_manager import tag_manager
from core.database import db_manager

def get_article_tags_from_db(article_id: int) -> List[str]:
    """從資料庫獲取文章標籤"""
    if not article_id:
        return []
    
    try:
        # 查詢 article_tags 表並 JOIN tags 表獲取 tag_code
        result = db_manager.supabase.table('article_tags').select(
            'tags(tag_code)'
        ).eq('article_id', article_id).execute()
        
        # 提取 tag_code 列表
        tag_codes = []
        for row in result.data:
            if row.get('tags') and row['tags'].get('tag_code'):
                tag_codes.append(row['tags']['tag_code'])
        
        return tag_codes
        
    except Exception as e:
        print(f"[ERROR] 查詢文章標籤失敗 (article_id: {article_id}): {e}")
        return []

def send_enhanced_batch_to_discord(
    webhook: str, 
    articles: List[Dict[str, Any]], 
    subscription: Dict[str, Any] = None,
    include_transparency: bool = True
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    增強版Discord批量推送 - 包含透明度資訊
    """
    if not webhook.startswith("https://discord.com/api/webhooks/"):
        print(f"❌ Invalid webhook URL: {webhook}")
        return False, articles
    
    if not articles:
        print("⚠️ No articles to push")
        return False, []
    
    print(f"📤 開始增強版批量推送 {len(articles)} 則新聞...")
    
    successful_articles = []
    failed_articles = []
    
    # 獲取用戶訂閱資訊
    frequency_type = subscription.get('push_frequency_type', 'daily') if subscription else 'daily'
    user_tags = subscription.get('subscribed_tags', []) if subscription else []
    user_keywords = subscription.get('keywords', []) if subscription else []
    
    for i, article in enumerate(articles):
        try:
            # 生成匹配解釋
            match_explanation = ""
            if include_transparency and subscription:
                match_explanation = generate_match_explanation(article, user_tags, user_keywords)
            
            # 創建增強版Discord embed
            embed = create_enhanced_embed(
                article, 
                i + 1, 
                len(articles), 
                frequency_type,
                match_explanation
            )
            
            payload = {"embeds": [embed]}
            
            # 發送請求
            response = requests.post(webhook, json=payload, timeout=15)
            response.raise_for_status()
            
            successful_articles.append(article)
            print(f"✅ 成功推送第 {i+1} 則: {article['title'][:50]}...")
            
            # 推送間隔
            if i < len(articles) - 1:
                time.sleep(1.5)
                
        except Exception as e:
            print(f"❌ 推送第 {i+1} 則失敗: {e}")
            failed_articles.append(article)
    
    # 發送總結訊息
    if successful_articles and include_transparency:
        send_push_summary_with_transparency(
            webhook, 
            len(successful_articles), 
            len(articles), 
            frequency_type,
            user_tags
        )
    
    overall_success = len(successful_articles) > 0
    return overall_success, failed_articles

def generate_match_explanation(
    article: Dict[str, Any], 
    user_tags: List[str], 
    user_keywords: List[str]
) -> str:
    """生成文章匹配原因說明"""
    explanations = []
    
    # 獲取文章標籤 - 從資料庫查詢
    article_tags = get_article_tags_from_db(article.get('id'))
    
    # 1. 標籤匹配檢查
    matched_tags = [tag for tag in article_tags if tag in user_tags]
    if matched_tags:
        # 獲取標籤中文名稱
        tag_info = tag_manager.get_tag_info(matched_tags)
        tag_names = [info['tag_name_zh'] for info in tag_info if info.get('tag_name_zh')]
        
        if tag_names:
            explanations.append(f"🏷️ **標籤匹配**: {', '.join(tag_names)}")
    
    # 2. 關鍵字匹配檢查
    title_lower = article.get('title', '').lower()
    summary_lower = article.get('summary', '').lower()
    
    matched_keywords = []
    for keyword in user_keywords:
        if keyword.lower() in title_lower or keyword.lower() in summary_lower:
            matched_keywords.append(keyword)
    
    if matched_keywords:
        explanations.append(f"🔍 **關鍵字匹配**: {', '.join(matched_keywords)}")
    
    # 3. 如果沒有明確匹配，說明是通用推送
    if not explanations:
        explanations.append("📰 **通用財經新聞**: 重要市場資訊")
    
    return "\n".join(explanations)

def create_enhanced_embed(
    article: Dict[str, Any], 
    index: int, 
    total: int, 
    frequency_type: str,
    match_explanation: str = ""
) -> Dict[str, Any]:
    """創建增強版Discord embed"""
    
    # 基本文章資訊
    embed = {
        "title": f"📰 {article['title']}",
        "description": article.get('summary', '摘要暫不可用'),
        "color": 3447003,  # Discord藍色
        "fields": [],
        "footer": {
            "text": f"第 {index}/{total} 則 • {frequency_type.upper()} 推送 • {time.strftime('%Y-%m-%d %H:%M:%S')}"
        },
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    }
    
    # 添加原文連結
    if article.get('original_url'):
        embed["fields"].append({
            "name": "🔗 原文連結",
            "value": f"[點此閱讀完整內容]({article['original_url']})",
            "inline": False
        })
    
    # 添加匹配原因說明
    if match_explanation:
        embed["fields"].append({
            "name": "📋 推送原因",
            "value": match_explanation,
            "inline": False
        })
    
    # 添加文章標籤資訊
    article_tags = get_article_tags_from_db(article.get('id'))
    if article_tags:
        # 獲取標籤顯示名稱
        tag_info = tag_manager.get_tag_info(article_tags)
        tag_display = []
        
        for info in tag_info:
            tag_name = info.get('tag_name_zh', info.get('tag_code', ''))
            tag_display.append(f"`{tag_name}`")
        
        if tag_display:
            embed["fields"].append({
                "name": "🏷️ 文章標籤",
                "value": " ".join(tag_display),
                "inline": False
            })
    
    return embed

def send_push_summary_with_transparency(
    webhook: str, 
    success_count: int, 
    total_count: int, 
    frequency_type: str,
    user_tags: List[str]
) -> bool:
    """發送帶透明度資訊的推送總結"""
    if success_count == 0:
        return False
    
    try:
        # 獲取用戶標籤資訊
        tag_info = tag_manager.get_tag_info(user_tags)
        user_tag_names = [info['tag_name_zh'] for info in tag_info if info.get('tag_name_zh')]
        
        # 計算推送統計
        taiwan_time = get_current_taiwan_time()
        next_push_times = get_next_push_times(frequency_type, taiwan_time)
        
        description = f"本次 **{frequency_type.upper()}** 推送已完成"
        if success_count < total_count:
            description += f"\n⚠️ {total_count - success_count} 則推送失敗"
        
        summary_embed = {
            "title": "📊 推送完成總結",
            "description": description,
            "color": 5763719,  # 綠色
            "fields": [
                {
                    "name": "📈 推送統計",
                    "value": f"✅ 成功推送: {success_count} 則\n📝 處理總數: {total_count} 則",
                    "inline": True
                },
                {
                    "name": "⏰ 下次推送",
                    "value": next_push_times,
                    "inline": True
                }
            ],
            "footer": {
                "text": f"推送完成時間: {taiwan_time.strftime('%Y-%m-%d %H:%M:%S')} (台灣時間)"
            },
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        }
        
        # 添加用戶訂閱標籤資訊
        if user_tag_names:
            summary_embed["fields"].append({
                "name": "🏷️ 您的訂閱標籤",
                "value": " • ".join(user_tag_names),
                "inline": False
            })
        
        # 添加系統資訊
        summary_embed["fields"].append({
            "name": "ℹ️ 系統資訊",
            "value": (
                "• 推送間隔: 1.5秒/則\n"
                "• 標籤匹配: AI + 關鍵字\n"
                "• 資料來源: Yahoo Finance"
            ),
            "inline": False
        })
        
        payload = {"embeds": [summary_embed]}
        
        response = requests.post(webhook, json=payload, timeout=10)
        response.raise_for_status()
        
        print("✅ 增強版推送總結發送成功")
        return True
        
    except Exception as e:
        print(f"❌ 推送總結發送失敗: {e}")
        return False

def get_next_push_times(frequency_type: str, current_time: datetime) -> str:
    """計算下次推送時間"""
    push_schedules = {
        "daily": ["08:00"],
        "twice": ["08:00", "20:00"],
        "thrice": ["08:00", "13:00", "20:00"]
    }
    
    times = push_schedules.get(frequency_type, ["08:00"])
    current_hour_min = current_time.strftime("%H:%M")
    
    # 找到下一個推送時間
    next_times = []
    for push_time in times:
        if push_time > current_hour_min:
            next_times.append(f"今日 {push_time}")
        else:
            next_times.append(f"明日 {push_time}")
    
    if not next_times:
        next_times = [f"明日 {times[0]}"]
    
    return "\n".join(next_times[:2])  # 最多顯示2個下次推送時間

def create_tag_preview_message(conversions: List[Dict[str, Any]]) -> str:
    """創建標籤轉換預覽訊息"""
    if not conversions:
        return "❌ 沒有找到匹配的標籤"
    
    preview_lines = ["🔮 **關鍵字轉換預覽**\n"]
    
    for conversion in conversions:
        keyword = conversion.get('keyword', '')
        matched_tags = conversion.get('matched_tags', [])
        
        if matched_tags:
            # 獲取標籤中文名稱
            tag_info = tag_manager.get_tag_info(matched_tags)
            tag_names = [info.get('tag_name_zh', tag) for info in tag_info]
            
            preview_lines.append(f"• `{keyword}` → {', '.join(tag_names)}")
        else:
            preview_lines.append(f"• `{keyword}` → ❌ 無匹配標籤")
    
    return "\n".join(preview_lines)

# 工具函數：用戶體驗優化

def validate_subscription_completeness(subscription: Dict[str, Any]) -> Dict[str, Any]:
    """驗證訂閱完整性並提供改善建議"""
    issues = []
    suggestions = []
    
    # 檢查關鍵字
    keywords = subscription.get('keywords', [])
    if not keywords:
        issues.append("沒有設定關鍵字")
        suggestions.append("建議新增1-3個關鍵字以獲得更精準的推送")
    elif len(keywords) > 10:
        issues.append("關鍵字過多")
        suggestions.append("關鍵字過多可能導致推送不精準，建議控制在10個以內")
    
    # 檢查標籤轉換狀態
    keywords_time = subscription.get('keywords_updated_at')
    tags_time = subscription.get('tags_updated_at')
    
    if keywords_time and tags_time and keywords_time > tags_time:
        issues.append("標籤轉換待處理")
        suggestions.append("您的關鍵字修改正在處理中，預計1小時內生效")
    elif not tags_time:
        issues.append("標籤尚未轉換")
        suggestions.append("新用戶關鍵字正在轉換中，首次推送可能需要等待1小時")
    
    # 檢查推送頻率合理性
    frequency = subscription.get('push_frequency_type', 'daily')
    if frequency == 'thrice' and len(keywords) < 3:
        suggestions.append("高頻推送建議設定更多關鍵字以確保內容豐富")
    
    return {
        "issues": issues,
        "suggestions": suggestions,
        "completeness_score": max(0, 100 - len(issues) * 20),
        "optimization_tips": [
            "定期檢視標籤匹配統計",
            "根據點擊率調整關鍵字",
            "使用標籤預覽功能確認轉換結果"
        ]
    }