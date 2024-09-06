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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from notion_client import Client
from bs4 import BeautifulSoup
import sqlite3
import re
from telegram import Bot
import asyncio

# .env 파일 로드
load_dotenv()

# 환경 변수에서 값을 가져옴import os
from dotenv import load_dotenv
import argparse
import time
import datetime
from datetime import datetime
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import sqlite3
import re
import asyncio

# .env 파일 로드
load_dotenv()

# 환경 변수에서 값을 가져옴
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_PAGE_ID = os.getenv('NOTION_PAGE_ID')
SLACK_ALERT_WEBHOOK = os.getenv('SLACK_ALERT_WEBHOOK')
SLACK_TOKEN = os.getenv('SLACK_TOKEN')
SLACK_CHANNEL_ID = os.getenv('SLACK_CHANNEL_ID')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# 인자 파싱
parser = argparse.ArgumentParser(description='국회 의사중계 모니터링 스크립트')
parser.add_argument('--notion_api_key', default=NOTION_API_KEY, help='Notion API key')
parser.add_argument('--notion_page_id', default=NOTION_PAGE_ID, help='Notion page ID')
parser.add_argument('--slack_alert_webhook', default=SLACK_ALERT_WEBHOOK, help='Slack alert webhook URL')
parser.add_argument('--slack_token', default=SLACK_TOKEN, help='Slack token')
parser.add_argument('--slack_channel_id', default=SLACK_CHANNEL_ID, help='Slack channel ID')
parser.add_argument('--telegram_bot_token', default=TELEGRAM_BOT_TOKEN, help='Telegram Bot Token')
parser.add_argument('--telegram_chat_id', default=TELEGRAM_CHAT_ID, help='Telegram Chat ID')

args = parser.parse_args()

# 환경 변수나 인자에서 가져온 값으로 변수 설정
NOTION_API_KEY = args.notion_api_key
NOTION_PAGE_ID = args.notion_page_id
SLACK_ALERT_WEBHOOK = args.slack_alert_webhook
SLACK_TOKEN = args.slack_token
SLACK_CHANNEL_ID = args.slack_channel_id
TELEGRAM_BOT_TOKEN = args.telegram_bot_token
TELEGRAM_CHAT_ID = args.telegram_chat_id

# API 클라이언트 초기화
notion = None
slack_client = None
telegram_bot = None

try:
    from notion_client import Client
    notion = Client(auth=NOTION_API_KEY)
    print("Notion 클라이언트가 성공적으로 초기화되었습니다.")
except Exception as e:
    print(f"Notion 클라이언트 초기화 실패: {str(e)}")

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    slack_client = WebClient(token=SLACK_TOKEN)
    print("Slack 클라이언트가 성공적으로 초기화되었습니다.")
except Exception as e:
    print(f"Slack 클라이언트 초기화 실패: {str(e)}")

try:
    from telegram import Bot
    telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)
    print("Telegram 봇이 성공적으로 초기화되었습니다.")
except Exception as e:
    print(f"Telegram 봇 초기화 실패: {str(e)}")

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

async def send_telegram_message(text):
    try:
        if telegram_bot and TELEGRAM_CHAT_ID:
            await telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
            print("Telegram 메시지 전송 성공")
        else:
            print("Telegram 봇 또는 채팅 ID가 설정되지 않았습니다.")
    except Exception as e:
        print(f"Telegram 메시지 전송 실패: {str(e)}")
    
    # 로컬 파일에 저장
    save_text_to_file(text, "telegram_messages.txt")

def send_slack_message(text):
    try:
        if slack_client and SLACK_CHANNEL_ID:
            new_content = get_new_content(text)
            if new_content:
                response = slack_client.chat_postMessage(
                    channel=SLACK_CHANNEL_ID,
                    text=new_content,
                )
                print("Slack 메시지 전송 성공")
                return response['ts']
        else:
            print("Slack 클라이언트 또는 채널 ID가 설정되지 않았습니다.")
    except Exception as e:
        print(f"Slack 메시지 전송 실패: {str(e)}")
    
    # 로컬 파일에 저장
    save_text_to_file(text, "slack_messages.txt")
    return None

def send_slack_reply(text, thread_ts):
    try:
        if slack_client and SLACK_CHANNEL_ID:
            new_content = get_new_content(text)
            if new_content:
                response = slack_client.chat_postMessage(
                    channel=SLACK_CHANNEL_ID,
                    thread_ts=thread_ts,
                    text=new_content
                )
                print("Slack 답글 전송 성공")
                return response['ts']
        else:
            print("Slack 클라이언트 또는 채널 ID가 설정되지 않았습니다.")
    except Exception as e:
        print(f"Slack 답글 전송 실패: {str(e)}")
    
    # 로컬 파일에 저장
    save_text_to_file(f"Thread: {thread_ts}\n{text}", "slack_replies.txt")
    return None

def append_block_to_notion(page_id, content, block_type="paragraph"):
    try:
        if notion and page_id:
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
                print("Notion에 내용 추가 성공")
        else:
            print("Notion 클라이언트 또는 페이지 ID가 설정되지 않았습니다.")
    except Exception as e:
        print(f"Notion에 내용 추가 실패: {str(e)}")
    
    # 로컬 파일에 저장
    save_text_to_file(content, "notion_content.txt")

def save_text_to_file(text, filename):
    new_content = get_new_content(text)
    if new_content:
        folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'transcripts')
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(f"{new_content}\n")
        print(f"{filename}에 내용 저장 완료")


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


