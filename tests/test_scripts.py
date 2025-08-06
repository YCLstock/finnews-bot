import pytest
from scripts.run_smart_pusher import SmartPusher

@pytest.fixture
def pusher():
    pusher_instance = SmartPusher()
    # 固定權重以便測試
    pusher_instance.tag_weight = 0.7
    pusher_instance.keyword_weight = 0.3
    return pusher_instance

# 模擬的文章資料
article_perfect_match = {
    'title': '蘋果發布驚人的M4晶片',
    'summary': '這次蘋果的發布會展示了最新的AI技術。',
    'tags': ['APPLE', 'AI_TECH']
}

article_tag_only = {
    'title': '庫克談論Vision Pro的未來',
    'summary': '執行長表示對擴增實境市場充滿信心。',
    'tags': ['APPLE']
}

article_keyword_only = {
    'title': '一篇關於蘋果西打的文章',
    'summary': '這個飲料品牌「蘋果西打」最近有新的動態。',
    'tags': ['FOOD', 'BEVERAGE']
}

article_no_match = {
    'title': '台積電股價再創新高',
    'summary': '半導體行業持續看好。',
    'tags': ['TSMC', 'SEMICONDUCTOR']
}

# 測試案例
@pytest.mark.parametrize("article, user_keywords, interest_topics, expected_score", [
    # 案例1: 標籤和關鍵字都完美匹配 (高分)
    (article_perfect_match, ['蘋果', 'AI'], ['APPLE', 'AI_TECH'], (1.0 * 0.7) + (1.0 * 0.3)),

    # 案例2: 只有標籤匹配 (語義相關，分數中等)
    (article_tag_only, ['蘋果'], ['APPLE'], (1.0 * 0.7) + (0.0 * 0.3)),

    # 案例3: 只有關鍵字匹配 (字面相關，分數較低)
    (article_keyword_only, ['蘋果西打'], ['TECH'], (0.0 * 0.7) + (1.0 * 0.3)),

    # 案例4: 完全不匹配 (0分)
    (article_no_match, ['蘋果'], ['APPLE'], (0.0 * 0.7) + (0.0 * 0.3)),

    # 案例5: 標籤部分匹配 (用戶關心的主題100%命中)
    (article_perfect_match, [], ['APPLE'], (1.0 * 0.7) + (0.0 * 0.3)), # interest_topics 裡的 'APPLE' 100% 被 article_tags 滿足

    # 案例6: 關鍵字在摘要中
    (article_perfect_match, ['AI技術'], ['TECH'], (0.0 * 0.7) + (1.0 * 0.3)),
])
def test_calculate_hybrid_score(pusher, article, user_keywords, interest_topics, expected_score):
    score = pusher._calculate_hybrid_score(article, user_keywords, interest_topics)
    assert abs(score - expected_score) < 0.001 # 使用浮點數比較
