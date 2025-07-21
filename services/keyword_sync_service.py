#!/usr/bin/env python3
"""
關鍵字同步服務
用於定時檢查用戶關鍵字變動並批量轉換為AI標籤
"""
import os
import json
import time
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

from core.database import db_manager
from core.config import settings

load_dotenv()

class KeywordSyncService:
    """關鍵字同步服務類"""
    
    def __init__(self):
        self.core_tags = ["APPLE", "TSMC", "TESLA", "AI_TECH", "CRYPTO"]
        self.api_key = os.environ.get('OPENAI_API_KEY')
        
        # 最小緩存（只有100%確定的映射）
        self.certain_mappings = {
            "aapl": ["APPLE"],
            "apple": ["APPLE"],
            "2330": ["TSMC"],
            "tsmc": ["TSMC"],
            "tsla": ["TESLA"],
            "tesla": ["TESLA"],
            "btc": ["CRYPTO"],
            "bitcoin": ["CRYPTO"],
        }
    
    def check_outdated_users(self) -> List[Dict[str, Any]]:
        """檢查需要更新標籤的用戶"""
        try:
            print("Checking users with outdated tags...")
            
            # 查詢keywords_updated_at > tags_updated_at的用戶
            result = db_manager.supabase.table('subscriptions').select(
                'user_id, original_keywords, keywords_updated_at, tags_updated_at'
            ).filter(
                'is_active', 'eq', True
            ).execute()
            
            outdated_users = []
            for user in result.data:
                keywords_time = user.get('keywords_updated_at')
                tags_time = user.get('tags_updated_at')
                
                # 如果關鍵字更新時間晚於標籤更新時間，需要更新
                if keywords_time and tags_time and keywords_time > tags_time:
                    outdated_users.append(user)
                elif not tags_time:  # 新用戶，從未轉換過標籤
                    outdated_users.append(user)
            
            print(f"Found {len(outdated_users)} users needing tag updates")
            return outdated_users
            
        except Exception as e:
            print(f"Check users failed: {e}")
            return []
    
    def batch_convert_keywords(self, users_data: List[Dict[str, Any]]) -> bool:
        """批量轉換用戶關鍵字為標籤"""
        if not users_data:
            print("No users need tag updates")
            return True
            
        print(f"Starting batch processing for {len(users_data)} users...")
        success_count = 0
        
        for user_data in users_data:
            user_id = user_data['user_id']
            keywords = user_data.get('original_keywords', [])
            
            if not keywords:
                print(f"User {user_id} has no keywords, skipping")
                continue
            
            print(f"Processing user {user_id}: {keywords}")
            
            # 轉換關鍵字為標籤
            converted_tags = self.convert_keywords_to_tags(keywords)
            
            if converted_tags:
                # 更新用戶標籤
                success = self.update_user_tags(user_id, converted_tags)
                if success:
                    success_count += 1
                    print(f"User {user_id} tags updated: {converted_tags}")
                else:
                    print(f"User {user_id} tag update failed")
            else:
                print(f"User {user_id} keyword conversion failed")
        
        print(f"Batch conversion completed: {success_count}/{len(users_data)} successful")
        return success_count > 0
    
    def convert_keywords_to_tags(self, keywords: List[str]) -> List[str]:
        """將關鍵字列表轉換為標籤"""
        if not keywords:
            return []
        
        # 1. 先檢查確定的映射
        certain_tags = []
        uncertain_keywords = []
        
        for keyword in keywords:
            keyword_lower = keyword.lower().strip()
            if keyword_lower in self.certain_mappings:
                certain_tags.extend(self.certain_mappings[keyword_lower])
            else:
                uncertain_keywords.append(keyword)
        
        # 2. 對不確定的關鍵字使用AI轉換
        ai_tags = []
        if uncertain_keywords and self.api_key:
            ai_tags = self._convert_with_ai(uncertain_keywords)
        elif uncertain_keywords:
            # 沒有AI API時使用規則匹配
            ai_tags = self._convert_with_rules(uncertain_keywords)
        
        # 3. 合併結果並去重
        all_tags = certain_tags + ai_tags
        final_tags = list(set(all_tags))  # 去重
        
        return final_tags[:5]  # 最多5個標籤
    
    def _convert_with_ai(self, keywords: List[str]) -> List[str]:
        """使用AI轉換關鍵字"""
        keywords_str = '", "'.join(keywords)
        
        prompt = f"""
用戶在投資App中輸入了關鍵字，請轉換為投資標籤。

用戶關鍵字: ["{keywords_str}"]

可選標籤庫:
- APPLE: 蘋果公司 (iPhone, Mac, 庫克, AAPL股票)
- TSMC: 台積電 (半導體, 晶圓, 晶片代工)
- TESLA: 特斯拉 (電動車, 馬斯克, 自駕車)
- AI_TECH: AI科技 (人工智慧, ChatGPT, 機器學習, AI相關股票)
- CRYPTO: 加密貨幣 (比特幣, 區塊鏈, 虛擬貨幣)

規則:
1. 在投資語境下，優先選擇股票/公司解釋
2. 每個關鍵字最多選擇2個標籤
3. 信心度低於0.7的不要包含
4. 如果完全不相關，該關鍵字返回空陣列

返回JSON格式，只包含符合條件的標籤:
{{"tags": ["APPLE", "AI_TECH"]}}
"""
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 200,
            'temperature': 0.1
        }
        
        try:
            response = requests.post('https://api.openai.com/v1/chat/completions', 
                                   headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                try:
                    parsed = json.loads(content)
                    tags = parsed.get('tags', [])
                    print(f"  AI conversion result: {keywords} -> {tags}")
                    return tags
                    
                except json.JSONDecodeError:
                    print(f"  AI response parsing failed: {content}")
                    return self._convert_with_rules(keywords)
            else:
                print(f"  AI API error: {response.status_code}")
                return self._convert_with_rules(keywords)
                
        except Exception as e:
            print(f"  AI conversion error: {e}")
            return self._convert_with_rules(keywords)
    
    def _convert_with_rules(self, keywords: List[str]) -> List[str]:
        """備用規則式轉換"""
        rule_mappings = {
            "蘋果": ["APPLE"],
            "台積電": ["TSMC"],
            "特斯拉": ["TESLA"],
            "電動車": ["TESLA"],
            "車": ["TESLA"],
            "馬斯克": ["TESLA"],
            "晶片": ["TSMC"],
            "半導體": ["TSMC"],
            "ai": ["AI_TECH"],
            "人工智慧": ["AI_TECH"],
            "比特幣": ["CRYPTO"],
            "加密貨幣": ["CRYPTO"],
        }
        
        tags = []
        for keyword in keywords:
            keyword_lower = keyword.lower().strip()
            # 檢查完全匹配
            if keyword_lower in rule_mappings:
                tags.extend(rule_mappings[keyword_lower])
            else:
                # 檢查部分匹配
                for rule_key, rule_tags in rule_mappings.items():
                    if rule_key in keyword_lower or keyword_lower in rule_key:
                        tags.extend(rule_tags)
        
        unique_tags = list(set(tags))
        print(f"  Rule conversion result: {keywords} -> {unique_tags}")
        return unique_tags
    
    def update_user_tags(self, user_id: str, tags: List[str]) -> bool:
        """更新用戶的訂閱標籤"""
        try:
            update_data = {
                'subscribed_tags': tags,
                'tags_updated_at': datetime.utcnow().isoformat()
            }
            
            result = db_manager.supabase.table('subscriptions').update(
                update_data
            ).eq('user_id', user_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Failed to update user {user_id} tags: {e}")
            return False
    
    def process_all_pending(self) -> bool:
        """處理所有待更新的用戶（主入口）"""
        print("Starting keyword sync service...")
        
        try:
            # 1. 檢查需要更新的用戶
            outdated_users = self.check_outdated_users()
            
            if not outdated_users:
                print("All user tags are up to date")
                return True
            
            # 2. 批量轉換關鍵字
            success = self.batch_convert_keywords(outdated_users)
            
            if success:
                print("Keyword sync service completed")
                return True
            else:
                print("Keyword sync service partially failed")
                return False
                
        except Exception as e:
            print(f"Keyword sync service failed: {e}")
            return False

# 創建全局實例
keyword_sync_service = KeywordSyncService()

if __name__ == "__main__":
    # 測試用例
    keyword_sync_service.process_all_pending()