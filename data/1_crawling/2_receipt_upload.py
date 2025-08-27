import os, time, glob
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import json
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta

import_info = "import_info.json"

with open(import_info,'r') as file:
    import_info = json.load(file)
    
id = import_info['id']
pw = import_info['pw']
url = import_info['url']


# 크롬 열기
options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--lang=ko-KR')
driver = webdriver.Chrome(options=options)

driver.get(url)

time.sleep(3)

# 아이디 입력
id_input = driver.find_element(By.ID, 'userId')
for char in id:
    id_input.send_keys(char)
    time.sleep(0.1)

# 비밀번호 입력
pw_input = driver.find_element(By.ID, 'password')
for char in pw:
    pw_input.send_keys(char)
    time.sleep(0.1)

login_button = driver.find_element(By.ID, 'btnLogin')
login_button.click()
time.sleep(3)

print('로그인 완료--------------------------------------')

# 매출확인 버튼 클릭
button1 = driver.find_element(By.XPATH, '//*[@id="lnb"]/div/ul/li[2]/a')
button1.click()
time.sleep(3)

print('매출창으로 이동 완료--------------------------------------')

# 영수증별 매출 버튼 클릭
button2 = driver.find_element(By.XPATH, '//*[@id="snb"]/ul/li[3]/ul/li[1]/a')
button2.click()
time.sleep(3)

print('영수증별 매출창으로 이동 완료--------------------------------------')


# 날짜 정의 및 필터링
today = datetime.today()
start_date = (today - timedelta(days=8)).strftime('%Y-%m-%d')
end_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')

js = """
  const [val, id] = arguments;
  const el = document.getElementById(id);
  el.removeAttribute('readonly');
  el.value = val;
  el.dispatchEvent(new Event('input'));
  el.dispatchEvent(new Event('change'));
"""

driver.execute_script(js, start_date, 'startDate')
driver.execute_script(js, end_date, 'endDate')
time.sleep(3)

button3 = driver.find_element(By.XPATH, '//*[@id="btnSearch"]')
button3.click()
time.sleep(10)

print('날짜구간 변경 완료--------------------------------------')

download_button = driver.find_element(By.XPATH, '//*[@id="btnExcel2"]')
download_button.click()
time.sleep(10)

print('영수증별 매출 엑셀파일 다운로드 완료--------------------------------------')