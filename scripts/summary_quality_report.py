#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
摘要品質監控報告工具
用於查看和分析摘要生成的品質統計
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.summary_quality_monitor import get_quality_monitor
import argparse

def show_current_session():
    """顯示當前會話統計"""
    monitor = get_quality_monitor()
    stats = monitor.get_session_summary()
    
    print("=== 當前會話統計 ===")
    print(f"總嘗試次數: {stats['total_attempts']}")
    print(f"成功次數: {stats['successful_summaries']}")
    print(f"失敗次數: {stats['failed_summaries']}")
    print(f"成功率: {stats['success_rate']:.1%}")
    print(f"中文有效次數: {stats['chinese_valid']}")
    print(f"中文有效率: {stats['chinese_valid_rate']:.1%}")
    print(f"需要重試次數: {stats['retry_needed']}")
    print(f"重試率: {stats['retry_rate']:.1%}")
    print(f"平均生成時間: {stats['avg_generation_time']:.2f}秒")

def show_recent_analysis(hours=24):
    """顯示最近N小時分析"""
    monitor = get_quality_monitor()
    analysis = monitor.analyze_recent_quality(hours)
    
    print(f"\n=== 最近 {hours} 小時分析 ===")
    
    if 'error' in analysis:
        print(f"錯誤: {analysis['error']}")
        return
    
    print(f"時間範圍: 最近 {analysis['period_hours']} 小時")
    print(f"總處理量: {analysis['total_attempts']} 篇")
    print(f"成功次數: {analysis['successful_summaries']}")
    print(f"成功率: {analysis['success_rate']:.1%}")
    print(f"中文有效次數: {analysis['chinese_valid']}")
    print(f"中文有效率: {analysis['chinese_valid_rate']:.1%}")
    print(f"重試次數: {analysis['retry_needed']}")
    print(f"重試率: {analysis['retry_rate']:.1%}")
    print(f"平均品質分數: {analysis['avg_quality_score']:.2f}")
    print(f"品質分數範圍: {analysis['min_quality_score']:.2f} ~ {analysis['max_quality_score']:.2f}")
    print(f"平均生成時間: {analysis['avg_generation_time']:.2f}秒")
    
    # 顯示最近樣本
    if 'sample_recent' in analysis and analysis['sample_recent']:
        print(f"\n--- 最近樣本 ---")
        for i, sample in enumerate(analysis['sample_recent'][-3:], 1):
            status = "成功" if sample['success'] else "失敗"
            print(f"{i}. {status} | 品質: {sample['quality_score']:.2f} | 嘗試: {sample['attempt_count']}次")
            print(f"   標題: {sample['title'][:50]}...")
            if sample['summary']:
                print(f"   摘要: {sample['summary'][:50]}...")

def show_full_report():
    """顯示完整品質報告"""
    monitor = get_quality_monitor()
    report = monitor.generate_quality_report()
    print(report)

def clear_old_logs(days=7):
    """清理舊日誌"""
    monitor = get_quality_monitor()
    print(f"正在清理 {days} 天前的日誌...")
    monitor.clear_old_logs(days)
    print("清理完成")

def main():
    parser = argparse.ArgumentParser(description='摘要品質監控報告工具')
    parser.add_argument('--session', action='store_true', help='顯示當前會話統計')
    parser.add_argument('--recent', type=int, default=24, help='顯示最近N小時分析 (預設24)')
    parser.add_argument('--report', action='store_true', help='顯示完整品質報告')
    parser.add_argument('--clear', type=int, help='清理N天前的日誌')
    parser.add_argument('--all', action='store_true', help='顯示所有資訊')
    
    args = parser.parse_args()
    
    if not any([args.session, args.recent != 24, args.report, args.clear, args.all]):
        args.all = True  # 預設顯示所有
    
    try:
        if args.clear:
            clear_old_logs(args.clear)
            return
        
        if args.session or args.all:
            show_current_session()
        
        if args.recent or args.all:
            show_recent_analysis(args.recent)
        
        if args.report or args.all:
            print("\n" + "="*60)
            show_full_report()
            
    except Exception as e:
        print(f"執行錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()