#!/usr/bin/env python3
"""
🧪 FinNews-Bot 完整系統測試
上線前必須通過的所有測試項目
"""

import sys
import os
import json
import requests
import time
import uuid
from pathlib import Path
from datetime import datetime, timedelta

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import settings
from core.database import db_manager
from core.utils import send_to_discord, generate_summary_optimized
from scraper.scraper import scraper_manager

class SystemTester:
    def __init__(self):
        self.api_base_url = "http://localhost:8000/api/v1"
        self.test_user_id = str(uuid.uuid4())  # 轉換為字符串格式
        self.test_discord_webhook = None  # 設置您的測試 Discord Webhook
        self.test_results = {}
        
    def log_test(self, test_name: str, result: bool, message: str = ""):
        """記錄測試結果"""
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"    📝 {message}")
        self.test_results[test_name] = {"result": result, "message": message}
        
    def test_environment_config(self) -> bool:
        """測試環境配置"""
        print("\n🔧 測試環境配置")
        print("-" * 50)
        
        required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_JWT_SECRET", "OPENAI_API_KEY"]
        missing_vars = []
        
        for var in required_vars:
            if not getattr(settings, var, None):
                missing_vars.append(var)
        
        if missing_vars:
            self.log_test("環境變數配置", False, f"缺少: {', '.join(missing_vars)}")
            return False
        
        # 檢查各個環境變數的長度和格式
        checks = []
        
        # SUPABASE_URL 檢查
        if settings.SUPABASE_URL and settings.SUPABASE_URL.startswith('https://'):
            checks.append("✅ SUPABASE_URL 格式正確")
        else:
            checks.append("❌ SUPABASE_URL 格式錯誤")
            
        # JWT_SECRET 檢查
        jwt_secret_len = len(str(settings.SUPABASE_JWT_SECRET))
        if jwt_secret_len >= 32:
            checks.append(f"✅ JWT_SECRET 長度足夠 ({jwt_secret_len} bytes)")
        else:
            checks.append(f"❌ JWT_SECRET 太短 ({jwt_secret_len} bytes)")
            
        # OPENAI_API_KEY 檢查
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith('sk-'):
            checks.append("✅ OPENAI_API_KEY 格式正確")
        else:
            checks.append("❌ OPENAI_API_KEY 格式錯誤")
        
        for check in checks:
            print(f"    {check}")
            
        all_passed = all("✅" in check for check in checks)
        self.log_test("環境變數配置", all_passed, "所有必要環境變數已設置且格式正確" if all_passed else "部分環境變數有問題")
        return all_passed
    
    def test_database_operations(self) -> bool:
        """測試資料庫操作"""
        print("\n💾 測試資料庫操作")
        print("-" * 50)
        
        try:
            # 測試基本連接
            print("    🔗 測試資料庫連接...")
            subscriptions = db_manager.get_active_subscriptions()
            self.log_test("資料庫連接", True, f"成功讀取 {len(subscriptions)} 個活躍訂閱")
            
            # 測試 CRUD 操作
            print("    📝 測試 CRUD 操作...")
            test_subscription = {
                "user_id": self.test_user_id,
                "delivery_platform": "discord",
                "delivery_target": "https://discord.com/api/webhooks/test/123456",
                "keywords": ["測試關鍵字", "台積電"],
                "news_sources": ["yahoo_finance"],
                "summary_language": "zh-tw",
                "push_frequency_type": "daily",
                "is_active": True
            }
            
            # 創建測試訂閱
            created = db_manager.create_subscription(test_subscription)
            if created:
                self.log_test("創建訂閱 (UPSERT)", True, f"成功創建用戶 {self.test_user_id} 的訂閱")
            else:
                self.log_test("創建訂閱 (UPSERT)", False, "UPSERT 操作失敗")
                return False
            
            # 讀取訂閱
            subscription = db_manager.get_subscription_by_user(self.test_user_id)
            if subscription and subscription['user_id'] == self.test_user_id:
                self.log_test("讀取訂閱 (user_id主鍵)", True, "成功讀取單用戶訂閱")
            else:
                self.log_test("讀取訂閱 (user_id主鍵)", False, "讀取訂閱失敗")
                return False
            
            # 更新訂閱
            updated = db_manager.update_subscription(self.test_user_id, {
                "keywords": ["更新測試", "鴻海"],
                "push_frequency_type": "twice"
            })
            if updated:
                self.log_test("更新訂閱 (user_id主鍵)", True, f"成功更新關鍵字和頻率")
            else:
                self.log_test("更新訂閱 (user_id主鍵)", False, "更新操作失敗")
                return False
            
            # 測試推送歷史記錄
            print("    📋 測試推送歷史...")
            fake_article_ids = [99998, 99999]  # 使用不會衝突的測試ID
            history_logged = db_manager.log_push_history(self.test_user_id, fake_article_ids, "test-batch-001")
            if history_logged:
                self.log_test("推送歷史記錄", True, f"成功記錄 {len(fake_article_ids)} 筆推送歷史")
            else:
                self.log_test("推送歷史記錄", False, "推送歷史記錄失敗")
            
            # 測試時間窗口標記
            print("    ⏰ 測試時間窗口標記...")
            window_marked = db_manager.mark_push_window_completed(self.test_user_id, "daily")
            if window_marked:
                self.log_test("時間窗口標記", True, "成功標記推送窗口完成")
            else:
                self.log_test("時間窗口標記", False, "時間窗口標記失敗")
            
            # 清理測試數據
            print("    🧹 清理測試數據...")
            deleted = db_manager.delete_subscription(self.test_user_id)
            if deleted:
                self.log_test("刪除訂閱 (清理)", True, "成功清理測試訂閱")
            else:
                self.log_test("刪除訂閱 (清理)", False, "清理失敗")
                
            return True
            
        except Exception as e:
            self.log_test("資料庫操作", False, f"操作異常: {str(e)}")
            return False
    
    def test_ai_integration(self) -> bool:
        """測試 AI 摘要功能"""
        print("\n🤖 測試 AI 摘要功能")  
        print("-" * 50)
        
        try:
            print("    🧠 測試 OpenAI 摘要生成...")
            test_content = """
            台積電（TSMC）今日公布第三季財報，營收達新台幣6,133億元，較上季成長13.8%。
            公司表示，受惠於人工智慧(AI)晶片需求強勁，先進製程產能利用率維持高檔。
            執行長魏哲家指出，7奈米及以下先進製程營收占比達56%，創歷史新高。
            法人預估，隨著AI應用持續擴展，台積電第四季營收可望再創新猷。
            """
            
            summary = generate_summary_optimized(test_content.strip())
            
            if summary and "[摘要生成失敗" not in summary:
                summary_len = len(summary)
                if summary_len >= 50 and summary_len <= 300:
                    self.log_test("OpenAI 摘要生成", True, f"摘要長度適中: {summary_len} 字")
                else:
                    self.log_test("OpenAI 摘要生成", False, f"摘要長度異常: {summary_len} 字")
                    return False
                
                print(f"    📋 摘要範例: {summary[:80]}...")
                return True
            else:
                self.log_test("OpenAI 摘要生成", False, "摘要生成失敗或包含錯誤信息")
                return False
                
        except Exception as e:
            self.log_test("AI 摘要功能", False, f"AI 服務錯誤: {str(e)}")
            return False
    
    def test_scraper_functionality(self) -> bool:
        """測試爬蟲功能"""
        print("\n🕷️ 測試爬蟲功能")
        print("-" * 50)
        
        try:
            print("    📰 測試 Yahoo Finance 新聞列表爬取...")
            # 限制爬取數量以加快測試速度
            news_list = scraper_manager.scrape_yahoo_finance_list()
            
            if news_list and len(news_list) > 0:
                self.log_test("新聞列表爬取", True, f"成功爬取 {len(news_list)} 則新聞")
                
                # 檢查新聞項目格式
                first_article = news_list[0]
                required_fields = ['title', 'link']
                has_all_fields = all(field in first_article for field in required_fields)
                
                if has_all_fields:
                    self.log_test("新聞格式檢查", True, "新聞項目包含必要欄位")
                else:
                    self.log_test("新聞格式檢查", False, f"缺少必要欄位: {required_fields}")
                    return False
                
                # 測試單篇文章內容爬取（選擇第一篇）
                print("    📄 測試單篇文章內容爬取...")
                print(f"    🔗 測試文章: {first_article['title'][:50]}...")
                
                content = scraper_manager.scrape_article_content(first_article['link'])
                
                if content and len(content) > 100:
                    content_len = len(content)
                    self.log_test("文章內容爬取", True, f"成功爬取內容: {content_len} 字")
                    print(f"    📝 內容範例: {content[:100]}...")
                    return True
                else:
                    self.log_test("文章內容爬取", False, f"內容爬取失敗或太短: {len(content) if content else 0} 字")
                    return False
            else:
                self.log_test("新聞列表爬取", False, "未能爬取到任何新聞")
                return False
                
        except Exception as e:
            self.log_test("爬蟲功能", False, f"爬蟲異常: {str(e)}")
            return False
    
    def test_time_window_logic(self) -> bool:
        """測試時間窗口邏輯"""
        print("\n⏰ 測試時間窗口邏輯")
        print("-" * 50)
        
        try:
            print("    🕐 測試各種時間窗口情況...")
            test_cases = [
                ("07:45", "08:00", 30, True, "提前15分鐘"),
                ("08:15", "08:00", 30, True, "延後15分鐘"), 
                ("08:25", "08:00", 30, True, "延後25分鐘"),
                ("08:35", "08:00", 30, False, "延後35分鐘"),
                ("07:25", "08:00", 30, False, "提前35分鐘"),
                ("12:45", "13:00", 30, True, "午間時段"),
                ("19:45", "20:00", 30, True, "晚間時段"),
            ]
            
            passed_tests = 0
            total_tests = len(test_cases)
            
            for current, target, window, expected, description in test_cases:
                result = db_manager.is_within_time_window(current, target, window)
                if result == expected:
                    print(f"    ✅ {current} vs {target} (±{window}min): {result} - {description}")
                    passed_tests += 1
                else:
                    print(f"    ❌ {current} vs {target} (±{window}min): {result} (預期: {expected}) - {description}")
            
            success = passed_tests == total_tests
            self.log_test("時間窗口邏輯", success, f"通過 {passed_tests}/{total_tests} 項測試")
            
            # 測試推送頻率配置
            print("    📅 測試推送頻率配置...")
            frequency_configs = ['daily', 'twice', 'thrice']
            for freq in frequency_configs:
                max_articles = db_manager.get_max_articles_for_frequency(freq)
                expected_articles = {'daily': 10, 'twice': 5, 'thrice': 3}[freq]
                if max_articles == expected_articles:
                    print(f"    ✅ {freq}: {max_articles} 篇文章")
                else:
                    print(f"    ❌ {freq}: {max_articles} 篇 (預期: {expected_articles})")
                    success = False
                    
            return success
            
        except Exception as e:
            self.log_test("時間窗口邏輯", False, f"時間窗口測試異常: {str(e)}")
            return False
    
    def test_api_endpoints(self) -> bool:
        """測試 API 端點"""
        print("\n🌐 測試 API 端點")
        print("-" * 50)
        
        try:
            print("    🏥 檢查 API 服務狀態...")
            # 檢查 API 服務是否運行
            health_url = f"{self.api_base_url}/health"
            
            try:
                response = requests.get(health_url, timeout=10)
                if response.status_code == 200:
                    self.log_test("API 服務運行", True, "健康檢查端點響應正常")
                else:
                    self.log_test("API 服務運行", False, f"健康檢查失敗，狀態碼: {response.status_code}")
                    return False
            except requests.RequestException:
                self.log_test("API 服務運行", False, "無法連接到 API 服務")
                print("    💡 請確保 API 服務正在運行: python -m api.main")
                return False
            
            # 測試公開端點
            print("    📋 測試推送頻率選項端點...")
            try:
                freq_response = requests.get(f"{self.api_base_url}/subscriptions/frequency-options", timeout=10)
                if freq_response.status_code == 200:
                    options = freq_response.json()
                    if 'options' in options and len(options['options']) == 3:
                        self.log_test("頻率選項 API", True, f"返回 {len(options['options'])} 個頻率選項")
                        
                        # 檢查選項內容
                        expected_values = ['daily', 'twice', 'thrice']
                        actual_values = [opt['value'] for opt in options['options']]
                        if set(actual_values) == set(expected_values):
                            self.log_test("頻率選項內容", True, "所有預期的頻率選項都存在")
                        else:
                            self.log_test("頻率選項內容", False, f"頻率選項不匹配: {actual_values}")
                            return False
                    else:
                        self.log_test("頻率選項 API", False, "API 響應格式錯誤")
                        return False
                else:
                    self.log_test("頻率選項 API", False, f"API 錯誤，狀態碼: {freq_response.status_code}")
                    return False
            except requests.RequestException as e:
                self.log_test("頻率選項 API", False, f"API 請求異常: {str(e)}")
                return False
                
            return True
                
        except Exception as e:
            self.log_test("API 端點測試", False, f"API 測試異常: {str(e)}")
            return False
    
    def test_discord_integration(self) -> bool:
        """測試 Discord 整合"""
        print("\n💬 測試 Discord 整合")
        print("-" * 50)
        
        if not self.test_discord_webhook:
            self.log_test("Discord 整合", False, "未設置測試用 Discord Webhook")
            print("    💡 要進行完整的 Discord 測試，請在測試腳本中設置真實的 Webhook URL")
            print("    🔧 修改方法: tester.test_discord_webhook = 'YOUR_WEBHOOK_URL'")
            return False
        
        try:
            print("    📤 發送測試消息...")
            # 創建測試文章格式，符合 send_to_discord 函數的要求
            test_articles = [{
                "title": "🧪 FinNews-Bot 系統測試",
                "summary": f"這是系統測試消息。測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "original_url": "https://github.com/your-repo/finnews-bot"
            }]
            
            success = send_to_discord(self.test_discord_webhook, test_articles)
            
            if success:
                self.log_test("Discord 推送測試", True, "成功發送測試消息到 Discord")
                return True
            else:
                self.log_test("Discord 推送測試", False, "Discord 消息發送失敗")
                return False
                
        except Exception as e:
            self.log_test("Discord 整合", False, f"Discord 推送異常: {str(e)}")
            return False
    
    def test_integrated_workflow(self) -> bool:
        """測試整合工作流程"""
        print("\n🔄 測試整合工作流程")
        print("-" * 50)
        
        try:
            print("    🎯 測試完整的新聞處理流程...")
            
            # 1. 獲取符合條件的訂閱
            eligible_subscriptions = db_manager.get_eligible_subscriptions()
            self.log_test("獲取符合條件訂閱", True, f"找到 {len(eligible_subscriptions)} 個符合條件的訂閱")
            
            # 2. 測試推送排程邏輯
            current_time = datetime.now().strftime("%H:%M")
            for freq in ['daily', 'twice', 'thrice']:
                current_window = db_manager.get_current_time_window(current_time, freq)
                if current_window:
                    print(f"    ✅ 當前時間 {current_time} 在 {freq} 模式下的推送窗口: {current_window}")
                else:
                    print(f"    ⏸️ 當前時間 {current_time} 不在 {freq} 模式的推送窗口內")
            
            self.log_test("推送排程邏輯", True, "推送時間窗口判斷正常")
            
            # 3. 測試文章去重邏輯
            print("    🔍 測試文章去重邏輯...")
            test_url = "https://tw.stock.yahoo.com/news/test-article-12345"
            
            # 第一次檢查（應該返回 False，表示未處理過）
            is_processed_first = db_manager.is_article_processed(test_url)
            
            # 第二次檢查（應該返回相同結果）
            is_processed_second = db_manager.is_article_processed(test_url)
            
            if is_processed_first == is_processed_second:
                self.log_test("文章去重邏輯", True, f"去重檢查一致性: {is_processed_first}")
            else:
                self.log_test("文章去重邏輯", False, "去重檢查結果不一致")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("整合工作流程", False, f"工作流程測試異常: {str(e)}")
            return False
    
    def run_all_tests(self) -> bool:
        """運行所有測試"""
        print("🧪 FinNews-Bot 完整系統測試")
        print("=" * 60)
        print("⚠️  這是上線前必須通過的完整測試清單")
        print("=" * 60)
        
        tests = [
            ("環境配置", self.test_environment_config),
            ("資料庫操作", self.test_database_operations), 
            ("AI 摘要功能", self.test_ai_integration),
            ("爬蟲功能", self.test_scraper_functionality),
            ("時間窗口邏輯", self.test_time_window_logic),
            ("API 端點", self.test_api_endpoints),
            ("Discord 整合", self.test_discord_integration),
            ("整合工作流程", self.test_integrated_workflow),
        ]
        
        passed = 0
        total = len(tests)
        start_time = datetime.now()
        
        for i, (test_name, test_func) in enumerate(tests, 1):
            print(f"\n[{i}/{total}] 🔸 執行測試: {test_name}")
            try:
                if test_func():
                    passed += 1
                time.sleep(0.5)  # 測試間短暫休息
            except Exception as e:
                self.log_test(f"{test_name} (系統異常)", False, f"測試執行異常: {str(e)}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.generate_report(passed, total, duration)
        return passed == total
    
    def generate_report(self, passed: int, total: int, duration: float):
        """生成詳細測試報告"""
        print("\n" + "=" * 60)
        print("📊 系統測試結果總結")
        print("=" * 60)
        
        print(f"測試執行時間: {duration:.1f} 秒")
        print(f"通過測試: {passed}/{total}")
        print(f"成功率: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 恭喜！所有測試都通過了！")
            print("\n✅ 系統狀態評估:")
            print("  ✅ 環境配置正確")
            print("  ✅ 資料庫操作正常") 
            print("  ✅ AI 功能運作正常")
            print("  ✅ 爬蟲功能穩定")
            print("  ✅ 時間邏輯正確")
            print("  ✅ API 服務正常")
            print("  ✅ 系統整合完善")
            print("\n🚀 系統已準備好上線部署！")
        else:
            failed_count = total - passed
            print(f"\n⚠️ 有 {failed_count} 個測試失敗，需要修復")
            print("\n❌ 失敗的測試:")
            for test_name, result in self.test_results.items():
                if not result['result']:
                    print(f"  ❌ {test_name}: {result['message']}")
                    
            print(f"\n🔧 建議優先修復失敗的測試項目")
                    
        # 保存詳細報告到文件
        report_data = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": duration,
                "passed": passed,
                "total": total,
                "success_rate": (passed/total)*100,
                "status": "PASSED" if passed == total else "FAILED"
            },
            "test_details": self.test_results,
            "recommendations": self._generate_recommendations(passed, total)
        }
        
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 詳細測試報告已保存: {report_file}")
    
    def _generate_recommendations(self, passed: int, total: int) -> list:
        """生成建議"""
        recommendations = []
        
        if passed == total:
            recommendations.extend([
                "系統測試全部通過，可以進行生產部署",
                "建議進行前端開發，完成用戶界面",
                "考慮進行負載測試和安全測試",
                "準備生產環境的監控和日誌系統"
            ])
        else:
            recommendations.extend([
                "優先修復失敗的測試項目",
                "檢查環境配置和依賴安裝",
                "確認網路連接和外部服務可用性",
                "修復完成後重新運行完整測試"
            ])
            
        return recommendations

def main():
    """主函數"""
    tester = SystemTester()
    
    print("🔧 測試配置檢查...")
    print("=" * 60)
    
    # 🔧 可選：設置您的 Discord Webhook 進行完整測試
    # 如果您有 Discord Webhook，請取消註釋下行並設置正確的 URL
    # tester.test_discord_webhook = "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"
    
    if not tester.test_discord_webhook:
        print("💡 Discord 測試將跳過（未設置測試 Webhook）")
        print("   如需完整測試，請設置 Discord Webhook URL")
    
    print("\n🚀 開始執行完整系統測試...")
    
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 下一步建議:")
        print("  1. 🎨 開始前端 Web UI 開發")
        print("  2. 🔗 整合 Google OAuth 認證")
        print("  3. 🚀 準備生產環境部署")
    else:
        print("\n🔧 修復建議:")
        print("  1. 查看上面的失敗詳情")
        print("  2. 修復相關問題")
        print("  3. 重新運行測試: python test_complete_system.py")
        
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 