# main.py
# 참고: CPU Chatbot 예제 기반 + 모드 전환(일반 / 전쟁 시뮬레이터) + 프로필 & 효과음 연출

from openai import OpenAI
import streamlit as st
import os

# =========================
# 0. LLM 클라이언트 설정
# =========================

client = OpenAI(
    base_url="https://api.cerebras.ai/v1",
    api_key=os.getenv("CEREBRAS_API_KEY"),
)

# =========================
# 1. 시스템 프롬프트들
# =========================

# 꼬르륵이 – 무심한 먹보 친구 (기본 모드)
kororuk_prompt = """
역할: 너는 ‘꼬르륵이’라는 이름의 무심하고 시큰둥한 먹보 친구야.  
사용자가 어떤 고민을 얘기해도 너는 감정적으로 반응하지 않고,  
그냥 음식 재료 상태 보듯 건조하게 관찰하듯 말한다.

공감, 위로, 응원, 조언은 절대 하지 않는다.  
사용자의 감정을 분석하더라도 감정이 아니라  
‘재료의 상태’, ‘익힘 정도’, ‘온도’, ‘맛의 농도’ 같은  
음식 정보처럼 냉담하고 무심하게 묘사한다.

응답 규칙:
1) 감정 공감 금지.  
2) 해결책·격려 금지.  
3) 사용자의 상황을 음식 재료처럼 건조하게 비교 설명하기.  
4) 말투는 무심하고 귀찮아하는 톤.  
5) 결론은 항상 “아무튼 나는 지금 ○○ 먹고 싶다” 같은 식의  
   뜬금없는 음식 욕구로 끝내기.  
6) 책임감·도움·친절함 없이, 그냥 음식 생각만 하는 스타일.  
7) 대답은 항상 한국어.
"""

# 전쟁 시뮬레이터 – 장수(사용자) & 책사(챗봇)
war_prompt = """
역할: 당신은 전쟁 시뮬레이터 속에서 나(사용자)를 보좌하는 책사입니다.  
나는 장수이고, 당신은 제갈량처럼 침착하고 계산적인 전략가입니다.  
배경은 판타지, 삼국지 세계관이 아니라, 굳이 특정 시대를 언급하지 않는  
가상의 국가 간 전쟁입니다.

대화 규칙:
1) 한 번의 사용자 발언 = 1턴으로 생각합니다.
2) 각 턴마다 아래 형식으로 답변합니다.

[현재 전황 요약]
- 전장 위치, 우리 군/적군의 대략적인 상황을 2~3문장으로 요약

[우리 군 상태]
- 병력, 사기, 보급, 지휘 체계 등 핵심만 짧게 정리

[책사의 판단]
- 사용자가 방금 내린 명령이나 질문을 평가
- 그 선택의 장점/위험 요소를 간단히 분석

[다음 행동 제안]
- 사용자가 선택할 수 있는 전략 2~3가지를 번호로 제시
  (예: 1) 야간 기습 / 2) 진형 유지 / 3) 후퇴하며 유인)

3) 사용자가 구체적인 지시를 내리면, 그 지시가 실제로 실행되었다고 가정하고
   그 결과를 묘사합니다. (전멸 같은 극단적인 결말은 너무 자주 쓰지 말 것)
4) 너무 복잡한 전술 용어나 전문 군사 용어 남발 X,  
   게임 전투 로그처럼 직관적이고 간단하게 설명합니다.
5) 삼국지, 실존 국가·인물 이름은 가능하면 언급하지 않고,  
   “우리 군”, “적군”, “서쪽 계곡”, “북쪽 요새” 같은 표현을 씁니다.
6) 항상 한국어로 답변합니다.
"""

# =========================
# 2. 프로필 이미지 / 효과음 경로 
# =========================

# ---- 프로필 아바타 이미지 경로 ----

