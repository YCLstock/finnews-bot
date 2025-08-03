#!/usr/bin/env python3
"""
智能語義聚類系統
基於語義相似度自動聚類用戶關鍵字
"""

import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Tuple, Optional
import json
from pathlib import Path
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemanticKeywordClustering:
    """語義關鍵字聚類系統"""
    
    def __init__(self, use_openai_embeddings: bool = True):
        """初始化聚類系統"""
        self.use_openai = use_openai_embeddings
        self.model = None
        
        # 檢查 OpenAI API Key
        if self.use_openai:
            import os
            self.openai_api_key = os.environ.get('OPENAI_API_KEY')
            if self.openai_api_key:
                logger.info("Using OpenAI Embeddings API for semantic clustering")
            else:
                logger.warning("OpenAI API key not found, falling back to rule-based clustering")
                self.use_openai = False
        
        # 不再使用本地模型，只保留 OpenAI API + 規則備用
        self.model = None
        
        # 初始化中英文語義對應字典
        self.load_semantic_mappings()
        self.load_topic_embeddings()
        
        # 聚類參數
        self.config = {
            'min_cluster_size': 2,
            'max_clusters': 3,
            'similarity_threshold': 0.7,
            'focus_threshold': 0.8  # 聚焦度閾值
        }
    
    def load_semantic_mappings(self):
        """載入中英文語義對應字典"""
        self.semantic_mappings = {
            # 科技類
            'AI': ['AI', 'ai', '人工智慧', '人工智能', 'artificial intelligence', 'machine learning', '機器學習'],
            '蘋果': ['蘋果', '苹果', 'Apple', 'AAPL', 'apple'],
            '微軟': ['微軟', '微软', 'Microsoft', 'MSFT', 'microsoft'],
            '谷歌': ['谷歌', '穀歌', 'Google', 'GOOGL', 'Alphabet', 'google'],
            '特斯拉': ['特斯拉', '特斯拉', 'Tesla', 'TSLA', 'tesla'],
            
            # 加密貨幣類
            '比特幣': ['比特幣', '比特币', 'Bitcoin', 'BTC', 'bitcoin'],
            '以太坊': ['以太坊', '以太坊', 'Ethereum', 'ETH', 'ethereum'],
            '加密貨幣': ['加密貨幣', '加密货币', 'cryptocurrency', 'crypto', '數字貨幣', '数字货币'],
            '區塊鏈': ['區塊鏈', '区块链', 'blockchain', 'block chain'],
            
            # 股市類
            '股票': ['股票', '股市', 'stock', 'stocks', 'equity', 'share'],
            '市場': ['市場', '市场', 'market', 'markets'],
            '交易': ['交易', '贸易', 'trading', 'trade', 'transaction'],
            '投資': ['投資', '投资', 'investment', 'investing', 'invest'],
            
            # 經濟類
            '經濟': ['經濟', '经济', 'economy', 'economic', 'economics'],
            '通膨': ['通膨', '通胀', 'inflation', '通貨膨脹', '通货膨胀'],
            '利率': ['利率', '利息', 'interest rate', 'rate', 'rates'],
            '聯準會': ['聯準會', '联准会', 'Fed', 'Federal Reserve', 'FED'],
            
            # 房地產類
            '房地產': ['房地產', '房地产', 'real estate', 'property', 'housing', '房價', '房价'],
            
            # 能源類
            '電動車': ['電動車', '电动车', 'electric vehicle', 'EV', 'electric car'],
            '能源': ['能源', '电力', 'energy', 'power', '綠能', '绿能'],
        }
        
        # 創建反向映射（從關鍵字到標準化名稱）
        self.keyword_to_standard = {}
        for standard_name, variations in self.semantic_mappings.items():
            for variation in variations:
                self.keyword_to_standard[variation.lower()] = standard_name

    def normalize_keywords(self, keywords: List[str]) -> List[str]:
        """標準化關鍵字，將語義相同的中英文詞彙統一"""
        normalized = []
        processed_standards = set()
        standard_groups = {}  # 用於收集屬於同一標準化名稱的所有關鍵字
        
        # 第一步：收集所有語義相同的關鍵字
        for keyword in keywords:
            keyword_lower = keyword.lower().strip()
            standard_name = self.keyword_to_standard.get(keyword_lower)
            
            if standard_name:
                if standard_name not in standard_groups:
                    standard_groups[standard_name] = []
                standard_groups[standard_name].append(keyword)
            else:
                # 沒有對應的標準化名稱，直接添加
                normalized.append(keyword)
        
        # 第二步：為每個標準化群組創建合併的關鍵字
        for standard_name, group_keywords in standard_groups.items():
            if len(group_keywords) == 1:
                # 只有一個關鍵字，直接使用
                normalized.append(group_keywords[0])
            else:
                # 多個語義相同的關鍵字，進行合併顯示
                # 選擇最常見或最標準的作為主要顯示，其他作為補充
                primary_keyword = group_keywords[0]
                other_keywords = group_keywords[1:]
                
                # 如果有中文，優先顯示中文；如果有英文全稱，優先顯示全稱
                for kw in group_keywords:
                    if any('\u4e00' <= char <= '\u9fff' for char in kw):  # 包含中文字符
                        primary_keyword = kw
                        other_keywords = [k for k in group_keywords if k != kw]
                        break
                
                if len(other_keywords) > 0:
                    combined = f"{primary_keyword} (包含: {', '.join(other_keywords)})"
                    normalized.append(combined)
                else:
                    normalized.append(primary_keyword)
        
        return normalized
    
    def load_topic_embeddings(self):
        """預計算Topics的語義向量"""
        topics_descriptions = {
            'crypto': 'cryptocurrency bitcoin ethereum blockchain digital currency',
            'tech': 'technology artificial intelligence apple microsoft google software',
            'electric-vehicles': 'electric vehicle tesla ev battery clean energy',
            'stock-market': 'stock market trading investment wall street',
            'earnings': 'earnings financial report quarterly profit revenue',
            'housing': 'real estate housing property mortgage rent',
            'inflation': 'inflation monetary policy federal reserve interest rate',
            'economies': 'economy economic gdp unemployment economic growth',
            'mergers-ipos': 'merger acquisition ipo public offering takeover',
            'tariff-updates': 'tariff trade war import export customs',
            'originals': 'analysis opinion exclusive interview research',
            'latest': 'breaking news latest update urgent alert'
        }
        
        self.topic_embeddings = {}
        self.topics_descriptions = topics_descriptions
        
        # 預計算 topic embeddings
        if self.use_openai and self.openai_api_key:
            try:
                descriptions_list = list(topics_descriptions.values())
                embeddings = self._get_openai_embeddings(descriptions_list)
                for i, topic in enumerate(topics_descriptions.keys()):
                    self.topic_embeddings[topic] = embeddings[i]
                logger.info(f"Precomputed OpenAI embeddings for {len(self.topic_embeddings)} topics")
            except Exception as e:
                logger.error(f"Failed to precompute OpenAI topic embeddings: {e}")
                self.topic_embeddings = {}
        
        # 備用：基於關鍵字的Topic映射
        self.fallback_topic_keywords = {
            'crypto': ['bitcoin', 'crypto', 'blockchain', '比特幣', '加密貨幣', '區塊鏈'],
            'tech': ['apple', 'microsoft', 'google', 'ai', '蘋果', '微軟', '人工智慧', '科技'],
            'electric-vehicles': ['tesla', 'electric', 'ev', '特斯拉', '電動車', '電動'],
            'stock-market': ['stock', 'market', 'trading', '股票', '股市', '交易'],
            'earnings': ['earnings', 'profit', 'revenue', '財報', '營收', '獲利'],
            'housing': ['house', 'real estate', 'property', '房地產', '房價', '房屋'],
            'inflation': ['inflation', 'fed', 'interest rate', '通膨', '利率', '聯準會'],
            'economies': ['economy', 'gdp', 'economic', '經濟', '景氣'],
            'mergers-ipos': ['merger', 'acquisition', 'ipo', '併購', '收購', '上市'],
            'tariff-updates': ['tariff', 'trade war', 'import', '關稅', '貿易戰'],
            'originals': ['analysis', 'opinion', 'research', '分析', '評論', '研究'],
            'latest': ['news', 'update', 'breaking', '新聞', '最新', '即時']
        }
    
    def cluster_keywords(self, keywords: List[str]) -> Dict[str, Any]:
        """
        對關鍵字進行語義聚類
        
        Returns:
            Dict containing clusters, focus_score, primary_topics
        """
        if len(keywords) <= 1:
            return self._single_keyword_result(keywords)
        
        # 預處理：標準化中英文語義相同的關鍵字
        original_keywords = keywords.copy()
        normalized_keywords = self.normalize_keywords(keywords)
        
        logger.info(f"原始關鍵字: {original_keywords}")
        logger.info(f"標準化後: {normalized_keywords}")
        
        try:
            if self.use_openai:
                result = self._openai_semantic_clustering(normalized_keywords)
                # 在結果中保留原始關鍵字信息
                result['original_keywords'] = original_keywords
                result['normalized_keywords'] = normalized_keywords
                return result
            else:
                result = self._fallback_clustering(normalized_keywords)
                result['original_keywords'] = original_keywords
                result['normalized_keywords'] = normalized_keywords
                return result
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            result = self._fallback_clustering(normalized_keywords)
            result['original_keywords'] = original_keywords
            result['normalized_keywords'] = normalized_keywords
            return result
    
    
    def _openai_semantic_clustering(self, keywords: List[str]) -> Dict[str, Any]:
        """使用 OpenAI Embeddings API 進行語義聚類"""
        try:
            # 1. 生成關鍵字的語義向量
            keyword_embeddings = self._get_openai_embeddings(keywords)
            
            # 2. 計算相似度矩陣
            similarity_matrix = cosine_similarity(keyword_embeddings)
            
            # 3. 執行聚類
            clusters = self._perform_clustering(keywords, keyword_embeddings, similarity_matrix)
            
            # 4. 計算聚焦度評分
            focus_score = self._calculate_focus_score(similarity_matrix, clusters)
            
            # 5. 映射到Topics
            primary_topics = self._map_clusters_to_topics_semantic(clusters, keyword_embeddings)
            
            # 6. 生成建議
            suggestions = self._generate_clustering_suggestions(clusters, focus_score)
            
            return {
                'clusters': clusters,
                'focus_score': focus_score,
                'primary_topics': primary_topics,
                'suggestions': suggestions,
                'similarity_matrix': similarity_matrix.tolist(),
                'method': 'openai_semantic_clustering'
            }
            
        except Exception as e:
            logger.error(f"OpenAI semantic clustering failed: {e}, falling back to rule-based clustering")
            return self._fallback_clustering(keywords)
    
    def _get_openai_embeddings(self, texts: List[str]) -> np.ndarray:
        """使用 OpenAI API 獲取文本向量"""
        import requests
        import json
        
        headers = {
            'Authorization': f'Bearer {self.openai_api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'input': texts,
            'model': 'text-embedding-ada-002'
        }
        
        try:
            response = requests.post(
                'https://api.openai.com/v1/embeddings',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                embeddings = [item['embedding'] for item in result['data']]
                return np.array(embeddings)
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                raise Exception(f"OpenAI API returned status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error calling OpenAI API: {e}")
            raise Exception("Failed to connect to OpenAI API")
        except Exception as e:
            logger.error(f"Error processing OpenAI API response: {e}")
            raise
    
    def _fallback_clustering(self, keywords: List[str]) -> Dict[str, Any]:
        """備用聚類方法（基於關鍵字匹配）"""
        logger.info("Using fallback clustering method")
        
        # 基於Topics關鍵字進行分組
        topic_groups = {}
        unassigned = []
        
        # 先檢查是否有標準化處理過的關鍵字
        for keyword in keywords:
            assigned = False
            keyword_lower = keyword.lower()
            
            # 提取主要關鍵字（如果是合併格式的話）
            main_keyword = keyword.split(' (包含:')[0] if '(包含:' in keyword else keyword
            main_keyword_lower = main_keyword.lower()
            
            for topic, topic_keywords in self.fallback_topic_keywords.items():
                for topic_kw in topic_keywords:
                    if (topic_kw.lower() in main_keyword_lower or 
                        main_keyword_lower in topic_kw.lower() or
                        topic_kw.lower() in keyword_lower or 
                        keyword_lower in topic_kw.lower()):
                        if topic not in topic_groups:
                            topic_groups[topic] = []
                        topic_groups[topic].append(keyword)
                        assigned = True
                        break
                if assigned:
                    break
            
            if not assigned:
                unassigned.append(keyword)
        
        # 組織聚類結果
        clusters = list(topic_groups.values())
        for kw in unassigned:
            clusters.append([kw])
        
        # 計算聚焦度（簡化版）
        if len(clusters) == 1:
            focus_score = 0.8
        elif len(clusters) <= 2:
            focus_score = 0.6
        else:
            focus_score = 0.3
        
        # 映射到Topics
        primary_topics = list(topic_groups.keys())
        if unassigned and len(primary_topics) == 0:
            primary_topics = ['latest']
        
        suggestions = self._generate_clustering_suggestions(clusters, focus_score)
        
        return {
            'clusters': clusters,
            'focus_score': focus_score,
            'primary_topics': primary_topics,
            'suggestions': suggestions,
            'method': 'fallback_clustering'
        }
    
    def _perform_clustering(self, keywords: List[str], embeddings: np.ndarray, 
                          similarity_matrix: np.ndarray) -> List[List[str]]:
        """執行實際的聚類算法"""
        n_keywords = len(keywords)
        
        if n_keywords <= 2:
            # 少於3個關鍵字，基於相似度分組
            avg_similarity = np.mean(similarity_matrix[np.triu_indices(n_keywords, k=1)])
            if avg_similarity > self.config['similarity_threshold']:
                return [keywords]  # 單一群組
            else:
                return [[kw] for kw in keywords]  # 各自獨立
        
        # 使用DBSCAN進行聚類
        clustering = DBSCAN(
            eps=1-self.config['similarity_threshold'],  # 距離閾值
            min_samples=self.config['min_cluster_size'],
            metric='precomputed'
        )
        
        # 將相似度矩陣轉換為距離矩陣
        distance_matrix = 1 - similarity_matrix
        cluster_labels = clustering.fit_predict(distance_matrix)
        
        # 組織聚類結果
        clusters = []
        clustered_keywords = set()
        
        for label in set(cluster_labels):
            if label == -1:  # 噪音點
                continue
            cluster_keywords = [keywords[i] for i in range(len(keywords)) 
                              if cluster_labels[i] == label]
            if len(cluster_keywords) >= self.config['min_cluster_size']:
                clusters.append(cluster_keywords)
                clustered_keywords.update(cluster_keywords)
        
        # 處理未聚類的關鍵字
        unclustered = [kw for kw in keywords if kw not in clustered_keywords]
        for kw in unclustered:
            clusters.append([kw])
        
        return clusters
    
    def _calculate_focus_score(self, similarity_matrix: np.ndarray, 
                             clusters: List[List[str]]) -> float:
        """計算聚焦度評分 (0-1, 1為最聚焦)"""
        if len(clusters) == 1:
            # 所有關鍵字在同一群組，計算內部相似度
            cluster_size = len(clusters[0])
            if cluster_size <= 1:
                return 1.0
            
            # 計算群組內平均相似度
            intra_similarity = np.mean(similarity_matrix[np.triu_indices(cluster_size, k=1)])
            return min(intra_similarity, 1.0)
        
        # 多個群組，聚焦度 = 1 / 群組數量 * 內部聚合度
        num_clusters = len([c for c in clusters if len(c) > 1])
        base_score = 1.0 / max(num_clusters, 1)
        
        # 考慮群組內聚合度
        if num_clusters > 0 and similarity_matrix.shape[0] > 1:
            try:
                cluster_coherence_scores = []
                for cluster in clusters:
                    if len(cluster) > 1:
                        indices = [i for i, kw in enumerate(clusters[0]) if kw in cluster]
                        if len(indices) > 1:
                            cluster_sim = similarity_matrix[np.ix_(indices, indices)]
                            coherence = np.mean(cluster_sim[np.triu_indices(len(indices), k=1)])
                            cluster_coherence_scores.append(coherence)
                
                if cluster_coherence_scores:
                    cluster_coherence = np.mean(cluster_coherence_scores)
                    base_score *= cluster_coherence
            except:
                # 如果計算失敗，使用基礎分數
                pass
        
        return min(base_score, 1.0)
    
    def _map_clusters_to_topics_semantic(self, clusters: List[List[str]], 
                                       keyword_embeddings: np.ndarray) -> List[str]:
        """將聚類映射到Topics（語義版本）"""
        primary_topics = []
        
        for cluster in clusters:
            if len(cluster) == 0:
                continue
                
            # 計算群組的中心向量
            cluster_indices = [i for i, kw in enumerate(cluster)]
            if len(cluster_indices) == 0:
                continue
                
            cluster_embedding = np.mean(keyword_embeddings[cluster_indices], axis=0)
            
            # 計算與各Topics的相似度
            topic_similarities = {}
            for topic, topic_embedding in self.topic_embeddings.items():
                similarity = cosine_similarity([cluster_embedding], [topic_embedding])[0][0]
                topic_similarities[topic] = similarity
            
            # 選擇最相似的Topic
            if topic_similarities:
                best_topic = max(topic_similarities, key=topic_similarities.get)
                if topic_similarities[best_topic] > 0.5:  # 相似度閾值
                    primary_topics.append(best_topic)
        
        return list(set(primary_topics))  # 去重
    
    def _generate_clustering_suggestions(self, clusters: List[List[str]], 
                                       focus_score: float) -> Dict[str, Any]:
        """生成聚類建議"""
        suggestions = {
            'type': 'clustering_analysis',
            'focus_score': focus_score,
            'recommendations': []
        }
        
        if focus_score >= self.config['focus_threshold']:
            suggestions['recommendations'].append({
                'type': 'excellent_focus',
                'message': f'您的關鍵字聚焦度很高 ({focus_score:.2f})，將為您提供高度相關的投資新聞',
                'action': 'maintain'
            })
        elif focus_score >= 0.5:
            suggestions['recommendations'].append({
                'type': 'moderate_focus', 
                'message': f'您的關鍵字覆蓋 {len(clusters)} 個主要領域，建議選擇最感興趣的1-2個領域',
                'action': 'optimize',
                'clusters': clusters
            })
        else:
            suggestions['recommendations'].append({
                'type': 'scattered_focus',
                'message': '您的關鍵字較為分散，建議聚焦於特定投資領域以獲得更精準的分析',
                'action': 'refocus',
                'suggested_clusters': [c for c in clusters if len(c) > 1]
            })
        
        return suggestions
    
    def _single_keyword_result(self, keywords: List[str]) -> Dict[str, Any]:
        """處理單一關鍵字的情況"""
        return {
            'clusters': [keywords] if keywords else [],
            'focus_score': 1.0,
            'primary_topics': self._map_single_keyword_to_topic(keywords[0] if keywords else ''),
            'suggestions': {
                'type': 'single_keyword',
                'recommendations': [{
                    'type': 'expand_keywords',
                    'message': '建議添加2-3個相關關鍵字以獲得更全面的投資洞察',
                    'action': 'expand'
                }]
            },
            'method': 'single_keyword'
        }
    
    def _map_single_keyword_to_topic(self, keyword: str) -> List[str]:
        """將單一關鍵字映射到Topic"""
        if not keyword:
            return ['latest']
        
        keyword_lower = keyword.lower()
        for topic, topic_keywords in self.fallback_topic_keywords.items():
            for topic_kw in topic_keywords:
                if (topic_kw.lower() in keyword_lower or 
                    keyword_lower in topic_kw.lower()):
                    return [topic]
        
        return ['latest']

# 創建全域實例（延遲初始化）
_clustering_instance = None

def get_clustering_instance():
    """獲取全域聚類實例"""
    global _clustering_instance
    if _clustering_instance is None:
        _clustering_instance = SemanticKeywordClustering()
    return _clustering_instance