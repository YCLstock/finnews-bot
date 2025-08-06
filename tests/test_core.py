import pytest
from core.topics_mapper import TopicsMapper

@pytest.fixture
def mapper():
    # 使用一個固定的、可預測的配置來進行測試
    # 這避免了測試受到 topics_keyword_mapping.json 變化的影響
    mapper_instance = TopicsMapper()
    mapper_instance.mapping_rules = {
        'exact_match_weight': 3,
        'partial_match_weight': 1,
    }
    return mapper_instance

@pytest.mark.parametrize("user_keyword, topic_keywords, expected_score", [
    # 測試精確匹配 (大小寫不敏感)
    ("bitcoin", ["bitcoin", "crypto"], 3),
    ("Bitcoin", ["bitcoin", "crypto"], 3),
    ("比特幣", ["比特幣", "加密貨幣"], 3),
    
    # 測試部分匹配 (用戶關鍵字是主題關鍵字的子字串)
    ("apple", ["apple inc", "aapl"], 1),
    
    # 測試部分匹配 (主題關鍵字是用戶關鍵字的子字串)
    ("ai", ["generative ai"], 1),

    # 測試無匹配
    ("stock", ["bitcoin", "crypto"], 0),
    
    # 測試列表中有多個關鍵字，應返回最高分
    ("tesla", ["tsla", "tesla", "tesla motors", "elon musk"], 3),
])
def test_calculate_match_score(mapper, user_keyword, topic_keywords, expected_score):
    score = mapper._calculate_match_score(user_keyword, topic_keywords)
    assert score == expected_score
