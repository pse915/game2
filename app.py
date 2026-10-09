"""실행: streamlit run app.py"""
import copy, csv, hashlib, hmac, io, json, re, time
from pathlib import Path
import pandas as pd
import streamlit as st
from component import game
from content import TITLE, SUBTITLE, NOTICE, SOURCE, CHAPTERS, NPCS, MAPS, ENDING, EVENTS
from engine import new_state, verify_pin, handle, public_state, validate_state, score, objective, student_digest
from storage import Store
# ===== 시트 주소 설정 (app.py 안에 직접 넣기) =====
# 방법 1: 아래 SHEET_ID에 시트 ID만 넣으세요. 예: "1AbCdEfGhIjKlMnOpQrStUvWx"
# 방법 2: 전체 URL을 복사했다면 SHEET_URL에 넣으세요. 예: "https://docs.google.com/spreadsheets/d/1AbC.../edit"
SHEET_ID = "여기에_시트_ID_붙여넣기"
SHEET_URL = "https://docs.google.com/spreadsheets/d/153iTRzhQVQVFfj_LKOM4Qt9Za-H4mxZYb7Pi-pY94mA/edit"
def _extract_sheet_id(value):
    m = re.search(r"/d/([a-zA-Z0-9-_]+)", value or "")
    if m:
        return m.group(1)
    v = (value or "").strip()
    return v
st.set_page_config(page_title=TITLE,page_icon='🏡',layout='wide',initial_sidebar_state='collapsed')
st.markdown('<style>.block-container{max-width:1140px;padding-top:1.2rem;padding-bottom:1rem}h1{font-size:1.7rem!important}div[data-testid="stMetricValue"]{font-size:1.6rem}</style>',unsafe_allow_html=True)
try:config=st.secrets.to_dict()
except Exception:config={}
# app.py 상수 하드코딩: Secrets에 sheet_id가 없어도 여기서 넣은 주소를 사용합니다.
_hardcoded_id = _extract_sheet_id(SHEET_URL) if SHEET_URL.strip() else _extract_sheet_id(SHEET_ID)
if _hardcoded_id and not _hardcoded_id.startswith("여기에_"):
    config["sheet_id"] = _hardcoded_id
@st.cache_resource
def make_store(config_json):
    return Store(json.loads(config_json))
store=make_store(json.dumps(config,sort_keys=True))

def sync_state(s):
    st.session_state.state=s
    for k in ('student_id','class_code','nickname','x','y','chapter','flags','stats','start_time'):
        st.session_state[k]=copy.deepcopy(s[k])

def enter(s,event):
    sync_state(s);st.session_state.last_event=None
    st.session_state.ui={'type':'notice','title':'미래마을에 오신 것을 환영해요.','text':NOTICE,'lines':['15~20분 수업에서는 게임 아래의 「20분 수업 모드」를 누르세요. NPC와 탐험·선택은 유지하고 필수 퀴즈 잠금만 줄입니다. 실명 대신 별명을 쓰세요.'], 'next':objective(s)}
    st.session_state.save_status=store.save(s,event)
    st.rerun()