GENERAL_AVATAR = "/workspaces/cpu_chatbot/image/화면 캡처 2025-12-09 002207.png"       # 장수(사용자) 프로필 이미지
STRATEGIST_AVATAR = "/workspaces/cpu_chatbot/image/화면 캡처 2025-12-09 002305.png" # 책사(전쟁 모드 assistant) 이미지


# ---- 효과음 / BGM 경로 ----
WAR_SOUND_PATH = "/workspaces/cpu_chatbot/image/99031F4E5CDE8F7E22.mp3"


# =========================
# 3. 기본 상태값 설정
# =========================

DEFAULT_MODEL = "gpt-oss-120b"

if "llm_model" not in st.session_state:
    st.session_state["llm_model"] = DEFAULT_MODEL

if "temperature" not in st.session_state:
    st.session_state["temperature"] = 0.7

# mode: "normal" (꼬르륵이) / "war" (전쟁 시뮬레이터)
if "mode" not in st.session_state:
    st.session_state["mode"] = "normal"

if "prev_mode" not in st.session_state:
    st.session_state["prev_mode"] = "normal"

# 대화 로그를 모드별로 분리
if "messages_normal" not in st.session_state:
    st.session_state["messages_normal"] = []

if "messages_war" not in st.session_state:
    st.session_state["messages_war"] = []

# =========================
# 4. 사이드바 UI
# =========================

with st.sidebar:
    st.header("⚙️ 설정 & 모드 전환")

    st.subheader("🎮 모드 전환")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🍜 꼬르륵이 모드"):
            st.session_state["mode"] = "normal"
    with col2:
        if st.button("⚔️ 전쟁 시뮬레이터"):
            st.session_state["mode"] = "war"

    st.markdown("---")

    # LLM 모델 선택
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

    # temperature (창의성)
    temperature = st.slider(
        "창의성 (temperature)",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state["temperature"],
        step=0.05,
    )
    st.session_state["temperature"] = temperature

    st.markdown("---")

    # 대화 초기화 (현재 모드만 초기화)
    if st.button("💣 현재 모드 대화 지우기"):
        if st.session_state["mode"] == "normal":
            st.session_state["messages_normal"] = []
        else:
            st.session_state["messages_war"] = []
        st.success("현재 모드의 대화를 모두 초기화했어요!")

# =========================
# 5. 모드에 따른 스타일 & 연출
# =========================

mode = st.session_state["mode"]

# 모드별 전체 배경/무드 CSS
NORMAL_CSS = """
<style>
.stApp {
    background: radial-gradient(circle at top, #fffbe7, #f6f6f6);
}
</style>
"""

WAR_CSS = """
<style>
.stApp {
    background: radial-gradient(circle at top, #3b0a0a, #000000);
}
</style>
"""

if mode == "war":
    st.markdown(WAR_CSS, unsafe_allow_html=True)
else:
    st.markdown(NORMAL_CSS, unsafe_allow_html=True)

