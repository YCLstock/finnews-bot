#!/usr/bin/env python3
"""
增強版Topics映射器
整合語義聚類和用戶引導功能
"""

from typing import List, Dict, Any, Tuple
import logging
from core.topics_mapper import TopicsMapper
from core.semantic_clustering import get_clustering_instance
from core.user_guidance import get_guidance_instance

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedTopicsMapper(TopicsMapper):
    """增強版Topics映射器，整合聚類和引導功能"""
    
    def __init__(self, config_file: str = None):
        super().__init__(config_file)
        self.clustering = get_clustering_instance()
        self.guidance = get_guidance_instance()
        
        # 增強配置
        self.enhanced_config = {
            'enable_clustering': True,
            'enable_guidance': True,
            'auto_optimize': True,
            'focus_threshold': 0.6,
            'max_topics_per_user': 3,
            'min_confidence_score': 0.3
        }
        
        logger.info("Enhanced Topics Mapper initialized")
    
    def enhanced_map_keywords_to_topics(self, user_keywords: List[str], 
                                      user_id: str = None) -> Dict[str, Any]:
        """
        增強版關鍵字到Topics映射
        包含聚類分析和優化建議
        """
        logger.info(f"Enhanced mapping for user {user_id} with keywords: {user_keywords}")
        
        if not user_keywords:
            return self._handle_empty_keywords(user_id)
        
        try:
            # 1. 執行語義聚類分析
            clustering_result = None
            if self.enhanced_config['enable_clustering']:
                clustering_result = self.clustering.cluster_keywords(user_keywords)
                logger.info(f"Clustering completed with focus score: {clustering_result.get('focus_score', 0)}")
            
            # 2. 基於聚類結果優化關鍵字映射
            optimized_keywords = self._optimize_keywords_with_clustering(
                user_keywords, clustering_result
            )
            
            # 3. 執行標準Topics映射
            topics_mapping = self.map_keywords_to_topics(optimized_keywords)
            
            # 4. 應用增強邏輯限制Topics數量
            topics_mapping = self._apply_enhanced_filtering(topics_mapping, clustering_result)
            
            # 5. 生成用戶引導建議
            guidance_suggestions = None
            if self.enhanced_config['enable_guidance'] and user_id:
                try:
                    guidance_analysis = self.guidance.analyze_user_keywords(user_id, user_keywords)
                    guidance_suggestions = guidance_analysis.get('guidance')
                except Exception as e:
                    logger.warning(f"Guidance analysis failed: {e}")
            
            # 6. 組合結果
            enhanced_result = {
                'original_keywords': user_keywords,
                'optimized_keywords': optimized_keywords,
                'topics_mapping': topics_mapping,
                'clustering_analysis': clustering_result,
                'guidance_suggestions': guidance_suggestions,
                'optimization_applied': optimized_keywords != user_keywords,
                'focus_score': clustering_result['focus_score'] if clustering_result else None,
                'enhancement_metadata': {
                    'clustering_enabled': self.enhanced_config['enable_clustering'],
                    'guidance_enabled': self.enhanced_config['enable_guidance'],
                    'auto_optimization': self.enhanced_config['auto_optimize']
                }
            }
            
            # 7. 自動優化（如果啟用且需要）
            if (self.enhanced_config['auto_optimize'] and 
                clustering_result and 
                clustering_result['focus_score'] < self.enhanced_config['focus_threshold']):
                
                auto_optimized = self._auto_optimize_keywords(clustering_result)
                enhanced_result['auto_optimization'] = auto_optimized
                logger.info("Auto-optimization applied")
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Enhanced mapping failed: {e}")
            return self._fallback_mapping(user_keywords, user_id)
    
    def _optimize_keywords_with_clustering(self, keywords: List[str], 
                                         clustering_result: Dict[str, Any]) -> List[str]:
        """基於聚類結果優化關鍵字"""
        if not clustering_result:
            return keywords
        
        clusters = clustering_result['clusters']
        focus_score = clustering_result['focus_score']
        
        # 如果聚焦度已經很好，不需要優化
        if focus_score >= 0.8:
            return keywords
        
        # 優化策略：保留最大的群組，合併小群組
        optimized = []
        
        try:
            # 找出最大的群組
            largest_cluster = max(clusters, key=len) if clusters else []
            if len(largest_cluster) >= 2:
                optimized.extend(largest_cluster)
            
            # 處理其他群組
            remaining_clusters = [c for c in clusters if c != largest_cluster]
            for cluster in remaining_clusters:
                if len(cluster) >= 2:
                    # 保留中等大小的群組
                    optimized.extend(cluster[:2])  # 限制每個群組最多2個關鍵字
                else:
                    # 單一關鍵字：如果與主群組相關則保留
                    if self._is_related_to_main_cluster(cluster[0], largest_cluster):
                        optimized.extend(cluster)
            
            # 確保不超過最大限制
            if len(optimized) > 5:
                optimized = optimized[:5]
            
            logger.info(f"Optimized keywords: {keywords} -> {optimized}")
            return optimized if optimized else keywords
            
        except Exception as e:
            logger.warning(f"Keyword optimization failed: {e}")
            return keywords
    
    def _is_related_to_main_cluster(self, keyword: str, main_cluster: List[str]) -> bool:
        """判斷關鍵字是否與主群組相關"""
        if not main_cluster:
            return True
        
        # 不再使用本地模型進行語義相似度判斷
        # 只使用簡單字符匹配作為備用
        
        # 備用方案：簡單字符匹配
        keyword_lower = keyword.lower()
        for cluster_kw in main_cluster:
            if (keyword_lower in cluster_kw.lower() or 
                cluster_kw.lower() in keyword_lower):
                return True
        
        return False
    
    def _apply_enhanced_filtering(self, topics_mapping: List[Tuple[str, float]], 
                                clustering_result: Dict[str, Any]) -> List[Tuple[str, float]]:
        """應用增強過濾邏輯"""
        if not topics_mapping:
            return [(self.mapping_rules['default_topic'], 1.0)]
        
        # 限制Topics數量
        max_topics = self.enhanced_config['max_topics_per_user']
        filtered_topics = topics_mapping[:max_topics]
        
        # 調整信心分數（基於聚類結果）
        if clustering_result:
            focus_score = clustering_result.get('focus_score', 0.5)
            adjusted_topics = []
            
            for topic, score in filtered_topics:
                # 聚焦度高的話，提高信心分數
                adjusted_score = score * (0.5 + 0.5 * focus_score)
                adjusted_topics.append((topic, min(adjusted_score, 1.0)))
            
            filtered_topics = adjusted_topics
        
        # 過濾低信心分數的Topics
        min_confidence = self.enhanced_config['min_confidence_score']
        final_topics = [(topic, score) for topic, score in filtered_topics 
                       if score >= min_confidence]
        
        # 確保至少有一個Topic
        if not final_topics:
            final_topics = [(self.mapping_rules['default_topic'], 0.5)]
        
        return final_topics
    
    def _auto_optimize_keywords(self, clustering_result: Dict[str, Any]) -> Dict[str, Any]:
        """自動優化關鍵字建議"""
        clusters = clustering_result['clusters']
        suggestions = clustering_result['suggestions']
        
        # 生成自動優化建議
        auto_optimization = {
            'type': 'auto_focus',
            'original_clusters': clusters,
            'recommended_action': None,
            'suggested_keywords': [],
            'reason': ''
        }
        
        # 找出最佳聚焦策略
        main_clusters = [c for c in clusters if len(c) > 1]
        
        if main_clusters:
            # 建議聚焦於最大的群組
            largest_cluster = max(main_clusters, key=len)
            auto_optimization['recommended_action'] = 'focus_on_main_cluster'
            auto_optimization['suggested_keywords'] = largest_cluster
            auto_optimization['reason'] = f'聚焦於「{", ".join(largest_cluster)}」相關投資以獲得更精準的新聞'
        
        elif len(clusters) > 3:
            # 太多分散的關鍵字，建議重新選擇
            auto_optimization['recommended_action'] = 'restart_selection'
            auto_optimization['reason'] = '關鍵字過於分散，建議重新選擇2-3個主要關注領域'
        
        else:
            # 保持現狀但建議添加相關關鍵字
            auto_optimization['recommended_action'] = 'add_related_keywords'
            auto_optimization['reason'] = '建議添加相關關鍵字以增強新聞推送的完整性'
        
        return auto_optimization
    
    def _handle_empty_keywords(self, user_id: str) -> Dict[str, Any]:
        """處理空關鍵字情況"""
        return {
            'original_keywords': [],
            'optimized_keywords': [],
            'topics_mapping': [(self.mapping_rules['default_topic'], 1.0)],
            'clustering_analysis': None,
            'guidance_suggestions': {
                'type': 'setup_required',
                'title': '設定投資關注領域',
                'message': '請添加您感興趣的投資關鍵字以開始個人化新聞推送',
                'action': 'start_onboarding',
                'icon': '🚀'
            },
            'optimization_applied': False,
            'focus_score': 0.0,
            'enhancement_metadata': {
                'status': 'empty_keywords',
                'requires_setup': True
            }
        }
    
    def _fallback_mapping(self, keywords: List[str], user_id: str) -> Dict[str, Any]:
        """備用映射邏輯"""
        logger.warning("Using fallback mapping")
        
        # 使用基礎Topics映射
        basic_mapping = self.map_keywords_to_topics(keywords)
        
        return {
            'original_keywords': keywords,
            'optimized_keywords': keywords,
            'topics_mapping': basic_mapping,
            'clustering_analysis': {
                'clusters': [keywords],
                'focus_score': 0.5,
                'primary_topics': [topic for topic, score in basic_mapping],
                'method': 'fallback'
            },
            'guidance_suggestions': {
                'type': 'basic_setup',
                'message': '基礎設定已完成，建議完成完整引導以獲得更好體驗',
                'action': 'consider_onboarding'
            },
            'optimization_applied': False,
            'focus_score': 0.5,
            'enhancement_metadata': {
                'status': 'fallback_mode',
                'clustering_failed': True
            }
        }
    
    def get_topics_for_user_subscription_enhanced(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """
        為用戶訂閱獲取增強版Topics列表
        包含優化建議和聚類分析
        """
        user_id = subscription.get('user_id')
        user_keywords = subscription.get('keywords', [])
        
        logger.info(f"Getting enhanced topics for user {user_id}")
        
        # 執行增強映射
        enhanced_mapping = self.enhanced_map_keywords_to_topics(user_keywords, user_id)
        
        # 提取Topics列表
        topics_mapping = enhanced_mapping['topics_mapping']
        recommended_topics = [topic for topic, score in topics_mapping]
        
        # 檢查是否需要優化
        focus_score = enhanced_mapping.get('focus_score', 0.5)
        needs_optimization = focus_score < self.enhanced_config['focus_threshold']
        
        # 組合完整結果
        result = {
            'user_id': user_id,
            'recommended_topics': recommended_topics,
            'topics_with_scores': topics_mapping,
            'enhancement_data': enhanced_mapping,
            'needs_optimization': needs_optimization,
            'optimization_priority': self._calculate_optimization_priority(enhanced_mapping),
            'user_experience_score': self._calculate_user_experience_score(enhanced_mapping)
        }
        
        return result
    
    def _calculate_optimization_priority(self, enhanced_mapping: Dict[str, Any]) -> str:
        """計算優化優先級"""
        focus_score = enhanced_mapping.get('focus_score', 0.5)
        
        if focus_score < 0.3:
            return 'high'
        elif focus_score < 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_user_experience_score(self, enhanced_mapping: Dict[str, Any]) -> float:
        """計算用戶體驗分數"""
        focus_score = enhanced_mapping.get('focus_score', 0.5)
        optimization_applied = enhanced_mapping.get('optimization_applied', False)
        has_guidance = enhanced_mapping.get('guidance_suggestions') is not None
        
        # 基礎分數來自聚焦度
        base_score = focus_score
        
        # 如果應用了優化，加分
        if optimization_applied:
            base_score += 0.1
        
        # 如果有引導建議，加分
        if has_guidance:
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def get_optimization_suggestions_for_user(self, user_id: str) -> Dict[str, Any]:
        """為特定用戶獲取優化建議"""
        try:
            from core.database import db_manager
            
            # 獲取用戶訂閱
            subscription = db_manager.supabase.table('subscriptions').select('*').eq('user_id', user_id).single().execute()
            
            if not subscription.data:
                return {'error': 'User not found'}
            
            # 獲取增強Topics
            enhanced_result = self.get_topics_for_user_subscription_enhanced(subscription.data)
            
            # 提取優化建議
            suggestions = enhanced_result['enhancement_data'].get('guidance_suggestions', {})
            auto_optimization = enhanced_result['enhancement_data'].get('auto_optimization', {})
            
            return {
                'user_id': user_id,
                'current_focus_score': enhanced_result['enhancement_data'].get('focus_score', 0.5),
                'optimization_priority': enhanced_result['optimization_priority'],
                'user_experience_score': enhanced_result['user_experience_score'],
                'guidance_suggestions': suggestions,
                'auto_optimization': auto_optimization,
                'recommended_actions': self._generate_recommended_actions(enhanced_result)
            }
            
        except Exception as e:
            logger.error(f"Error getting optimization suggestions for user {user_id}: {e}")
            return {'error': str(e)}
    
    def _generate_recommended_actions(self, enhanced_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成推薦行動"""
        actions = []
        
        optimization_priority = enhanced_result['optimization_priority']
        focus_score = enhanced_result['enhancement_data'].get('focus_score', 0.5)
        
        if optimization_priority == 'high':
            actions.append({
                'type': 'urgent_optimization',
                'title': '立即優化關鍵字設定',
                'description': f'您的關鍵字聚焦度較低 ({focus_score:.1%})，強烈建議重新設定',
                'action': 'restart_onboarding',
                'priority': 'high'
            })
        elif optimization_priority == 'medium':
            actions.append({
                'type': 'moderate_optimization',
                'title': '建議優化關鍵字設定',
                'description': f'優化您的關鍵字設定可提升新聞推送的相關性',
                'action': 'optimize_keywords',
                'priority': 'medium'
            })
        
        return actions

# 創建全域實例
_enhanced_mapper_instance = None

def get_enhanced_mapper_instance():
    """獲取全域增強映射器實例"""
    global _enhanced_mapper_instance
    if _enhanced_mapper_instance is None:
        _enhanced_mapper_instance = EnhancedTopicsMapper()
    return _enhanced_mapper_instance