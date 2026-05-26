import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib.parse

st.set_page_config(page_title="증권사 리포트 족집게", layout="wide")
st.title("🎯 오늘 증권사들이 픽한 핵심 리포트 선별기")
st.write("네이버 증권 리포트를 분석합니다. (PC: 바로가기 / 모바일: 검색으로 안전하게)")

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
            
            # PC용 원문 링크
            raw_link = "https://finance.naver.com/research/" + title_a["href"]
            # 모바일용 검색 링크 (종목명+증권사 검색)
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

# 접속 환경 감지 함수
def is_mobile_device():
    user_agent = st.context.headers.get("User-Agent", "").lower()
    return any(device in user_agent for device in ["mobile", "android", "iphone", "ipad"])

if st.button("🔄 최신 리포트 분석하기"):
    with st.spinner("🌐 데이터를 분석하는 중..."):
        try:
            df = get_naver_reports()
            is_mobile = is_mobile_device()
            
            # 링크 선택 로직
            def get_target_link(row):
                return row["검색링크"] if is_mobile else row["링크"]
            
            st.success(f"총 {len(df)}개의 리포트를 분석했습니다! ({'모바일 모드' if is_mobile else 'PC 모드'})")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🔥 1. 여러 증권사가 동시에 주목한 종목")
                counts = df["종목명"].value_counts()
                hot_stocks = counts[counts > 1].index.tolist()
                for stock in hot_stocks:
                    stock_data = df[df["종목명"] == stock]
                    with st.expander(f"📈 {stock} ({len(stock_data)}개 증권사 추천)"):
                        for _, row in stock_data.iterrows():
                            # 모바일이면 검색, PC면 원문 바로가기
                            link = get_target_link(row)
                            st.link_button(f"🏢 {row['증권사']} 리포트 확인", link, use_container_width=True)
            
            with col2:
                st.markdown("### 🚀 2. [목표주가 상향] 핵심 리포트")
                up_reports = df[df["리포트 제목"].str.contains("상향|올려|우상향|상향조정|목표가|매수|Top pick", case=False, na=False)]
                for _, row in up_reports.iterrows():
                    with st.container(border=True):
                        st.caption(f"{row['증권사']} | {row['작성일']}")
                        link = get_target_link(row)
                        st.link_button(f"⭐ {row['종목명']}: {row['리포트 제목']}", link, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 📋 전체 리포트 목록")
            # 전체 목록에서도 모바일/PC별로 링크가 자동으로 바뀌게 설정
            df_display = df.copy()
            df_display["링크"] = df_display.apply(get_target_link, axis=1)
            st.dataframe(df_display.drop(columns=["검색링크"]), use_container_width=True)
            
        except Exception as e:
            st.error(f"분석 중 에러가 발생했습니다: {e}")