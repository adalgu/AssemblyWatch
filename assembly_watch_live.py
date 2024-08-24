import os
from dotenv import load_dotenv
import argparse
from slack_sdk.errors import SlackApiError
from slack_sdk import WebClient
import time
import datetime
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from notion_client import Client
from bs4 import BeautifulSoup
import sqlite3

# .env 파일 로드
load_dotenv()

# 환경 변수에서 값을 가져옴
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_PAGE_ID = os.getenv('NOTION_PAGE_ID')
SLACK_ALERT_WEBHOOK = os.getenv('SLACK_ALERT_WEBHOOK')
SLACK_TOKEN = os.getenv('SLACK_TOKEN')
SLACK_CHANNEL_ID = os.getenv('SLACK_CHANNEL_ID')

# 인자 파싱 (환경 변수로 설정되지 않은 값들을 위해)
parser = argparse.ArgumentParser(description='국회 의사중계 모니터링 스크립트')
parser.add_argument('--notion_api_key',
                    default=NOTION_API_KEY, help='Notion API key')
parser.add_argument('--notion_page_id',
                    default=NOTION_PAGE_ID, help='Notion page ID')
parser.add_argument('--slack_alert_webhook',
                    default=SLACK_ALERT_WEBHOOK, help='Slack alert webhook URL')
parser.add_argument('--slack_token', default=SLACK_TOKEN, help='Slack token')
parser.add_argument('--slack_channel_id',
                    default=SLACK_CHANNEL_ID, help='Slack channel ID')

args = parser.parse_args()

# 환경 변수나 인자에서 가져온 값으로 변수 설정
NOTION_API_KEY = args.notion_api_key
NOTION_PAGE_ID = args.notion_page_id
SLACK_ALERT_WEBHOOK = args.slack_alert_webhook
SLACK_TOKEN = args.slack_token
SLACK_CHANNEL_ID = args.slack_channel_id

# 알림을 원하는 키워드 입력 (이 부분은 환경 변수나 설정 파일로 관리할 수도 있습니다)
ALERT_KEYWORDS = ['카카오', '카카오모빌리티', '택시', '모빌리티', '류긍선', '김범수']

# Notion 클라이언트 초기화
notion = Client(auth=NOTION_API_KEY)

# Slack 클라이언트 초기화
slack_client = WebClient(token=SLACK_TOKEN)

# 데이터베이스 연결
conn = sqlite3.connect('assembly_watch.db')
cursor = conn.cursor()


# 테이블 생성
cursor.execute('''
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    title TEXT,
    date TEXT,
    start_time TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY,
    session_id INTEGER,
    timestamp TEXT,
    content TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions (id)
)
''')

conn.commit()


def initialize_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging"])
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def get_live_broadcasts():
    driver = initialize_chrome_driver()
    url = 'https://assembly.webcast.go.kr/main/'
    driver.get(url)
    time.sleep(2)

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, 'html.parser')
    soup = soup.find('div', class_='ma_video_list')

    table_data = []
    for li in soup.select('ul#gvlist li'):
        title = li.select_one('.tit_box .tit')
        title = title.get_text(strip=True) if title else None

        status = li.select_one('.btn_box .mark')
        if status:
            status = status.get_text(strip=True)
        elif li.select_one('.btn_box .btn_vdo_red'):
            status = "생중계"
        else:
            status = None

        live_link = li.select_one('.btn_box .btn_vdo_red')
        if live_link:
            href_value = live_link.get('href')[2:]
            live_link = "https://assembly.webcast.go.kr/main/" + href_value
        else:
            live_link = None

        if status == "생중계" and live_link:
            table_data.append({
                'name': title,
                'status': status,
                'live_link': live_link,
            })

    return table_data


def save_text_to_file(text, filename):
    # 'transcripts' 폴더 경로 생성
    folder_path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'transcripts')

    # 'transcripts' 폴더가 없으면 생성
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # 파일 경로 생성
    file_path = os.path.join(folder_path, filename)

    # 파일에 텍스트 추가
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(text + "\n")


