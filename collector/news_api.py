# Naver 뉴스 검색 API 호출 및 데이터 취득

import os
import re
import requests
from dotenv import load_dotenv

# .env 파일에서 API 키를 로드합니다.
load_dotenv()


class NewsCollector:
    def __init__(self):
        self.client_id = os.getenv("NAVER_CLIENT_ID")
        self.client_secret = os.getenv("NAVER_CLIENT_SECRET")
        self.base_url = "https://openapi.naver.com/v1/search/news.json"

    def fetch_economic_news(self, query="경제", page_size=5, start=1, sort="date"):
        """
        Naver 뉴스 검색 API를 통해 경제 관련 기사를 수집합니다.
        sort: sim(정확도순) | date(날짜순)
        """
        if not self.client_id or not self.client_secret:
            print("NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET이 설정되지 않았습니다.")
            return []

        params = {
            "query": query,
            "display": page_size,
            "start": start,
            "sort": sort,
        }
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

        try:
            response = requests.get(self.base_url, params=params, headers=headers)
            response.raise_for_status()  # 200 OK가 아니면 에러 발생

            data = response.json()
            items = data.get("items", [])
            return self._format_articles(items)

        except Exception as e:
            print(f"뉴스 수집 중 오류 발생: {e}")
            return []

    def _strip_html(self, text):
        if not text:
            return text
        # Naver 뉴스 검색 결과는 <b> 태그가 포함됨
        text = re.sub(r"<[^>]+>", "", text)
        return text.replace("&quot;", "\"").replace("&amp;", "&")

    def _format_articles(self, items):
        """
        AI 모델이 처리하기 쉽도록 필요한 데이터만 추출하여 정제합니다.
        """
        formatted_list = []
        for item in items:
            clean_article = {
                "title": self._strip_html(item.get("title")),
                "author": None,
                "description": self._strip_html(item.get("description")),
                "content": None,
                "url": item.get("originallink") or item.get("link"),
                "publishedAt": item.get("pubDate"),
            }
            formatted_list.append(clean_article)

        return formatted_list


# 테스트 실행부
if __name__ == "__main__":
    collector = NewsCollector()
    news_data = collector.fetch_economic_news(query="금리", page_size=3, sort="date")

    for i, news in enumerate(news_data):
        print(f"[{i+1}] {news['title']}")
        desc = news["description"] or ""
        print(f"요약 재료: {desc[:50]}...")
        print("-" * 30)
