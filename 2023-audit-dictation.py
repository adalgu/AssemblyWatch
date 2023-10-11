import requests
import json
from notion_client import Client
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
import time
import os

# url = "https://assembly.webcast.go.kr/main/player.asp?xcode=55&xcgcd=DCM00005521410A101&"  # 산자위
# url = "https://assembly.webcast.go.kr/main/player.asp?xcode=54&xcgcd=DCM00005421410A101&"  # 국토위
# url = "https://assembly.webcast.go.kr/main/player.asp?xcode=54&xcgcd=DCM00005421410A101&"

# 10월11일
url = "https://assembly.webcast.go.kr/main/player.asp?xcode=56&xcgcd=DCM00005621410A801&"  # 과방위


# 현재 스크립트의 절대 경로를 얻습니다.
current_script_path = os.path.abspath(__file__)

# 현재 스크립트의 디렉토리를 얻습니다.
current_script_dir = os.path.dirname(current_script_path)

# 작업 디렉토리를 현재 스크립트의 디렉토리로 설정합니다.
os.chdir(current_script_dir)


def save_text_to_file(text, filename):
    """
    Save the given text to a file.

    :param text: str, text to save
    :param filename: str, name of the file
    """
    with open(filename, 'a', encoding='utf-8') as file:
        file.write(text + "\n")


# NOTION_API_KEY와 NOTION_PAGE_ID는 환경 변수 또는 직접 문자열로 입력할 수 있습니다.
# Replace with your Notion API key
NOTION_API_KEY = "secret_qQXJvW0U5AKlbxAtQFzq7yac9mx8WahKxYkTFTzOEtV"
# Replace with your Notion page ID
# NOTION_PAGE_ID = "d053dce5b00842e7ad201e48bbbc603b" #국토위
NOTION_PAGE_ID = "ec8af56b6fe449c6a3662f1580c84de6"  # 과방위

notion = Client(auth=NOTION_API_KEY)


def append_block_to_page(page_id, content, block_type):
    try:
        # Append block
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
        # print("Block added:", new_block)
        return new_block
    except Exception as e:
        print("Error:", str(e))
        return None


def send_message_to_slack(text):
    webhook_url = 'https://hooks.slack.com/services/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'
    headers = {'Content-Type': 'application/json'}
    payload = {'text': text}
    response = requests.post(
        webhook_url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        print("Message sent to Slack")
    else:
        print(
            f"Failed to send message to Slack: {response.status_code}, {response.text}")


def initialize_chrome_driver():
    """Initialize the Chrome driver with necessary configurations."""
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging"])

    # Add headless option
    # chrome_options.add_argument("--headless")

    service = Service(executable_path=ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


driver = initialize_chrome_driver()


try:
    driver.get(url)
    # Time sleep to wait for the page to load completely
    time.sleep(5)

    # Locate the button using XPath
    button = driver.find_element(By.XPATH, "//*[@id='smi_btn']")
    # Click the button using ENTER key
    button.click()

    print("AI 자막 켜기 완료")

    # Find elements and print text
    title = driver.find_element(By.CSS_SELECTOR, "#xsubj").text
    date = driver.find_element(By.CSS_SELECTOR, "#xdate").text
    print(title, "\n", date)

    # Store the initial state of the dynamic content
    prev_elements = driver.find_elements(
        By.CSS_SELECTOR, "p[class^='smi_word stxt']")
    prev_texts = [el.text for el in prev_elements]

    # Set an interval to check for changes in the content
    interval = 5  # seconds

    # Create a filename using the date and the first word of the title
    # Replace any special characters or spaces in the date string
    safe_date = date.replace(" ", "_").replace("-", "_").replace(":", "_")
    first_word_of_title = title.split(" ")[0]
    filename = f"{safe_date}_{first_word_of_title}.txt"

    # Define full path
    full_path = os.path.join(current_script_dir, filename)

    while True:
        # Wait for the specified interval
        time.sleep(interval)

        # Get the current state of the dynamic content
        curr_elements = driver.find_elements(
            By.CSS_SELECTOR, "p[class^='smi_word stxt']")
        curr_texts = []

        # Find the maximum index of span id to exclude the last typing text
        max_index = -1
        for el in curr_elements:
            span_elements = el.find_elements(By.TAG_NAME, "span")
            for span in span_elements:
                span_id = span.get_attribute("id")
                index = int(span_id.split("_")[1])
                max_index = max(max_index, index)

        # Scrape texts excluding the last typing text
        for el in curr_elements:
            span_elements = el.find_elements(By.TAG_NAME, "span")
            for span in span_elements:
                span_id = span.get_attribute("id")
                index = int(span_id.split("_")[1])
                # Exclude the last typing text
                if index < max_index:
                    curr_texts.append(span.text)

        # Check if the content has changed
        if curr_texts != prev_texts:
            # print("Content has changed!")
            new_texts = [text for text in curr_texts if text not in prev_texts]
            # print("New Texts:")
            print("\n".join(new_texts))

            # Save the new texts to a file
            save_text_to_file("\n".join(new_texts), full_path)

            # # Send a message to Slack
            # send_message_to_slack()

            # Usage example
            content = str(new_texts)
            block_type = "paragraph"
            append_block_to_page(NOTION_PAGE_ID, content, block_type)

            # Update the previous content
            prev_texts = curr_texts

# Handle possible exceptions
except Exception as e:
    print(f"An error occurred: {str(e)}")

# Ensure the driver is closed properly
finally:
    driver.quit()
