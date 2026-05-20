import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

st.set_page_config(page_title="증권사 리포트 족집게", layout="wide")
st.title("🎯 오늘 증권사들이 픽한 핵심 리포트 선별기")
st.write("네이버 증권의 최신 종목 리포트를 실시간으로 분석합니다. (100% 무료)")

def get_naver_reports():
    report_list = []
    # 1페이지부터 5페이지까지 훑는 반복 작업(루프) 시작
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
            
            # 여기서 제목과 링크를 같이 뽑아냅니다
            title_a = cols[1].find("a")
            if not title_a: continue
            
            report_list.append({
                "작성일": cols[4].get_text(strip=True),
                "종목명": cols[0].get_text(strip=True),
                "리포트 제목": title_a.get_text(strip=True),
                "증권사": cols[2].get_text(strip=True),
                "링크": "https://finance.naver.com/research/" + title_a["href"]
            })
    return pd.DataFrame(report_list)

if st.button("🔄 최신 리포트 분석하기"):
    with st.spinner("🌐 네이버 증권에서 오늘 자 리포트를 수집 및 분석하는 중..."):
        try:
            df = get_naver_reports()
            st.success(f"총 {len(df)}개의 최신 리포트를 성공적으로 가져왔습니다!")
            
            # 왼쪽/오른쪽 화면 분할
            col1, col2 = st.columns(2)
            
         # col1: 중복 추천 종목 (접혀 있는 리스트 디자인)
            with col1:
                st.markdown("### 🔥 1. 여러 증권사가 동시에 주목한 종목")
                counts = df["종목명"].value_counts()
                hot_stocks = counts[counts > 1].index.tolist()
                
                if hot_stocks:
                    for stock in hot_stocks:
                        stock_data = df[df["종목명"] == stock]
                        count = len(stock_data)
                        
                        # 평소에는 종목명만 보이고, 누르면 상세 증권사 목록이 펼쳐짐
                        with st.expander(f"📈 {stock} (총 {count}개 증권사 추천)"):
                            for _, row in stock_data.iterrows():
                                st.link_button(f"🏢 {row['증권사']} 리포트 바로가기", row['링크'], use_container_width=True)
                else:
                    st.write("현재 중복 추천 종목이 없습니다.")

            # col2: 상향 리포트 디자인 개선
            with col2:
                st.markdown("### 🚀 2. [목표주가 상향] 핵심 리포트")
                up_reports = df[df["리포트 제목"].str.contains("상향|올려|우상향|상향조정|목표가|매수|Top pick", case=False, na=False)]
                
                if not up_reports.empty:
                    for _, row in up_reports.iterrows():
                        # 각 리포트를 테두리 있는 깔끔한 박스(컨테이너) 안에 담음
                        with st.container(border=True):
                            st.caption(f"{row['증권사']} | {row['작성일']}")
                            st.link_button(f"⭐ {row['종목명']}: {row['리포트 제목']}", row['링크'], use_container_width=True)
                else:
                    st.write("제목에 '상향'이 포함된 리포트가 없습니다.")
            # 아래쪽에 전체 목록 출력
            st.markdown("---")
            st.markdown("### 📋 전체 리포트 목록")
            st.dataframe(df, use_container_width=True, column_config={
    "링크": st.column_config.LinkColumn("원문 보기")
})
            
        except Exception as e:
            st.error(f"분석 중 에러가 발생했습니다: {e}")