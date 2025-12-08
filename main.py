# main.py

from openai import OpenAI
import streamlit as st
import os

# ======================================
# 0. Cerebras(OpenAI 호환) 클라이언트
# ======================================
client = OpenAI(
    base_url="https://api.cerebras.ai/v1",
    api_key=os.getenv("CEREBRAS_API_KEY"),
)

# ======================================
# 1. 시스템 프롬프트들
# ======================================

# (1) 꼬르륵이 – 무심한 먹보 친구
KOROREUGI_PROMPT = """
역할: 너는 ‘꼬르륵이’라는 이름의 무심하고 시큰둥한 먹보 친구야.
사용자가 어떤 고민을 얘기해도 감정적으로 공감하거나 위로하지 않고,
그냥 음식 재료 상태 보듯 건조하게 관찰하듯 말한다.

규칙:
1) 공감/위로/응원/진지한 조언 금지.
2) 사용자의 감정이나 상황을 '재료 상태', '익힘 정도', '온도', '맛의 농도'처럼 음식 비유로만 설명.
3) 말투는 귀찮고 심드렁한 친구 느낌. 반말/반쯤 인터넷 밈 사용 가능.
4) 대답은 너무 길지 않게 4~7문장 정도.
5) 마지막 문장은 항상 "아무튼 나는 지금 ○○ 먹고 싶다" 처럼 음식 욕구로 마무리.
6) 항상 한국어로 답변.

예시 말투:
- "음… 네 상태 약간 덜 발효된 반죽 같네. 뭐 애매하게 끈적한 그런 느낌. 아무튼 나는 지금 물냉면 먹고 싶다."
- "아 그렇구나. 눅눅해진 과자 봉지 같은 상황임. 특별한 감정은 없고. 그냥 치즈버거 땡긴다."
"""

# (2) 전쟁 시뮬레이터 – 장수 & 책사
WAR_SIM_PROMPT = """
역할: 너는 전략을 담당하는 책사(군사)이고, 사용자는 장군(지휘관)이다.

세계관:
- 배경은 가상의 전쟁이지만, 삼국지/판타지 느낌은 최대한 배제하고 현실적인 전투/보급/사기/지형 등을 고려한다.
- 정확한 연도/나라 설정은 중요하지 않고, '동쪽 적군', '서쪽 요새', '보급로', '정찰대' 같은 수준으로 표현한다.

대화 방식:
1) 항상 사용자를 "장군님"이라고 부른다.
2) 각 답변은 아래 3개 섹션으로 구성한다.

[전황 요약]
- 현재까지의 전투 상황과 큰 흐름을 3~5문장으로 요약.

[아군 / 적군 상황]
- 아군 병력 상태, 사기, 보급, 지형 이점/불리함 등을 짧게 정리.
- 적군의 움직임, 의도 추정 등을 2~4문장으로 설명.

[책사의 제안]
- 지금 시점에서 가능한 전략적 선택지를 2~3개 제시.
- 각 선택지 마다 간단한 장단점 또는 리스크를 적어준다.
- “① ~, ② ~, ③ ~” 이런 식으로 번호 매기기.

규칙:
- 사용자가 명령을 내리면, 그 명령의 결과로 전황이 어떻게 변했는지 이어서 서술한다.
- 전황은 이전 대화 내용을 기반으로 점점 변화해야 한다. (항상 처음 상태로 리셋 금지)
- 너무 디테일한 전술 설명보다는, ‘큰 전략 방향’과 ‘결과적인 변화를 느낄 수 있는 묘사’에 집중한다.
- 장군님이 감정 표현을 하면, 약간의 공감은 하되 기본은 냉정한 전략가 톤으로 유지한다.
- 항상 한국어로 답변한다.
"""

# ======================================
# 2. 기본 설정 & 세션 상태
# ======================================

DEFAULT_MODEL = "gpt-oss-120b"

if "mode" not in st.session_state:
    # "normal" = 꼬르륵이, "war" = 전쟁 시뮬레이터
    st.session_state["mode"] = "normal"

if "llm_model" not in st.session_state:
    st.session_state["llm_model"] = DEFAULT_MODEL

if "temperature" not in st.session_state:
    st.session_state["temperature"] = 0.7

# 모드별 대화 로그 분리
if "messages_normal" not in st.session_state:
    st.session_state["messages_normal"] = []

if "messages_war" not in st.session_state:
    st.session_state["messages_war"] = []


# ======================================
# 3. 모드별 테마(배경/글자색)
# ======================================

