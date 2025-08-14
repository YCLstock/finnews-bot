#!/usr/bin/env python3
"""
翻譯服務模組
獨立的標題翻譯功能，不影響現有摘要生成流程

Design Principles:
- 獨立運作，失敗時不影響主流程
- 支援快取機制避免重複翻譯  
- 提供品質評估和信心分數
- 支援多種翻譯引擎（目前使用OpenAI）
"""

import openai
import logging
import time
from typing import Optional, Dict, Any, Tuple
from functools import lru_cache
import hashlib
import re

from core.config import settings

# 設置日誌
logger = logging.getLogger(__name__)

class TranslationService:
    """翻譯服務類別"""
    
    def __init__(self):
        """初始化翻譯服務"""
        self.openai_client = openai
        self.openai_client.api_key = settings.OPENAI_API_KEY
        
        # 翻譯配置
        self.model = "gpt-3.5-turbo"
        self.max_retries = 2
        self.timeout = 10
        
        # 品質控制
        self.min_confidence = 0.7
        self.max_length_ratio = 2.5  # 翻譯長度不應超過原文2.5倍
        
    def _generate_cache_key(self, title: str) -> str:
        """為標題生成快取鍵值"""
        return hashlib.md5(title.encode('utf-8')).hexdigest()[:12]
    
    def _is_already_chinese(self, text: str) -> bool:
        """檢查文本是否已經是中文"""
        # 計算中文字符比例
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        total_chars = len(re.findall(r'[a-zA-Z\u4e00-\u9fff]', text))
        
        if total_chars == 0:
            return False
            
        chinese_ratio = len(chinese_chars) / total_chars
        return chinese_ratio >= 0.6  # 需要60%以上中文字符才算純中文
    
    def _validate_translation(self, original: str, translation: str) -> Tuple[bool, float]:
        """
        驗證翻譯品質
        
        Returns:
            Tuple[bool, float]: (是否有效, 信心分數)
        """
        if not translation or not translation.strip():
            return False, 0.0
        
        translation = translation.strip()
        
        # 基本長度檢查
        if len(translation) > len(original) * self.max_length_ratio:
            logger.warning(f"翻譯過長: 原文 {len(original)} 字，翻譯 {len(translation)} 字")
            return False, 0.3
        
        # 檢查是否包含中文
        if not self._is_already_chinese(translation):
            logger.warning("翻譯結果不包含中文")
            return False, 0.2
        
        # 檢查是否包含原文（可能翻譯失敗）
        if original.lower() in translation.lower():
            logger.warning("翻譯結果包含原文，可能翻譯不完整")
            return False, 0.4
        
        # 品質評分（基於長度比例、中文字符等）
        chinese_ratio = len(re.findall(r'[\u4e00-\u9fff]', translation)) / len(translation)
        length_ratio = len(translation) / len(original)
        
        # 計算信心分數
        confidence = min(
            chinese_ratio * 1.2,  # 中文字符比例
            (2.0 - abs(length_ratio - 1.0)) if length_ratio > 0 else 0,  # 長度適中
            1.0
        )
        
        is_valid = confidence >= self.min_confidence
        
        return is_valid, confidence
    
    def _build_translation_prompt(self, title: str) -> str:
        """構建翻譯提示詞"""
        system_prompt = """你是一位專業的財經新聞翻譯專家。請將以下英文或芬蘭文的新聞標題準確翻譯成繁體中文。

翻譯要求：
1. 使用繁體中文
2. 保持原文的專業性和準確性
3. 符合台灣的財經新聞用語習慣
4. 如果包含公司名稱，保留英文原名或使用常見中文譯名
5. 只返回翻譯結果，不要額外解釋

原標題：{title}

翻譯："""
        
        return system_prompt.format(title=title)
    
    @lru_cache(maxsize=1000)
    def _translate_with_cache(self, title_hash: str, title: str) -> Optional[Dict[str, Any]]:
        """帶快取的翻譯實現"""
        return self._translate_without_cache(title)
    
    def _translate_without_cache(self, title: str) -> Optional[Dict[str, Any]]:
        """不帶快取的翻譯實現"""
        try:
            # 檢查是否已經是中文
            if self._is_already_chinese(title):
                logger.info(f"標題已是中文，無需翻譯: {title[:50]}...")
                return {
                    'translated_title': title,
                    'confidence': 1.0,
                    'method': 'no_translation_needed',
                    'processing_time': 0.0
                }
            
            start_time = time.time()
            
            # 建立翻譯請求
            messages = [
                {
                    "role": "system", 
                    "content": "你是專業的財經新聞翻譯專家，請將標題翻譯成繁體中文。只返回翻譯結果。"
                },
                {
                    "role": "user", 
                    "content": f"請翻譯: {title}"
                }
            ]
            
            # 呼叫 OpenAI API
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=200,
                temperature=0.3,
                timeout=self.timeout
            )
            
            processing_time = time.time() - start_time
            
            if response.choices and response.choices[0].message.content:
                translation = response.choices[0].message.content.strip()
                
                # 驗證翻譯品質
                is_valid, confidence = self._validate_translation(title, translation)
                
                if is_valid:
                    logger.info(f"翻譯成功: {title[:30]}... → {translation[:30]}...")
                    return {
                        'translated_title': translation,
                        'confidence': confidence,
                        'method': 'openai_gpt35',
                        'processing_time': processing_time
                    }
                else:
                    logger.warning(f"翻譯品質不達標: {translation[:50]}... (信心分數: {confidence:.2f})")
                    return None
            else:
                logger.error("OpenAI API 返回空結果")
                return None
                
        except openai.RateLimitError:
            logger.error("OpenAI API 速率限制")
            return None
        except openai.APITimeoutError:
            logger.error(f"OpenAI API 請求超時 ({self.timeout}s)")
            return None
        except openai.APIError as e:
            logger.error(f"OpenAI API 錯誤: {e}")
            return None
        except Exception as e:
            logger.exception(f"翻譯過程發生未預期錯誤: {e}")
            return None
    
    def translate_title_to_chinese(self, title: str, use_cache: bool = True) -> Optional[str]:
        """
        將標題翻譯為中文
        
        Args:
            title: 原始標題
            use_cache: 是否使用快取
            
        Returns:
            翻譯後的標題，失敗時返回 None
        """
        if not title or not title.strip():
            logger.warning("輸入標題為空")
            return None
        
        title = title.strip()
        
        try:
            if use_cache:
                cache_key = self._generate_cache_key(title)
                result = self._translate_with_cache(cache_key, title)
            else:
                result = self._translate_without_cache(title)
            
            if result:
                return result['translated_title']
            else:
                return None
                
        except Exception as e:
            logger.exception(f"翻譯服務調用失敗: {e}")
            return None
    
    def translate_title_with_details(self, title: str) -> Dict[str, Any]:
        """
        翻譯標題並返回詳細資訊
        
        Returns:
            Dict包含: translated_title, confidence, method, processing_time, error
        """
        if not title or not title.strip():
            return {
                'translated_title': None,
                'confidence': 0.0,
                'method': 'error',
                'processing_time': 0.0,
                'error': 'Empty title'
            }
        
        title = title.strip()
        
        try:
            cache_key = self._generate_cache_key(title)
            result = self._translate_with_cache(cache_key, title)
            
            if result:
                result['error'] = None
                return result
            else:
                return {
                    'translated_title': None,
                    'confidence': 0.0,
                    'method': 'failed',
                    'processing_time': 0.0,
                    'error': 'Translation failed validation'
                }
                
        except Exception as e:
            logger.exception(f"翻譯詳細資訊獲取失敗: {e}")
            return {
                'translated_title': None,
                'confidence': 0.0,
                'method': 'error',
                'processing_time': 0.0,
                'error': str(e)
            }
    
    def batch_translate(self, titles: list) -> Dict[str, Optional[str]]:
        """
        批次翻譯標題
        
        Args:
            titles: 標題列表
            
        Returns:
            Dict[原標題, 翻譯結果]
        """
        results = {}
        
        for title in titles:
            if not title:
                results[title] = None
                continue
                
            try:
                translated = self.translate_title_to_chinese(title)
                results[title] = translated
                
                # 批次處理時添加短暫延遲避免API限制
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"批次翻譯失敗 {title}: {e}")
                results[title] = None
        
        return results
    
    def clear_cache(self):
        """清除翻譯快取"""
        self._translate_with_cache.cache_clear()
        logger.info("翻譯快取已清除")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """獲取快取統計資訊"""
        cache_info = self._translate_with_cache.cache_info()
        return {
            'hits': cache_info.hits,
            'misses': cache_info.misses,
            'current_size': cache_info.currsize,
            'max_size': cache_info.maxsize,
            'hit_rate': cache_info.hits / (cache_info.hits + cache_info.misses) if (cache_info.hits + cache_info.misses) > 0 else 0
        }


# 全域翻譯服務實例
_translation_service = None

def get_translation_service() -> TranslationService:
    """獲取翻譯服務實例（單例模式）"""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service

# 便利函數
def translate_title_to_chinese(title: str) -> Optional[str]:
    """
    便利函數：將標題翻譯為中文
    
    Args:
        title: 原始標題
        
    Returns:
        翻譯後的標題，失敗時返回 None
    """
    service = get_translation_service()
    return service.translate_title_to_chinese(title)