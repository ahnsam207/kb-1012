import base64
import random
import time
from pathlib import Path

import streamlit as st


BOARD_SIZE = 3
HOLE_COUNT = BOARD_SIZE * BOARD_SIZE
MOLE_LIFETIME_SECONDS = 1.5
MOLE_LIFETIME_DECREMENT_SECONDS = 0.1
MIN_MOLE_LIFETIME_SECONDS = 0.5
GAME_DURATION_SECONDS = 60
HOLE_IMAGE = base64.b64encode(
    Path(__file__).with_name("hole.png").read_bytes()
).decode("ascii")
MOLE_IMAGE = base64.b64encode(
    Path(__file__).with_name("img.png").read_bytes()
).decode("ascii")

st.set_page_config(page_title="두더지 잡기 게임", page_icon="🐹", layout="wide")
st.title("두더지 잡기 게임")


def show_next_mole(previous_position: int | None = None) -> None:
    choices = [
        position
        for position in range(HOLE_COUNT)
        if position != previous_position
    ]
    st.session_state.mole_position = random.choice(choices)
    st.session_state.mole_id += 1
    st.session_state.mole_started_at = time.monotonic()


def reset_game_state() -> None:
    st.session_state.game_status = "ready"
    st.session_state.score = 0
    st.session_state.lives = 3
    st.session_state.mole_lifetime_seconds = MOLE_LIFETIME_SECONDS
    st.session_state.game_started_at = None
    st.session_state.game_ended_at = None
    st.session_state.mole_position = None
    st.session_state.mole_started_at = None
    st.session_state.mole_id = 0
    st.session_state.resolved_mole_ids = set()
    st.session_state.message = ""


def start_game() -> None:
    if st.session_state.game_status != "ready":
        return
    st.session_state.game_status = "playing"
    st.session_state.game_started_at = time.monotonic()
    show_next_mole()


def finish_game() -> None:
    if st.session_state.game_status == "playing":
        st.session_state.game_status = "over"
        st.session_state.game_ended_at = time.monotonic()
        st.session_state.mole_position = None
        st.session_state.message = "게임 오버!"


def resolve_mole(mole_id: int, caught: bool) -> None:
    if (
        st.session_state.game_status != "playing"
        or mole_id != st.session_state.mole_id
        or mole_id in st.session_state.resolved_mole_ids
    ):
        return

    st.session_state.resolved_mole_ids.add(mole_id)
    old_position = st.session_state.mole_position
    if caught:
        st.session_state.score += 10
        st.session_state.mole_lifetime_seconds = max(
            MIN_MOLE_LIFETIME_SECONDS,
            round(
                st.session_state.mole_lifetime_seconds
                - MOLE_LIFETIME_DECREMENT_SECONDS,
                1,
            ),
        )
        st.session_state.message = "두더지를 잡았습니다! +10점"
    else:
        st.session_state.lives = max(0, st.session_state.lives - 1)
        st.session_state.message = "두더지를 놓쳤어요!"

    if st.session_state.lives > 0:
        show_next_mole(old_position)
    else:
        finish_game()


def handle_hole_click(hole_index: int, mole_id: int) -> None:
    if st.session_state.game_status != "playing":
        return

    if time.monotonic() - st.session_state.game_started_at >= GAME_DURATION_SECONDS:
        finish_game()
        return

    if (
        mole_id != st.session_state.mole_id
        or mole_id in st.session_state.resolved_mole_ids
    ):
        return

    elapsed = time.monotonic() - st.session_state.mole_started_at
    if elapsed >= st.session_state.mole_lifetime_seconds:
        resolve_mole(mole_id, caught=False)
    elif hole_index == st.session_state.mole_position:
        resolve_mole(mole_id, caught=True)


def initialize_game_state() -> None:
    if "game_status" not in st.session_state:
        reset_game_state()


initialize_game_state()

