from slack_sdk.errors import SlackApiError
from slack_sdk import WebClient
import os
import time
import datetime
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.common.keys import Keys
from notion_client import Client

# 환경 설정
NOTION_API_KEY = "secret_qQXJvW0U5AKlbxAtQFzq7yac9mx8WahKxYkTFTzOEtV"
# NOTION_PAGE_ID = "ec8af56b6fe449c6a3662f1580c84de6"
# SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/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'


# Replace with your Notion page ID
# NOTION_PAGE_ID = "d053dce5b00842e7ad201e48bbbc603b" #국토위
NOTION_PAGE_ID = "ec8af56b6fe449c6a3662f1580c84de6"  # 과방위
# NOTION_PAGE_ID = "c30031bd3285408d919d3e1f91b75092"  # 정무위

# 10월11일
# URL = "https://assembly.webcast.go.kr/main/player.asp?xcode=56&xcgcd=DCM00005621410A801&"  # 과방위
# URL = "https://assembly.webcast.go.kr/main/player.asp?xcode=26&xcgcd=DCM00002621410A201&"  # 정무위
URL = "https://assembly.webcast.go.kr/main/player.asp?xcode=56&xcgcd=DCM00005621410A801&"   # 과방위

# Notion 클라이언트 초기화
notion = Client(auth=NOTION_API_KEY)


def save_text_to_file(text, filename):
    with open(filename, 'a', encoding='utf-8') as file:
        file.write(text + "\n")


def append_block_to_page(page_id, content, block_type="paragraph"):
    try:
        new_block = notion.blocks.children.append(
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
        return new_block
    except Exception as e:
        print("Error:", str(e))
        return None


# WebClient 인스턴스화: API 메서드를 호출할 클라이언트 생성
# client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

# Slack API token
token = 'xoxp-194626280262-697909535825-6021120508370-d755cbd9b65973873643c7dc74f66e11'
# token = 'xoxb-194626280262-6021023650051-1LDDyo8zrPrVNPk8ufa66f1t'
# WebClient 인스턴스화: API 메서드를 호출할 클라이언트 생성
client = WebClient(token=token)


# 채널 ID
# channel_id = "CSD2UDY3D"
channel_id = "C060BR0E4KF"


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


def send_reply_to_thread(text, ts):
    """
    슬랙 스레드에 메시지를 보내는 함수
    """
    try:
        # 스레드 메시지 보내기
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=ts,
            text=text
        )
    except SlackApiError as e:
        print(f"Error sending reply: {e.response['error']}")


def initialize_chrome_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging"])
    # Add headless option
    # chrome_options.add_argument("--headless")
    service = Service(executable_path=ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def get_current_time():
    """현재 시간을 문자열로 반환합니다."""
    now = datetime.datetime.now()
    return now.strftime("%p %I시:%M분").replace("AM", "오전").replace("PM", "오후")


def main():
    driver = initialize_chrome_driver()

    while True:

        try:
            driver.get(URL)
            time.sleep(5)

            button = driver.find_element(By.XPATH, "//*[@id='smi_btn']")
            button.click()

            print("AI 자막 켜기 완료")

            title = driver.find_element(By.CSS_SELECTOR, "#xsubj").text
            date = driver.find_element(By.CSS_SELECTOR, "#xdate").text
            print(title, "\n", date)

            prev_elements = driver.find_elements(
                By.CSS_SELECTOR, "p[class^='smi_word stxt']")
            prev_texts = [el.text for el in prev_elements]

            interval = 3  # 크롤링 간격
            time_recording_interval = 60  # 시간 기록 간격 (1분)
            last_time_recorded = time.time()  # 마지막으로 시간을 기록한 시점

            safe_date = date.replace(" ", "_").replace(
                "-", "_").replace(":", "_")
            first_word_of_title = title.split(" ")[0]
            filename = f"{safe_date}_{first_word_of_title}.txt"

            full_path = os.path.join(os.path.dirname(
                os.path.abspath(__file__)), filename)

            initial_text = f"{title}\n{date}\n{get_current_time()}\n"
            # 메시지 보내기 예시
            # initial_text = "*[국토교통위원회 국정감사(국토교통부 등)]* \n 2023년 10월 10일 (화)"
            ts = send_message(initial_text)
            save_text_to_file(initial_text, full_path)
            append_block_to_page(NOTION_PAGE_ID, initial_text)

            while True:
                time.sleep(interval)

                # 5분마다 현재 시간 기록
                if time.time() - last_time_recorded >= time_recording_interval:
                    current_time_text = f"\n{get_current_time()}\n"
                    save_text_to_file(current_time_text, full_path)
                    append_block_to_page(NOTION_PAGE_ID, current_time_text)
                    last_time_recorded = time.time()  # 시간 기록 업데이트

                curr_elements = driver.find_elements(
                    By.CSS_SELECTOR, "p[class^='smi_word stxt']")
                curr_texts = []

                max_index = -1
                for el in curr_elements:
                    span_elements = el.find_elements(By.TAG_NAME, "span")
                    for span in span_elements:
                        span_id = span.get_attribute("id")
                        index = int(span_id.split("_")[1])
                        max_index = max(max_index, index)

                for el in curr_elements:
                    span_elements = el.find_elements(By.TAG_NAME, "span")
                    for span in span_elements:
                        span_id = span.get_attribute("id")
                        index = int(span_id.split("_")[1])
                        if index < max_index:
                            curr_texts.append(span.text)

                if curr_texts != prev_texts:
                    new_texts = [
                        text for text in curr_texts if text not in prev_texts]
                    print("\n".join(new_texts))

                    save_text_to_file("\n".join(new_texts), full_path)
                    content = str(new_texts)
                    append_block_to_page(NOTION_PAGE_ID, content)
                    send_reply_to_thread(content, ts)

                    prev_texts = curr_texts

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            print("Retrying in 5 seconds...")
            time.sleep(5)  # wait for 60 seconds before retrying

        finally:
            driver.quit()
            driver = initialize_chrome_driver()  # reinitialize the driver


if __name__ == "__main__":
    main()