def append_block_to_notion(page_id, content, block_type="paragraph"):
    try:
        notion.blocks.children.append(
            block_id=page_id,
            children=[
                {
                    "object": "block",
                    "type": block_type,
                    block_type: {
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
        print(f"Error appending to Notion: {str(e)}")


def send_slack_message(text):
    try:
        response = slack_client.chat_postMessage(
            channel=SLACK_CHANNEL_ID,
            text=text,
        )
        return response['ts']
    except SlackApiError as e:
        print(f"Error sending Slack message: {e.response['error']}")
        return None


def send_slack_reply(text, thread_ts):
    try:
        response = slack_client.chat_postMessage(
            channel=SLACK_CHANNEL_ID,
            thread_ts=thread_ts,
            text=text
        )
        return response['ts']
    except SlackApiError as e:
        print(f"Error sending Slack reply: {e.response['error']}")
        return None


def add_session_to_db(title, date, start_time):
    cursor.execute('INSERT INTO sessions (title, date, start_time) VALUES (?, ?, ?)',
                   (title, date, start_time))
    conn.commit()
    return cursor.lastrowid


def add_transcript_to_db(session_id, timestamp, content):
    cursor.execute('INSERT INTO transcripts (session_id, timestamp, content) VALUES (?, ?, ?)',
                   (session_id, timestamp, content))
    conn.commit()


def monitor_broadcast(url, title, db):
    driver = initialize_chrome_driver()
    driver.get(url)
    time.sleep(5)

    try:
        button = driver.find_element(By.XPATH, "//*[@id='smi_btn']")
        button.click()
        print("AI 자막 켜기 완료")

        date = driver.find_element(By.CSS_SELECTOR, "#xdate").text
        start_time = get_current_time()
        initial_text = f"{title}\n{date}\n{start_time}\n"

        ts = send_slack_message(initial_text)

        safe_date = date.replace(" ", "_").replace("-", "_").replace(":", "_")
        first_word_of_title = title.split(" ")[0]
        filename = f"{safe_date}_{first_word_of_title}.txt"

        save_text_to_file(initial_text, filename)
        append_block_to_notion(NOTION_PAGE_ID, initial_text)

        session_id = db.add_session(title, date, start_time)

        prev_texts = set()
        last_time_recorded = time.time()

        while True:
            time.sleep(3)

            if time.time() - last_time_recorded >= 60:
                current_time_text = f"\n{get_current_time()}\n"
                save_text_to_file(current_time_text, filename)
                append_block_to_notion(NOTION_PAGE_ID, current_time_text)
                db.add_transcript(
                    session_id, get_current_time(), current_time_text)
                last_time_recorded = time.time()

            curr_elements = driver.find_elements(
                By.CSS_SELECTOR, "p[class^='smi_word stxt']")
            curr_texts = set()

            for el in curr_elements:
                span_elements = el.find_elements(By.TAG_NAME, "span")
                for span in span_elements:
                    curr_texts.add(span.text)

            new_texts = curr_texts - prev_texts
            if new_texts:
                content = "\n".join(new_texts)

                save_text_to_file(content, filename)
                append_block_to_notion(NOTION_PAGE_ID, content)
                send_slack_reply(content, ts)
                db.add_transcript(session_id, get_current_time(), content)

                if any(keyword in content for keyword in ALERT_KEYWORDS):
                    alert_message = f"⚠️ {title} {get_current_time()} \n{
                        content}\n"
                    send_slack_message(alert_message)

                prev_texts = curr_texts

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        driver.quit()


def get_current_time():
    now = datetime.datetime.now()
    return now.strftime("%p %I시:%M분").replace("AM", "오전").replace("PM", "오후")


def main():
    while True:
        try:
            live_broadcasts = get_live_broadcasts()
            if live_broadcasts:
                print("현재 생중계 중인 방송:")
                for idx, broadcast in enumerate(live_broadcasts, 1):
                    print(f"{idx}. {broadcast['name']}")

                choice = int(input("모니터링할 방송 번호를 선택하세요: ")) - 1
                if 0 <= choice < len(live_broadcasts):
                    selected_broadcast = live_broadcasts[choice]
                    print(f"선택된 방송: {selected_broadcast['name']}")
                    monitor_broadcast(
                        selected_broadcast['live_link'], selected_broadcast['name'])
                else:
                    print("잘못된 선택입니다.")
            else:
                current_time = get_current_time()
                print("현재 생중계 중인 방송이 없습니다. (현재 시각: {current_time})")
                time.sleep(300)  # 5분 대기 후 다시 확인
        except Exception as e:
            current_time = get_current_time()
            print(f"An error occurred in main loop: {
                  str(e)} (현재 시각: {current_time})")
            time.sleep(60)  # 1분 대기 후 다시 시도


if __name__ == "__main__":
    main()
    conn.close()  # 데이터베이스 연결 종료
