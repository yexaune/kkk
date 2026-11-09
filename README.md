# 🗝️ 열쇠 미로 탈출 게임

벽·통로·열쇠·잠긴 문·출구로 이루어진 미로에서 **제한된 이동 횟수** 안에 탈출하는 Streamlit 게임입니다.
게임이 끝나면 **BFS로 미리 계산한 최단 경로**와 내가 이동한 경로를 비교해 경로 효율을 보여 줍니다.

## 주요 기능
- 난이도(쉬움/보통/어려움)와 시드에 따른 미로 자동 생성 (항상 풀 수 있고, 문은 반드시 열쇠가 필요)
- 방향 버튼 이동, 열쇠 획득 → 잠긴 문 통과, 이동 횟수 제한
- 열쇠 보유 여부까지 고려한 BFS 최단 경로 계산
- 결과 화면: 이동 횟수 / 최단 횟수 / 차이 / 경로 효율 + 최단 경로 오버레이

## 파일 구성
| 파일 | 설명 |
|---|---|
| `app.py` | Streamlit 화면과 게임 진행(입력·출력) |
| `maze_logic.py` | 미로 생성, 검증, BFS 최단 경로, 점수 계산 |
| `requirements.txt` | 필요한 라이브러리 |

## 로컬 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```

## GitHub 업로드
```bash
git init
git add .
git commit -m "열쇠 미로 탈출 게임 초기 버전"
git branch -M main
git remote add origin https://github.com/<내-아이디>/maze-escape.git
git push -u origin main
```

## Streamlit Community Cloud 배포
1. https://share.streamlit.io 에 GitHub 계정으로 로그인
2. **New app** → 위 저장소 선택 → Branch `main`, Main file path `app.py`
3. **Deploy** 클릭 → 발급된 URL을 보고서에 첨부
