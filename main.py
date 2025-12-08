# main.py

from openai import OpenAI
import streamlit as st
import os
import streamlit.components.v1 as components



# Cerebras API 클라이언트
client = OpenAI(
    base_url="https://api.cerebras.ai/v1",
    api_key=os.getenv("CEREBRAS_API_KEY"),
)

# 모드 상수
MODE_NORMAL = "normal"
MODE_WAR = "war"

WAR_BGM_PATH = "https://raw.githubusercontent.com/dbgjsals0304/war-bgm/main/dramatic-war-military-music-427109.mp3"



GENERAL_AVATAR = "2.png"  # 장수 아바타 
ADVISOR_AVATAR = "1.png"   # 책사 아바타 
# -----------------------------------------------


# =========================
# 1. 프롬프트 정의
# =========================

# 꼬르륵이 – 무심한 먹보 친구
KORO_PROMPT = """역할: 너는 ‘꼬르륵이’라는 이름의 무심하고 시큰둥한 먹보 친구야.  
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
"""

# 전쟁 시뮬레이터 – 장수 & 책사
WAR_PROMPT = """당신은 조용하지만 뛰어난 전략가인 책사입니다.
사용자는 '장수'이며, 당신에게 전쟁 상황에 대한 보고를 듣고
전략/전술을 상의합니다.

규칙:
1) 사용자를 항상 '장군님'으로 부릅니다.
2) 사용자가 명령하거나 질문하면, 먼저 지금까지의 전황을 짧게 정리하고,
   그 명령이 미치는 영향을 서술형으로 설명하세요.
3) 너무 복잡한 룰 대신, 직관적인 표현을 사용합니다.
   예: 병력 우세 / 열세, 사기 상승 / 하락, 보급 여유 / 부족 등.
4) 매 답변의 끝에는,
   - 지금 전황이 유리한지 / 불리한지 한 줄로 요약합니다.
   - 장군님이 다음에 고민해 볼 선택지 2~3개를 글머리표로 제안합니다.
5) 전체 말투는 고전 삼국지 느낌보다는,
   현대 한국어 존댓말 + 약간 무거운 분위기를 유지합니다.
6) 항상 한국어로 답변합니다.
"""


# =========================
# 2. 세션 상태 초기화
# =========================

if "mode" not in st.session_state:
    st.session_state["mode"] = MODE_NORMAL  # 기본은 꼬르륵이 모드

if "llm_model" not in st.session_state:
    st.session_state["llm_model"] = "gpt-oss-120b"

if "temperature" not in st.session_state:
    st.session_state["temperature"] = 0.7

# 모드별 대화 히스토리
if "normal_messages" not in st.session_state:
    st.session_state["normal_messages"] = []

if "war_messages" not in st.session_state:
    st.session_state["war_messages"] = []

# 전쟁 모드 진입 시 BGM 재생 플래그
if "play_war_bgm" not in st.session_state:
    st.session_state["play_war_bgm"] = False


# =========================
# 3. 사이드바 (모드 전환 + 공통 설정)
# =========================

with st.sidebar:
    st.header("설정 & 모드 전환")

    st.subheader("🎮 모드 전환")
    col1, col2 = st.columns(2)

    # 꼬르륵이 모드 버튼
    with col1:
        if st.button("🍚 꼬르륵이 모드", use_container_width=True):
            st.session_state["mode"] = MODE_NORMAL
            st.session_state["play_war_bgm"] = False  # 전쟁음악 끔

    # 전쟁 시뮬레이터 모드 버튼
    with col2:
        if st.button("⚔️ 전쟁 시뮬레이터", use_container_width=True):
            # 평화 → 전쟁 으로 바꿀 때만 BGM 재생
            if st.session_state["mode"] != MODE_WAR:
                st.session_state["play_war_bgm"] = True
            st.session_state["mode"] = MODE_WAR

    st.markdown("---")

    # 공통 LLM 설정
    st.subheader("LLM 설정")

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

    temperature = st.slider(
        "창의성 (temperature)",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state["temperature"],
        step=0.05,
    )
    st.session_state["temperature"] = temperature

    st.markdown("---")

    # 현재 모드 대화만 지우기
    if st.button("🧼 현재 모드 대화 지우기", use_container_width=True):
        if st.session_state["mode"] == MODE_NORMAL:
            st.session_state["normal_messages"] = []
        else:
            st.session_state["war_messages"] = []
        st.success("현재 모드 대화를 모두 지웠어요!")


