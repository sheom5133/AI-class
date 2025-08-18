import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from gtts import gTTS
import os
import time
from io import BytesIO

# 웹사이트의 사용자 에이전트 설정
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# 세션 상태 초기화
if 'article_data' not in st.session_state:
    st.session_state.article_data = None
if 'summary' not in st.session_state:
    st.session_state.summary = None
if 'audio_file' not in st.session_state:
    st.session_state.audio_file = None

@st.cache_data(show_spinner=False)
def get_article_content(url):
    """
    주어진 URL의 뉴스 기사 제목과 본문을 가져오는 함수
    """
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_element = soup.select_one('.media_end_head_title')
        title = title_element.get_text().strip() if title_element else "제목 없음"
        
        article_content = soup.select_one('#dic_area')
        
        if not article_content:
            st.warning("❌ 기사 본문을 찾을 수 없습니다. URL을 다시 확인해주세요.")
            return None, None
            
        text = article_content.get_text().strip()
        text = re.sub(r'\s+', ' ', text)
        
        return title, text
    except Exception as e:
        st.error(f"❌ 뉴스 기사 크롤링 실패: {e}")
        return None, None

@st.cache_data(show_spinner=False)
def summarize_text(text):
    """
    텍스트를 간단하게 요약하는 함수 (1500자 제한)
    """
    if len(text) > 1500:
        return text[:1500] + "..."
    return text

@st.cache_data(show_spinner=False)
def text_to_speech(text):
    """
    텍스트를 음성으로 변환하여 BytesIO 객체로 반환
    """
    try:
        tts = gTTS(text=text, lang='ko', slow=False)
        # BytesIO 객체를 사용하여 파일을 메모리에 저장
        audio_stream = BytesIO()
        tts.write_to_fp(audio_stream)
        audio_stream.seek(0) # 스트림의 시작 위치로 이동
        return audio_stream
    except Exception as e:
        st.error(f"❌ 음성 변환 실패: {e}")
        return None

def main():
    """
    Streamlit 웹 애플리케이션의 메인 함수
    """
    st.set_page_config(page_title="뉴스 요약 TTS 서비스", layout="centered")
    
    st.title("📰 뉴스 요약 및 음성 변환 서비스")
    st.markdown("""
        네이버 뉴스 기사 URL을 입력하면, 
        기사 내용을 요약하고 음성으로 들려줍니다.
    """)
    st.divider()

    news_url = st.text_input("🔗 네이버 뉴스 기사 URL을 입력하세요:", 
                             placeholder="예: https://n.news.naver.com/m/article/...")

    col1, col2 = st.columns(2)

    with col1:
        summarize_button = st.button("📝 뉴스 요약", use_container_width=True)
    
    with col2:
        listen_button = st.button("🔊 뉴스 듣기", use_container_width=True)

    if summarize_button:
        if not news_url:
            st.warning("URL을 입력해주세요!")
            return

        with st.spinner("⏳ 기사 내용을 가져오는 중..."):
            title, content = get_article_content(news_url)
            
            if content:
                st.session_state.article_data = {'title': title, 'content': content}
                st.session_state.summary = summarize_text(content)
                st.session_state.audio_file = None  # Reset audio file on new summary
            else:
                st.session_state.article_data = None
                st.session_state.summary = None
                st.session_state.audio_file = None
    
    if listen_button:
        if not st.session_state.summary:
            st.warning("먼저 '뉴스 요약' 버튼을 눌러 요약 내용을 생성해주세요.")
            return

        with st.spinner("⏳ 음성 파일을 생성하는 중..."):
            # 파일을 BytesIO 객체로 받아 세션 상태에 저장
            audio_bytes = text_to_speech(st.session_state.summary)
            if audio_bytes:
                st.session_state.audio_file = audio_bytes
        
    if st.session_state.summary:
        st.subheader(f"✅ 기사 제목: {st.session_state.article_data['title']}")
        st.markdown("---")
        st.write("**📝 요약 내용:**")
        st.info(st.session_state.summary)
        
    # 세션에 저장된 오디오 파일이 있으면 재생
    if st.session_state.audio_file:
        st.success("🎉 음성 파일이 성공적으로 생성되었습니다!")
        st.audio(st.session_state.audio_file, format="audio/mpeg")

    st.divider()
    st.info("💡 **사용 방법:** 네이버 뉴스 기사 URL을 입력하고 '뉴스 요약' 버튼을 먼저 누른 다음, '뉴스 듣기' 버튼을 누르세요.")
    st.markdown("---")
    st.markdown("© 2025. Powered by Streamlit")

if __name__ == "__main__":
    main()
