"""열쇠 미로 탈출 게임 - 최단 경로(BFS)와 내 경로 비교 (Streamlit)"""
import random

import streamlit as st

from maze_logic import (
    DIRECTIONS,
    DOOR,
    EXIT,
    FALLBACK_MAZE,
    KEY,
    START,
    WALL,
    build_maze,
    evaluate,
    move_limit,
    shortest_path,
)

st.set_page_config(page_title="열쇠 미로 탈출", page_icon="🗝️", layout="centered")

DIFFICULTY = {
    "쉬움": {"size": 11, "slack": 1.6, "loops": 3},
    "보통": {"size": 15, "slack": 1.35, "loops": 6},
    "어려움": {"size": 21, "slack": 1.15, "loops": 10},
}

st.session_state.setdefault("difficulty_sel", "보통")
st.session_state.setdefault("seed_sel", 1)


# ------------------------------------------------------------------ 게임 상태 관리
def new_game(randomize=False):
    """선택한 난이도/시드로 새 미로를 만들고 게임 상태를 초기화한다."""
    s = st.session_state
    if randomize:
        s.seed_sel = random.randint(1, 9999)
    cfg = DIFFICULTY.get(s.get("difficulty_sel"), DIFFICULTY["보통"])
    try:
        seed = int(s.get("seed_sel", 1))
    except (TypeError, ValueError):
        seed = 1

    s.notice = ""
    try:
        maze = build_maze(cfg["size"], seed, cfg["loops"])
        best = shortest_path(maze)
        if best is None:
            raise ValueError("풀 수 없는 미로")
    except Exception:  # 어떤 이유로든 생성 실패 시 예비 미로 사용
        maze = FALLBACK_MAZE
        best = shortest_path(maze)
        s.notice = "⚠️ 미로 생성에 문제가 있어 기본 미로로 시작합니다."

    start = next((r, row.index(START)) for r, row in enumerate(maze) if START in row)
    s.maze = maze
    s.best = best
    s.best_moves = len(best) - 1
    s.limit = move_limit(s.best_moves, cfg["slack"])
    s.pos = start
    s.trail = [start]
    s.moves = 0
    s.has_key = False
    s.status = "playing"  # playing / won / lost
    s.msg = "방향 버튼으로 이동하세요. 먼저 🔑 열쇠를 찾아야 합니다!"


def move(direction):
    """방향 버튼 콜백: 이동 가능 여부를 검사하고 상태를 갱신한다."""
    s = st.session_state
    if s.status != "playing":
        return
    delta = DIRECTIONS.get(direction)
    if delta is None:
        s.msg = "⚠️ 알 수 없는 방향입니다."
        return

    nr, nc = s.pos[0] + delta[0], s.pos[1] + delta[1]
    maze = s.maze
    if not (0 <= nr < len(maze) and 0 <= nc < len(maze[0])):
        s.msg = "🚫 미로 밖으로는 나갈 수 없어요. (이동 횟수 차감 없음)"
        return
    cell = maze[nr][nc]
    if cell == WALL:
        s.msg = "🧱 벽이에요! (이동 횟수 차감 없음)"
        return
    if cell == DOOR and not s.has_key:
        s.msg = "🔒 잠긴 문이에요. 열쇠를 먼저 찾아오세요! (이동 횟수 차감 없음)"
        return

    s.pos = (nr, nc)
    s.moves += 1
    s.trail.append(s.pos)
    s.msg = ""

    if cell == KEY and not s.has_key:
        s.has_key = True
        s.msg = "🔑 열쇠를 획득했어요! 이제 잠긴 문을 열 수 있어요."
    elif cell == DOOR:
        s.msg = "🔓 문을 열고 통과했어요!"

    if cell == EXIT:
        s.status = "won"
    elif s.moves >= s.limit:
        s.status = "lost"


