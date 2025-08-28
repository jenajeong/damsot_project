import os, time, glob
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from google.oauth2.service_account import Credentials
import json
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
import gspread

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, "import_info.json")

with open(json_path, "r", encoding="utf-8") as f:
    info = json.load(f)
    
id = info['id']
pw = info['pw']
url = info['url']
key_path = info["key_path"]
spread_id = info["SPREAD_ID"]
local_path = info["local_path"]


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

# ==========================
# # 원하는 날짜로 수동 설정
start_date = datetime(2025, 8, 6).strftime('%Y-%m-%d')   
# ==========================

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

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file(key_path, scopes=scope)
client = gspread.authorize(creds)

spreadsheet = client.open_by_key(spread_id)
worksheet = spreadsheet.worksheet("영수증별 매출")

print('업로드할 시트 가져오기 완료--------------------------------------')

list_of_files = glob.glob(os.path.join(local_path, "*.xlsx"))
latest_file = max(list_of_files, key=os.path.getctime) 

df = pd.read_excel(
    latest_file,
    usecols="B:P",  # B~P 열만
    skiprows=4      # 5행부터 읽기
)

print('로컬에서 엑셀 파일 가져오기 완료--------------------------------------')

last_row = len(worksheet.get_all_values())
if last_row > 1:  # 헤더 외에 데이터가 있으면
    worksheet.batch_clear([f"A2:P{last_row}"])

data = df.values.tolist()  # 헤더 빼고 값만
worksheet.update("A2", data)


print('구글 스프레드시트에 업로드 완료--------------------------------------')