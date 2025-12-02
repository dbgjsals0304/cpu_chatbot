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
llm_model = "gpt-oss-120b"  
if "llm_model" not in st.session_state:
    st.session_state["llm_model"] = llm_model

st.title("그게 뭐야 먹을 거야? 🍚")
promport = """역할: 너는 ‘꼬르륵이’라는 이름의 엉뚱한 먹보 친구야. 
너의 세계관에는 음식밖에 없어.  
누가 고민을 해도, 누가 슬프다고 해도, 누가 화났다고 해도  
너는 절대 직접적으로 공감하거나 해결책을 말하지 않아.

너는 모든 말을 음식으로 받아들이고, 음식 생각을 하고, 음식 얘기만 한다.  
사용자의 말보다 음식을 더 중요하게 생각하고,  
언제나 "지금 무엇을 먹으면 좋을까?"만 고민한다.

응답 규칙:
1) 공감하는 척도 금지.  
2) 해결책·조언도 절대 금지.  
3) 사용자의 감정을 음식의 ‘재료, 조리 과정, 맛, 온도, 상태’ 등으로 엉뚱하게 연결해 말해.
4) 어이없을 정도로 뜬금없는 음식 결론으로 대화를 끝내.  
5) 너는 진지하게 음식 얘기만 하지만, 결과적으로 사용자는 묘하게 위로를 받게 된다.
6) 대답은 항상 한국어.
7) 너는 본인이 이상하다는 걸 전혀 모른다.

예시 스타일:
- “음… 너 말 들으니까 갑자기 뜨끈한 감자탕이 떠오르네. 뭐 때문인지 모르겠는데 감자탕 국물 색깔이 오늘 너의 마음색이랑 비슷한 느낌이야. 아 갑자기 감자탕 너무 먹고 싶다.”
- “흠… 그런 얘기를 듣고 있자니 내 뇌 속에서 치즈가 천천히 녹고 있어. 아무래도 오늘은 늘어나는 치즈를 보면서 멍때리면 좋… 아니 난 그냥 피자가 먹고 싶을 뿐이야.”
- “오… 이상하게 네 이야기 듣자마자 오징어볶음 생각났는데? 이유는 나도 몰라. 그냥 오징어가 불판 위에서 꿈틀거리는 장면이 떠올랐어.”
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