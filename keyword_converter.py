#!/usr/bin/env python3
"""
用戶關鍵字AI轉換服務
用於將用戶輸入的關鍵字轉換為標準標籤
"""
import os
import json
import requests
import time
from dotenv import load_dotenv

load_dotenv()

class KeywordConverter:
    def __init__(self):
        self.core_tags = ["APPLE", "TSMC", "TESLA", "AI_TECH", "CRYPTO"]
        self.api_key = os.environ.get('OPENAI_API_KEY')
        
        # 本地緩存常見轉換，避免重複API調用
        self.common_conversions = {
            "蘋果": ["APPLE"],
            "apple": ["APPLE"],
            "台積電": ["TSMC"],
            "tsmc": ["TSMC"],
            "特斯拉": ["TESLA"],
            "tesla": ["TESLA"],
            "AI": ["AI_TECH"],
            "人工智慧": ["AI_TECH"],
            "比特幣": ["CRYPTO"],
            "bitcoin": ["CRYPTO"],
            "加密貨幣": ["CRYPTO"],
            "晶片": ["TSMC"],
            "半導體": ["TSMC"],
            "電動車": ["TESLA"],
            "馬斯克": ["TESLA"],
            "庫克": ["APPLE"],
            "iphone": ["APPLE"]
        }
    
    def convert_keywords_to_tags(self, keywords_list):
        """
        將用戶關鍵字列表轉換為標準標籤
        
        Args:
            keywords_list: ["蘋果", "AI", "晶片"]
            
        Returns:
            {
                "success": True,
                "mappings": [
                    {"keyword": "蘋果", "tags": ["APPLE"], "confidence": 0.95},
                    {"keyword": "AI", "tags": ["AI_TECH"], "confidence": 0.98}
                ],
                "final_tags": ["APPLE", "AI_TECH", "TSMC"]
            }
        """
        
        if not keywords_list:
            return {"success": False, "error": "No keywords provided"}
        
        try:
            # 先檢查本地緩存
            cached_results = []
            uncached_keywords = []
            
            for keyword in keywords_list:
                keyword_lower = keyword.lower().strip()
                if keyword_lower in self.common_conversions:
                    cached_results.append({
                        "keyword": keyword,
                        "tags": self.common_conversions[keyword_lower],
                        "confidence": 0.99,
                        "source": "cache"
                    })
                else:
                    uncached_keywords.append(keyword)
            
            # 對未緩存的關鍵字使用AI處理
            ai_results = []
            if uncached_keywords and self.api_key:
                ai_results = self._convert_with_ai(uncached_keywords)
            elif uncached_keywords:
                # 沒有AI API時使用規則匹配
                ai_results = self._convert_with_rules(uncached_keywords)
            
            # 合併結果
            all_mappings = cached_results + ai_results
            
            # 提取最終標籤列表（去重）
            all_tags = []
            for mapping in all_mappings:
                all_tags.extend(mapping["tags"])
            final_tags = list(set(all_tags))
            
            return {
                "success": True,
                "mappings": all_mappings,
                "final_tags": final_tags,
                "stats": {
                    "total_keywords": len(keywords_list),
                    "cached": len(cached_results),
                    "ai_processed": len(ai_results)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Conversion failed: {str(e)}"
            }
    
    def _convert_with_ai(self, keywords_list):
        """使用AI轉換關鍵字"""
        keywords_str = '", "'.join(keywords_list)
        
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

返回JSON格式:
{{
  "conversions": [
    {{"keyword": "蘋果", "tags": ["APPLE"], "confidence": 0.95}},
    {{"keyword": "AI", "tags": ["AI_TECH"], "confidence": 0.98}}
  ]
}}
"""
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 300,
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
                    conversions = parsed.get('conversions', [])
                    
                    # 過濾低信心度結果
                    filtered_conversions = []
                    for conv in conversions:
                        if conv.get('confidence', 0) >= 0.7:
                            conv['source'] = 'ai'
                            filtered_conversions.append(conv)
                    
                    return filtered_conversions
                    
                except json.JSONDecodeError:
                    print(f"AI response parsing failed: {content}")
                    return self._convert_with_rules(keywords_list)
            else:
                print(f"AI API error: {response.status_code}")
                return self._convert_with_rules(keywords_list)
                
        except Exception as e:
            print(f"AI conversion error: {e}")
            return self._convert_with_rules(keywords_list)
    
    def _convert_with_rules(self, keywords_list):
        """備用規則式轉換"""
        results = []
        
        rule_mappings = {
            # 擴展的規則映射
            "車": ["TESLA"],
            "汽車": ["TESLA"],
            "電動": ["TESLA"],
            "馬斯克": ["TESLA"],
            "musk": ["TESLA"],
            
            "晶片": ["TSMC"],
            "半導體": ["TSMC"],
            "晶圓": ["TSMC"],
            "台積": ["TSMC"],
            
            "智慧": ["AI_TECH"],
            "智能": ["AI_TECH"],
            "機器": ["AI_TECH"],
            "gpt": ["AI_TECH"],
            "chatgpt": ["AI_TECH"],
            
            "幣": ["CRYPTO"],
            "區塊鏈": ["CRYPTO"],
            "blockchain": ["CRYPTO"],
            "虛擬": ["CRYPTO"],
            
            "手機": ["APPLE"],
            "電腦": ["APPLE"],
            "筆電": ["APPLE"],
            "mac": ["APPLE"],
            "ipad": ["APPLE"]
        }
        
        for keyword in keywords_list:
            keyword_lower = keyword.lower().strip()
            found_tags = []
            
            # 檢查完全匹配
            if keyword_lower in rule_mappings:
                found_tags = rule_mappings[keyword_lower]
            else:
                # 檢查部分匹配
                for rule_key, tags in rule_mappings.items():
                    if rule_key in keyword_lower or keyword_lower in rule_key:
                        found_tags.extend(tags)
            
            if found_tags:
                results.append({
                    "keyword": keyword,
                    "tags": list(set(found_tags)),  # 去重
                    "confidence": 0.8,
                    "source": "rules"
                })
        
        return results
    
    def update_user_subscription_tags(self, user_id, keywords_list):
        """
        為特定用戶更新訂閱標籤
        這個函數會被您的後端API調用
        """
        conversion_result = self.convert_keywords_to_tags(keywords_list)
        
        if not conversion_result["success"]:
            return conversion_result
        
        # 更新資料庫中的訂閱標籤
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_key:
            return {"success": False, "error": "Database credentials missing"}
        
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            update_data = {
                'subscribed_tags': conversion_result["final_tags"],
                'original_keywords': keywords_list,
                'updated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            
            response = requests.patch(
                f"{supabase_url}/rest/v1/subscriptions",
                headers=headers,
                json=update_data,
                params={'user_id': f'eq.{user_id}'},
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                # 記錄轉換結果用於改進
                self._log_conversion_result(user_id, conversion_result)
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "tags_assigned": conversion_result["final_tags"],
                    "conversion_details": conversion_result["mappings"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Database update failed: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Database update error: {str(e)}"
            }
    
    def _log_conversion_result(self, user_id, conversion_result):
        """記錄轉換結果用於分析和改進"""
        # 這裡可以記錄到日誌文件或資料庫
        log_entry = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "user_id": user_id,
            "conversion_details": conversion_result
        }
        
        try:
            with open('keyword_conversion.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"Log writing failed: {e}")

# 創建全局實例
keyword_converter = KeywordConverter()

if __name__ == "__main__":
    # 測試用例
    test_keywords = ["蘋果", "AI", "晶片", "車"]
    result = keyword_converter.convert_keywords_to_tags(test_keywords)
    print(json.dumps(result, ensure_ascii=False, indent=2))