#!/usr/bin/env python3
"""
用戶教育引導系統
幫助用戶優化關鍵字選擇，提升投資新聞的相關性
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json
import logging
from core.semantic_clustering import get_clustering_instance

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserGuidanceSystem:
    """用戶引導系統"""
    
    def __init__(self):
        self.clustering = get_clustering_instance()
        self.guidance_templates = self._load_guidance_templates()
    
    def _load_guidance_templates(self) -> Dict[str, Any]:
        """載入引導模板"""
        return {
            'onboarding': {
                'welcome': {
                    'title': '歡迎使用 FinNews-Bot！',
                    'subtitle': '讓我們幫您設定個人化的財經新聞推送',
                    'description': '通過幾個簡單問題，我們將為您量身定制最相關的投資洞察'
                },
                'investment_focus': {
                    'question': '您最感興趣的投資領域是什麼？',
                    'subtitle': '選擇1-2個主要領域以獲得更精準的新聞推送',
                    'options': [
                        {
                            'id': 'tech_innovation',
                            'name': '科技與創新',
                            'description': 'AI、電動車、半導體等前沿科技',
                            'keywords': ['AI', '人工智慧', '科技股', '創新', '半導體'],
                            'topics': ['tech', 'electric-vehicles'],
                            'icon': '💻'
                        },
                        {
                            'id': 'crypto_digital',
                            'name': '加密貨幣與數位資產', 
                            'description': '比特幣、以太幣、區塊鏈技術',
                            'keywords': ['比特幣', '加密貨幣', '區塊鏈', 'Bitcoin', 'Ethereum'],
                            'topics': ['crypto'],
                            'icon': '₿'
                        },
                        {
                            'id': 'traditional_markets',
                            'name': '傳統市場投資',
                            'description': '股市、房地產、債券等傳統資產',
                            'keywords': ['股票', '房地產', '股市', '投資', '債券'],
                            'topics': ['stock-market', 'housing'],
                            'icon': '📈'
                        },
                        {
                            'id': 'macro_economics',
                            'name': '總體經濟分析',
                            'description': '通膨、利率、經濟政策影響',
                            'keywords': ['通膨', '利率', '經濟政策', '聯準會', 'Fed'],
                            'topics': ['inflation', 'economies'],
                            'icon': '🏛️'
                        },
                        {
                            'id': 'corporate_events',
                            'name': '企業事件追蹤',
                            'description': '財報、併購、IPO等企業動態',
                            'keywords': ['財報', '併購', 'IPO', '企業', '季報'],
                            'topics': ['earnings', 'mergers-ipos'],
                            'icon': '🏢'
                        },
                        {
                            'id': 'mixed_portfolio',
                            'name': '多元化投資組合',
                            'description': '關注多個投資領域的綜合資訊',
                            'keywords': ['投資組合', '多元化', '資產配置'],
                            'topics': ['latest', 'stock-market'],
                            'icon': '🎯'
                        }
                    ]
                },
                'keyword_customization': {
                    'title': '自訂您的關鍵字',
                    'subtitle': '基於您的選擇，我們推薦以下關鍵字',
                    'description': '您可以調整、新增或移除關鍵字以獲得最符合需求的新聞推送',
                    'tips': [
                        '建議保持3-5個關鍵字以獲得最佳效果',
                        '相關的關鍵字將為您提供更連貫的投資洞察',
                        '您可以隨時回來修改這些設定'
                    ]
                }
            },
            'optimization': {
                'scattered_keywords': {
                    'title': '關鍵字優化建議',
                    'message': '我們發現您的關鍵字涵蓋多個不同領域，這可能導致新聞推送較為分散。',
                    'suggestion': '建議選擇1-2個最感興趣的領域，以獲得更深入的投資洞察。',
                    'icon': '🎯'
                },
                'single_keyword': {
                    'title': '擴展關鍵字建議',
                    'message': '您目前只有少量關鍵字，可能會錯過相關的投資機會。',
                    'suggestion': '建議在相同領域添加2-3個相關關鍵字，以獲得更全面的市場資訊。',
                    'icon': '📝'
                },
                'excellent_focus': {
                    'title': '關鍵字設定優秀！',
                    'message': '您的關鍵字聚焦度很高，將為您提供高度相關的投資新聞。',
                    'suggestion': '繼續保持當前設定，我們將為您推送最相關的財經資訊。',
                    'icon': '⭐'
                }
            }
        }
    
    def start_user_onboarding(self, user_id: str) -> Dict[str, Any]:
        """開始用戶引導流程"""
        logger.info(f"Starting onboarding for user: {user_id}")
        
        return {
            'user_id': user_id,
            'step': 'welcome',
            'progress': 1,
            'total_steps': 3,
            'content': self.guidance_templates['onboarding']['welcome'],
            'next_action': 'show_investment_focus'
        }
    
    def process_investment_focus_selection(self, user_id: str, 
                                         selected_options: List[str]) -> Dict[str, Any]:
        """處理投資領域選擇"""
        logger.info(f"Processing investment focus for user {user_id}: {selected_options}")
        
        if len(selected_options) > 2:
            return {
                'status': 'warning',
                'message': '建議選擇1-2個主要領域以獲得更聚焦的新聞推送',
                'step': 'investment_focus',
                'selected': selected_options,
                'suggestion': '選擇過多領域可能導致新聞推送過於分散，影響閱讀體驗'
            }
        
        if len(selected_options) == 0:
            return {
                'status': 'error',
                'message': '請至少選擇一個投資領域',
                'step': 'investment_focus'
            }
        
        # 基於選擇生成推薦關鍵字
        recommended_keywords = []
        recommended_topics = []
        selected_details = []
        
        for option_id in selected_options:
            option = next((opt for opt in self.guidance_templates['onboarding']['investment_focus']['options'] 
                          if opt['id'] == option_id), None)
            if option:
                recommended_keywords.extend(option['keywords'][:3])  # 限制每個領域3個關鍵字
                recommended_topics.extend(option['topics'])
                selected_details.append({
                    'id': option['id'],
                    'name': option['name'],
                    'description': option['description'],
                    'icon': option['icon']
                })
        
        return {
            'status': 'success',
            'step': 'keyword_customization',
            'progress': 2,
            'recommended_keywords': recommended_keywords,
            'recommended_topics': list(set(recommended_topics)),
            'selected_focus': selected_details,
            'customization_template': self.guidance_templates['onboarding']['keyword_customization']
        }
    
    def finalize_onboarding(self, user_id: str, final_keywords: List[str]) -> Dict[str, Any]:
        """完成用戶引導流程"""
        logger.info(f"Finalizing onboarding for user {user_id} with keywords: {final_keywords}")
        
        # 分析最終關鍵字
        analysis = self.analyze_user_keywords(user_id, final_keywords)
        
        # 保存引導完成狀態
        self._save_onboarding_completion(user_id, final_keywords, analysis)
        
        return {
            'status': 'completed',
            'step': 'finished',
            'progress': 3,
            'user_id': user_id,
            'final_keywords': final_keywords,
            'analysis': analysis,
            'message': '恭喜！您的個人化新聞推送已設定完成。',
            'next_steps': [
                '您將在每日推送時間收到相關的財經新聞',
                '可以隨時調整關鍵字設定',
                '根據您的閱讀習慣，我們會持續優化推送內容'
            ]
        }
    
    def analyze_user_keywords(self, user_id: str, keywords: List[str]) -> Dict[str, Any]:
        """分析用戶關鍵字並提供建議"""
        if not keywords:
            return self._handle_empty_keywords(user_id)
        
        try:
            # 執行語義聚類分析
            clustering_result = self.clustering.cluster_keywords(keywords)
            
            # 生成引導建議
            guidance = self._generate_guidance_from_clustering(clustering_result)
            
            # 保存分析結果
            self._save_clustering_analysis(user_id, keywords, clustering_result)
            
            return {
                'user_id': user_id,
                'original_keywords': keywords,
                'clustering_result': clustering_result,
                'guidance': guidance,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing keywords for user {user_id}: {e}")
            return self._fallback_analysis(user_id, keywords)
    
    def _generate_guidance_from_clustering(self, clustering_result: Dict[str, Any]) -> Dict[str, Any]:
        """根據聚類結果生成引導建議"""
        focus_score = clustering_result['focus_score']
        clusters = clustering_result['clusters']
        suggestions = clustering_result['suggestions']
        
        templates = self.guidance_templates['optimization']
        
        if focus_score >= 0.8:
            template = templates['excellent_focus']
            return {
                'type': 'excellent',
                'title': template['title'],
                'message': template['message'],
                'suggestion': template['suggestion'],
                'icon': template['icon'],
                'action': 'proceed',
                'optimization_needed': False,
                'focus_score': focus_score
            }
        elif focus_score >= 0.5:
            template = templates['scattered_keywords']
            return {
                'type': 'moderate',
                'title': template['title'],
                'message': f'{template["message"]} (聚焦度: {focus_score:.1%})',
                'suggestion': template['suggestion'],
                'icon': template['icon'],
                'suggestions': self._create_focus_suggestions(clusters),
                'action': 'optimize',
                'optimization_needed': True,
                'focus_score': focus_score
            }
        else:
            template = templates['scattered_keywords']
            return {
                'type': 'scattered',
                'title': '關鍵字過於分散',
                'message': f'您的關鍵字較為分散 (聚焦度: {focus_score:.1%})，建議聚焦於特定投資領域。',
                'suggestion': '建議重新選擇2-3個最感興趣的關鍵字，以獲得更精準的投資洞察。',
                'icon': '🎯',
                'suggestions': self._create_refocus_suggestions(clusters),
                'action': 'refocus',
                'optimization_needed': True,
                'focus_score': focus_score
            }
    
    def _create_focus_suggestions(self, clusters: List[List[str]]) -> List[Dict[str, Any]]:
        """創建聚焦建議"""
        suggestions = []
        
        # 找出最大的群組作為主要聚焦領域
        main_clusters = [c for c in clusters if len(c) > 1]
        
        if main_clusters:
            largest_cluster = max(main_clusters, key=len)
            suggestions.append({
                'type': 'focus_on_cluster',
                'title': f'專注於「{", ".join(largest_cluster)}」相關投資',
                'description': '這是您最關注的領域，專注於此將獲得更深入的分析',
                'recommended_keywords': largest_cluster,
                'confidence': 0.8,
                'action': 'replace_keywords'
            })
        
        # 建議合併相似的小群組
        small_clusters = [c for c in clusters if len(c) == 1]
        if len(small_clusters) >= 2:
            suggestions.append({
                'type': 'merge_similar',
                'title': '合併相關關鍵字',
                'description': '將相似的關鍵字組合成投資主題',
                'scattered_keywords': [kw for cluster in small_clusters for kw in cluster],
                'confidence': 0.6,
                'action': 'group_keywords'
            })
        
        return suggestions
    
    def _create_refocus_suggestions(self, clusters: List[List[str]]) -> List[Dict[str, Any]]:
        """創建重新聚焦建議"""
        return [
            {
                'type': 'choose_primary_focus',
                'title': '選擇主要投資領域',
                'description': '建議從以下群組中選擇1-2個作為主要關注領域',
                'cluster_options': [
                    {
                        'keywords': cluster,
                        'estimated_topic': self._estimate_cluster_topic(cluster),
                        'description': self._get_topic_description(self._estimate_cluster_topic(cluster))
                    } for cluster in clusters if len(cluster) >= 1
                ],
                'confidence': 0.9,
                'action': 'restart_selection'
            }
        ]
    
    def _estimate_cluster_topic(self, cluster: List[str]) -> str:
        """估算群組對應的主要Topic"""
        cluster_text = ' '.join(cluster).lower()
        
        # 檢查每個topic的關鍵字
        topic_scores = {}
        for topic, keywords in self.clustering.fallback_topic_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in cluster_text:
                    score += 1
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        else:
            return 'latest'
    
    def _get_topic_description(self, topic: str) -> str:
        """獲取Topic的描述"""
        descriptions = {
            'crypto': '加密貨幣與區塊鏈技術',
            'tech': '科技股與人工智慧',
            'electric-vehicles': '電動車與新能源',
            'stock-market': '股市與交易',
            'earnings': '企業財報與獲利',
            'housing': '房地產與不動產',
            'inflation': '通膨與貨幣政策',
            'economies': '總體經濟',
            'mergers-ipos': '企業併購與IPO',
            'tariff-updates': '關稅與貿易',
            'originals': '深度分析與評論',
            'latest': '最新財經新聞'
        }
        return descriptions.get(topic, '相關投資領域')
    
    def _save_clustering_analysis(self, user_id: str, keywords: List[str], 
                                 clustering_result: Dict[str, Any]):
        """保存聚類分析結果到資料庫"""
        try:
            # 由於資料庫可能還沒有表，我們先嘗試導入資料庫管理器
            from core.database import db_manager
            
            analysis_data = {
                'user_id': user_id,
                'original_keywords': keywords,
                'clustered_keywords': clustering_result['clusters'],
                'cluster_confidence': clustering_result['focus_score'],
                'primary_topics': clustering_result['primary_topics'],
                'cluster_method': clustering_result['method']
            }
            
            db_manager.supabase.table('keyword_clusters').insert(analysis_data).execute()
            logger.info(f"Saved clustering analysis for user {user_id}")
            
        except Exception as e:
            logger.warning(f"Could not save clustering analysis: {e}")
    
    def _save_onboarding_completion(self, user_id: str, keywords: List[str], analysis: Dict[str, Any]):
        """保存引導完成記錄"""
        try:
            from core.database import db_manager
            
            guidance_data = {
                'user_id': user_id,
                'guidance_type': 'onboarding',
                'original_keywords': [],
                'suggested_keywords': keywords,
                'user_choice': 'completed',
                'guidance_result': analysis
            }
            
            db_manager.supabase.table('user_guidance_history').insert(guidance_data).execute()
            
            # 更新用戶訂閱表
            focus_score = analysis.get('clustering_result', {}).get('focus_score', 0.5)
            db_manager.supabase.table('subscriptions').update({
                'guidance_completed': True,
                'focus_score': focus_score,
                'last_guidance_at': datetime.now(timezone.utc).isoformat()
            }).eq('user_id', user_id).execute()
            
            logger.info(f"Saved onboarding completion for user {user_id}")
            
        except Exception as e:
            logger.warning(f"Could not save onboarding completion: {e}")
    
    def _handle_empty_keywords(self, user_id: str) -> Dict[str, Any]:
        """處理空關鍵字的情況"""
        return {
            'user_id': user_id,
            'type': 'empty_keywords',
            'guidance': {
                'type': 'setup_required',
                'title': '設定您的投資關注領域',
                'message': '請添加3-5個您感興趣的投資關鍵字，我們將為您推送相關的財經新聞。',
                'action': 'start_onboarding',
                'examples': ['Tesla', '比特幣', 'AI人工智慧', '房地產', '蘋果股票'],
                'icon': '🚀'
            }
        }
    
    def _fallback_analysis(self, user_id: str, keywords: List[str]) -> Dict[str, Any]:
        """備用分析方法"""
        return {
            'user_id': user_id,
            'original_keywords': keywords,
            'clustering_result': {
                'clusters': [keywords],
                'focus_score': 0.5,
                'primary_topics': ['latest'],
                'method': 'fallback'
            },
            'guidance': {
                'type': 'basic',
                'title': '關鍵字已設定',
                'message': '您的關鍵字已設定完成，我們將為您推送相關新聞。',
                'action': 'proceed',
                'optimization_needed': False
            }
        }
    
    def optimize_existing_user(self, user_id: str) -> Dict[str, Any]:
        """為現有用戶提供優化建議"""
        try:
            from core.database import db_manager
            
            # 獲取用戶當前訂閱資訊
            subscription = db_manager.supabase.table('subscriptions').select('*').eq('user_id', user_id).single().execute()
            
            if not subscription.data:
                return {'error': 'User subscription not found'}
            
            current_keywords = subscription.data.get('keywords', [])
            
            if not current_keywords:
                return self._handle_empty_keywords(user_id)
            
            # 分析當前關鍵字
            analysis = self.analyze_user_keywords(user_id, current_keywords)
            
            # 添加優化建議
            analysis['optimization_suggestions'] = self._generate_optimization_suggestions(
                subscription.data, analysis
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error optimizing existing user {user_id}: {e}")
            return {'error': str(e)}
    
    def _generate_optimization_suggestions(self, subscription: Dict[str, Any], 
                                         analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """為現有用戶生成優化建議"""
        suggestions = []
        
        focus_score = analysis.get('clustering_result', {}).get('focus_score', 0.5)
        
        if focus_score < 0.5:
            suggestions.append({
                'type': 'improve_focus',
                'priority': 'high',
                'title': '提升關鍵字聚焦度',
                'description': f'您的關鍵字聚焦度較低 ({focus_score:.1%})，建議重新設定以獲得更相關的新聞',
                'action': 'restart_onboarding'
            })
        
        # 檢查上次引導時間
        last_guidance = subscription.get('last_guidance_at')
        if not last_guidance:
            suggestions.append({
                'type': 'complete_guidance',
                'priority': 'medium',
                'title': '完成用戶引導',
                'description': '完成引導流程以獲得更好的個人化體驗',
                'action': 'start_onboarding'
            })
        
        return suggestions

# 創建全域實例
_guidance_instance = None

def get_guidance_instance():
    """獲取全域引導系統實例"""
    global _guidance_instance
    if _guidance_instance is None:
        _guidance_instance = UserGuidanceSystem()
    return _guidance_instance