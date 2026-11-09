"""미로 생성 · 검증 · 최단 경로 탐색 로직 (화면(Streamlit)과 분리한 순수 파이썬 모듈)"""
from __future__ import annotations

import math
import random
from collections import deque

WALL, PATH, KEY, DOOR, EXIT, START = "#", ".", "K", "D", "E", "S"
VALID_CHARS = {WALL, PATH, KEY, DOOR, EXIT, START}
DIRECTIONS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}

# 미로 생성에 실패했을 때 사용하는 예비 미로 (열쇠 없이는 출구에 갈 수 없음)
FALLBACK_MAZE = (
    "#########",
    "#S.#...E#",
    "#.##...##",
    "#...#...#",
    "###.#.#.#",
    "#K..D.#.#",
    "#########",
)


# ---------------------------------------------------------------- 기본 도구
def _neighbors(maze, r, c):
    """(r, c)의 상하좌우 중 미로 안에 있고 벽이 아닌 칸을 차례로 돌려준다."""
    for dr, dc in DIRECTIONS.values():
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(maze) and 0 <= nc < len(maze[0]) and maze[nr][nc] != WALL:
            yield nr, nc


def find_cell(maze, symbol):
    """미로에서 특정 문자의 첫 위치를 찾는다. 없으면 ValueError."""
    for r, row in enumerate(maze):
        c = row.find(symbol)
        if c != -1:
            return r, c
    raise ValueError(f"미로에 '{symbol}' 칸이 없습니다.")


def validate_maze(maze):
    """미로 형식과 풀이 가능 여부를 검사하고, 풀 수 있으면 최단 경로를 돌려준다."""
    if not maze or not all(isinstance(row, str) for row in maze):
        raise ValueError("미로 데이터가 비어 있거나 형식이 올바르지 않습니다.")
    if len({len(row) for row in maze}) != 1:
        raise ValueError("미로의 모든 행은 길이가 같아야 합니다.")
    flat = "".join(maze)
    if not set(flat) <= VALID_CHARS:
        raise ValueError("미로에 허용되지 않은 문자가 있습니다.")
    if flat.count(START) != 1 or flat.count(EXIT) != 1:
        raise ValueError("시작(S)과 출구(E)는 각각 하나씩 있어야 합니다.")
    path = shortest_path(maze)
    if path is None:
        raise ValueError("출구에 도달할 수 없는 미로입니다.")
    return path


# ---------------------------------------------------------------- 최단 경로 (BFS)
def shortest_path(maze):
    """열쇠 보유 여부까지 상태에 포함한 BFS.

    상태 = (행, 열, 열쇠를 가졌는가). 열쇠가 없으면 잠긴 문(D)을 통과할 수 없다.
    반환: [(r, c), ...] (시작~출구), 도달 불가능하면 None.
    """
    start = find_cell(maze, START)
    goal = find_cell(maze, EXIT)
    begin = (start[0], start[1], False)
    parent = {begin: None}
    queue = deque([begin])

    while queue:
        state = queue.popleft()
        r, c, has_key = state
        if (r, c) == goal:
            route = []
            while state is not None:
                route.append((state[0], state[1]))
                state = parent[state]
            return route[::-1]
        for nr, nc in _neighbors(maze, r, c):
            cell = maze[nr][nc]
            if cell == DOOR and not has_key:
                continue
            nxt = (nr, nc, has_key or cell == KEY)
            if nxt not in parent:
                parent[nxt] = state
                queue.append(nxt)
    return None


# ---------------------------------------------------------------- 미로 생성
def _distances(grid, start, blocked=None):
    """start에서 갈 수 있는 모든 칸까지의 거리 (blocked 칸은 벽처럼 취급)."""
    dist = {start: 0}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for n in _neighbors(grid, r, c):
            if n != blocked and n not in dist:
                dist[n] = dist[(r, c)] + 1
                queue.append(n)
    return dist


def _carve(size, rng, loops):
    """DFS로 완전 미로를 만들고, 벽 몇 개를 허물어 갈림길(순환)을 추가한다."""
    grid = [[WALL] * size for _ in range(size)]
    grid[1][1] = PATH
    stack = [(1, 1)]
    while stack:
        r, c = stack[-1]
        options = [
            (r + dr * 2, c + dc * 2, dr, dc)
            for dr, dc in DIRECTIONS.values()
            if 0 < r + dr * 2 < size - 1
            and 0 < c + dc * 2 < size - 1
            and grid[r + dr * 2][c + dc * 2] == WALL
        ]
        if options:
            nr, nc, dr, dc = rng.choice(options)
            grid[r + dr][c + dc] = PATH
            grid[nr][nc] = PATH
            stack.append((nr, nc))
        else:
            stack.pop()

    removable = [
        (r, c)
        for r in range(1, size - 1)
        for c in range(1, size - 1)
        if grid[r][c] == WALL and (r % 2 == 1) != (c % 2 == 1)
    ]
    rng.shuffle(removable)
    for r, c in removable[:loops]:
        grid[r][c] = PATH
    return grid


def _place_items(grid):
    """최단 경로 중간쯤에 잠긴 문을, 문 이전 구역의 가장 먼 곳에 열쇠를 놓는다."""
    size = len(grid)
    start, goal = (1, 1), (size - 2, size - 2)
    dist = _distances(grid, start)
    if goal not in dist:
        return None

    route = [goal]
    while route[-1] != start:
        r, c = route[-1]
        route.append(next(n for n in _neighbors(grid, r, c) if dist.get(n, -1) == dist[(r, c)] - 1))
    route.reverse()
    if len(route) < 5:
        return None

    middle = len(route) / 2
    for idx in sorted(range(2, len(route) - 1), key=lambda i: abs(i - middle)):
        door = route[idx]
        reachable = _distances(grid, start, blocked=door)
        if goal in reachable:  # 이 칸을 막아도 우회로가 있으면 문 자리로 부적합
            continue
        key = max(reachable, key=reachable.get)
        if key == start:
            continue
        placed = [row[:] for row in grid]
        placed[start[0]][start[1]] = START
        placed[goal[0]][goal[1]] = EXIT
        placed[door[0]][door[1]] = DOOR
        placed[key[0]][key[1]] = KEY
        return placed
    return None


def build_maze(size=15, seed=1, loops=6):
    """시드가 같으면 같은 미로가 나온다. 실패하면 예비 미로를 돌려준다."""
    size = max(7, int(size))
    if size % 2 == 0:
        size += 1
    for attempt in range(200):
        rng = random.Random(int(seed) * 1000 + attempt)
        placed = _place_items(_carve(size, rng, max(0, int(loops))))
        if placed:
            maze = tuple("".join(row) for row in placed)
            try:
                validate_maze(maze)
                return maze
            except ValueError:
                continue
    return FALLBACK_MAZE


# ---------------------------------------------------------------- 점수 계산
def move_limit(shortest_moves, slack):
    """최단 이동 횟수에 여유 비율을 곱해 이동 제한 횟수를 정한다."""
    return max(shortest_moves + 1, math.ceil(shortest_moves * slack))


def evaluate(moves, shortest_moves):
    """실제 이동 횟수와 최단 이동 횟수를 비교한다."""
    if moves <= 0:
        return {"diff": 0, "efficiency": 0.0}
    return {
        "diff": moves - shortest_moves,
        "efficiency": round(min(100.0, shortest_moves / moves * 100), 1),
    }