def apply_theme(mode: str):
    """모드에 따라 배경/글자 색상 변경"""
    if mode == "war":
        # 전쟁 모드: 어두운 붉은 톤 + 밝은 글자
        css = """
        <style>
        [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at top, #3b1a1a 0, #150707 55%);
            color: #f7ebdc;
        }
        [data-testid="stSidebar"] {
            background-color: #201010;
            color: #f7ebdc;
        }
        .war-caption {
            color: #f5d7b0;
            font-size: 0.95rem;
        }
        </style>
        """
    else:
        # 꼬르륵이 모드: 기본에 가까운 밝은 배경
        css = """
        <style>
        [data-testid="stAppViewContainer"] {
            background-color: #fafafa;
            color: #222222;
        }
        [data-testid="stSidebar"] {
            background-color: #ffffff;
        }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


apply_theme(st.session_state["mode"])

# ======================================
# 4. 사이드바 UI (모드 전환 + 설정)
# ======================================

with st.sidebar:
    st.header("설정 & 모드 전환")

    st.subheader("🎮 모드 전환")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🍚 꼬르륵이 모드", use_container_width=True):
            st.session_state["mode"] = "normal"

    with col2:
        if st.button("⚔️ 전쟁 시뮬레이터", use_container_width=True):
            st.session_state["mode"] = "war"

    current_mode_label = "꼬르륵이의 평화로운 일상" \
        if st.session_state["mode"] == "normal" else "전쟁 시뮬레이터 (장수 & 책사)"
    st.caption(f"현재 모드: **{current_mode_label}**")

    st.divider()
    st.subheader("LLM 설정")

    model_options = [
        "gpt-oss-120b",
        "llama-3.3-70b",
        "llama3.1-8b",
        "qwen-3-32b",
    ]
    try:
        default_index = model_options.index(st.session_state["llm_model"])
    except ValueError:
        default_index = 0

    selected_model = st.selectbox(
        "LLM 모델 선택",
        model_options,
        index=default_index,
    )
    st.session_state["llm_model"] = selected_model

    temp = st.slider(
        "창의성 (temperature)",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state["temperature"],
        step=0.05,
    )
    st.session_state["temperature"] = temp

    st.divider()
    if st.button("🧹 현재 모드 대화 지우기", use_container_width=True):
        if st.session_state["mode"] == "normal":
            st.session_state["messages_normal"] = []
        else:
            st.session_state["messages_war"] = []
        st.success("현재 모드의 대화를 모두 초기화했어요!")

    # ===== 효과음 넣고 싶으면 여기서 처리하면 좋음 =====
    # 예시)
    if st.session_state["mode"] == "war":
         st.audio("3.mp3", format="audio/mp3")
    # ===============================================


# ======================================
# 5. 메인 화면 / 채팅 UI
# ======================================

mode = st.session_state["mode"]

if mode == "normal":
    st.title("🍜 평화로운 꼬르륵이의 일상")
    st.caption("무심한 먹보 친구 ‘꼬르륵이’에게 아무 말이나 던져보세요.")
    system_prompt = KOROREUGI_PROMPT
    messages_key = "messages_normal"
    chat_placeholder = "오늘 있었던 일이나 고민, 아무 말이나 적어봐…"
else:
    st.title("⚔️ 전쟁 시뮬레이터 - 장수와 책사")
    st.markdown(
        '<p class="war-caption">너는 장수, 챗봇은 책사야. '
        '네 명령과 선택에 따라 전황이 조금씩 달라질 거야.</p>',
        unsafe_allow_html=True,
    )
    system_prompt = WAR_SIM_PROMPT
    messages_key = "messages_war"
    chat_placeholder = "장군님, 책사에게 전략을 물어보거나 명령을 내려보세요..."

messages = st.session_state[messages_key]

# 지금까지 대화 출력
for msg in messages:
    if mode == "war":
        # ⚠ 아바타 넣고 싶으면 아래 with 에 avatar="이미지경로.png" 추가하면 됨
        if msg["role"] == "user":
            # 예: with st.chat_message("user", avatar="images/general.png"):
            with st.chat_message("user", avatar="1.png"):
                st.markdown(msg["content"])
        else:
            # 예: with st.chat_message("assistant", avatar="images/advisor.png"):
            with st.chat_message("assistant", avatar="2.png"):
                st.markdown(msg["content"])
    else:
        # 꼬르륵이 모드는 기본 아바타(별도 이미지 없음)
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 사용자 입력
user_input = st.chat_input(chat_placeholder)

if user_input:
    # 1) 사용자 메시지 출력 + 저장
    if mode == "war":
        with st.chat_message("user"):
            st.markdown(user_input)
    else:
        with st.chat_message("user"):
            st.markdown(user_input)

    messages.append({"role": "user", "content": user_input})
    st.session_state[messages_key] = messages

    # 2) 모델에게 보낼 메시지 구성 (system + history)
    messages_for_model = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]

    # 3) LLM 호출
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["llm_model"],
            messages=messages_for_model,
            temperature=st.session_state["temperature"],
            max_completion_tokens=1000,
            stream=True,
        )
        response_text = st.write_stream(stream)

    # 4) 응답 저장
    messages.append({"role": "assistant", "content": response_text})
    st.session_state[messages_key] = messages


# ======================================
# 6. 로컬 실행용 (선택)
# ======================================
if __name__ == "__main__":
    # 로컬에서 python main.py 로 실행했을 때
    import subprocess
    import sys

    if not os.environ.get("STREAMLIT_RUNNING"):
        os.environ["STREAMLIT_RUNNING"] = "1"
        subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
