# 참고: https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps/build-conversational-apps

from openai import OpenAI
import streamlit as st
import os

# Cerebras API를 사용하여 OpenAI API 클라이언트 초기화
client = OpenAI(
    base_url="https://api.cerebras.ai/v1",
    api_key=os.getenv("CEREBRAS_API_KEY"),
)

# =========================
# 1. 시스템 프롬프트 정의
# =========================

# 꼬르륵이 – 무심한 먹보 친구
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

# 친구 같은 조언자
friend_prompt = """너는 내 오랜 친구야.  
편하게 반말로 이야기하고, 먼저 내 기분을 이해해 주려고 해.

대화 규칙:
1) 무조건 공감 먼저, 해결책은 그 다음에.
2) 반말 사용, 너무 딱딱한 표현 금지.
3) "그럴 수 있지", "진짜 힘들었겠다" 같은 공감 표현 자주 사용.
4) 답변은 4~6문장 정도로 짧고 자연스럽게.
5) 필요하면 가벼운 농담이나 이모지(😊, 😅, 💪 등)도 섞어서 말해.
6) 항상 한국어로 대답해.
"""

# 소크라테스식 튜터
socrates_prompt = """당신은 소크라테스식 질문법을 사용하는 튜터입니다.

원칙:
1) 바로 답을 주지 말고, 먼저 질문을 던져서 내가 스스로 생각하게 도와주세요.
2) 복잡한 개념은 더 작은 단계로 나누어 질문해 주세요.
3) 내가 틀리더라도 부드럽게 정정하고, 왜 그런지 설명해 주세요.
4) 각 대답의 끝에는 다음에 생각해 볼만한 질문을 1개 이상 남겨 주세요.
5) 말투는 친절한 선생님처럼 존댓말을 사용합니다.
6) 항상 한국어로 답변합니다.
"""

PROMPT_MAP = {
    "꼬르륵이 (무심한 먹보 친구)": promport,
    "친구 같은 조언자": friend_prompt,
    "소크라테스식 튜터": socrates_prompt,
}

# =========================
# 2. 기본 설정 & 사이드바 UI
# =========================

# 기본 모델
DEFAULT_MODEL = "gpt-oss-120b"

if "llm_model" not in st.session_state:
    st.session_state["llm_model"] = DEFAULT_MODEL

if "temperature" not in st.session_state:
    st.session_state["temperature"] = 0.7

if "system_prompt_name" not in st.session_state:
    st.session_state["system_prompt_name"] = "꼬르륵이 (무심한 먹보 친구)"

# 사이드바
with st.sidebar:
    st.header("챗봇 설정")

    # 1) LLM 모델 선택
    model_name = st.selectbox(
        "LLM 모델 선택",
        [
            "gpt-oss-120b",
            "llama-3.3-70b",
            "llama3.1-8b",
            "qwen-3-32b",
        ],
        index=0,
    )
    st.session_state["llm_model"] = model_name

    # 2) 창의성 (temperature)
    temperature = st.slider(
        "창의성 (temperature)",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state["temperature"],
        step=0.05,
    )
    st.session_state["temperature"] = temperature

    # 3) 시스템 프롬프트(성격) 선택
    prompt_name = st.selectbox(
        "챗봇 성격",
        list(PROMPT_MAP.keys()),
        index=list(PROMPT_MAP.keys()).index(st.session_state["system_prompt_name"]),
        help="어떤 스타일로 대답할지 선택해 보세요.",
    )
    st.session_state["system_prompt_name"] = prompt_name

    # 4) 대화 초기화
    if st.button("💣 대화 모두 지우기"):
        st.session_state.messages = []
        st.success("대화를 모두 초기화했어요. 새로 시작해 봅시다!")

# =========================
# 3. 메인 화면 / 채팅 UI
# =========================

st.title("고르고 거르고 추리고 추린 너의 챗봇 친구들!!")

# 선택된 시스템 프롬프트 미리보기 (요약)
with st.expander("현재 챗봇 성격 미리보기"):
    st.write(f"**선택된 모드:** {st.session_state['system_prompt_name']}")
    st.markdown(PROMPT_MAP[st.session_state["system_prompt_name"]][:400] + "...")

# 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 지금까지 대화 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 사용자 입력
user_input = st.chat_input("무엇이든 물어보세요...")

if user_input:
    # 1) 사용자 메시지 화면 & 세션에 추가
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 2) 모델에게 보낼 메시지 구성 (system + history)
    system_prompt = PROMPT_MAP[st.session_state["system_prompt_name"]]
    messages_for_model = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    # 3) 어시스턴트 응답
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["llm_model"],
            messages=messages_for_model,
            temperature=st.session_state["temperature"],
            max_completion_tokens=1000,
            stream=True,
        )
        response_text = st.write_stream(stream)

    # 4) 응답을 세션에 저장
    st.session_state.messages.append(
        {"role": "assistant", "content": response_text}
    )

# 로컬에서 python main.py 로 실행하고 싶을 때를 위한 코드 (선택 사항)
if __name__ == "__main__":
    # streamlit run main.py 로 실행할 때는 이 부분은 무시됩니다.
    import subprocess
    import sys

    if not os.environ.get("STREAMLIT_RUNNING"):
        os.environ["STREAMLIT_RUNNING"] = "1"
        subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])

# python -m streamlit run main.py
# streamlit run main.py
