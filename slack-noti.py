import os
import time
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# WebClient 인스턴스화: API 메서드를 호출할 클라이언트 생성
client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

# Slack API token
token = 'xoxp-194626280262-697909535825-6021120508370-d755cbd9b65973873643c7dc74f66e11'
# WebClient 인스턴스화: API 메서드를 호출할 클라이언트 생성
client = WebClient(token=token)


# 채널 ID
channel_id = "CSD2UDY3D"


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


def main():
    # 메시지 보내기 예시
    initial_text = "*[국토교통위원회 국정감사(국토교통부 등)]* \n 2023년 10월 10일 (화)"
    ts = send_message(initial_text)

    # 메시지가 성공적으로 보내졌다면, 이후 스레드에 댓글 달기
    if ts:
        while True:

            # 예시: 랜덤 텍스트 생성
            new_texts = ["Text1", "Text2", "Text3"]
            message = "New texts scraped:\n" + '\n'.join(new_texts)

            # 스레드에 댓글 달기
            send_reply_to_thread(message, ts)

            # 일정 시간 대기 (예: 1분)
            time.sleep(1)


if __name__ == "__main__":
    main()


# import json
# import requests
# from slack_sdk import WebClient
# from slack_sdk.errors import SlackApiError
# import logging
# import os
# # Import WebClient from Python SDK (github.com/slackapi/python-slack-sdk)
# from slack_sdk import WebClient
# from slack_sdk.errors import SlackApiError

# # WebClient instantiates a client that can call API methods
# # When using Bolt, you can use either `app.client` or the `client` passed to listeners.
# client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
# logger = logging.getLogger(__name__)


# def send_message_to_slack(text):
#     webhook_url = 'https://hooks.slack.com/services/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'
#     headers = {'Content-Type': 'application/json'}
#     payload = {'text': text}
#     response = requests.post(
#         webhook_url, headers=headers, data=json.dumps(payload))

#     if response.status_code == 200:
#         print("Message sent to Slack")
#     else:
#         print(
#             f"Failed to send message to Slack: {response.status_code}, {response.text}")


# def send_reply_to_thread(text):
#     # Slack API token
#     token = 'xoxp-194626280262-697909535825-6021120508370-d755cbd9b65973873643c7dc74f66e11'

#     # ID of channel you want to post message to
#     channel_id = "CSD2UDY3D"

#     client = WebClient(token=token)

#     try:
#         # Send a message
#         response = client.chat_postMessage(
#             channel=channel_id,
#             text="*[국토교통위원회 국정감사(국토교통부 등)]* \n 2023년 10월 10일 (화)",

#         )

#         # Get the timestamp of the message
#         ts = response['ts']

#         # Send a threaded message
#         client.chat_postMessage(
#             channel=channel_id,
#             thread_ts=ts,
#             text="This is a threaded reply to the message above."
#         )

#     except SlackApiError as e:
#         # You will get a SlackApiError if "ok" is False
#         assert e.response["ok"] is False
#         print(f"Got an error: {e.response['error']}")


# def main():
#     new_texts = ["잘 들어가나", "Text2", "Text3"]  # Example texts
#     message = "New texts scraped:\n" + '\n'.join(new_texts)
#     # send_message_to_slack(message)
#     send_reply_to_thread(message)


# if __name__ == "__main__":
#     main()
