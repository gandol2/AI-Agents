import os, re

from crewai.tools import tool
from firecrawl import FirecrawlApp, ScrapeOptions

@tool
def web_search_tool(query: str):
    """
    웹 검색 도구.
    Args:
        query: str
            웹에서 검색할 쿼리
    Returns:
        웹사이트 내용을 담은 검색 결과 목록을 마크다운 형식으로 반환
    """
    app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

    response = app.search(
                    query=query,
                    limit=2,
                    scrape_options=ScrapeOptions(formats=["markdown"])
                )
    # print(response)

    if not response.success:
        return "ERROR using tool."

    cleaned_chunks = []

    for result in response.data:
        title = result["title"]
        url = result["url"]
        markdown = result["markdown"]
        cleaned = re.sub(r'\\+|\n+', '', markdown).strip()
        cleaned = re.sub(r"\[[^\]]+\]\([^\)]+\)|https?://[^\s]+", "", cleaned)

        cleaned_result = {
            "title": title,
            "url": url,
            "markdown": cleaned,
        }
        cleaned_chunks.append(cleaned_result)
    return cleaned_chunks
        
# print(web_search_tool("remote jobs in korea rust developer"))