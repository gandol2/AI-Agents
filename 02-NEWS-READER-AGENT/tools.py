from crewai.tools import tool
from crewai_tools import SerperDevTool
from playwright.sync_api import sync_playwright
import time
from bs4 import BeautifulSoup

# Initialize the tool for internet searching capabilities
search_tool = SerperDevTool(n_results=30)

# print(search_tool.run(search_query="우크라이나 러시아 전쟁"))

@tool
def scrap_tool(url:str):
    """
    웹사이트 내용을 읽어야 할때 이 함수를 사용하세요. 
    만약 웹사이트에 접근할수 없으면 아무것도 반환하지 않습니다.
    Returns the content of a website.
    Input should be a 'url' string. for example (https://www.chosun.com/international/international_general/2025/09/28/SE5VCAM3KRDGPHE4OJO5U6VGDU/)
    """

    print(f"Scrapping URL : {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        time.sleep(5)

        html = page.content()

        browser.close()

        soup = BeautifulSoup(html, 'html.parser')

        unwanted_tags = []

        for tag in soup.find_all(unwanted_tags):
            tag.decompose()

        content = soup.get_text(separator=" ")

        return content if content != "" else "컨텐츠가 없습니다."

# scrap_tool("https://www.chosun.com/international/international_general/2025/09/28/SE5VCAM3KRDGPHE4OJO5U6VGDU/")
