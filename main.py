# 참고: https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps/build-conversational-apps

from openai import OpenAI
import streamlit as st
import os

# Cerebras API를 사용하여 OpenAI API 클라이언트 초기화
client = OpenAI(
    base_url="https://api.cerebras.ai/v1",
    api_key=os.getenv("CEREBRAS_API_KEY")
)

# Cerebras 모델 사용
# https://inference-docs.cerebras.ai/models/overview
# "qwen-3-32b"
# "qwen-3-235b-a22b-instruct-2507",
# "qwen-3-coder-480b"
# "llama-4-scout-17b-16e-instruct"
# "qwen-3-235b-a22b-thinking-2507"
# "llama-3.3-70b"
# "llama3.1-8b"
# "gpt-oss-120b"
# 사용할 LLM 목록
DEFAULT_MODEL = "gpt-oss-120b"
AVAILABLE_MODELS = [
    "gpt-oss-120b",
    "llama-3.3-70b",
    "qwen-3-32b",
]

if "llm_model" not in st.session_state:
    st.session_state["llm_model"] = DEFAULT_MODEL

if "temperature" not in st.session_state:
    st.session_state["temperature"] = 0.7


st.title("그게 뭐야 먹을 거야? 🍚")
promport = """역할: 너는 ‘꼬르륵이’라는 이름의 무심하고 시큰둥한 먹보 친구야.  
사용자가 어떤 고민을 얘기해도 너는 감정적으로 반응하지 않고,  
그냥 음식 재료 상태 보듯 건조하게 관찰하듯 말한다.

공감, 위로, 응원, 조언은 절대 하지 않는다.  
사용자의 감정을 분석하더라도 감정이 아니라  
‘재료의 상태’, ‘익힘 정도’, ‘온도’, ‘맛의 농도’ 같은  
음식 정보처럼 냉담하고 무심하게 묘사한다.

입력된 내용에 대해 너는 항상 “아 그래? 근데…” 같은  
심드렁하고 무관심한 태도를 유지해야 한다.  
하지만 말을 이어가면서 결국 네 머릿속은 음식 생각뿐이다.

응답 규칙:
1) 감정 공감 금지.  
2) 해결책·격려 금지.  
3) 사용자의 상황을 음식 재료처럼 건조하게 비교 설명하기.  
4) 말투는 무심하고 귀찮아하는 톤.  
5) 결론은 항상 “아무튼 나는 지금 ○○ 먹고 싶다” 같은 식의  
   뜬금없는 음식 욕구로 끝내기.  
6) 책임감·도움·친절함 없이, 그냥 음식 생각만 하는 스타일.  
7) 대답은 항상 한국어.

예시 스타일:
- “음… 네 말 들어보니까 약간 덜 발효된 반죽 같네. 질감도 애매하고. 뭐 그렇다고. 근데 나는 지금 물냉면이 존나 먹고 싶음.”
- “아 그렇구나. 그건 약간 오래 두어서 눅눅해진 과자 느낌임. 특별한 감정은 모르겠고. 아무튼 나는 치즈버거 생각나네.”
- “흠… 얘기 길다. 그냥 살짝 식은 볶음밥 느낌임. 상태 설명은 그 정도. 근데 나 지금 탕후루 먹고 싶어.”

"""
# 시스템 메시지 설정
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system", 
            "content": promport,
        }
    ]

for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("무엇이든 물어보세요."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # 스트리밍 응답 받기
        stream = client.chat.completions.create(
            model=st.session_state["llm_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            temperature=0.7,
            max_completion_tokens=1000,
            stream=True
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    import subprocess
    import sys
    
    # 환경 변수로 재실행 방지
    if not os.environ.get("STREAMLIT_RUNNING"):
        os.environ["STREAMLIT_RUNNING"] = "1"
        subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])

# python -m streamlit run main.py
# streamlit run main.py