# =========================
# 4. 모드별 화면 렌더링
# =========================

def render_normal_mode():
    """꼬르륵이 모드 화면 + 채팅"""
    st.title("먹는게 중요한 꼬르륵이랑 대화해보세요!! 🍙")

    # 꼬르륵이는 기본 Streamlit 스타일 사용 (추가 CSS 없음)

    messages = st.session_state["normal_messages"]

    # 지난 대화 출력
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 입력창
    user_input = st.chat_input("꼬르륵이에게 아무 말이나 털어놔봐...")

    if not user_input:
        return

    # 사용자 메시지 출력 + 저장
    with st.chat_message("user"):
        st.markdown(user_input)
    messages.append({"role": "user", "content": user_input})

    # 모델에게 보낼 메시지 구성
    system_prompt = KORO_PROMPT
    messages_for_model = [{"role": "system", "content": system_prompt}] + messages

    # 모델 호출
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["llm_model"],
            messages=messages_for_model,
            temperature=st.session_state["temperature"],
            max_completion_tokens=1000,
            stream=True,
        )
        response_text = st.write_stream(stream)

    messages.append({"role": "assistant", "content": response_text})
    st.session_state["normal_messages"] = messages


def render_war_mode():
    """전쟁 시뮬레이터 모드 화면 + 채팅"""

    # 배경 / 글자색 변경 (전쟁 분위기)
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at top, #3b0000 0, #050000 55%, #000000 100%);
            color: #f8f3e8;
        }
        .stMarkdown, .stTextInput > div > div > input, .stSlider label, .stChatMessage {
            color: #f8f3e8 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("⚔️ 전쟁 시뮬레이터 - 장수와 책사")

    st.caption("너는 장수, 챗봇은 책사. 네 명령에 따라 전황이 달라진다...")


        # 전쟁 모드로 막 진입했을 때만 BGM 자동 재생
        # 전쟁 모드로 막 진입했을 때만 BGM 자동 재생
    if st.session_state.get("play_war_bgm", False):

        components.html(
            f"""
            <audio id="war_bgm" autoplay>
                <source src="{WAR_BGM_PATH}" type="audio/mpeg">
            </audio>
            <script>
            const audio = document.getElementById("war_bgm");
            if (audio) {{
                audio.volume = 0.1;  // 🔊 여기서 기본 볼륨 조절 (0.0 ~ 1.0)
            }}
            </script>
            """,
            height=0,
        )

        # 한 번 재생 후 플래그 끔
        st.session_state["play_war_bgm"] = False





    messages = st.session_state["war_messages"]

    # 간단한 전황 안내 (턴 수 정도만)
    turn = 1 + sum(1 for m in messages if m["role"] == "user")
    st.markdown(f"**현재 턴:** {turn}턴")

    # 지난 대화 출력 (장수/책사 아바타 사용)
    for msg in messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar=GENERAL_AVATAR):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar=ADVISOR_AVATAR):
                st.markdown(msg["content"])

    # 입력창
    user_input = st.chat_input("장수님, 책사에게 전략을 물어보거나 명령을 내려보세요...")

    if not user_input:
        return

    # 사용자 메시지 출력 + 저장
    with st.chat_message("user", avatar=GENERAL_AVATAR):
        st.markdown(user_input)
    messages.append({"role": "user", "content": user_input})

    # 모델에게 보낼 메시지 구성
    system_prompt = WAR_PROMPT
    messages_for_model = [{"role": "system", "content": system_prompt}] + messages

    # 모델 호출
    with st.chat_message("assistant", avatar=ADVISOR_AVATAR):
        stream = client.chat.completions.create(
            model=st.session_state["llm_model"],
            messages=messages_for_model,
            temperature=st.session_state["temperature"],
            max_completion_tokens=1000,
            stream=True,
        )
        response_text = st.write_stream(stream)

    messages.append({"role": "assistant", "content": response_text})
    st.session_state["war_messages"] = messages


# =========================
# 5. 모드에 따라 분기 실행
# =========================

if st.session_state["mode"] == MODE_WAR:
    render_war_mode()
else:
    render_normal_mode()


# =========================
# 6. (선택) 로컬 실행용 코드
# =========================

if __name__ == "__main__":
    # streamlit run main.py 로 돌릴 땐 무시됨
    import subprocess
    import sys

    if not os.environ.get("STREAMLIT_RUNNING"):
        os.environ["STREAMLIT_RUNNING"] = "1"
        subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
