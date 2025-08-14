#!/usr/bin/env python3
"""
翻譯功能演示腳本
展示翻譯服務的各項功能和使用方法
"""

import os
import sys
import logging
import time
from typing import List, Dict, Any

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.translation_service import get_translation_service, translate_title_to_chinese
from core.config import settings

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TranslationDemo:
    """翻譯功能演示類別"""
    
    def __init__(self):
        self.service = get_translation_service()
        self.sample_titles = [
            # 英文財經新聞標題
            "Apple reports record quarterly revenue driven by iPhone sales",
            "Tesla stock surges on strong delivery numbers",
            "Microsoft announces AI integration across Office suite",
            "Amazon Web Services sees 20% growth in cloud revenue", 
            "Google parent Alphabet beats earnings expectations",
            
            # 芬蘭文標題（模擬）
            "Nokia julkaisee uuden 5G-teknologian",
            "Suomen talous kasvaa odotettua nopeammin",
            
            # 已經是中文的標題（不應翻譯）
            "台積電第三季營收創新高",
            "鴻海集團宣布投資電動車領域",
            
            # 中英混合標題（需要翻譯）
            "Tesla 在中國市場表現強勁",
            "Apple iPhone 在台銷售創紀錄"
        ]
    
    def demo_basic_translation(self):
        """展示基本翻譯功能"""
        print("\n" + "="*60)
        print("基本翻譯功能演示")
        print("="*60)
        
        for i, title in enumerate(self.sample_titles[:5], 1):
            print(f"\n{i}. 原標題: {title}")
            
            try:
                translated = translate_title_to_chinese(title)
                
                if translated:
                    print(f"   翻譯結果: {translated}")
                    print("   ✅ 翻譯成功")
                else:
                    print("   ❌ 翻譯失敗")
                    
            except Exception as e:
                print(f"   ❌ 發生錯誤: {e}")
                
            # 添加延遲避免API限制
            time.sleep(1)
    
    def demo_detailed_translation(self):
        """展示詳細翻譯資訊"""
        print("\n" + "="*60)
        print("📊 詳細翻譯資訊演示")
        print("="*60)
        
        sample_title = self.sample_titles[0]
        print(f"\n📰 分析標題: {sample_title}")
        
        try:
            details = self.service.translate_title_with_details(sample_title)
            
            print(f"\n翻譯詳細資訊:")
            print(f"  - 翻譯結果: {details.get('translated_title', 'N/A')}")
            print(f"  - 信心分數: {details.get('confidence', 0):.2f}")
            print(f"  - 翻譯方法: {details.get('method', 'N/A')}")
            print(f"  - 處理時間: {details.get('processing_time', 0):.3f} 秒")
            print(f"  - 錯誤資訊: {details.get('error', 'None')}")
            
        except Exception as e:
            print(f"❌ 獲取詳細資訊失敗: {e}")
    
    def demo_chinese_detection(self):
        """展示中文檢測功能"""
        print("\n" + "="*60)
        print("🔍 中文檢測功能演示")
        print("="*60)
        
        test_titles = [
            "蘋果公司發布新產品",  # 純中文
            "Tesla 股價上漲",  # 中英混合
            "Apple Inc. Reports",  # 純英文
            "Nokia julkaisee",  # 芬蘭文
            ""  # 空字符串
        ]
        
        for title in test_titles:
            is_chinese = self.service._is_already_chinese(title)
            status = "✅ 已是中文" if is_chinese else "🔄 需要翻譯"
            print(f"'{title}' -> {status}")
    
    def demo_batch_translation(self):
        """展示批次翻譯功能（使用Mock）"""
        print("\n" + "="*60)
        print("📦 批次翻譯功能演示 (模擬)")
        print("="*60)
        
        batch_titles = self.sample_titles[2:5]
        print(f"批次翻譯 {len(batch_titles)} 個標題...")
        
        # 由於API限制，我們不進行真實的批次翻譯，而是展示功能結構
        print("\n批次翻譯結果 (模擬):")
        for i, title in enumerate(batch_titles, 1):
            print(f"{i}. {title}")
            print(f"   -> [模擬翻譯結果]")
        
        print("\n注意: 真實的批次翻譯會調用 service.batch_translate() 方法")
    
    def demo_cache_functionality(self):
        """展示快取功能"""
        print("\n" + "="*60)
        print("💾 快取功能演示")
        print("="*60)
        
        # 清除快取
        self.service.clear_cache()
        print("🗑️ 已清除快取")
        
        # 顯示初始快取狀態
        cache_info = self.service.get_cache_info()
        print(f"\n初始快取狀態:")
        print(f"  - 快取命中: {cache_info['hits']}")
        print(f"  - 快取未命中: {cache_info['misses']}")
        print(f"  - 當前大小: {cache_info['current_size']}")
        print(f"  - 最大大小: {cache_info['max_size']}")
        print(f"  - 命中率: {cache_info['hit_rate']:.1%}")
    
    def demo_error_handling(self):
        """展示錯誤處理功能"""
        print("\n" + "="*60)
        print("⚠️ 錯誤處理功能演示")
        print("="*60)
        
        error_cases = [
            "",  # 空標題
            None,  # None 值
            "   ",  # 純空格
            "a" * 1000,  # 過長標題
        ]
        
        for case in error_cases:
            print(f"\n測試案例: {repr(case)}")
            try:
                result = translate_title_to_chinese(case)
                print(f"結果: {result}")
            except Exception as e:
                print(f"捕獲異常: {e}")
    
    def show_configuration(self):
        """顯示翻譯服務配置"""
        print("\n" + "="*60)
        print("⚙️ 翻譯服務配置")
        print("="*60)
        
        print(f"OpenAI API Key: {'已設置' if settings.OPENAI_API_KEY else '未設置'}")
        print(f"翻譯模型: {self.service.model}")
        print(f"最大重試次數: {self.service.max_retries}")
        print(f"請求超時: {self.service.timeout} 秒")
        print(f"最小信心分數: {self.service.min_confidence}")
        print(f"最大長度比例: {self.service.max_length_ratio}")
    
    def run_full_demo(self):
        """執行完整演示"""
        print("翻譯功能完整演示")
        print(f"時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 檢查API密鑰
        if not settings.OPENAI_API_KEY:
            print("\n警告: 未檢測到 OpenAI API Key")
            print("某些功能將無法正常演示")
            print("請設置 OPENAI_API_KEY 環境變數")
        
        # 執行各項演示
        demo_functions = [
            ("配置資訊", self.show_configuration),
            ("中文檢測", self.demo_chinese_detection),
            ("快取功能", self.demo_cache_functionality),
            ("錯誤處理", self.demo_error_handling),
        ]
        
        # 如果有API密鑰，添加需要API的演示
        if settings.OPENAI_API_KEY:
            demo_functions.extend([
                ("基本翻譯", self.demo_basic_translation),
                ("詳細資訊", self.demo_detailed_translation),
            ])
        
        demo_functions.append(("批次翻譯", self.demo_batch_translation))
        
        for demo_name, demo_func in demo_functions:
            try:
                demo_func()
            except KeyboardInterrupt:
                print(f"\n⛔ 用戶中斷演示")
                break
            except Exception as e:
                print(f"\n❌ 演示 '{demo_name}' 發生錯誤: {e}")
                continue
        
        print("\n" + "="*60)
        print("🎉 翻譯功能演示完成!")
        print("="*60)
        print("\n後續步驟:")
        print("1. 在 Supabase Dashboard 中新增 translated_title 欄位")
        print("2. 整合翻譯功能到爬蟲流程")
        print("3. 修改 Discord 推送邏輯")
        print("4. 進行端到端測試")

def main():
    """主函數"""
    print("啟動翻譯功能演示...")
    
    try:
        demo = TranslationDemo()
        demo.run_full_demo()
    except KeyboardInterrupt:
        print("\n演示被用戶中斷")
    except Exception as e:
        logger.exception(f"演示過程發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()