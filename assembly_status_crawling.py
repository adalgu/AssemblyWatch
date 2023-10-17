from tabulate import tabulate
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import pandas as pd
import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Notion, Slack 클라이언트 초기화
from notion_client import Client
NOTION_DATABASE_ID = "a008ba7d186340a08288adda750a03ad"
NOTION_API_KEY = "secret_qQXJvW0U5AKlbxAtQFzq7yac9mx8WahKxYkTFTzOEtV"

notion = Client(auth=NOTION_API_KEY)


def initialize_chrome_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging"])
    # Add headless option
    chrome_options.add_argument("--headless")
    service = Service(executable_path=ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


driver = initialize_chrome_driver()
# 웹사이트에 접속
url = 'https://assembly.webcast.go.kr/main/'
driver.get(url)
time.sleep(2)

# 이 시점에서 페이지는 로드되었으므로, BeautifulSoup 등을 사용하여 HTML을 파싱할 수 있습니다.
html = driver.page_source

# 웹 드라이버 종료
driver.quit()

soup = BeautifulSoup(html, 'html.parser')
soup = soup.find('div', class_='ma_video_list')
# soup = soup.find('div', class_='ma_video_list')
print(soup.prettify())
# Parsing the provided HTML and extracting the required information
committee_data = []

table_data_corrected = []
# soup = BeautifulSoup(html, 'html.parser')
for li in soup.select('ul#gvlist li'):
    # 위원회명
    title = li.select_one('.tit_box .tit')
    if title:
        title = title.get_text(strip=True)
    else:
        title = None

    # 상태
    if li.select_one('.btn_box .mark'):
        status = li.select_one('.btn_box .mark').get_text(strip=True)
    elif li.select_one('.btn_box .btn_vdo_red'):
        status = "생중계"
    else:
        status = None

    # 링크1 (생중계)
    live_link = li.select_one('.btn_box .btn_vdo_red')
    if live_link:
        live_link = live_link['href']
    else:
        live_link = None

    # 링크2 (영상회의록)
    vod_link = li.select_one('.btn_box .onvod')
    if vod_link:
        vod_link = vod_link['href']
    else:
        vod_link = None

    # 상세 설명
    desc = li.select_one('.desc')
    if desc:
        desc = desc.get_text(strip=True)
    else:
        desc = None

    table_data_corrected.append({
        'name': title,
        'status': status,
        'live_link': live_link,
        'vod_link': vod_link,
        'description': desc
    })

# 데이터를 DataFrame으로 변환합니다.
df_corrected = pd.DataFrame(table_data_corrected)


result = print(tabulate(df_corrected, headers="keys", tablefmt="simple_grid"))


def create_notion_page(database_id, title):
    try:
        new_page = notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "title": [{"type": "text", "text": {"content": title}}]}
        )
        return new_page['id']
    except Exception as e:
        print("Error creating a new Notion page:", str(e))
        return None


def append_to_notion(page_id, content):
    try:
        notion.blocks.children.append(
            block_id=page_id,
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": content
                                }
                            }
                        ]
                    }
                }
            ]
        )
    except Exception as e:
        print("Error appending block to Notion page:", str(e))


SLACK_ALERT_WEBHOOK = "https://hooks.slack.com/services/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"  # 2023-국정감사-모니터링
# SLACK_ALERT_WEBHOOK = "https://hooks.slack.com/services/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"  # 대외협력실_new

# WebClient 인스턴스화: API 메서드를 호출할 클라이언트 생성
# client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

# Slack API token
# User OAuth Token
token = 'xoxp-194626280262-697909535825-6033906233927-b41117a1bea58c97265e28c720369ba2'
# 채널 ID
channel_id = "C060BR0E4KF"  # 모니터링

# slack
client = WebClient(token=token)


def send_message(text):
    """
    슬랙에 메시지를 보내는 함수
    """
    try:
        # 메시지 보내기
        response = client.chat_postMessage(
            channel=channel_id,
            text=text,
        )
        # 메시지의 'ts' 값 반환
        return response['ts']
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")
        return None


send_message(result)
