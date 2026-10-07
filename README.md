# 미래마을을 구해라! 생애설계 어드벤처
중3~60대 생애 시뮬레이션 (기술·가정② p.102-103)

## 실행
```
pip install -r requirements.txt
streamlit run app.py
```

## 구글시트 설정
1. Google Cloud 콘솔 → 서비스 계정 생성 → JSON 키 발급
2. 새 스프레드시트 생성 (제목 자유)
3. 스프레드시트 공유 버튼 → 서비스계정 이메일(…iam.gserviceaccount.com)에 편집자 권한 부여
4. 로컬: `.streamlit/secrets.toml` 생성 (secrets.toml.example 복사 후 값 입력)
5. worksheets `logs`, `results`는 첫 저장 시 자동 생성됨. 수동 생성 시 헤더:
   - logs: timestamp, 학번, class_code, nickname, chapter, choice_id, choice_text, my_children, tfr_delta, vitality, happiness, burden
   - results: timestamp, 학번, class_code, nickname, ending_type, final_tfr, tfr_delta, final_aging, play_time_sec, full_path_summary

## GitHub → Streamlit Cloud 배포 5단계
1. GitHub New Repository 생성 → 본 폴더 파일 전체 push (`git init; git add .; git commit -m "future village"; git push`)
2. https://share.streamlit.io → New app → 저장소/브랜치/main file `app.py` 선택
3. App settings → Secrets → secrets.toml.example 내용을 실제 값으로 채워 붙여넣기 (SHEET_URL + [gcp_service_account])
4. Deploy → 로그에 `logs` 시트 쓰기 테스트 (게임에서 1개 선택 후 시트 확인)
5. 학생 배포: 앱 URL + 반 코드 공지, 학번+닉네임으로 시작

## 수업 50분 흐름
- 도입 10분: 노령화지수 14.5%→95.1% 신문 제시, “우리 마을이 이렇게 되면?” 예측
- 전개 25분: 개별 플레이 (CH0~CH5 + 퀴즈 6문제), 선택 이유 메모
- 정리 15분: 교사 대시보드로 반 평균 TFR 기여도·엔딩 분포 공유, p.103 대비책과 연결 (“어떤 선택이 출산율을 올렸나?”)

## 발문
- 도입: 1) 65세 20%면 우리 학교는? 2) 결혼·출산을 미루는 이유는? 3) 수명이 길어지면 좋은 점/어려운 점은?
- 정리: 1) 네 TFR 기여도는? 무엇을 바꿨나? 2) 마을을 살린 정책 2가지는? 3) 가족친화문화를 위해 내가 할 일은?
