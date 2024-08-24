from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.support import expected_conditions as EC
import os
from dotenv import load_dotenv
import argparse
from slack_sdk.errors import SlackApiError
from slack_sdk import WebClient
import time
import datetime
from datetime import datetime
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from notion_client import Client
from bs4 import BeautifulSoup
import sqlite3
import re
from telegram import Bot
from telegram.error import TelegramError
import asyncio

# .env 파일 로드
load_dotenv()

# 환경 변수에서 값을 가져옴
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_PAGE_ID = os.getenv('NOTION_PAGE_ID')
SLACK_ALERT_WEBHOOK = os.getenv('SLACK_ALERT_WEBHOOK')
SLACK_TOKEN = os.getenv('SLACK_TOKEN')
SLACK_CHANNEL_ID = os.getenv('SLACK_CHANNEL_ID')
TELEGRAM_BOT_TOKEN = os.getenv(
    'TELEGRAM_BOT_TOKEN', '7479535936:AAGiiWLhtbR-l10VuJo2AHEKqfc3ILxrJ0c')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# 인자 파싱
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
parser.add_argument('--telegram_bot_token',
                    default=TELEGRAM_BOT_TOKEN, help='Telegram Bot Token')
parser.add_argument('--telegram_chat_id',
                    default=TELEGRAM_CHAT_ID, help='Telegram Chat ID')

args = parser.parse_args()

# 환경 변수나 인자에서 가져온 값으로 변수 설정
NOTION_API_KEY = args.notion_api_key
NOTION_PAGE_ID = args.notion_page_id
SLACK_ALERT_WEBHOOK = args.slack_alert_webhook
SLACK_TOKEN = args.slack_token
SLACK_CHANNEL_ID = args.slack_channel_id
TELEGRAM_BOT_TOKEN = args.telegram_bot_token
TELEGRAM_CHAT_ID = args.telegram_chat_id

# 알림을 원하는 키워드 입력
ALERT_KEYWORDS = ['카카오', '카카오모빌리티', '택시', '모빌리티', '류긍선', '김범수']

# Notion 클라이언트 초기화
notion = Client(auth=NOTION_API_KEY)

# Slack 클라이언트 초기화
slack_client = WebClient(token=SLACK_TOKEN)

# Telegram 봇 초기화
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)

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

last_content = ""


def get_new_content(new_message):
    return new_message  # 모든 내용을 그대로 반환
    # global last_content
    # if not last_content:
    #     last_content = new_message
    #     return new_message

    # # Find the common prefix
    # i = 0
    # while i < len(last_content) and i < len(new_message) and last_content[i] == new_message[i]:
    #     i += 1

    # # Extract only the new content
    # new_content = new_message[i:]

    # last_content = new_message
    # return new_content.strip()


async def send_telegram_message(text):
    try:
        await telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
        # print(f"Telegram message sent: {text}")  # 디버깅용 출력
    except Exception as e:
        print(f"Error sending Telegram message: {str(e)}")


def send_slack_message(text):
    try:
        new_content = get_new_content(text)
        if new_content:
            response = slack_client.chat_postMessage(
                channel=SLACK_CHANNEL_ID,
                text=new_content,
            )
            # print(f"Slack message sent: {new_content}")  # 디버깅용 출력
            return response['ts']
    except SlackApiError as e:
        print(f"Error sending Slack message: {e.response['error']}")
    except Exception as e:
        print(f"Unexpected error sending Slack message: {str(e)}")
    return None


def send_slack_reply(text, thread_ts):
    try:
        new_content = get_new_content(text)
        if new_content:
            response = slack_client.chat_postMessage(
                channel=SLACK_CHANNEL_ID,
                thread_ts=thread_ts,
                text=new_content
            )
            # print(f"Slack reply sent: {new_content}")  # 디버깅용 출력
            return response['ts']
    except SlackApiError as e:
        print(f"Error sending Slack reply: {e.response['error']}")
    except Exception as e:
        print(f"Unexpected error sending Slack reply: {str(e)}")
    return None


def append_block_to_notion(page_id, content, block_type="paragraph"):
    try:
        new_content = get_new_content(content)
        if new_content:
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
                                        "content": new_content
                                    }
                                }
                            ]
                        }
                    }
                ]
            )
            # print(f"Notion block appended: {new_content}")  # 디버깅용 출력
    except Exception as e:
        print(f"Error appending to Notion: {str(e)}")


def save_text_to_file(text, filename):
    new_content = get_new_content(text)
    if new_content:
        folder_path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'transcripts')
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(f"{new_content}\n")
        # print(f"Text saved to file: {new_content}")  # 디버깅용 출력


def initialize_chrome_driver():
    chrome_options = Options()
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


def add_session_to_db(title, date, start_time):
    cursor.execute('INSERT INTO sessions (title, date, start_time) VALUES (?, ?, ?)',
                   (title, date, start_time))
    conn.commit()
    return cursor.lastrowid


def add_transcript_to_db(session_id, timestamp, content):
    cursor.execute('INSERT INTO transcripts (session_id, timestamp, content) VALUES (?, ?, ?)',
                   (session_id, timestamp, content))
    conn.commit()


def get_context(sentence, keyword, context_words=5):
    words = sentence.split()
    keyword_index = next(i for i, word in enumerate(
        words) if keyword.lower() in word.lower())
    start = max(0, keyword_index - context_words)
    end = min(len(words), keyword_index + context_words + 1)
    context = ' '.join(words[start:end])
    return f"...{context}..." if start > 0 or end < len(words) else context