def teacher_panel():
    st.title('교사 대시보드')
    password=str(config.get('teacher_password',''))
    if not password or password.startswith('교사용_'):
        st.warning('Secrets에 안전한 teacher_password를 설정해야 교사 화면을 사용할 수 있습니다.');return
    if not st.session_state.get('teacher_ok'):
        if time.time()<st.session_state.get('teacher_wait',0):st.warning('잠시 후 다시 시도해 주세요.');return
        with st.form('teacher_login'):
            typed=st.text_input('교사용 비밀번호를 입력하세요.',type='password')
            submitted=st.form_submit_button('교사 화면에 접속합니다.')
        if submitted:
            if hmac.compare_digest(typed,password):st.session_state.teacher_ok=True;st.rerun()
            else:st.session_state.teacher_wait=time.time()+3;st.error('비밀번호가 맞지 않아요.')
        return
    c1,c2,c3=st.columns(3)
    if c1.button('자료를 새로 불러옵니다.'):st.rerun()
    if c2.button('CSV 백업을 시트로 재전송합니다.'):
        try:st.success(f'{store.sync()}개 로그를 새로 전송했어요. 엔딩 기록도 확인했어요.')
        except RuntimeError as e:st.error(str(e))
    if c3.button('교사 화면에서 로그아웃합니다.'):
        st.session_state.teacher_ok=False;st.rerun()
    # logs에는 미완료 학생도 포함되므로 결과 시트 스키마 변경 없이 수업 상황을 확인합니다.
    recent={}
    for record in store.logs():
        try:
            st_data=validate_state(json.loads(record['state_json']))
            recent[(st_data['class_code'],st_data['student_id'])]=student_digest(st_data)
        except (ValueError,KeyError,TypeError):continue
    if recent:
        st.subheader('학생별 스토리 진행과 생애설계 기록')
        st.caption('기존 logs의 최신 저장 기록을 읽습니다. 진행 중 학생도 표시됩니다. 기록 저장은 기존 방식 그대로입니다.')
        progress_df=pd.DataFrame(recent.values())
        selected_class=st.selectbox('진행 현황 반 선택',['전체 반']+sorted(progress_df['반'].unique().tolist()),key='progress_class')
        if selected_class!='전체 반':progress_df=progress_df[progress_df['반']==selected_class]
        st.dataframe(progress_df,hide_index=True,use_container_width=True)
        st.download_button('학급 진행·생애설계 요약 CSV',progress_df.to_csv(index=False).encode('utf-8-sig'),'생애설계_학급요약.csv','text/csv')
    rows=store.results()
    if store.error:st.warning(store.error)
    if not rows:st.info('아직 저장된 엔딩이 없어요. 미완료 학생은 평균에 포함하지 않습니다.');return
    df=pd.DataFrame(rows)
    for k in ('contribution','final_tfr','happiness','care','minutes','quiz_correct'):df[k]=pd.to_numeric(df[k],errors='coerce')
    classes=['전체 반']+sorted(df['class_code'].astype(str).unique().tolist())
    target=st.selectbox('살펴볼 반을 선택하세요.',classes)
    if target!='전체 반':df=df[df.class_code.astype(str)==target]
    st.caption('results 시트와 미전송 엔딩 백업을 사용하며 반+학번별 최신 완료 기록만 집계합니다. 새 게임을 시작했지만 아직 끝내지 않았다면 이전 완료 기록이 남아 있습니다.')
    c1,c2,c3=st.columns(3);c1.metric('완료 학생 수',len(df));c2.metric('평균 가상 TFR',f'{df.final_tfr.mean():.2f}');c3.metric('평균 TFR 기여도',f'{df.contribution.mean():+.2f}')
    chart=df.groupby('class_code')['contribution'].mean().rename('평균 TFR 기여도')
    st.subheader('반별 평균 TFR 기여도를 비교합니다.')
    st.bar_chart(chart,color='#9ad6b5',height=250)
    st.caption('게임 규칙에 따른 가상 점수입니다. 개인의 가치·가족의 우열·현실 출산율을 평가하지 않습니다.')
    display=df.rename(columns={'class_code':'반','student_id':'학번','nickname':'별명','ending':'엔딩','contribution':'기여도','final_tfr':'가상 TFR','happiness':'행복','care':'돌봄 부담','minutes':'경과 시간(분)','quiz_correct':'완료 퀴즈'})
    st.dataframe(display[['반','학번','별명','엔딩','기여도','가상 TFR','행복','돌봄 부담','경과 시간(분)','완료 퀴즈']],hide_index=True,use_container_width=True)
    safe_export=display.map(lambda value: "'"+value if isinstance(value,str) and value.startswith(('=','+','-','@','\t','\r')) else value)
    st.download_button('결과 CSV를 내려받습니다.',safe_export.to_csv(index=False).encode('utf-8-sig'),'수업결과.csv','text/csv')
    st.info('학생 식별정보가 포함되어 있습니다. 수업 목적 외 공유를 금지하고 학교 개인정보 보유기간에 따라 삭제하세요. 서버 CSV는 Streamlit Cloud 재시작 시 사라질 수 있습니다.')