# add_session_to_db 함수 수정
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


def load_default_keywords():
    default_keywords_file = 'default_keywords.txt'
    keywords = []
    if os.path.exists(default_keywords_file):
        with open(default_keywords_file, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    keywords.append(line)
        if not keywords:
            print(f"경고: {default_keywords_file}에 유효한 키워드가 없습니다.")
    else:
        print(f"경고: {default_keywords_file}를 찾을 수 없습니다.")
    return keywords


def get_user_keywords():
    print("\n알림 키워드 설정")
    print("1. 기본 키워드 사용")
    print("2. 직접 키워드 입력")
    choice = input("선택해주세요 (1 또는 2): ")

    if choice == "1":
        keywords = load_default_keywords()
        print("기본 키워드:", keywords)
    elif choice == "2":
        keywords_input = input("키워드를 쉼표로 구분하여 입력해주세요: ")
        keywords = [keyword.strip()
                    for keyword in keywords_input.split(',') if keyword.strip()]
    else:
        print("잘못된 선택입니다. 기본 키워드를 사용합니다.")
        keywords = load_default_keywords()

    return keywords


async def monitor_broadcast(url, title, is_live, alert_keywords):
    driver = initialize_chrome_driver()
    driver.get(url)
    time.sleep(5)

    try:
        if not is_live:
            # 녹화 영상용 자막 켜기
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

            # 영상 일시에서 모든 정보 추출
            date_time_match = re.search(
                r'(\d{4}년 \d{2}월 \d{2}일 \(\w\) \d{2}:\d{2})', video_datetime)
            if date_time_match:
                video_full_datetime = date_time_match.group(1)
            else:
                print("영상 날짜와 시간을 추출할 수 없습니다.")
                video_full_datetime = "날짜 정보 없음"
        else:
            # 생방송용 자막 켜기
            try:
                button = driver.find_element(By.XPATH, "//*[@id='smi_btn']")
                button.click()
                print("AI 자막 켜기 완료")
            except:
                print("AI 자막 켜기 실패")

            video_title = title
            video_full_datetime = datetime.now().strftime("%Y년 %m월 %d일 (%a) %H:%M")

        initial_text = f"회의명: {video_title}\n회의 일시: {video_full_datetime}\n"

        ts = send_slack_message(initial_text)
        await send_telegram_message(initial_text)
        append_block_to_notion(NOTION_PAGE_ID, initial_text)

        # 파일명 생성
        safe_date = video_full_datetime.split()[0].replace("년", "").replace("월", "").replace("일", "")
        safe_title = re.sub(r'[^\w\s-]', '', video_title)
        safe_title = re.sub(r'[-\s]+', '_', safe_title)
        filename = f"{safe_date}_{safe_title}.txt"

        save_text_to_file(initial_text, filename)

        session_id = add_session_to_db(video_title, video_full_datetime, video_full_datetime.split()[-1])


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

            if is_live:
                active_subtitles = driver.find_elements(
                    By.CSS_SELECTOR, "p[class^='smi_word stxt']")
            else:
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

                        print(complete_sentence)
                        save_text_to_file(complete_sentence, filename)
                        append_block_to_notion(
                            NOTION_PAGE_ID, complete_sentence)
                        send_slack_reply(complete_sentence, ts)
                        await send_telegram_message(complete_sentence)
                        add_transcript_to_db(
                            session_id, get_current_time(), complete_sentence)

                        if any(keyword in complete_sentence.lower() for keyword in alert_keywords):
                            detected_keywords = [keyword for keyword in alert_keywords if keyword.lower(
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
    return now.strftime("%Y년 %m월 %d일 (%a) %H:%M")


async def main():
    print("국회 영상 모니터링 프로그램을 시작합니다.")
    # 알림 키워드 설정
    alert_keywords = get_user_keywords()
    print(f"설정된 알림 키워드: {alert_keywords}")

    print("\n1. 생방송")
    print("2. 녹화방송")
    choice = input("선택해주세요 (1 또는 2): ")

    if choice == "1":
        live_broadcasts = get_live_broadcasts()
        if live_broadcasts:
            print("현재 생중계 중인 방송:")
            for idx, broadcast in enumerate(live_broadcasts, 1):
                print(f"{idx}. {broadcast['name']}")

            broadcast_choice = int(input("모니터링할 방송 번호를 선택하세요: ")) - 1
            if 0 <= broadcast_choice < len(live_broadcasts):
                selected_broadcast = live_broadcasts[broadcast_choice]
                print(f"선택된 방송: {selected_broadcast['name']}")
                await monitor_broadcast(selected_broadcast['live_link'], selected_broadcast['name'], True, alert_keywords)
            else:
                print("잘못된 선택입니다.")
        else:
            print("현재 생중계 중인 방송이 없습니다.")
    elif choice == "2":
        default_url = "https://w3.assembly.go.kr/main/player.do?menu=30&mc=354&ct1=21&ct2=391&ct3=A2&wv=1&"
        user_input = input("녹화 방송 URL을 입력하세요 (엔터를 누르면 기본 URL 사용): ").strip()
        broadcast_url = user_input if user_input else default_url
        broadcast_title = "녹화된 방송"
        print(f"녹화된 방송 모니터링 시작: {broadcast_title}")
        print(f"URL: {broadcast_url}")
        await monitor_broadcast(broadcast_url, broadcast_title, False, alert_keywords)
    else:
        print("잘못된 선택입니다.")

if __name__ == "__main__":
    asyncio.run(main())