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
WAR_PROMPT = """
당신은 뛰어난 책사이며, 사용자는 '장군님'입니다.  
당신의 목표는 '현실적인 군사 지휘 로그 + 게임 UI 느낌'을 동시에 제공하는 것입니다.

장군님의 명령이 내려지면 다음 형식을 반드시 따라 출력하십시오:

━━━━━━━━━━━━━━━━━━━━━━━━━━
🎮 1) 명령 수행 선언 (1줄)
"네, 장군님. 명령을 수행하겠습니다."

⚔️ 2) 전투 로그 (3~6줄)
- 실시간 게임 로그처럼 시간 스탬프 작성  
  예:  
  [00:01] 전방 보병 돌격 개시  
  [00:03] 적 궁병 후퇴 시작  
  [00:05] 우리 기병 좌측에서 측면 진입 성공  
- 로그는 간결하게, 행동 위주로 작성  
- 과장 금지, 실제 전투처럼 차분한 톤 유지

📊 3) 전투 수치 보고 (1~2줄)
- 실제 게임 UI 느낌으로 정리  
  예:
  아군 피해: 12명 | 적군 피해: 28명  
  아군 사기: 73 → 78 상승  
  적군 사기: 65 → 54 하락  

📈 4) 전황 게이지 (1줄)
- 전황을 시각적으로 표시  
  예:
  전황: ██████░░░░ 60% (우세)  
  전황: ███░░░░░░░ 28% (불리)  

🧭 5) 전황 요약 (1~2줄)
예: "현재 전황은 우리 측이 조금 우세합니다."

📝 6) 다음 행동 선택지 (정확히 2개만)
예:
- 우측 기병 돌파를 계속 밀어붙인다  
- 전방 보병을 후퇴시키고 방어선 재정비  
━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ 절대 지켜야 할 규칙:
- 전체 출력은 10~13줄 이내.
- 설명충 금지. 배경 이야기 금지.
- 현대 한국어 존댓말 사용, 군사 보고 톤 유지.
- 명령을 받지 않으면 분석 대신 "명령을 내려주십시오, 장군님."이라고 안내.
- 반드시 한국어로 답변.

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

    if st.session_state.get("play_war_bgm", False):

     components.html(
        f"""
        <audio id="war_bgm" autoplay>
            <source src="{WAR_BGM_PATH}" type="audio/mpeg">
        </audio>

        <script>
        const audio = document.getElementById("war_bgm");
        if (audio) {{
            audio.volume = 0.05;  // 🔊 볼륨 조절 (0.0 ~ 1.0)

            // 🔥 90초(1분30초) 후 BGM 자동 정지
            setTimeout(() => {{
                audio.pause();
                audio.currentTime = 0;  // (선택) 0초로 되돌림
            }}, 90000);  // 90000ms = 90초
        }}
        </script>
        """,
        height=0,
    )

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
