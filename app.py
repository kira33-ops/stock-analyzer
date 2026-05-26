import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib.parse

# 페이지 설정
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
            
            raw_link = "https://finance.naver.com" + title_a["href"]
            search_query = urllib.parse.quote(f"{cols[0].get_text(strip=True)} {cols[2].get_text(strip=True)} 리포트")
            search_link = f"https://search.naver.com/search.naver?query={search_query}"
            
            report_list.append({
                "작성일": cols[4].get_text(strip=True),
                "종목명": cols[0].get_text(strip=True),
                "리포트 제목": title_a.get_text(strip=True),
                "증권사": cols[2].get_text(strip=True),
                "링크": raw_link,
                "검색링크": search_link
            })
    return pd.DataFrame(report_list)

# 분석 실행
if st.button("🔄 최신 리포트 분석하기"):
    with st.spinner("분석 중..."):
        df = get_naver_reports()
        # 접속 환경 확인
        user_agent = st.context.headers.get("User-Agent", "").lower()
        is_mobile = "mobile" in user_agent or "android" in user_agent or "iphone" in user_agent
        
        # 링크 결정 함수
        def get_link(row):
            return row["검색링크"] if is_mobile else row["링크"]
        
        def make_link_html(text, row):
            target = get_link(row)
            label = "🔎 네이버에서 찾기" if is_mobile else "📄 리포트 원문보기"
            return f'<a href="{target}" target="_blank" style="text-decoration:none; color:blue; font-weight:bold;">{text} ({label})</a>'

        st.success(f"총 {len(df)}개의 리포트를 분석했습니다!")
        
        # 1. 중복 종목 분석
        st.markdown("### 🔥 1. 여러 증권사가 동시에 주목한 종목")
        counts = df["종목명"].value_counts()
        hot_stocks = counts[counts > 1].index.tolist()
        for stock in hot_stocks:
            stock_data = df[df["종목명"] == stock]
            with st.expander(f"📈 {stock} ({len(stock_data)}개 증권사 추천)"):
                for _, row in stock_data.iterrows():
                    st.markdown(make_link_html(f"{row['증권사']} 리포트", row), unsafe_allow_html=True)
        
        # 2. 목표주가 상향 분석
        st.markdown("### 🚀 2. [목표주가 상향] 핵심 리포트")
        up_reports = df[df["리포트 제목"].str.contains("상향|올려|우상향|상향조정|목표가|매수|Top pick", case=False, na=False)]
        for _, row in up_reports.iterrows():
            with st.container(border=True):
                st.caption(f"{row['증권사']} | {row['작성일']}")
                st.markdown(make_link_html(f"{row['종목명']}: {row['리포트 제목']}", row), unsafe_allow_html=True)
        
        # 3. 전체 목록
        st.markdown("### 📋 전체 리포트 목록")
        st.dataframe(df.drop(columns=["링크", "검색링크"]), use_container_width=True)