button_selectors = [
    f".st-key-hole_{hole_index} [data-testid='stButton'] button"
    for hole_index in range(HOLE_COUNT)
]
st.markdown(
    f"""
    <style>
    {", ".join(button_selectors)} {{
        min-height: 160px;
        background-color: transparent;
        background-position: center;
        background-repeat: no-repeat;
        background-size: contain;
    }}
    {", ".join(f"{selector}[kind='secondary']" for selector in button_selectors)} {{
        background-image: url("data:image/png;base64,{HOLE_IMAGE}");
    }}
    {", ".join(f"{selector}[kind='primary']" for selector in button_selectors)} {{
        background-image: url("data:image/png;base64,{MOLE_IMAGE}");
    }}
    {", ".join(f"{selector} p" for selector in button_selectors)} {{
        opacity: 0;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def update_game_state() -> None:
    if st.session_state.game_status != "playing":
        return

    now = time.monotonic()
    if now - st.session_state.game_started_at >= GAME_DURATION_SECONDS:
        finish_game()
        return

    if (
        st.session_state.mole_id not in st.session_state.resolved_mole_ids
        and now - st.session_state.mole_started_at
        >= st.session_state.mole_lifetime_seconds
    ):
        resolve_mole(st.session_state.mole_id, caught=False)


def render_game() -> None:
    update_game_state()
    instructions, board = st.columns([1, 2], gap="large")

    with instructions:
        st.subheader("게임 안내")
        st.write("게임판에 나타나는 두더지를 빠르게 클릭하세요.")
        st.write(
            f"두더지는 {st.session_state.mole_lifetime_seconds:g}초 동안 나타나며, "
            f"제한 시간 {GAME_DURATION_SECONDS}초 안에 최대한 많이 잡아 보세요."
        )
        st.write("두더지를 잡을 때마다 표시 시간이 0.1초씩 줄어들며, 최소 0.5초입니다.")
        st.write("두더지를 놓치면 라이프가 줄어들고, 라이프가 모두 없어지면 게임이 끝납니다.")

        st.metric("현재 점수", st.session_state.score)
        st.write(f"라이프: {st.session_state.lives}")

        if st.session_state.game_started_at is None:
            remaining_game_seconds = GAME_DURATION_SECONDS
        else:
            game_time = (
                st.session_state.game_ended_at
                if st.session_state.game_ended_at is not None
                else time.monotonic()
            )
            elapsed_game = game_time - st.session_state.game_started_at
            remaining_game_seconds = max(0, GAME_DURATION_SECONDS - int(elapsed_game))
        st.write(f"남은 시간: {remaining_game_seconds}초")

        with st.container(height=104, border=False):
            if st.session_state.game_status == "over":
                st.error("게임 오버!")
                st.write(f"최종 점수: {st.session_state.score}점")
            elif st.session_state.message:
                st.info(st.session_state.message)

        if st.session_state.game_status == "ready":
            st.button("게임 시작", key="start_game", on_click=start_game)
        elif st.session_state.game_status == "over":
            st.button("다시 시작", key="restart_game", on_click=reset_game_state)

    with board:
        st.subheader("게임판")
        for row in range(BOARD_SIZE):
            columns = st.columns(BOARD_SIZE)
            for column_index, column in enumerate(columns):
                hole_index = row * BOARD_SIZE + column_index
                is_mole = (
                    st.session_state.game_status == "playing"
                    and hole_index == st.session_state.mole_position
                )
                label = "두더지" if is_mole else "빈 구멍"
                column.button(
                    label,
                    key=f"hole_{hole_index}",
                    type="primary" if is_mole else "secondary",
                    on_click=handle_hole_click,
                    args=(hole_index, st.session_state.mole_id),
                    disabled=st.session_state.game_status != "playing",
                    use_container_width=True,
                )


@st.fragment(run_every=0.1)
def game_fragment() -> None:
    render_game()


game_fragment()
