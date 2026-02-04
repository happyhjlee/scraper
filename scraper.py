import os
import time
import pandas as pd
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# 1. 브라우저 설정 (Cloud Shell & GitHub Actions 공용)
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
# Cloud Shell 환경인 경우 아래 경로가 필요할 수 있음 (GitHub Actions에선 무시됨)
if os.path.exists("/usr/bin/google-chrome"):
    options.binary_location = "/usr/bin/google-chrome"

# 2. 드라이버 실행
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    url = "https://www.kif.re.kr/kif4/info/info_list?mid=55"
    driver.get(url)
    time.sleep(7) 

    # 3. Iframe 진입
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    if iframes:
        driver.switch_to.frame(0)
        print("Iframe 진입 성공")

    # 4. 데이터 추출
    entire_text = driver.find_element(By.TAG_NAME, "body").text
    raw_posts = entire_text.split("요약보기")
    
    final_data = []
    for post in raw_posts:
        lines = [l.strip() for l in post.split('\n') if l.strip()]
        if len(lines) >= 4:
            try:
                start_idx = 0
                for i, line in enumerate(lines):
                    if "총" in line and "건" in line:
                        start_idx = i + 1
                        break
                current_lines = lines[start_idx:] if start_idx > 0 else lines
                
                if len(current_lines) >= 4 and len(current_lines[0]) > 5:
                    final_data.append({
                        "제목": current_lines[0],
                        "행사기간": current_lines[1],
                        "주관기관": current_lines[2],
                        "등록일": current_lines[3]
                    })
            except:
                continue

    # 5. 데이터프레임 생성 및 RSS XML 문자열 만들기
    df = pd.DataFrame(final_data)
    
    if not df.empty:
        print(f"성공: {len(df)}건 수집 완료")
        
        # RSS 생성 로직 통합
        now = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0900")
        rss_xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
    <title>KIF 금융 행사 피드</title>
    <link>{url}</link>
    <description>KIF 주요기관 행사 및 연수 자동 수집 피드</description>
    <lastBuildDate>{now}</lastBuildDate>"""

        for _, row in df.iterrows():
            rss_xml += f"""
    <item>
        <title><![CDATA[{row['제목']}]]></title>
        <link>{url}</link>
        <description><![CDATA[행사기간: {row['행사기간']}<br>주관기관: {row['주관기관']}<br>등록일: {row['등록일']}]]></description>
        <pubDate>{now}</pubDate>
        <guid isPermaLink="false">{row['제목']}</guid>
    </item>"""
        
        rss_xml += "\n</channel>\n</rss>"

        # 6. 파일 저장
        with open("kif_feed.xml", "w", encoding="utf-8") as f:
            f.write(rss_xml)
        print("kif_feed.xml 저장 완료")
        
        # CSV 저장 (선택 사항)
        df.to_csv("kif_list.csv", index=False, encoding="utf-8-sig")
    else:
        print("수집된 데이터가 없습니다.")

except Exception as e:
    print(f"오류 발생: {e}")

finally:
    driver.quit()
