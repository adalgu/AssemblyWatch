from bs4 import BeautifulSoup
import pandas as pd
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# 웹페이지 URL
url = 'https://assembly.webcast.go.kr/main/'


def initialize_chrome_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging"])
    # Add headless option
    # chrome_options.add_argument("--headless")
    service = Service(executable_path=ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


driver = initialize_chrome_driver()
driver.get(url)

# JavaScript가 데이터를 로드하는데 시간이 필요하므로, 몇 초간 대기합니다.
time.sleep(2)  # 5초 대기. 필요한 경우 시간을 조절합니다.

# 페이지 소스를 가져와 BeautifulSoup 객체를 생성합니다.
soup = BeautifulSoup(driver.page_source, 'html.parser')

# 웹 드라이버를 종료합니다.
driver.quit()


# 데이터를 저장할 리스트 초기화
data = []

# 예: "ma_video_list" 클래스를 가진 div 태그의 내용 추출
ma_video_list = soup.find('div', class_='ma_video_list')
if ma_video_list:
    print(ma_video_list.prettify())
else:
    print("태그를 찾을 수 없습니다.")

# 각 항목에서 정보를 추출하여 저장할 리스트를 초기화합니다.
titles = []
descs = []
links = []

# 각 <li> 항목을 순회하면서 정보를 추출합니다.
for li in soup.select('ul#gvlist li'):
    title = li.find('h3', class_='tit').get_text(strip=True)
    desc = li.find('p', class_='desc').get_text(strip=True)
    link_tag = li.find('a', class_='btn')
    link = link_tag['href'] if link_tag else None  # 링크가 없는 경우 None으로 처리

    titles.append(title)
    descs.append(desc)
    links.append(link)

# 추출한 정보를 기반으로 DataFrame을 생성합니다.
df = pd.DataFrame({
    'Title': titles,
    'Description': descs,
    'Link': links
})

# DataFrame 출력
print(df)