with st.sidebar:
    st.header('미래마을 수업실')
    mode=st.radio('화면을 선택하세요.',['학생 게임','교사 대시보드'])
    st.caption(SOURCE)
    st.caption('제작: 수업용 원본 픽셀 RPG입니다. 외부 게임 이미지나 소리를 사용하지 않습니다.')
if mode=='교사 대시보드':teacher_panel();st.stop()
st.title(TITLE)
st.caption(SUBTITLE+' · 중3 15세 → 65세 · 15~20분')
if 'state' not in st.session_state:
    st.info('학번·반·별명을 입력해 시작해요. 이어하기에는 동일한 반·학번과 본인이 정한 저장 비밀번호가 필요합니다.')
    with st.expander('수업 모형과 개인정보 안내를 읽습니다.',expanded=True):st.write(NOTICE);st.write('실명은 입력하지 마세요. 입력 정보와 선택 기록은 교사의 수업용 시트에 저장됩니다. 저장 비밀번호는 해시값으로만 보관됩니다.')
    with st.form('start'):
        c1,c2,c3=st.columns(3)
        sid=c1.text_input('학번을 입력하세요. (숫자·영문·하이픈)',max_chars=20)
        cls=c2.text_input('반 코드를 입력하세요. (예: 3-2)',max_chars=20)
        nick=c3.text_input('별명을 입력하세요.',max_chars=12)
        pin=st.text_input('본인 저장 비밀번호를 입력하세요. (4~32자)',type='password',max_chars=32)
        confirmed=st.checkbox('새로 시작하면 이전 진행 대신 새 기록을 최신 기록으로 사용한다는 점을 확인했습니다.')
        a,b=st.columns(2);resume=a.form_submit_button('이어하기');fresh=b.form_submit_button('새로시작')
    if resume or fresh:
        sid,cls,nick=sid.strip(),cls.strip(),nick.strip()
        if not re.fullmatch(r'[A-Za-z0-9-]{1,20}',sid) or not re.fullmatch(r'[A-Za-z0-9가-힣_-]{1,20}',cls) or not nick or len(pin)<4:
            st.error('학번·반·별명과 4자 이상의 비밀번호를 확인해 주세요.')
        elif time.time()<st.session_state.get('login_wait',0):st.warning('잠시 후 다시 시도해 주세요.')
        else:
            try:
                old=store.latest(sid,cls)
                if old and not verify_pin(old,pin):
                    st.session_state.login_wait=time.time()+3;st.error('기존 기록의 저장 비밀번호가 맞지 않아요. 교사에게 문의하세요.')
                elif resume:
                    if old:enter(old,'이어하기')
                    else:st.warning('일치하는 최신 기록을 찾지 못했어요. Google 연결을 확인하거나 개인 저장파일을 복원해 주세요.')
                elif not confirmed:st.warning('새로시작 확인란을 선택해 주세요.')
                else:enter(new_state(sid,cls,nick,pin),'새로시작')
            except (ValueError,KeyError,TypeError):st.error('기존 저장 기록의 형식이 올바르지 않아요. 교사에게 문의하세요.')
            if store.error:st.warning(store.error)
    with st.expander('개인 저장파일에서 복원합니다.'):
        upload=st.file_uploader('본인의 미래마을 JSON 저장파일을 선택하세요.',type=['json'])
        filepin=st.text_input('파일의 저장 비밀번호를 입력하세요.',type='password',key='file_pin')
        if st.button('저장파일을 복원합니다.'):
            try:
                if upload is None:raise ValueError('파일을 먼저 선택해 주세요.')
                if upload.size>1_000_000:raise ValueError('파일이 너무 커요.')
                restored=validate_state(json.loads(upload.getvalue()))
                if not verify_pin(restored,filepin):raise ValueError('저장 비밀번호가 맞지 않아요.')
                restored['revision']+=1;enter(restored,'파일복원')
            except (ValueError,KeyError,TypeError,UnicodeError) as e:st.error(str(e))
    st.caption('키 설정 없이도 체험할 수 있지만 로컬 CSV는 영구 저장소가 아닙니다. 정규 수업에서는 Google Sheets 연결을 권장합니다.')
    st.stop()