async def monitor_broadcast(url, title):
    driver = initialize_chrome_driver()
    driver.get(url)
    time.sleep(5)

    try:
        # 자막 켜기 (녹화 영상용)
        try:
            subtitle_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "a.btn-subtitles[title='자막보기']"))
            )
            subtitle_button.click()
            print("자막 켜기 완료")
        except TimeoutException:
            print("자막 버튼을 찾을 수 없거나 클릭할 수 없습니다.")

        # 재생 버튼 클릭
        try:
            play_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button.vjs-big-play-button[title='영상재생하기']"))
            )
            play_button.click()
            print("영상 재생 시작")
        except TimeoutException:
            print("재생 버튼을 찾을 수 없습니다.")
        except ElementClickInterceptedException:
            print("재생 버튼을 클릭할 수 없습니다. 영상이 이미 재생 중일 수 있습니다.")

        # 영상 제목과 일시 가져오기
        video_title = driver.find_element(By.ID, "vtit01").text
        video_datetime = driver.find_element(By.ID, "vtit02").text

        # 영상 일시에서 날짜 추출
        video_date = re.search(
            r'(\d{4}년 \d{2}월 \d{2}일)', video_datetime).group(1)

        start_time = datetime.now().strftime(
            "%p %I시:%M분").replace("AM", "오전").replace("PM", "오후")
        initial_text = f"제목: {video_title}\n날짜: {
            video_date}\n시작 시간: {start_time}\n"

        ts = send_slack_message(initial_text)
        await send_telegram_message(initial_text)
        append_block_to_notion(NOTION_PAGE_ID, initial_text)

        # 파일명 생성
        safe_date = video_date.replace(" ", "_").replace(
            "년", "").replace("월", "").replace("일", "")
        safe_title = re.sub(r'[^\w\s-]', '', video_title)
        safe_title = re.sub(r'[-\s]+', '_', safe_title)
        filename = f"{safe_date}_{safe_title}.txt"

        save_text_to_file(initial_text, filename)

        session_id = add_session_to_db(video_title, video_date, start_time)

        current_sentence = ""
        last_subtitle = ""
        last_time_recorded = time.time()

        while True:
            await asyncio.sleep(0.5)

            if time.time() - last_time_recorded >= 60:
                current_time_text = f"\n{get_current_time()}\n"
                save_text_to_file(current_time_text, filename)
                append_block_to_notion(NOTION_PAGE_ID, current_time_text)
                add_transcript_to_db(
                    session_id, get_current_time(), current_time_text)
                last_time_recorded = time.time()

            active_subtitles = driver.find_elements(
                By.CSS_SELECTOR, ".ls_subtittable[style*='color: rgb(44, 134, 194)']")

            if active_subtitles:
                current_subtitle = active_subtitles[0].text.strip()

                # 중복 자막 제거
                if current_subtitle != last_subtitle:
                    current_sentence += " " + current_subtitle
                    current_sentence = current_sentence.strip()
                    last_subtitle = current_subtitle

                    # 문장 끝 확인 (마침표, 물음표, 느낌표)
                    if re.search(r'[.?!]$', current_subtitle):
                        # 중복 구문 제거
                        words = current_sentence.split()
                        unique_words = []
                        for word in words:
                            if not unique_words or word != unique_words[-1]:
                                unique_words.append(word)
                        complete_sentence = " ".join(unique_words)

                        # complete_sentence_with_time = f"[{get_current_time()}] {
                        #     complete_sentence}"
                        print(complete_sentence)
                        save_text_to_file(
                            complete_sentence, filename)
                        append_block_to_notion(
                            NOTION_PAGE_ID, complete_sentence)
                        send_slack_reply(complete_sentence, ts)
                        await send_telegram_message(complete_sentence)
                        add_transcript_to_db(
                            session_id, get_current_time(), complete_sentence)

                        if any(keyword in complete_sentence.lower() for keyword in ALERT_KEYWORDS):
                            detected_keywords = [keyword for keyword in ALERT_KEYWORDS if keyword.lower(
                            ) in complete_sentence.lower()]
                            for keyword in detected_keywords:
                                context = get_context(
                                    complete_sentence, keyword)
                                alert_message = (
                                    f"⚠️ 키워드 감지: '{keyword}'\n"
                                    f"제목: {video_title}\n"
                                    f"시간: {get_current_time()}\n"
                                    f"맥락: {context}\n"
                                    f"전체 문장: {complete_sentence}\n"
                                )
                                send_slack_message(alert_message)
                                await send_telegram_message(alert_message)

                        current_sentence = ""  # 문장 초기화

    except Exception as e:
        print(f"An error occurred in monitor_broadcast: {str(e)}")
    finally:
        driver.quit()


def get_current_time():
    now = datetime.now()
    return now.strftime("%p %I시:%M분").replace("AM", "오전").replace("PM", "오후")


async def main():
    # 기본 URL 설정
    default_url = "https://w3.assembly.go.kr/main/player.do?menu=30&mc=354&ct1=21&ct2=391&ct3=A2&wv=1&"

    # 사용자로부터 URL 입력 받기
    user_input = input("녹화 방송 URL을 입력하세요 (엔터를 누르면 기본 URL 사용): ").strip()

    # 사용자 입력이 없으면 기본 URL 사용
    broadcast_url = user_input if user_input else default_url

    broadcast_title = "녹화된 방송"  # 제목은 고정값으로 설정하거나 필요에 따라 수정 가능

    try:
        print(f"녹화된 방송 모니터링 시작: {broadcast_title}")
        print(f"URL: {broadcast_url}")
        await monitor_broadcast(broadcast_url, broadcast_title)
    except Exception as e:
        print(f"An error occurred in main: {str(e)}")
    finally:
        conn.close()  # 데이터베이스 연결 종료


if __name__ == "__main__":
    asyncio.run(main())
