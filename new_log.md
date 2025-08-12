INFO:scraper.scraper:正在處理新文章: Do Wall Street Analysts Like Accenture Stock?...
INFO:scraper.scraper:使用 ScraperV2 抓取: https://finance.yahoo.com/news/wall-street-analysts-accenture-stock-07...
ERROR:scraper.scraper:處理文章時發生錯誤: https://finance.yahoo.com/news/wall-street-analysts-accenture-stock-074522441.html
Traceback (most recent call last):
  File "D:\ai-new\finnews-bot\scraper\scraper.py", line 130, in _process_single_article
    content = self.scrape_article_content(news_item['link'])
  File "D:\ai-new\finnews-bot\scraper\scraper.py", line 162, in scrape_article_content
    result = self.scraper_v2._scrape_single_article(url)
  File "D:\ai-new\finnews-bot\scraper\scraper_v2.py", line 62, in _scrape_single_article
    ('div', {'data-testid': 'article-content-wrapper'})
TypeError: 'tuple' object is not callable
INFO:httpx:HTTP Request: GET https://gbobozzqoqfhqmttwzwn.supabase.co/rest/v1/news_articles?select=id&original_url=eq.https%3A%2F%2Ffinance.yahoo.com%2Fnews%2Fadobe-stock-outlook-wall-street-074033271.html "HTTP/2 200 OK"
INFO:scraper.scraper:正在處理新文章: Adobe Stock Outlook: Is Wall Street Bullish or Bea...
INFO:scraper.scraper:使用 ScraperV2 抓取: https://finance.yahoo.com/news/adobe-stock-outlook-wall-street-0740332...
ERROR:scraper.scraper:處理文章時發生錯誤: https://finance.yahoo.com/news/adobe-stock-outlook-wall-street-074033271.html
Traceback (most recent call last):
  File "D:\ai-new\finnews-bot\scraper\scraper.py", line 130, in _process_single_article
    content = self.scrape_article_content(news_item['link'])
  File "D:\ai-new\finnews-bot\scraper\scraper.py", line 162, in scrape_article_content
    result = self.scraper_v2._scrape_single_article(url)
  File "D:\ai-new\finnews-bot\scraper\scraper_v2.py", line 62, in _scrape_single_article
    ('div', {'data-testid': 'article-content-wrapper'})
TypeError: 'tuple' object is not callable
INFO:httpx:HTTP Request: GET https://gbobozzqoqfhqmttwzwn.supabase.co/rest/v1/news_articles?select=id&original_url=eq.https%3A%2F%2Ffinance.yahoo.com%2Fnews%2F5-must-read-analyst-questions-072742641.html "HTTP/2 200 OK"
INFO:scraper.scraper:正在處理新文章: 5 Must-Read Analyst Questions From Jackson Financi...
INFO:scraper.scraper:使用 ScraperV2 抓取: https://finance.yahoo.com/news/5-must-read-analyst-questions-072742641...
ERROR:scraper.scraper:處理文章時發生錯誤: https://finance.yahoo.com/news/5-must-read-analyst-questions-072742641.html
Traceback (most recent call last):
  File "D:\ai-new\finnews-bot\scraper\scraper.py", line 130, in _process_single_article
    content = self.scrape_article_content(news_item['link'])
  File "D:\ai-new\finnews-bot\scraper\scraper.py", line 162, in scrape_article_content
    result = self.scraper_v2._scrape_single_article(url)
  File "D:\ai-new\finnews-bot\scraper\scraper_v2.py", line 62, in _scrape_single_article
    ('div', {'data-testid': 'article-content-wrapper'})