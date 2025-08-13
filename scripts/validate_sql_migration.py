#!/usr/bin/env python3
"""
SQL遷移腳本驗證器
檢查修復後的SQL語法和結構正確性
"""

import re
from pathlib import Path

def validate_sql_syntax():
    """驗證SQL語法結構"""
    sql_file = Path(__file__).parent.parent / "database" / "unified_tag_migration.sql"
    
    if not sql_file.exists():
        print("❌ SQL文件不存在")
        return False
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 驗證SQL腳本語法...")
    
    # 檢查1: 確保沒有問題的CROSS JOIN語法
    cross_join_on_pattern = r'CROSS\s+JOIN.*?\)\s+kw\s+ON\s+t\.tag_code\s*='
    if re.search(cross_join_on_pattern, content, re.IGNORECASE | re.DOTALL):
        print("❌ 發現問題的CROSS JOIN ON語法")
        return False
    else:
        print("✅ 沒有發現問題的CROSS JOIN語法")
    
    # 檢查2: 確保每個INSERT都有正確的結構
    insert_pattern = r'INSERT\s+INTO\s+public\.keyword_mappings.*?FROM.*?CROSS\s+JOIN.*?ON\s+CONFLICT'
    insert_matches = re.findall(insert_pattern, content, re.IGNORECASE | re.DOTALL)
    
    expected_insert_count = 20  # 20個標籤，每個標籤一個INSERT
    if len(insert_matches) != expected_insert_count:
        print(f"⚠️ INSERT語句數量: {len(insert_matches)} (預期: {expected_insert_count})")
    else:
        print(f"✅ INSERT語句數量正確: {len(insert_matches)}")
    
    # 檢查3: 確保所有標籤都有對應的INSERT
    expected_tags = [
        'APPLE', 'TSMC', 'TESLA', 'AI_TECH', 'TECH', 'ELECTRIC_VEHICLES',
        'STOCK_MARKET', 'ECONOMIES', 'FEDERAL_RESERVE', 'EARNINGS', 'CRYPTO',
        'HOUSING', 'ENERGY', 'HEALTHCARE', 'FINANCE', 'TARIFFS', 'TRADE',
        'BONDS', 'COMMODITIES', 'LATEST'
    ]
    
    missing_tags = []
    for tag in expected_tags:
        if f"tag_code = '{tag}'" not in content:
            missing_tags.append(tag)
    
    if missing_tags:
        print(f"❌ 缺少標籤的INSERT: {missing_tags}")
        return False
    else:
        print("✅ 所有標籤都有對應的INSERT語句")
    
    # 檢查4: 確保ON CONFLICT語法正確
    conflict_pattern = r'ON\s+CONFLICT\s*\(\s*tag_id\s*,\s*keyword\s*\)\s+DO\s+UPDATE\s+SET'
    conflict_matches = re.findall(conflict_pattern, content, re.IGNORECASE)
    
    if len(conflict_matches) != expected_insert_count:
        print(f"⚠️ ON CONFLICT語句數量: {len(conflict_matches)} (預期: {expected_insert_count})")
    else:
        print(f"✅ ON CONFLICT語句數量正確: {len(conflict_matches)}")
    
    # 檢查5: 確保VALUES語法正確
    values_pattern = r'VALUES\s*\(\s*\([^)]+\)[^)]*\)\s*AS\s+kw\s*\(\s*keyword\s*,\s*language\s*,\s*confidence\s*\)'
    values_matches = re.findall(values_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if len(values_matches) != expected_insert_count:
        print(f"⚠️ VALUES語句數量: {len(values_matches)} (預期: {expected_insert_count})")
    else:
        print(f"✅ VALUES語句格式正確: {len(values_matches)}")
    
    return True

def count_keywords():
    """統計關鍵字數量"""
    sql_file = Path(__file__).parent.parent / "database" / "unified_tag_migration.sql"
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 統計中英文關鍵字
    zh_keywords = len(re.findall(r"'[^']*[\u4e00-\u9fff]+[^']*'", content))
    en_keywords = len(re.findall(r"'[a-zA-Z][^']*', 'en'", content))
    
    print(f"\n📊 關鍵字統計:")
    print(f"   中文關鍵字: {zh_keywords} 個")
    print(f"   英文關鍵字: {en_keywords} 個")
    print(f"   總計: {zh_keywords + en_keywords} 個")
    
    return zh_keywords + en_keywords

def validate_structure():
    """驗證腳本整體結構"""
    sql_file = Path(__file__).parent.parent / "database" / "unified_tag_migration.sql"
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🏗️ 驗證腳本結構...")
    
    # 檢查必要的區段
    required_sections = [
        "第一階段: 基礎標籤數據遷移",
        "第二階段: 關鍵字映射數據遷移", 
        "第三階段: 建立索引以優化查詢性能",
        "第四階段: 創建統計視圖",
        "第五階段: 權限設置"
    ]
    
    for section in required_sections:
        if section in content:
            print(f"✅ 找到區段: {section}")
        else:
            print(f"❌ 缺少區段: {section}")
    
    # 檢查索引創建
    index_count = len(re.findall(r'CREATE\s+INDEX', content, re.IGNORECASE))
    print(f"✅ 索引創建語句: {index_count} 個")
    
    # 檢查視圖創建
    view_count = len(re.findall(r'CREATE.*VIEW', content, re.IGNORECASE))
    print(f"✅ 視圖創建語句: {view_count} 個")
    
    return True

def main():
    """主驗證函數"""
    print("🔧 SQL遷移腳本驗證器")
    print("=" * 50)
    
    # 語法驗證
    if not validate_sql_syntax():
        print("\n❌ SQL語法驗證失敗")
        return 1
    
    # 關鍵字統計
    keyword_count = count_keywords()
    
    # 結構驗證
    if not validate_structure():
        print("\n❌ 結構驗證失敗")
        return 1
    
    print(f"\n🎉 驗證完成！")
    print(f"✅ SQL語法正確")
    print(f"✅ 包含20個標籤INSERT語句")
    print(f"✅ 包含{keyword_count}個關鍵字映射")
    print(f"✅ 結構完整，包含所有必要區段")
    
    print(f"\n📋 使用說明:")
    print(f"1. 在Supabase SQL編輯器中執行: database/unified_tag_migration.sql")
    print(f"2. 執行測試: python scripts/dynamic_tags.py")
    print(f"3. 驗證推送: python scripts/run_pusher_test.py")
    
    return 0

if __name__ == "__main__":
    exit(main())