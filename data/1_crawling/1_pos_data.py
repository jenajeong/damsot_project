from datetime import datetime
from selenium import webdriver
from datetime import datetime, timedelta
import os, time
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import json
import gspread
from google.oauth2.service_account import Credentials

# 중요한 정보 불러오기
# 로그인 정보(ID, PW), 구글 api키, 구글 스프레드시트 ID

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, "import_info.json")

with open(json_path, "r", encoding="utf-8") as f:
    info = json.load(f)
    
id = info['id']
pw = info['pw']
url = info['url']
key_path = os.path.join(BASE_DIR, info['key_path'])
SPREAD_ID = info['SPREAD_ID']

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

# 상품별 매출 클릭
button2 = driver.find_element(By.XPATH, '//*[@id="snb"]/ul/li[2]/ul/li[1]/a')
button2.click()
time.sleep(3)

# 날짜 정의 및 필터링
today = datetime.today()
start_date = today - timedelta(days=8)
end_date = (today - timedelta(days=1))

# ==========================
# # 원하는 날짜로 수동 설정
start_date = datetime(2025, 8, 6)
# ==========================

start_date = start_date.strftime("%Y-%m-%d")
end_date = end_date.strftime("%Y-%m-%d")

driver.execute_script("document.getElementById('startDate').value = arguments[0];", start_date)
driver.execute_script("document.getElementById('endDate').value = arguments[0];", end_date)
time.sleep(3)

button3 = driver.find_element(By.XPATH, '//*[@id="btnSearch"]')
button3.click()
time.sleep(10)

print('데이터에 접속 완료--------------------------------------')

# Google Sheets 인증 + 워크시트 객체 준비
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file(key_path, scopes=SCOPES)
gc = gspread.authorize(creds)
ws = gc.open_by_key(SPREAD_ID).worksheet("상품별 매출") 

# 첫 번째 페이지부터 크롤링 시작
page_num = 1

while True:
    print(f"\n====== {page_num}번째 페이지 시작 ======\n")

    rows = driver.find_elements(By.XPATH, '//*[@id="tableList"]/tbody/tr')

    for index, row in enumerate(rows[1:], start=2):
        try:
            link = row.find_element(By.XPATH, './td[4]/a') # 메뉴 클릭
            driver.execute_script("arguments[0].click();", link)
            time.sleep(2)

            tbody_rows = driver.find_elements(By.XPATH, '//*[@id="itemTimeList"]/tbody/tr')
            batch_rows = []                           
            
            for r_idx, r in enumerate(tbody_rows, start=1):
                cols     = r.find_elements(By.TAG_NAME, 'td')
                row_data = [c.text.strip() for c in cols]
                batch_rows.append(row_data)         
                print(f"{r_idx}번째 행 수집") #row 데이터 수집

            if batch_rows:                          
                # append_rows 로 한 번에 업로드(api한도)
                ws.append_rows(batch_rows, value_input_option="USER_ENTERED")
                print(f"▶ {len(batch_rows)}행 시트 업로드 완료")
                

            # 팝업 닫기
            driver.find_element(By.XPATH,
                '//*[@id="itemTime-detail-popup"]//button').click()
            time.sleep(1)

        except Exception as e:
            print(f"[{index}] 항목 처리 중 오류: {e}")
            continue

    # 다음 페이지 버튼 클릭
    try:
        next_button = driver.find_element(By.XPATH, '//*[@id="contents_body"]/div[2]/div/ul/li/div/span/a[2]')
        driver.execute_script("arguments[0].click();", next_button)
        time.sleep(5)
        page_num += 1
        
        if page_num >=3: #현재까진 메뉴가 2번째 페이지까지만 존재
            break
    except NoSuchElementException:
        print("---------------- 더 이상 다음 페이지 없음. 종료합니다.")
        break

driver.quit()
