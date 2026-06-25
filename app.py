import streamlit as st
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
from deep_translator import GoogleTranslator
import torch

st.set_page_config(page_title="이미지 캡션 생성 데모", layout="centered")

@st.cache_resource
def load_model():
    name = "Salesforce/blip-image-captioning-base"  # 배포용 경량 모델
    processor = BlipProcessor.from_pretrained(name)
    model = BlipForConditionalGeneration.from_pretrained(name)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    return processor, model, device

st.markdown("# 이미지 캡션 생성 데모")
st.write("입력 이미지 (이미지 파일을 끌어다 놓을 수 있습니다):")

uploaded = st.file_uploader("파일 선택", type=["jpg", "jpeg", "png"])

if uploaded is not None:
    image = Image.open(uploaded).convert("RGB")
    st.image(image, width=280)
    st.caption(uploaded.name)

    if st.button("캡션 생성"):
        step = st.empty()
        def show(a, b, c):
            def fmt(t, on): return f"<span style='background:#90EE90;font-weight:bold'>{t}</span>" if on else t
            step.markdown(f"{fmt('모델 불러오기', a)} &gt; {fmt('이미지 분석', b)} &gt; {fmt('텍스트 생성', c)}",
                          unsafe_allow_html=True)

        show(True, False, False)
        processor, model, device = load_model()

        show(True, True, False)
        inputs = processor(image, return_tensors="pt").to(device)
        outputs = model.generate(
            **inputs, max_new_tokens=40,
            num_beams=5, num_return_sequences=5, do_sample=False,
        )
        captions = [processor.decode(o, skip_special_tokens=True) for o in outputs]

        show(True, True, True)

        translator = GoogleTranslator(source="en", target="ko")
        st.subheader("생성된 캡션 (영어 / 한국어) — 5개")
        for i, eng in enumerate(captions, 1):
            try:
                kor = translator.translate(eng)
            except Exception:
                kor = "(번역 실패)"
            st.markdown(f"**{i}. (영어)** `{eng}`")
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**(한국어)** {kor}", unsafe_allow_html=True)
            st.divider()
else:
    st.info("생성된 캡션이 여기에 표시됩니다.")
