import random
import time

import streamlit as st


GAME_DURATION = 30
BOARD_SIZE = 3
CELL_COUNT = BOARD_SIZE * BOARD_SIZE

st.set_page_config(page_title="두더지 잡기", page_icon="🐹", layout="centered")

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #f4f8ed 0%, #ffffff 48%);
    }
    .block-container {
        max-width: 700px;
        padding-top: 2.5rem;
    }
    .st-key-game_board [data-testid="stButton"] button {
        min-height: 76px;
        border: 1px solid #d6dfca;
        border-radius: 8px;
        background: #edf3e5;
        font-size: 1.8rem;
        transition: transform 120ms ease, background 120ms ease;
    }
    .st-key-game_board [data-testid="stButton"] button:hover {
        background: #dce9ce;
        transform: translateY(-2px);
    }
    .st-key-game_board [data-testid="stButton"] button[kind="primary"] {
        font-size: 5.4rem;
    }
    .st-key-game_board [data-testid="stButton"] button:disabled {
        color: #75836a;
        opacity: 0.72;
    }
    @media (max-width: 520px) {
        .st-key-game_board [data-testid="stButton"] button {
            min-height: 58px;
            font-size: 1.45rem;
        }
        .st-key-game_board [data-testid="stButton"] button[kind="primary"] {
            font-size: 4.35rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("두더지 잡기")
st.caption("30초 동안 나타나는 두더지를 빠르게 눌러 보세요.")

for key, value in {
    "game_active": False,
    "score": 0,
    "mole_index": None,
    "deadline": 0.0,
    "game_message": "시작 버튼을 누르면 게임이 시작됩니다.",
}.items():
    if key not in st.session_state:
        st.session_state[key] = value


def handle_hole_click(index):
    if not st.session_state.game_active:
        return

    if index == st.session_state.mole_index:
        st.session_state.score += 10
        possible_positions = [position for position in range(CELL_COUNT) if position != index]
        st.session_state.mole_index = random.choice(possible_positions)
        st.session_state.game_message = "잡았다! 계속 잡아 보세요."
    else:
        st.session_state.game_message = "아깝다! 두더지를 찾아보세요."


@st.fragment(run_every="1s")
def render_game():
    remaining = max(0, int(st.session_state.deadline - time.monotonic() + 0.999))
    if st.session_state.game_active and remaining == 0:
        st.session_state.game_active = False
        st.session_state.mole_index = None
        st.session_state.game_message = f"시간 종료! 최종 점수는 {st.session_state.score}점입니다."

    score_col, time_col = st.columns(2)
    score_col.metric("점수", st.session_state.score)
    time_col.metric("남은 시간", f"{remaining if st.session_state.game_active else 0}초")

    if st.session_state.game_active:
        st.progress(remaining / GAME_DURATION)

    st.markdown(f"**{st.session_state.game_message}**")

    if not st.session_state.game_active:
        button_label = "다시 시작" if st.session_state.score else "게임 시작"
        if st.button(button_label, type="primary", use_container_width=True):
            st.session_state.score = 0
            st.session_state.game_active = True
            st.session_state.deadline = time.monotonic() + GAME_DURATION
            st.session_state.mole_index = random.randrange(CELL_COUNT)
            st.session_state.game_message = "두더지를 잡아 보세요!"

    with st.container(key="game_board"):
        for row in range(BOARD_SIZE):
            columns = st.columns(BOARD_SIZE, gap="small")
            for column in range(BOARD_SIZE):
                index = row * BOARD_SIZE + column
                is_mole = st.session_state.game_active and index == st.session_state.mole_index
                label = "🐹" if is_mole else "🕳️"
                columns[column].button(
                    label,
                    key=f"hole_{index}",
                    type="primary" if is_mole else "secondary",
                    use_container_width=True,
                    disabled=not st.session_state.game_active,
                    on_click=handle_hole_click,
                    args=(index,),
                )


render_game()