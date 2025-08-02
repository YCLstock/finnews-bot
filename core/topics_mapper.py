#!/usr/bin/env python3
"""
用戶關鍵字到Yahoo Finance Topics映射系統
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

class TopicsMapper:
    """將用戶關鍵字映射到Yahoo Finance Topics"""
    
    def __init__(self, config_file: str = None):
        """初始化映射器"""
        if config_file is None:
            config_file = Path(__file__).parent.parent / 'topics_keyword_mapping.json'
        
        self.config_file = Path(config_file)
        self.load_mapping_config()
    
    def load_mapping_config(self):
        """載入映射配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            self.topics_mapping = config['topics_mapping']
            self.mapping_rules = config['mapping_rules']
            self.exclusion_patterns = config.get('exclusion_patterns', [])
            
            print(f"Loaded mapping config: {len(self.topics_mapping)} topics")
            
        except Exception as e:
            print(f"Error loading mapping config: {e}")
            # 使用備用配置
            self._load_fallback_config()
    
    def _load_fallback_config(self):
        """載入備用配置"""
        self.topics_mapping = {
            'crypto': {
                'keywords': ['bitcoin', 'crypto', 'blockchain', '比特幣', '加密貨幣'],
                'priority': 1
            },
            'tech': {
                'keywords': ['apple', 'tesla', 'ai', '蘋果', '特斯拉', '人工智慧'],
                'priority': 2
            },
            'latest': {
                'keywords': ['news', 'breaking', '新聞', '最新'],
                'priority': 12
            }
        }
        
        self.mapping_rules = {
            'exact_match_weight': 3,
            'partial_match_weight': 1,
            'case_sensitive': False,
            'min_confidence_score': 0.3,
            'max_topics_per_keyword': 2,
            'default_topic': 'latest'
        }
        
        self.exclusion_patterns = []
    
    def map_keywords_to_topics(self, user_keywords: List[str]) -> List[Tuple[str, float]]:
        """
        將用戶關鍵字映射到Topics
        
        Args:
            user_keywords: 用戶的關鍵字列表
            
        Returns:
            List of (topic, confidence_score) 按信心分數排序
        """
        if not user_keywords:
            return [(self.mapping_rules['default_topic'], 1.0)]
        
        topic_scores = {}
        
        for user_keyword in user_keywords:
            if self._is_excluded_keyword(user_keyword):
                continue
                
            # 計算每個topic的匹配分數
            for topic_name, topic_config in self.topics_mapping.items():
                topic_keywords = topic_config['keywords']
                priority = topic_config.get('priority', 10)
                
                match_score = self._calculate_match_score(user_keyword, topic_keywords)
                
                if match_score > 0:
                    # 結合匹配分數和優先級
                    weighted_score = match_score * (1.0 / priority)  # 優先級越低分數越高
                    
                    if topic_name in topic_scores:
                        topic_scores[topic_name] += weighted_score
                    else:
                        topic_scores[topic_name] = weighted_score
        
        # 過濾並排序結果
        min_confidence = self.mapping_rules['min_confidence_score']
        max_topics = self.mapping_rules['max_topics_per_keyword']
        
        filtered_topics = [(topic, score) for topic, score in topic_scores.items() 
                          if score >= min_confidence]
        
        # 按分數排序
        filtered_topics.sort(key=lambda x: x[1], reverse=True)
        
        # 限制結果數量
        result = filtered_topics[:max_topics]
        
        # 如果沒有匹配結果，返回預設topic
        if not result:
            result = [(self.mapping_rules['default_topic'], 0.5)]
        
        return result
    
    def _calculate_match_score(self, user_keyword: str, topic_keywords: List[str]) -> float:
        """計算用戶關鍵字與topic關鍵字的匹配分數"""
        user_keyword_lower = user_keyword.lower()
        max_score = 0
        
        for topic_keyword in topic_keywords:
            topic_keyword_lower = topic_keyword.lower()
            
            # 精確匹配
            if user_keyword_lower == topic_keyword_lower:
                score = self.mapping_rules['exact_match_weight']
            # 包含匹配
            elif user_keyword_lower in topic_keyword_lower or topic_keyword_lower in user_keyword_lower:
                score = self.mapping_rules['partial_match_weight']
            else:
                score = 0
            
            max_score = max(max_score, score)
        
        return max_score
    
    def _is_excluded_keyword(self, keyword: str) -> bool:
        """檢查關鍵字是否應該被排除"""
        keyword_lower = keyword.lower()
        
        for pattern in self.exclusion_patterns:
            if pattern.lower() in keyword_lower:
                return True
        
        return False
    
    def get_topics_for_user_subscription(self, subscription: Dict[str, Any]) -> List[str]:
        """
        為用戶訂閱獲取相關的Topics列表
        
        Args:
            subscription: 用戶訂閱資料，包含keywords欄位
            
        Returns:
            推薦的topics列表
        """
        user_keywords = subscription.get('keywords', [])
        
        if not user_keywords:
            # 如果沒有關鍵字，返回熱門topics
            return ['latest', 'tech', 'crypto']
        
        # 映射到topics
        topic_matches = self.map_keywords_to_topics(user_keywords)
        
        # 提取topic名稱
        recommended_topics = [topic for topic, score in topic_matches]
        
        # 確保至少有一個topic
        if not recommended_topics:
            recommended_topics = ['latest']
        
        return recommended_topics
    
    def explain_mapping(self, user_keywords: List[str]) -> Dict[str, Any]:
        """
        解釋映射結果，用於調試和用戶查看
        
        Args:
            user_keywords: 用戶關鍵字列表
            
        Returns:
            詳細的映射解釋
        """
        topic_matches = self.map_keywords_to_topics(user_keywords)
        
        explanation = {
            'input_keywords': user_keywords,
            'mapped_topics': topic_matches,
            'mapping_details': {},
            'excluded_keywords': []
        }
        
        for keyword in user_keywords:
            if self._is_excluded_keyword(keyword):
                explanation['excluded_keywords'].append(keyword)
                continue
            
            keyword_matches = []
            for topic_name, topic_config in self.topics_mapping.items():
                score = self._calculate_match_score(keyword, topic_config['keywords'])
                if score > 0:
                    keyword_matches.append({
                        'topic': topic_name,
                        'score': score,
                        'priority': topic_config.get('priority', 10),
                        'matched_keywords': [tk for tk in topic_config['keywords'] 
                                           if keyword.lower() in tk.lower() or tk.lower() in keyword.lower()]
                    })
            
            explanation['mapping_details'][keyword] = keyword_matches
        
        return explanation

# 創建全域實例
topics_mapper = TopicsMapper()

def main():
    """測試映射功能"""
    test_cases = [
        ['bitcoin', 'crypto'],
        ['apple', 'tesla', 'ai'],
        ['房地產', '股票'],
        ['最新', '新聞'],
        []  # 空關鍵字
    ]
    
    print("=" * 60)
    print("Topics Keyword Mapping Test")
    print("=" * 60)
    
    for i, keywords in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {keywords}")
        print("-" * 30)
        
        # 獲取映射結果
        topics = topics_mapper.map_keywords_to_topics(keywords)
        print(f"Mapped Topics: {topics}")
        
        # 獲取詳細解釋
        explanation = topics_mapper.explain_mapping(keywords)
        print(f"Details: {explanation['mapping_details']}")
        
        if explanation['excluded_keywords']:
            print(f"Excluded: {explanation['excluded_keywords']}")

if __name__ == "__main__":
    main()