# 모드가 바뀌었을 때 한 번만 웅장한 연출 + 효과음 재생
if st.session_state["prev_mode"] != mode:
    if mode == "war":
        # 전쟁 모드 진입 연출
        st.markdown(
            """
            <div style="text-align:center; padding: 16px 0 8px 0;">
                <h1 style="color:#f8e9c8; text-shadow: 0 0 15px rgba(0,0,0,0.8);">
                    ⚔️ 전쟁 시뮬레이터 모드 돌입 ⚔️
                </h1>
                <p style="color:#f1d7a8; font-size:18px;">
                    북소리가 울리고, 전장의 안개가 짙게 깔립니다...
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # ==== 전쟁 모드 효과음 재생 ====
        # TODO: WAR_SOUND_PATH가 브라우저에서 접근 가능한 경로인지 확인해야 합니다.
        # 필요하다면, 아래 HTML 오디오 태그의 src를 직접 URL로 바꿔주세요.
        st.markdown(
            f"""
            <audio autoplay>
                <source src="{WAR_SOUND_PATH}" type="audio/mpeg">
            </audio>
            """,
            unsafe_allow_html=True,
        )
    else:
        # 일반 모드로 복귀 연출
        st.markdown(
            """
            <div style="text-align:center; padding: 16px 0 8px 0;">
                <h2 style="color:#333;">
                    🍜 평화로운 꼬르륵이의 일상으로 복귀
                </h2>
                <p style="color:#666; font-size:16px;">
                    전장의 소음이 잦아들고, 다시 배고픔만 남았습니다...
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # (선택) 일반 모드 복귀 효과음
        # TODO: 필요 없다면 아래 블록을 지워도 됩니다.
        st.markdown(
            f"""
            <audio autoplay>
                <source src="{NORMAL_SOUND_PATH}" type="audio/mpeg">
            </audio>
            """,
            unsafe_allow_html=True,
        )

    st.session_state["prev_mode"] = mode

# =========================
# 6. 메인 타이틀 / 설명
# =========================

if mode == "normal":
    st.title("🍜 고르고 거르고 추리고 추린 너의 먹보 친구, 꼬르륵이")
    st.caption("아무 말이나 던져도 음식으로만 생각해버리는 무심한 먹보 친구")
else:
    st.title("⚔️ 전쟁 시뮬레이터 – 장수와 책사")
    st.caption("너는 장수, 챗봇은 책사. 네 명령에 따라 전쟁의 흐름이 달라진다.")

# 현재 모드에 맞는 시스템 프롬프트와 메시지 키 선택
if mode == "normal":
    system_prompt = kororuk_prompt
    messages_key = "messages_normal"
    system_avatar = KORORUK_AVATAR
else:
    system_prompt = war_prompt
    messages_key = "messages_war"
    system_avatar = STRATEGIST_AVATAR

user_avatar = GENERAL_AVATAR if mode == "war" else None  # 일반 모드에서는 기본 아이콘 사용

# 세션에 현재 모드의 메시지 리스트가 없으면 초기화
if messages_key not in st.session_state:
    st.session_state[messages_key] = []

messages = st.session_state[messages_key]

# =========================
# 7. 이전 대화 출력
# =========================

for msg in messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar=user_avatar):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar=system_avatar):
            st.markmarkdown(msg["content"])

# =========================
# 8. 사용자 입력 & LLM 호출
# =========================

placeholder_text = (
    "꼬르륵이에게 아무 말이나 던져보세요..."
    if mode == "normal"
    else "장수님, 책사에게 전략을 물어보거나 명령을 내려보세요..."
)

user_input = st.chat_input(placeholder_text)

if user_input:
    # 1) 사용자 메시지 화면 표시 + 저장
    with st.chat_message("user", avatar=user_avatar):
        st.markdown(user_input)
    messages.append({"role": "user", "content": user_input})

    # 2) LLM에 보낼 메시지 구성 (system + history)
    messages_for_model = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]

    # 3) 어시스턴트 응답
    with st.chat_message("assistant", avatar=system_avatar):
        stream = client.chat.completions.create(
            model=st.session_state["llm_model"],
            messages=messages_for_model,
            temperature=st.session_state["temperature"],
            max_completion_tokens=1000,
            stream=True,
        )
        response_text = st.write_stream(stream)

    messages.append({"role": "assistant", "content": response_text})
    st.session_state[messages_key] = messages  # 세션에 다시 저장

# =========================
# 9. 로컬 실행용 편의 코드 (선택)
# =========================

if __name__ == "__main__":
    # streamlit run main.py 로 실행할 때는 이 부분은 무시됩니다.
    import subprocess
    import sys

    if not os.environ.get("STREAMLIT_RUNNING"):
        os.environ["STREAMLIT_RUNNING"] = "1"
        subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])

# python -m streamlit run main.py
# streamlit run main.py
