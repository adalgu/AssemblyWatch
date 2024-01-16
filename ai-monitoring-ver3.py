from datetime import date
import sys
from dotenv import load_dotenv
import os
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
from notion_client import Client

# Load environment variables from .env file
load_dotenv()

# Notion, Slack configuration
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
SLACK_USER_TOKEN = os.getenv("SLACK_USER_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

# sys.exit()
NOTION_DATABASE_ID = "a008ba7d186340a08288adda750a03ad"
NOTION_API_KEY = "secret_qQXJvW0U5AKlbxAtQFzq7yac9mx8WahKxYkTFTzOEtV"

# notion = Client(auth=NOTION_API_KEY)
# Initialize Notion and Slack clients
notion = Client(auth=NOTION_API_KEY)
slack_client = WebClient(token=SLACK_USER_TOKEN)
# token = 'xoxp-194626280262-697909535825-6033906233927-b41117a1bea58c97265e28c720369ba2'
# slack_client = WebClient(token=token)


def initialize_chrome_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging"])
    chrome_options.add_argument("--headless")
    service = Service(executable_path=ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def fetch_committee_status(url):
    driver = initialize_chrome_driver()
    driver.get(url)
    time.sleep(2)

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, 'html.parser')
    soup = soup.find('div', class_='ma_video_list')
    committee_data = []

    for li in soup.select('ul#gvlist li'):
        title = li.select_one('.tit_box .tit')
        title = title.get_text(strip=True) if title else None

        if li.select_one('.btn_box .mark'):
            status = li.select_one('.btn_box .mark').get_text(strip=True)
        elif li.select_one('.btn_box .btn_vdo_red'):
            status = "생중계"
        else:
            status = None

        live_link = li.select_one('.btn_box .btn_vdo_red')
        live_link = "https://assembly.webcast.go.kr/main/" + \
            live_link.get('href')[2:] if live_link else None

        vod_link = li.select_one('.btn_box .onvod')
        vod_link = vod_link['href'] if vod_link else None

        desc = li.select_one('.desc')
        desc = desc.get_text(strip=True) if desc else None

        committee_data.append({
            'name': title,
            'status': status,
            'live_link': live_link,
            'vod_link': vod_link,
            'description': desc
        })

    return pd.DataFrame(committee_data)


def send_to_slack(df):
    """DataFrame에서 슬랙으로 메시지 보내기"""
    slack_client.chat_postMessage(
        channel=SLACK_CHANNEL_ID,
        text="<상임위명, 상태, 생방송링크, 설명>"
    )
    for _, committee in df.iterrows():
        message = f"{committee['name']}, "
        if committee['status']:
            message += f"{committee['status']}, "
        if committee['live_link']:
            message += f"{committee['live_link']}, "
        if committee['description']:
            message += f"{committee['description']}\n"
            try:
                slack_client.chat_postMessage(
                    channel=SLACK_CHANNEL_ID,
                    text=message
                )
            except SlackApiError as e:
                print(f"Error sending message to Slack: {e.response['error']}")


def check_webcast_status():
    url = 'https://assembly.webcast.go.kr/main/'
    df = fetch_committee_status(url)
    print(tabulate(df, headers="keys", tablefmt="simple_grid"))

    # 슬랙에 메시지로 보내기
    send_to_slack(df)


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


def create_committee_page_in_notion(committee_name, database_id):
    """노션에 상임위 페이지 생성. 이미 존재하는 경우 해당 페이지 ID 반환."""
    # 오늘 날짜와 상임위 이름을 결합하여 페이지 이름 생성
    today = date.today().strftime('%Y-%m-%d')
    full_name = f"{today} {committee_name}"

    filter_condition = {
        "property": "title",
        "text": {
            "equals": full_name
        }
    }

    matched_pages = notion.databases.query(
        database_id=database_id,
        filter=filter_condition
    ).get("results")

    # 일치하는 페이지가 있으면 그 페이지의 ID를 반환
    if matched_pages:
        return matched_pages[0]["id"]

    # 없으면 새로운 페이지 생성
    return create_notion_page(database_id, full_name)


def create_committee_pages_in_notion(committees, database_id):
    """노션에 여러 상임위 페이지 생성."""
    page_ids = {}
    for committee in committees:
        page_id = create_committee_page_in_notion(committee, database_id)
        page_ids[committee] = page_id
    return page_ids


if __name__ == "__main__":
    check_webcast_status()
    # 지정한 상임위 리스트 (예: 정무위, 국토위)
    specified_committees = ["정무위", "국토위"]

    # # 페이지 생성
    # page_ids = create_committee_pages_in_notion(
    #     specified_committees, NOTION_DATABASE_ID)
    # print(page_ids)

    NOTION_API_KEY = os.getenv("NOTION_API_KEY")
    DATABASE_ID = "a008ba7d186340a08288adda750a03ad"
    NOTION_VERSION = "2022-06-28"
    URL = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }

    data = {
        "filter": {
            "property": "title",
            "text": {
                "equals": True
            }
        }
    }

    response = requests.post(URL, headers=headers, json=data)
    response_data = response.json()

    print(response_data)
