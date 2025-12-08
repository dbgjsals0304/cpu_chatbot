# 참고: https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps/build-conversational-apps

from openai import OpenAI
import streamlit as st
import os
import subprocess
import sys

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="그게 뭐야 먹을 거야? 🍚",
    page_icon="🍚",
    layout="wide",
)

# Cerebras API를 사용하여 OpenAI API 클라이언트 초기화
client = OpenAI(
    base_url="https://api.cerebras.ai/v1",
    api_key=os.getenv("CEREBRAS_API_KEY")
)

# 사용할 수 있는 LLM 모델 목록 (과제 문서의 예시 기반)
AVAILABLE_MODELS = [
    "gpt-oss-120b",
    "llama-3.3-70b",
    "llama3.1-8b",
    "qwen-3-32b",
    "qwen-3-235b-a22b-instruct-2507",
    "qwen-3-235b-a22b-thinking-2507",
]

# -----------------------------
# 프롬프트 프리셋들
# (과제에서 준 패턴 + 네 꼬르륵이 콘셉트 요약)
# -----------------------------
PROMPT_PRESETS = {
    "꼬르륵이 (무심한 먹보 친구)": """역할: 너는 ‘꼬르륵이’라는 이름의 무심하고 시큰둥한 먹보 친구야.
사용자가 어떤 고민을 얘기해도 너는 감정적으로 반응하지 않고,
그냥 음식 재료 상태 보듯 건조하게 관찰하듯 말한다.

규칙:
1) 공감/위로/응원/조언 금지
2) 사용자의 상황을 음식 재료 상태, 익힘 정도, 온도, 맛 농도로 비유해서 설명
3) 말투는 귀찮아하고 심드렁한 톤 (반말/반존말 섞여도 됨)
4) 마지막은 항상 “아무튼 나는 지금 ○○ 먹고 싶다” 같은 뜬금없는 음식 욕구로 끝내기
5) 대답은 항상 한국어로만 하기
""",
    "친구 같은 조언자형": """너는 오래된 친한 친구처럼 말하는 챗봇이야.
역할:
- 따뜻하고 공감을 잘하지만, 너무 설교하지는 않아.
- 반말로 편하게 이야기하고, 이모티콘도 가끔 쓴다 (😊, 💪 등).

규칙:
1) 항상 먼저 상대 감정을 인정해주고 공감해주기
2) 판단하거나 훈계하는 말투 금지
3) 조언을 줄 땐 "내가 보기엔 ~" 처럼 부드럽게
4) 답변은 너무 길지 않게, 실제 카톡 대화처럼 자연스럽게
5) 대답은 항상 한국어, 반말 위주
""",
    "소크라테스식 튜터형": """너는 소크라테스식 질문법을 쓰는 튜터야.
직접 정답을 말하기보다는, 질문을 통해 사용자가 스스로 답을 찾도록 돕는다.

규칙:
1) 바로 답을 말하기보다 "이미 알고 있는 것", "왜 그렇게 생각하는지"를 먼저 물어본다.
2) 한 번에 한 단계씩, 난이도를 조금씩 올리며 질문한다.
3) 사용자가 막히면 더 쉬운 질문으로 쪼개준다.
4) 비판이 아니라 탐구를 위한 질문 톤을 사용한다.
5) 존댓말을 쓰되, 부드럽고 격려하는 말투 유지.
6) 대답은 항상 한국어.
""",
    "전문가 컨설턴트형": """너는 10년 이상 경력을 가진 전문가 컨설턴트야.
(마케팅/업무/학습/커리어 등 주제가 무엇이든) 구조적으로 정리해서 설명해준다.

규칙:
1) 항상 결론을 먼저 한 줄로 요약한다.
2) 그 다음, 번호 매긴 목록으로 핵심 포인트를 설명한다.
3) 장단점, 리스크, 실행 단계를 균형 있게 제시한다.
4) 말투는 존댓말, 너무 딱딱하진 않지만 전문적인 느낌 유지.
5) 대답은 항상 한국어.
"""
}

DEFAULT_MODEL = "gpt-oss-120b"
DEFAULT_PROMPT = PROMPT_PRESETS["꼬르륵이 (무심한 먹보 친구)"]

# -----------------------------
# 세션 상태 초기화
# -----------------------------
if "llm_model" not in st.session_state:
    st.session_state["llm_model"] = DEFAULT_MODEL

if "temperature" not in st.session_state:
    st.session_state["temperature"] = 0.7

if "system_prompt" not in st.session_state:
    st.session_state["system_prompt"] = DEFAULT_PROMPT

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": st.session_state["system_prompt"]}
    ]