# ------------------------------------------------------------------ 미로 그리기
def render_maze(reveal):
    """미로를 HTML 격자로 그린다. reveal=True면 최단 경로(초록)와 내 경로(파랑)를 겹쳐 보여준다."""
    s = st.session_state
    maze, trail, best = s.maze, set(s.trail), set(s.best)
    cols = len(maze[0])
    cell_px = 26 if cols <= 15 else 22
    html = [
        f'<div style="display:grid;grid-template-columns:repeat({cols},{cell_px}px);'
        f'gap:1px;width:max-content;max-width:100%;margin:auto;background:#999;padding:1px;">'
    ]
    for r, row in enumerate(maze):
        for c, ch in enumerate(row):
            bg, icon = "#f7f7f7", ""
            if ch == WALL:
                bg = "#2b2b2b"
            else:
                in_trail, in_best = (r, c) in trail, (r, c) in best
                if reveal and in_trail and in_best:
                    bg = "#d6c6f5"
                elif reveal and in_best:
                    bg = "#b9efc2"
                elif in_trail:
                    bg = "#cfe6ff"
                if ch == KEY and not (s.has_key and (r, c) != s.pos):
                    icon = "🔑"
                elif ch == DOOR:
                    icon = "🔓" if s.has_key else "🔒"
                elif ch == EXIT:
                    icon = "🏁"
                if (r, c) == s.pos:
                    icon = "🏃"
            html.append(
                f'<div style="width:{cell_px}px;height:{cell_px}px;background:{bg};'
                f'font-size:{cell_px - 8}px;line-height:{cell_px}px;text-align:center;">{icon}</div>'
            )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


# ------------------------------------------------------------------ 화면 구성
if "maze" not in st.session_state:
    new_game()
s = st.session_state

st.title("🗝️ 열쇠 미로 탈출")
st.caption("열쇠를 얻고, 잠긴 문을 열고, 제한된 이동 횟수 안에 출구(🏁)로 탈출하세요. 끝나면 최단 경로와 비교해 드려요.")

with st.sidebar:
    st.header("⚙️ 게임 설정")
    st.selectbox("난이도", list(DIFFICULTY.keys()), key="difficulty_sel")
    st.number_input("미로 번호(시드)", min_value=1, max_value=9999, step=1, key="seed_sel")
    st.button("🔄 이 설정으로 새 게임", on_click=new_game, use_container_width=True)
    st.button("🎲 무작위 미로로 새 게임", on_click=new_game, args=(True,), use_container_width=True)
    st.divider()
    st.markdown(
        "**범례**\n\n🏃 나 · 🔑 열쇠 · 🔒/🔓 잠긴 문 · 🏁 출구\n\n"
        "🟦 내가 지나간 길 · 🟩 최단 경로 · 🟪 겹친 길"
    )

if s.get("notice"):
    st.warning(s.notice)

c1, c2, c3 = st.columns(3)
c1.metric("이동 횟수", s.moves)
c2.metric("남은 횟수", max(0, s.limit - s.moves))
c3.metric("열쇠", "보유 🔑" if s.has_key else "없음")
st.progress(min(1.0, s.moves / s.limit))

render_maze(reveal=s.status != "playing")

if s.status == "playing":
    if s.msg:
        st.info(s.msg)
    pad_top = st.columns([1, 1, 1])
    pad_bottom = st.columns([1, 1, 1])
    pad_top[1].button("⬆️", on_click=move, args=("up",), use_container_width=True, key="b_up")
    pad_bottom[0].button("⬅️", on_click=move, args=("left",), use_container_width=True, key="b_left")
    pad_bottom[1].button("⬇️", on_click=move, args=("down",), use_container_width=True, key="b_down")
    pad_bottom[2].button("➡️", on_click=move, args=("right",), use_container_width=True, key="b_right")
else:
    if s.status == "won":
        st.success("🎉 탈출 성공!")
        st.balloons()
    else:
        st.error("⏰ 이동 횟수를 모두 사용했어요. 아래 초록색 최단 경로를 확인해 보세요!")

    result = evaluate(s.moves, s.best_moves)
    st.subheader("📊 경로 비교 결과")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("내 이동 횟수", s.moves)
    r2.metric("최단 이동 횟수", s.best_moves)
    r3.metric("차이", f"+{result['diff']}")
    r4.metric("경로 효율", f"{result['efficiency']}%" if s.status == "won" else "-")

    if s.status == "won":
        if result["diff"] == 0:
            st.write("🏆 **완벽해요!** 최단 경로와 같은 횟수로 탈출했어요.")
        elif result["efficiency"] >= 70:
            st.write("👍 **훌륭해요!** 거의 최단 경로에 가까웠어요. 조금만 더 줄여 볼까요?")
        else:
            st.write("🤔 **돌아간 길이 꽤 있어요.** 초록색 최단 경로와 비교하며 어디서 헤맸는지 살펴보세요.")
    st.caption("경로 효율 = 최단 이동 횟수 ÷ 내 이동 횟수 × 100")
    st.button("🔄 같은 미로 다시 도전", on_click=new_game)
