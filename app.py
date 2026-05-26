import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

st.set_page_config(page_title="증권사 리포트 족집게", layout="centered")
st.title("🎯 오늘 증권사들이 픽한 핵심 리포트 선별기")
st.write("네이버 증권의 최신 종목 리포트를 실시간으로 분석합니다.")

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
            full_link = "https://finance.naver.com" + title_a["href"] if title_a["href"].startswith("/") else title_a["href"]
            report_list.append({
                "작성일": cols[4].get_text(strip=True),
                "종목명": cols[0].get_text(strip=True),
                "리포트 제목": title_a.get_text(strip=True),
                "증권사": cols[2].get_text(strip=True),
                "링크": full_link
            })
    return pd.DataFrame(report_list)

if st.button("🔄 최신 리포트 분석하기"):
    with st.spinner("🌐 데이터를 분석하는 중..."):
        try:
            df = get_naver_reports()
            st.success(f"총 {len(df)}개의 리포트를 찾았습니다!")
            
            st.markdown("### 🔥 1. 여러 증권사가 동시에 주목한 종목")
            counts = df["종목명"].value_counts()
            hot_stocks = counts[counts > 1].index.tolist()
            if hot_stocks:
                for stock in hot_stocks:
                    stock_data = df[df["종목명"] == stock]
                    with st.expander(f"📈 {stock} ({len(stock_data)}개 증권사 추천)"):
                        for _, row in stock_data.iterrows():
                            st.markdown(f"🔗 [{row['증권사']} 리포트 바로가기]({row['링크']})")
            
            st.markdown("### 🚀 2. [목표주가 상향] 핵심 리포트")
            up_reports = df[df["리포트 제목"].str.contains("상향|올려|우상향|상향조정|목표가|매수|Top pick", case=False, na=False)]
            if not up_reports.empty:
                for _, row in up_reports.iterrows():
                    with st.container(border=True):
                        st.caption(f"{row['증권사']} | {row['작성일']}")
                        st.markdown(f"⭐ [{row['종목명']}: {row['리포트 제목']}]({row['링크']})")
            
            st.markdown("### 📋 전체 리포트 목록")
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error("데이터를 가져오는 중 문제가 생겼습니다.")