#!/usr/bin/env python3
"""
摘要品質監控模組
負責追蹤、統計和報告摘要生成的品質指標
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import re

logger = logging.getLogger(__name__)

@dataclass
class SummaryQualityMetric:
    """摘要品質指標"""
    timestamp: str
    title: str
    summary: str
    chinese_ratio: float
    has_english_words: bool
    is_valid: bool
    quality_score: float
    attempt_count: int
    generation_time: float
    success: bool
    error_message: Optional[str] = None

class SummaryQualityMonitor:
    """摘要品質監控器"""
    
    def __init__(self, log_file_path: str = "logs/summary_quality.jsonl"):
        """
        初始化品質監控器
        
        Args:
            log_file_path: 日誌文件路徑
        """
        self.log_file_path = Path(log_file_path)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 統計數據
        self.session_stats = {
            'total_attempts': 0,
            'successful_summaries': 0,
            'failed_summaries': 0,
            'chinese_valid': 0,
            'chinese_invalid': 0,
            'retry_needed': 0,
            'total_generation_time': 0.0
        }
        
    def record_summary_attempt(self, metric: SummaryQualityMetric):
        """記錄摘要生成嘗試"""
        # 更新會話統計
        self.session_stats['total_attempts'] += 1
        
        if metric.success:
            self.session_stats['successful_summaries'] += 1
        else:
            self.session_stats['failed_summaries'] += 1
            
        if metric.is_valid:
            self.session_stats['chinese_valid'] += 1
        else:
            self.session_stats['chinese_invalid'] += 1
            
        if metric.attempt_count > 1:
            self.session_stats['retry_needed'] += 1
            
        self.session_stats['total_generation_time'] += metric.generation_time
        
        # 寫入日誌文件
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                json.dump(asdict(metric), f, ensure_ascii=False)
                f.write('\n')
                
            logger.debug(f"📊 品質指標已記錄: {metric.title[:30]}... (品質分數: {metric.quality_score:.2f})")
            
        except Exception as e:
            logger.error(f"記錄品質指標失敗: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """獲取當前會話的品質統計摘要"""
        stats = self.session_stats.copy()
        
        # 計算比例
        if stats['total_attempts'] > 0:
            stats['success_rate'] = stats['successful_summaries'] / stats['total_attempts']
            stats['chinese_valid_rate'] = stats['chinese_valid'] / stats['total_attempts']
            stats['retry_rate'] = stats['retry_needed'] / stats['total_attempts']
            stats['avg_generation_time'] = stats['total_generation_time'] / stats['total_attempts']
        else:
            stats['success_rate'] = 0.0
            stats['chinese_valid_rate'] = 0.0
            stats['retry_rate'] = 0.0
            stats['avg_generation_time'] = 0.0
            
        return stats
    
    def analyze_recent_quality(self, hours: int = 24) -> Dict[str, Any]:
        """分析最近N小時的摘要品質"""
        if not self.log_file_path.exists():
            return {'error': '沒有品質數據'}
            
        cutoff_time = datetime.now() - timedelta(hours=hours)
        metrics = []
        
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            metric = json.loads(line)
                            metric_time = datetime.fromisoformat(metric['timestamp'])
                            
                            if metric_time >= cutoff_time:
                                metrics.append(metric)
                        except (json.JSONDecodeError, KeyError, ValueError):
                            continue
                            
        except Exception as e:
            logger.error(f"分析品質數據失敗: {e}")
            return {'error': f'數據讀取失敗: {e}'}
        
        if not metrics:
            return {'error': f'最近 {hours} 小時沒有數據'}
        
        # 統計分析
        total = len(metrics)
        successful = sum(1 for m in metrics if m['success'])
        chinese_valid = sum(1 for m in metrics if m['is_valid'])
        retry_needed = sum(1 for m in metrics if m['attempt_count'] > 1)
        
        quality_scores = [m['quality_score'] for m in metrics if m['success']]
        generation_times = [m['generation_time'] for m in metrics]
        
        analysis = {
            'period_hours': hours,
            'total_attempts': total,
            'successful_summaries': successful,
            'success_rate': successful / total if total > 0 else 0,
            'chinese_valid': chinese_valid,
            'chinese_valid_rate': chinese_valid / total if total > 0 else 0,
            'retry_needed': retry_needed,
            'retry_rate': retry_needed / total if total > 0 else 0,
            'avg_quality_score': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'min_quality_score': min(quality_scores) if quality_scores else 0,
            'max_quality_score': max(quality_scores) if quality_scores else 0,
            'avg_generation_time': sum(generation_times) / len(generation_times) if generation_times else 0,
            'sample_recent': metrics[-3:] if len(metrics) >= 3 else metrics  # 最近3個樣本
        }
        
        return analysis
    
    def generate_quality_report(self) -> str:
        """生成品質報告"""
        session_stats = self.get_session_summary()
        recent_analysis = self.analyze_recent_quality(24)
        
        report_lines = [
            "📊 **摘要品質監控報告**",
            f"報告時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "🔄 **當前會話統計**:",
            f"  - 總嘗試次數: {session_stats['total_attempts']}",
            f"  - 成功率: {session_stats['success_rate']:.1%}",
            f"  - 中文有效率: {session_stats['chinese_valid_rate']:.1%}",
            f"  - 重試率: {session_stats['retry_rate']:.1%}",
            f"  - 平均生成時間: {session_stats['avg_generation_time']:.2f}秒",
            ""
        ]
        
        if 'error' not in recent_analysis:
            report_lines.extend([
                "📈 **24小時趨勢分析**:",
                f"  - 總處理量: {recent_analysis['total_attempts']} 篇",
                f"  - 成功率: {recent_analysis['success_rate']:.1%}",
                f"  - 中文有效率: {recent_analysis['chinese_valid_rate']:.1%}",
                f"  - 重試率: {recent_analysis['retry_rate']:.1%}",
                f"  - 平均品質分數: {recent_analysis['avg_quality_score']:.2f}",
                f"  - 品質分數範圍: {recent_analysis['min_quality_score']:.2f} ~ {recent_analysis['max_quality_score']:.2f}",
                f"  - 平均生成時間: {recent_analysis['avg_generation_time']:.2f}秒",
                ""
            ])
            
            # 添加最近樣本
            if recent_analysis.get('sample_recent'):
                report_lines.append("🎯 **最近處理樣本**:")
                for i, sample in enumerate(recent_analysis['sample_recent'][-3:], 1):
                    status = "✅ 成功" if sample['success'] else "❌ 失敗"
                    report_lines.append(f"  {i}. {status} | 品質: {sample['quality_score']:.2f} | 嘗試: {sample['attempt_count']}次")
                    report_lines.append(f"     標題: {sample['title'][:50]}...")
                    report_lines.append(f"     摘要: {sample['summary'][:50]}...")
                report_lines.append("")
        else:
            report_lines.extend([
                "❌ **24小時分析**:",
                f"  - {recent_analysis['error']}",
                ""
            ])
        
        # 品質建議（針對混合語言策略）
        if session_stats['chinese_valid_rate'] < 0.85:
            report_lines.extend([
                "⚠️ **品質建議**:",
                "  - 摘要品質偏低，可能包含過多禁用英文詞彙",
                "  - 檢查是否有語法性英文詞彙滲透",
                "  - 考慮調整專業術語白名單",
                ""
            ])
        elif session_stats['chinese_valid_rate'] >= 0.92:
            report_lines.extend([
                "🎉 **品質優秀**:",
                "  - 混合語言摘要品質穩定，專業性與可讀性平衡良好",
                "  - 中文為主、專業術語適度的策略運行正常",
                ""
            ])
        
        return "\n".join(report_lines)
    
    def clear_old_logs(self, days: int = 7):
        """清理舊的日誌數據"""
        if not self.log_file_path.exists():
            return
            
        cutoff_time = datetime.now() - timedelta(days=days)
        kept_lines = []
        removed_count = 0
        
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            metric = json.loads(line)
                            metric_time = datetime.fromisoformat(metric['timestamp'])
                            
                            if metric_time >= cutoff_time:
                                kept_lines.append(line)
                            else:
                                removed_count += 1
                        except (json.JSONDecodeError, KeyError, ValueError):
                            # 保留無法解析的行
                            kept_lines.append(line)
                            
            # 重寫文件
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                f.writelines(kept_lines)
                
            logger.info(f"📁 清理完成: 保留 {len(kept_lines)} 條記錄，清理 {removed_count} 條舊記錄")
            
        except Exception as e:
            logger.error(f"清理日誌失敗: {e}")

# 全域品質監控實例
_quality_monitor = None

def get_quality_monitor() -> SummaryQualityMonitor:
    """獲取品質監控實例（單例模式）"""
    global _quality_monitor
    if _quality_monitor is None:
        _quality_monitor = SummaryQualityMonitor()
    return _quality_monitor

def record_summary_quality(title: str, summary: str, chinese_ratio: float, 
                          has_english_words: bool, is_valid: bool, 
                          quality_score: float, attempt_count: int, 
                          generation_time: float, success: bool, 
                          error_message: Optional[str] = None,
                          detailed_analysis: Optional[dict] = None):
    """便利函數：記錄摘要品質指標（支援詳細分析）"""
    monitor = get_quality_monitor()
    
    # 如果有詳細分析，添加到錯誤訊息中
    if detailed_analysis and not success:
        analysis_info = []
        if detailed_analysis.get('forbidden_words'):
            analysis_info.append(f"禁用詞彙: {detailed_analysis['forbidden_words']}")
        if detailed_analysis.get('unknown_words'):
            analysis_info.append(f"未知詞彙: {detailed_analysis['unknown_words']}")
        if analysis_info:
            error_message = f"{error_message or ''} | {'; '.join(analysis_info)}"
    
    metric = SummaryQualityMetric(
        timestamp=datetime.now().isoformat(),
        title=title,
        summary=summary,
        chinese_ratio=chinese_ratio,
        has_english_words=has_english_words,
        is_valid=is_valid,
        quality_score=quality_score,
        attempt_count=attempt_count,
        generation_time=generation_time,
        success=success,
        error_message=error_message
    )
    
    monitor.record_summary_attempt(metric)

# 專業術語白名單系統
ALLOWED_ENGLISH_TERMS = {
    'companies': [
        # 科技公司
        'Apple', 'Microsoft', 'Google', 'Meta', 'Amazon', 'Tesla', 'NVIDIA', 'Intel',
        'Samsung', 'Sony', 'Adobe', 'Oracle', 'IBM', 'Cisco', 'Netflix',
        # 金融機構
        'JPMorgan', 'Goldman', 'BlackRock', 'Berkshire', 
        # 台灣公司常用英文名
        'TSMC', 'MediaTek', 'ASE', 'Foxconn', 'HTC'
    ],
    'finance_terms': [
        # 基本金融術語
        'GDP', 'IPO', 'CEO', 'CFO', 'COO', 'CTO', 'ROI', 'ROE', 'ROA', 'KPI',
        'ESG', 'ETF', 'REIT', 'M&A', 'IPO', 'ICO', 'DeFi', 'NFT',
        # 貨幣和市場
        'USD', 'EUR', 'JPY', 'CNY', 'TWD', 'NYSE', 'NASDAQ', 'S&P',
        # 財報術語
        'EBITDA', 'P/E', 'EPS', 'P/B', 'PEG'
    ],
    'tech_terms': [
        # 技術術語
        'AI', 'ML', 'IoT', '5G', '6G', 'VR', 'AR', 'API', 'SDK', 'SaaS',
        'Cloud', 'Edge', 'Blockchain', 'Web3', 'FinTech', 'RegTech',
        # 產業術語
        'EV', 'IC', 'OLED', 'LED', 'CPU', 'GPU', 'RAM', 'SSD', 'HDD'
    ],
    'units': [
        # 單位
        'TB', 'GB', 'MB', 'GHz', 'MHz', 'nm', 'kWh', 'MW', 'GW'
    ]
}

# 語法性英文詞彙（應該避免）
FORBIDDEN_ENGLISH_WORDS = [
    'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
    'this', 'that', 'these', 'those', 'a', 'an', 'as', 'if', 'when', 'where',
    'what', 'who', 'how', 'why', 'which', 'from', 'up', 'down', 'out', 'off',
    'over', 'under', 'again', 'further', 'then', 'once'
]

def get_all_allowed_terms() -> set:
    """獲取所有允許的英文術語"""
    all_terms = set()
    for category in ALLOWED_ENGLISH_TERMS.values():
        all_terms.update(term.lower() for term in category)
    return all_terms

def validate_mixed_language_summary(text: str) -> tuple[bool, float, bool, dict]:
    """
    驗證混合語言摘要的品質
    
    Returns:
        Tuple[是否有效, 中文字符比例, 包含禁用英文詞彙, 詳細分析]
    """
    if not text or len(text.strip()) < 10:
        return False, 0.0, False, {'error': 'Text too short'}
    
    text = text.strip()
    
    # 計算中文字符比例（改進版：僅計算字母+中文，排除數字和符號）
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    # 只計算文字字符：中文字符 + 英文字母
    text_chars_only = re.findall(r'[a-zA-Z\u4e00-\u9fff]', text)
    
    if len(text_chars_only) == 0:
        return False, 0.0, False, {'error': 'No text characters'}
    
    chinese_ratio = len(chinese_chars) / len(text_chars_only)
    
    # 提取所有英文詞彙
    english_words = re.findall(r'\b[a-zA-Z]+\b', text)
    english_words_lower = [word.lower() for word in english_words]
    
    # 分類英文詞彙
    allowed_terms = get_all_allowed_terms()
    forbidden_words = []
    allowed_words = []
    unknown_words = []
    
    for word in english_words_lower:
        if word in FORBIDDEN_ENGLISH_WORDS:
            forbidden_words.append(word)
        elif word in allowed_terms:
            allowed_words.append(word)
        else:
            unknown_words.append(word)
    
    # 判斷是否包含禁用詞彙
    has_forbidden_words = len(forbidden_words) > 0
    
    # 計算詳細分析
    analysis = {
        'chinese_chars': len(chinese_chars),
        'text_chars_only': len(text_chars_only),  # 更新為新的計算方式
        'english_words_count': len(english_words),
        'forbidden_words': forbidden_words,
        'allowed_words': allowed_words,
        'unknown_words': unknown_words,
        'chinese_ratio': chinese_ratio
    }
    
    # 有效條件：中文字符比例 >= 55% 且不包含禁用英文詞彙
    # 再次調降標準：考慮到台灣財經新聞常使用英文公司名和技術術語
    is_valid = chinese_ratio >= 0.55 and not has_forbidden_words
    
    return is_valid, chinese_ratio, has_forbidden_words, analysis

# 向後兼容的函數（保持舊的接口）
def validate_chinese_text(text: str) -> tuple[bool, float, bool]:
    """
    向後兼容的驗證函數
    
    Returns:
        Tuple[是否有效, 中文字符比例, 包含英文單詞]
    """
    is_valid, chinese_ratio, has_forbidden_words, _ = validate_mixed_language_summary(text)
    return is_valid, chinese_ratio, has_forbidden_words