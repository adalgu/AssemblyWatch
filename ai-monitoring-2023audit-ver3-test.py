import argparse
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
from notion_client import Client

# 1. argparse를 사용하여 필요한 인자들을 정의하고 기본값을 설정합니다.
parser = argparse.ArgumentParser(description='Script arguments')
parser.add_argument('--notion_api_key',
                    default="secret_qQXJvW0U5AKlbxAtQFzq7yac9mx8WahKxYkTFTzOEtV", help='Notion API key')
parser.add_argument('--notion_page_id',
                    default="8430012bce944e1fb984115429054274", help='Notion page ID')
parser.add_argument(
    '--url', default="https://assembly.webcast.go.kr/main/player.asp?xcode=54&xcgcd=DCM000054214110201&", help='URL to monitor')
parser.add_argument('--slack_alert_webhook',
                    default="https://hooks.slack.com/services/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", help='Slack alert webhook URL')
parser.add_argument(
    '--token', default='xoxp-194626280262-697909535825-6033906233927-b41117a1bea58c97265e28c720369ba2', help='Slack token')
parser.add_argument('--channel_id', default="C060BR0E4KF",
                    help='Slack channel ID')

args = parser.parse_args()

# 2. 코드 내에서 argparse로 받은 인자 값을 사용합니다.
NOTION_API_KEY = args.notion_api_key
NOTION_PAGE_ID = args.notion_page_id
URL = args.url
SLACK_ALERT_WEBHOOK = args.slack_alert_webhook
token = args.token
channel_id = args.channel_id

# 알림을 원하는 키워드 입력 (예: 카카오, 카카오모빌리티, 택시, 모빌리티)
error_keywords = ['카카오', '카카오모빌리티', '택시', '모빌리티',
                  '류긍선', '김범수']  # 이 리스트에 검사하고자 하는 단어들을 추가

# Notion 클라이언트 초기화
notion = Client(auth=NOTION_API_KEY)

# slack
client = WebClient(token=token)

# 전역 변수 추가
ts = None


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


# def send_reply_to_thread(text, ts):
#     """
#     슬랙 스레드에 메시지를 보내는 함수
#     """
#     try:
#         # 스레드 메시지 보내기
#         client.chat_postMessage(
#             channel=channel_id,
#             thread_ts=ts,
#             text=text
#         )
#     except SlackApiError as e:
#         print(f"Error sending reply: {e.response['error']}")


def send_reply_to_thread(text, ts):
    """
    슬랙 스레드에 메시지를 보내는 함수
    """
    try:
        # 스레드 메시지 보내기
        response = client.chat_postMessage(
            channel=channel_id,
            thread_ts=ts,
            text=text
        )

        # If the message is sent successfully, construct the thread link and return
        message_timestamp = response['ts']
        # Modify the following line with your actual Slack workspace domain
        workspace_domain = "kakaomobility"
        thread_link = f"https://{workspace_domain}.slack.com/archives/{channel_id}/p{message_timestamp.replace('.', '')}?thread_ts={ts}&cid={channel_id}"
        return thread_link

    except SlackApiError as e:
        print(f"Error sending reply: {e.response['error']}")
        return None


def send_slack_msg(slackurl, msg, title, ts=None):
    # Constructing the Slack message with the thread link if ts is provided
    if ts:
        # Modify the following line with your actual Slack workspace domain
        workspace_domain = "kakaomobility"
        thread_link = f"https://{workspace_domain}.slack.com/archives/{channel_id}/p{ts.replace('.', '')}?thread_ts={ts}&cid={channel_id}"
        msg += f"\n\n[바로보기]({thread_link})"

    slack_data = {
        "attachments": [
            {
                "color": "#e50000",
                "fields": [
                    {
                        "title": title,
                        "value": msg,
                        "short": "false",
                    }
                ]
            }
        ]
    }

    response = requests.post(
        slackurl, headers={'Content-Type': 'application/json'}, json=slack_data)
    response.raise_for_status()


def initialize_chrome_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging"])
    # Add headless option
    chrome_options.add_argument("--headless")
    service = Service(executable_path=ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def get_current_time():
    """현재 시간을 문자열로 반환합니다."""
    now = datetime.datetime.now()
    return now.strftime("%p %I시:%M분").replace("AM", "오전").replace("PM", "오후")


def main():
    driver = initialize_chrome_driver()

    # 초기 슬랙 메시지의 'ts' 값을 저장할 변수 선언
    ts = None

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
            # 첫 메시지를 보내고 'ts' 값을 저장
            if not ts:
                ts = send_message(initial_text)
            else:
                send_reply_to_thread(initial_text, ts)

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
                    # print("\n".join(new_texts))

                    save_text_to_file("\n".join(new_texts), full_path)
                    content = str(new_texts)
                    append_block_to_page(NOTION_PAGE_ID, content)
                    send_reply_to_thread(content, ts)

                    prev_texts = curr_texts
                    # 여기에 에러 메시지 확인 및 슬랙 알림 로직 추가
                    if any(keyword in content for keyword in error_keywords):
                        alert_message = f"⚠️ {title} {get_current_time()} \n {content}\n"
                        # send_to_slack(slack_channel_id, ts, alert_message)
                        send_slack_msg(SLACK_ALERT_WEBHOOK,
                                       alert_message, title, ts)

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            print("Retrying in 5 seconds...")
            time.sleep(5)  # wait for 60 seconds before retrying

        finally:
            driver.quit()
            driver = initialize_chrome_driver()  # reinitialize the driver


if __name__ == "__main__":
    main()