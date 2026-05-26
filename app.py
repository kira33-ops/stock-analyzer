import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

st.set_page_config(page_title="증권사 리포트 족집게", layout="centered")
st.title("🎯 오늘 증권사들이 픽한 핵심 리포트 선별기")

def get_naver_reports():
    report_list = []
    for page in range(1, 6):
        url = f"https://finance.naver.com/research/company_list.naver?&page={page}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "lxml")
        table = soup.find("table", class_="type_1")
        if not table: continue 
        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 5: continue
            title_a = cols[1].find("a")
            if not title_a: continue
            
            # [최종] 모바일 상세 뷰어 전용 주소로 변환
            link_path = title_a["href"]
            full_link = "https://m.stock.naver.com" + link_path
            
            report_list.append({
                "작성일": cols[4].get_text(strip=True),
                "종목명": cols[0].get_text(strip=True),
                "리포트 제목": title_a.get_text(strip=True),
                "증권사": cols[2].get_text(strip=True),
                "링크": full_link
            })
    return pd.DataFrame(report_list)

if st.button("🔄 최신 리포트 분석하기"):
    with st.spinner("분석 중..."):
        try:
            df = get_naver_reports()
            st.success(f"총 {len(df)}개 리포트 발견!")
            
            # 새 창 열기 강화
            for _, row in df.head(10).iterrows():
                st.markdown(f'<a href="{row["링크"]}" target="_blank" rel="noopener noreferrer">📄 {row["종목명"]} ({row["증권사"]}) - 바로보기</a>', unsafe_allow_html=True)
                
        except Exception as e:
            st.error("데이터 로딩 실패")