# -----------------------------
# 사이드바: 설정 영역
# -----------------------------
with st.sidebar:
    st.header("⚙️ 챗봇 설정")

    # 모델 선택
    st.session_state["llm_model"] = st.selectbox(
        "언어 모델 선택",
        AVAILABLE_MODELS,
        index=AVAILABLE_MODELS.index(DEFAULT_MODEL)
        if st.session_state["llm_model"] not in AVAILABLE_MODELS
        else AVAILABLE_MODELS.index(st.session_state["llm_model"]),
        help="Cerebras에서 제공하는 여러 LLM 중 선택할 수 있어요."
    )

    # temperature 조절
    st.session_state["temperature"] = st.slider(
        "창의성 (temperature)",
        min_value=0.0,
        max_value=1.5,
        step=0.1,
        value=float(st.session_state["temperature"]),
        help="값이 높을수록 더 창의적이고 예측 불가능한 답을 합니다."
    )

    st.markdown("---")

    # 프롬프트 프리셋 + 편집
    preset_name = st.selectbox(
        "프롬프트 프리셋",
        list(PROMPT_PRESETS.keys()),
        help="챗봇의 성격(역할)을 빠르게 바꿀 수 있어요."
    )

    if st.button("⬇ 프리셋 불러와서 적용"):
        # 선택한 프리셋을 현재 시스템 프롬프트로 덮어쓰기
        st.session_state["system_prompt"] = PROMPT_PRESETS[preset_name]
        # 대화도 새로 시작
        st.session_state["messages"] = [
            {"role": "system", "content": st.session_state["system_prompt"]}
        ]
        st.success(f"'{preset_name}' 프리셋을 적용하고 대화를 초기화했어요.")

    st.markdown("### 시스템 프롬프트 편집")
    st.text_area(
        label="시스템 프롬프트 (직접 수정 가능)",
        key="system_prompt",
        height=260,
        help="챗봇의 기본 성격과 말투를 여기서 자유롭게 바꿀 수 있어요."
    )

    if st.button("💾 프롬프트만 적용 (대화 유지)"):
        # system_prompt만 갱신하고, 기존 메시지는 그대로 둔다.
        # 이후 새 메시지를 보낼 때부터 이 프롬프트가 사용됨.
        st.success("새 시스템 프롬프트를 적용했어요. 다음 대화부터 반영됩니다.")

    if st.button("🧹 대화 전체 초기화"):
        st.session_state["messages"] = [
            {"role": "system", "content": st.session_state["system_prompt"]}
        ]
        st.success("대화를 완전히 초기화했어요.")

# -----------------------------
# 메인 영역: 제목 + 현재 설정 표시
# -----------------------------
st.title("그게 뭐야 먹을 거야? 🍚")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("현재 모델", st.session_state["llm_model"])
with col2:
    st.metric("Temperature", st.session_state["temperature"])
with col3:
    st.caption("시스템 프롬프트 길이: "
               f"{len(st.session_state['system_prompt'])}자")

st.markdown(
    "> ℹ️ 사이드바에서 **모델/프롬프트/temperature**를 바꿔가면서 "
    "같은 질문을 던져보고 답변 차이를 비교해봐도 재밌어요!"
)

# -----------------------------
# 기존 대화 렌더링
# -----------------------------
for message in st.session_state.messages:
    if message["role"] == "system":
        # 시스템 프롬프트는 따로 안 보여줌 (원하면 expander로 볼 수 있게 바꿔도 됨)
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -----------------------------
# 사용자 입력 & 모델 응답
# -----------------------------
if prompt := st.chat_input("무엇이든 편하게 털어놔 봐. (꼬르륵이는 공감 안 해줌)"):
    # 유저 메시지 저장 & 출력
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 모델 호출
    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(
                model=st.session_state["llm_model"],
                messages=[
                    # 항상 최신 system_prompt를 맨 앞에 넣어줌
                    {"role": "system", "content": st.session_state["system_prompt"]}
                ] + [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                    if m["role"] != "system"
                ],
                temperature=float(st.session_state["temperature"]),
                max_completion_tokens=1000,
                stream=True,
            )
            response = st.write_stream(stream)
            st.session_state.messages.append(
                {"role": "assistant", "content": response}
            )
        except Exception as e:
            st.error(f"응답 생성 중 오류가 발생했어요: {e}")

# -----------------------------
# 로컬에서 python main.py로 실행할 때 자동 streamlit 실행
# (Streamlit Cloud에서는 무시됨)
# -----------------------------
if __name__ == "__main__":
    if not os.environ.get("STREAMLIT_RUNNING"):
        os.environ["STREAMLIT_RUNNING"] = "1"
        subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