s=st.session_state.state
payload={'state':public_state(s),'maps':MAPS,'events':EVENTS,'npcs':NPCS,'chapters':CHAPTERS,'notice':NOTICE,'ui':st.session_state.get('ui'),'save_status':st.session_state.get('save_status','')}
event=game(payload,key='village_'+s['run_id'])
if isinstance(event,dict) and event.get('id') and event['id']!=st.session_state.get('last_event'):
    st.session_state.last_event=event['id']
    try:
        updated,ui=handle(s,event);sync_state(updated);st.session_state.ui=ui
        st.session_state.save_status=store.save(updated,event.get('kind','진행'))
    except (ValueError,KeyError,TypeError,IndexError) as e:
        updated=copy.deepcopy(s);updated['revision']+=1;sync_state(updated)
        st.session_state.ui={'type':'notice','title':'한 번 더 확인해 주세요.','text':str(e)}
    st.rerun()
status=st.session_state.get('save_status','')
if '백업' in status or '실패' in status or '오류' in status:st.warning(status)
else:st.caption(status)
c1,c2,c3=st.columns(3)
raw=json.dumps(st.session_state.state,ensure_ascii=False,indent=2).encode('utf-8')
c1.download_button('개인 저장파일을 내려받습니다.',raw,'미래마을_'+s['class_code']+'_'+s['student_id']+'.json','application/json')
if c2.button('현재 진행을 저장합니다.'):
    st.session_state.save_status=store.save(s,'수동저장');st.rerun()
if c3.button('저장하고 시작화면으로 돌아갑니다.'):
    message=store.save(s,'나가기')
    if '로컬 파일 쓰기도 실패' in message:st.error(message)
    else:
        for key in ['state','ui','last_event','student_id','class_code','nickname','x','y','chapter','flags','stats','start_time']:st.session_state.pop(key,None)
        st.rerun()
with st.expander('선택 기록과 경제 상황을 확인합니다.'):
    st.write(f"현재 월 주거비는 {s['stats']['housing']}만원, 개인 월 소득은 {s['stats']['income']}만원입니다. 실제 가계 계산이 아닌 수업용 설정입니다.")
    for h in s['history']:st.write(f"{h['age']}세: {h['label']}");st.caption(' '.join(h['extra']))
    st.caption('이동은 화면 내부에서 즉시 처리되며, 25초 주기 또는 대화·선택·포탈 이동·저장 버튼에서 서버에 반영됩니다. 브라우저를 닫기 전에 저장하세요.')
if s['finished']:
    d,t=score(s)
    st.subheader('나의 엔딩을 수업 기록으로 남깁니다.')
    st.write(public_state(s)['ending_info']['message'])
    st.bar_chart(pd.DataFrame({'가상 TFR':[1.30,t]},index=['전국 비교 기준(가정)','나의 가상 결과']),height=230,color='#9ad6b5')
    st.caption('전국 기준 1.30은 수업용 가정값입니다. 음수 결과는 고정 계산식의 한계이며 실제 출산율이 아닙니다.')
    st.write('어떤 정책이 행복과 돌봄 부담을 함께 바꾸었나요? 자녀 수를 바꾸지 않고도 더 나은 삶을 만드는 방법은 무엇인가요?')
    report={'반':s['class_code'],'학번':s['student_id'],'별명':s['nickname'],'엔딩':s['ending'],'TFR 기여도':d,'최종 가상 TFR':t,'선택 기록':s['history']}
    st.download_button('나의 결과 기록을 내려받습니다.',json.dumps(report,ensure_ascii=False,indent=2),'미래마을_결과.json','application/json')
