# 중3부터 시작하는 미래마을을 구해라!
## 생애설계 어드벤처 · 수업용 원본 픽셀 RPG

천재교육 기술·가정② p.102–103 사용자 제공 스크린샷을 바탕으로 만든 15~20분 게임입니다. 게임의 픽셀 도형과 음향은 코드에서 직접 만듭니다. 포켓몬 등 기존 게임의 이미지·음악·캐릭터는 포함하지 않습니다.

## 1. 전체 코드와 실행
이 ZIP의 파일이 전체 소스입니다. 별도 빌드·Node·외부 게임 자산·유료 API가 필요하지 않습니다. Python 3.11을 권장합니다.

```bash
python -m venv .venv
# Windows에서는 .venv\Scripts\activate 를 실행합니다.
# macOS/Linux에서는 source .venv/bin/activate 를 실행합니다.
pip install -r requirements.txt
streamlit run app.py
```
브라우저에서 터미널에 표시된 주소(기본 http://localhost:8501)를 엽니다. Google 키가 없어도 로컬 백업 모드로 플레이할 수 있습니다. 교사 화면은 teacher_password를 설정해야 열립니다.

| 파일 | 역할 |
|---|---|
| app.py | 시작·복원·인증·교사 대시보드·세션 상태를 처리합니다. |
| engine.py | 이동 검증, 퀴즈, 분기, 점수, 엔딩을 계산합니다. |
| content.py | 6챕터·22선택·12NPC·10도감·6퀴즈를 담습니다. |
| storage.py | logs/results 저장·CSV 백업·재전송을 처리합니다. |
| component/frontend/index.html | 게임 화면의 구조를 정의합니다. |
| component/frontend/style.css | 태블릿 대응 픽셀풍 UI를 정의합니다. |
| component/frontend/game.js | 타일 이동·NPC·상점 소등·폐교·포탈·원본 그래픽을 구현합니다. |
| tests/ | 분기·점수·저장 회귀 테스트를 제공합니다. |
| docs/ | 분기표·수치표·대사집·50분 수업안·점검표를 제공합니다. |

### 조작과 진행
- 게임 화면을 한 번 누른 후 방향키/WASD로 이동합니다. 태블릿은 화면의 방향버튼을 누릅니다.
- NPC 상하좌우 한 칸 옆에서 **말걸기** 또는 Enter를 누릅니다. 노란 `!`가 이번 챕터 안내자입니다.
- 대화창을 닫은 뒤 이동할 수 있습니다. Esc로 대화창을 닫습니다.
- 순서는 담임교사 → 취업상담사 → 시청직원 → 어린이집원장 → 워킹맘선배 → 80대 할머니 → 미래시장입니다.
- 신혼마을과 직장거리의 아래쪽 포탈은 지름길입니다. 건물 내부 화면 대신 건물 앞 NPC가 시설의 기능을 제공합니다.
- 잠긴 선택지는 도감만 읽어서 열리지 않습니다. 척척박사·시청직원·인사담당자의 **상담 버튼**을 눌러야 합니다.
- 32세 이후 정책카드를 사용할 수 있습니다. 38세 선택 전에 사용하면 양육비 사건도 완화됩니다.
- 할머니/의사 옆에서 네 영역 점검을 저장해야 58세 A가 열립니다.
- 65세에는 미래시장에게 엔딩홀 입장을 요청합니다. 모든 챕터를 마쳐도 자동 엔딩은 아닙니다.
- 소리는 기본 꺼짐입니다. 소리를 켜면 짧은 원본 효과음만 재생됩니다.
- 화면 확대는 브라우저 권한에 따라 제한될 수 있습니다. 이동·대화·저장은 확대 없이 동작합니다.

## 2. 분기표·수치·대사집
[전체 분기표와 밸런싱표](docs/02_분기표_밸런싱.md), [NPC 대사집](docs/03_NPC대사집.md), [교과서 지식과 정답](docs/04_지식과퀴즈.md)을 참조하세요. 실제 게임과 동일한 content.py에서 표를 생성했습니다.

### 현실과 수업 모형의 구분
- 시작값은 마을출산율 1.30, 고령화율 14%, 활력·행복·돌봄부담 각각 50입니다.
- TFR 기여도는 `(내 자녀수 - 1.30) + 보너스합`, 최종 가상 TFR은 `1.30 + 기여도`입니다. 반올림은 소수 둘째 자리입니다. 자녀 선택 전에는 마을 1.30, 기여도 0.00을 유지합니다.
- 전국 비교 그래프의 1.30은 **요청된 수업용 가정값**입니다. 현재 대한민국 전국평균이라고 주장하지 않습니다.
- 개인 자녀 수로 국가 합계출산율을 계산할 수 없습니다. 실제 출산율은 음수가 될 수 없지만 요청된 고정식에서는 최저 -0.25가 나올 수 있습니다. 값은 숨기거나 보정하지 않고 모형의 한계를 안내합니다.
- `3명+`는 계산상 3명입니다. 실제 정책 대상·지원 자격·입양 가능 여부는 게임과 다를 수 있습니다.
- 무자녀인 경우 38세 선택은 이웃·가족 돌봄 참여로 읽습니다. 개인 육아휴직·어린이집 TFR 보너스는 제외하며 공동 돌봄·유연근무는 반영합니다.
- 비혼·동거를 행복 감점 대상으로 삼지 않습니다. 결혼·출산 선택보다 정보 접근·주거·돌봄 지원의 차이를 설명합니다.
- 요청된 엔딩 분류 자체가 자녀 수의 영향을 크게 받습니다. **인구와 돌봄 위험 시나리오**일 뿐 바람직한 가족·삶의 순위로 사용하지 마세요. 성적은 선택한 자녀 수나 엔딩으로 매기지 않습니다.
- 엔딩 중복 시 **D → C → A → B** 순서로 적용합니다. D는 행복≤30 또는 돌봄≥80, C는 가상TFR≤0.99 또는 고령화율≥20%, A는 가상TFR≥1.60, 나머지는 B입니다.
- 제도 보너스는 휴직·어린이집·유연근무 각 0.05, 최대 0.15입니다. 현재 선택 구조에서 한 경로가 세 제도를 모두 얻을 필요는 없지만 계산기는 모두 지원합니다.
- 고령화율 변화는 정책의 실제 효과가 아닌 시나리오 연출 수치입니다. 주거비·소득도 수업용 가정값입니다.
- p.103의 “확 늙어버린 대한민국”은 2016.9.7 기사입니다. 18년은 당시 2018년 진입을 예상한 자료로 다룹니다. 노령화지수 95.1% 역시 **2015년** 수치입니다.
- `저출산=2명 이하 지속`은 사용자가 지정한 수업 문구를 그대로 표시합니다. 합계출산율의 통계적 정의는 도감의 보충 설명으로 구별합니다.

## 3. Secrets와 Google Sheets 설정
### 시트와 서비스계정을 준비합니다.
1. Google Cloud 프로젝트에서 **Google Sheets API**를 켭니다. 이 앱은 시트 ID로 직접 열므로 Drive API 권한을 요구하지 않습니다.
2. 서비스계정을 만들고 JSON 키를 발급받습니다. 키 파일은 GitHub에 올리지 않습니다.
3. 새 Google 스프레드시트를 만들고 URL에서 `/d/`와 `/edit` 사이의 ID를 복사합니다.
4. 시트 오른쪽 위 **공유**에서 JSON의 `client_email` 주소를 **편집자**로 초대합니다. 링크 공개는 필요하지 않습니다.
5. `.streamlit/secrets.toml.example`을 참고해 로컬 `.streamlit/secrets.toml` 또는 Cloud Secrets에 실제 값을 넣습니다. `private_key`는 삼중 따옴표 안에 실제 여러 줄로 넣고 `BEGIN`/`END` 줄을 유지합니다.
6. 학생용 PIN과 별개로 `teacher_password`를 충분히 길고 무작위로 정합니다. 이 값을 학생에게 배포하지 않습니다.

### GitHub push → Streamlit Community Cloud 배포 5단계
**1단계. 저장소를 준비합니다.** ZIP을 풀어 이 README와 app.py가 있는 폴더를 GitHub 저장소로 만듭니다. GitHub Desktop을 써도 됩니다.
```bash
git init
git add .
git commit -m "미래마을 수업 RPG를 추가합니다."
git branch -M main
git remote add origin https://github.com/계정명/저장소명.git
git push -u origin main
```
`git status`와 GitHub 파일 목록에서 secrets.toml과 fallback_logs.csv가 없는지 확인합니다. 키를 이미 커밋했다면 .gitignore 추가만으로 해결되지 않으므로 키를 폐기하고 재발급하세요.

**2단계. Cloud 앱을 만듭니다.** https://share.streamlit.io/ 에 GitHub로 로그인하고 Create app/New app을 누릅니다. 저장소와 main 브랜치를 선택합니다.

**3단계. 실행 파일을 지정합니다.** Main file path에 `app.py`, 가능하면 Python 3.11을 선택합니다. 파일을 하위 폴더에 넣었다면 해당 경로를 지정합니다.

**4단계. Secrets를 입력합니다.** Advanced settings 또는 앱 Settings → Secrets에 예시 전체 구조와 실제 인증 값을 붙여 넣고 저장합니다. TOML에서 `[gcp_service_account]` 위에 `sheet_id`, `teacher_password`를 둡니다. 필수 패키지는 requirements.txt로 설치됩니다.

**5단계. 배포하고 실제 연결을 점검합니다.** Deploy를 누릅니다. 테스트 학번으로 새로시작 → 첫 선택 → 저장 → 시작화면 → 이어하기를 확인합니다. 엔딩 후 logs와 results 시트, 교사 막대그래프를 확인하고 수업 링크를 공유합니다. Cloud 메뉴 이름은 서비스 업데이트로 조금 달라질 수 있습니다.

### 저장 방식과 헤더
첫 연결에서 빈 `logs`, `results` 워크시트를 자동 생성합니다. 기존 워크시트가 있으면 헤더가 정확히 같아야 합니다.
```text
logs: event_id,saved_at,class_code,student_id,nickname,run_id,event,state_json
results: event_id,saved_at,class_code,student_id,nickname,run_id,ending,contribution,final_tfr,happiness,care,minutes,quiz_correct
```
- `state_json`에는 전체 상태·플래그·선택 기록·비밀번호 해시가 있습니다. 서비스계정 키는 없습니다.
- 반+학번이 일치하는 최신 logs를 복원합니다. 숫자 자동 변환을 막아 `001` 같은 학번을 보존합니다. 저장은 RAW 모드이므로 시트 수식 주입을 막습니다.
- 새로시작은 확인란과 기존 PIN 확인을 거쳐 새 run_id를 생성합니다. 감사용 이전 행을 삭제하지 않고 최신 기록을 논리적으로 덮어씁니다.
- 선택·퀴즈·대화·포탈은 즉시 저장하며 이동은 25초 주기 또는 다음 이벤트에서 저장합니다. 세션 필수 키는 student_id, class_code, nickname, x, y, chapter, flags, stats, start_time입니다.
- 서버 재실행에서도 시트로 복원할 수 있습니다. 로그인 실패 때는 짧은 재시도 대기시간을 둡니다.
- 쓰기 실패 시 `fallback_logs.csv`에 백업하고 게임을 계속합니다. 로컬 쓰기마저 실패하면 빨간/경고 안내와 개인 JSON 다운로드를 이용합니다.
- 교사가 **CSV 백업을 시트로 재전송**하면 event_id를 기준으로 중복 전송을 막고, logs만 성공했던 엔딩도 results에 복구합니다. CSV는 감사용으로 남습니다.
- 교사 평균은 results와 미전송 엔딩을 합치고 반+학번별 최신 완료 한 건만 사용합니다. 미완료 학생을 0점으로 평균내지 않습니다.
- Cloud 로컬 디스크는 **영구 저장소가 아닙니다**. 종료 전 개인 JSON도 내려받으세요. 서버 CSV가 사라지면 개인 저장파일로 복구해야 합니다.
- 여러 반이 같은 시트를 동시에 쓰면 Google 쓰기 할당량에 도달할 수 있습니다. 반별 앱·시트를 나누거나 자동저장 간격을 조정하세요. 할당량 오류는 CSV로 전환됩니다. 대규모 운영용 데이터베이스는 아닙니다.
- 짧은 PIN은 강력한 인증이 아닙니다. 가능하면 학생이 8자 이상을 사용하고 실명·민감정보를 저장하지 않도록 지도하세요. JSON 복원은 편의를 위한 기능으로 성적 조작 방지 기능이 아닙니다.
- 동일 학생이 두 기기에서 동시에 진행하면 최신 저장이 우선합니다. 수업에서는 한 학생 한 기기 사용을 권장합니다.
- 시트와 서버 CSV 보유기간은 학교 규정에 맞춰 정하고 수업 종료 후 삭제합니다. PIN 분실은 교사가 해당 학생 기록을 별도 보관 후 제거하거나 새 학번으로 시작하게 합니다.

## 4. 50분 수업안
[수업안과 평가·발문](docs/05_50분수업안.md)을 그대로 인쇄해 사용할 수 있습니다.

## 검사와 남은 확인
```bash
python -m unittest discover -s tests -v
python -m compileall -q .
# Node가 있는 개발 환경에서만 선택적으로 실행합니다.
node --check component/frontend/game.js
```
제작 환경에서 실제 실행한 검사 목록은 [검증 보고서](docs/06_검증보고서.md)에 적었습니다. 실제 Google 인증, Streamlit Cloud 배포, iPad/Android 입력과 브라우저 렌더링을 완료한 것으로 주장하지 않습니다. [배포 후 점검표](docs/07_배포후점검표.md)를 반드시 수행하세요.

## 근거와 공식 문서
- 내용 근거는 사용자가 제공한 천재교육 기술·가정② p.102–103 스크린샷입니다. 현재 통계를 외삽하지 않았습니다.
- Streamlit 양방향 컴포넌트: https://docs.streamlit.io/develop/concepts/custom-components/components-v1/intro
- Streamlit custom components API: https://docs.streamlit.io/develop/api-reference/custom-components
- Streamlit Secrets: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- gspread 서비스계정 인증: https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account
- 컴포넌트는 declare_component와 Streamlit v1 postMessage 프로토콜을 사용합니다. 단방향 components.html에 저장 기능을 억지로 붙이지 않았습니다. 인증과 모든 점수 계산은 Python 측에서 수행합니다.
