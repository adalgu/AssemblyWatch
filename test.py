from selenium import webdriver

# user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
# options.add_argument('user-agent={0}'.format(user_agent))
driver = webdriver.Chrome('./chromedriver', options=options)
# 아무런 경고가 없다면 이상없이 작동되는 것입니다

driver.get(url='https://naver.com')
# 페이지 이동

print(driver.current_url)
# 이동되었는지 확인

driver.close()
# 종료
