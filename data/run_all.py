import subprocess
import os

# 현재 파일 기준 루트 디렉토리
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 실행할 스크립트 경로 리스트
scripts = [
    os.path.join(BASE_DIR, "1_crawling", "1_pos_data.py"),
    os.path.join(BASE_DIR, "1_crawling", "2_receipt_upload.py"),
    os.path.join(BASE_DIR, "2_preprocessing", "1_merge_data.py"),
    os.path.join(BASE_DIR, "2_preprocessing", "2_outlier_value.py"),
    os.path.join(BASE_DIR, "2_preprocessing", "3_missing_value.py"),
]

for script in scripts:
    print(f"\n----------[ {script} ] 실행 중----------")
    try:
        result = subprocess.run(
            ["python", script],
            capture_output=True,
            text=True,
            check=True   # 에러 시 바로 예외 발생
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"~~~~~~~~~~[ {script} ] 에러 발생~~~~~~~~~~")
        print(e.stderr)
        break  # 에러 발생 시 전체 파이프라인 중단
