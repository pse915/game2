"""Streamlit host: authentication, durable snapshots and teacher dashboard."""
from __future__ import annotations
import csv, hashlib, hmac, io, json, os, re, secrets
from datetime import datetime, timezone
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from content import public_content, REQUIRED, CONCEPTS
from engine import SCHEMA, new_state, apply, recap, ready
from storage import make_store, StorageError

st.set_page_config(page_title='서라벌여중 | 나의 미래 다이어리',page_icon='🌅',layout='wide',initial_sidebar_state='collapsed')
st.markdown('''<style>
.stApp{background:#101b26;color:#e7f1ea} .block-container{padding-top:.8rem;max-width:1500px}
[data-testid="stSidebar"]{background:#172737} h1,h2,h3{letter-spacing:-.035em}
div.stButton>button[kind="primary"]{background:#e8ad6a;color:#172737;border:0}
[data-testid="stHeader"]{background:transparent}
</style>''', unsafe_allow_html=True)

@st.cache_resource(show_spinner=False)
def get_store():
    cfg={}
    try:
        cfg=dict(st.secrets)
    except Exception:
        pass
    if os.getenv('GOOGLE_SHEET_ID') and 'sheet_id' not in cfg:
        cfg['sheet_id']=os.getenv('GOOGLE_SHEET_ID')
    return make_store(cfg)

try:
    store=get_store()
    store_problem=''
except StorageError as exc:
    store_problem=str(exc)
    store=None

frontend=Path(__file__).parent/'frontend'
component=components.declare_component('sewol_port_world', path=str(frontend))

def digest_pin(pin,salt=None):
    salt=salt or secrets.token_hex(16)
    encoded=hashlib.pbkdf2_hmac('sha256',pin.encode('utf-8'),bytes.fromhex(salt),200_000).hex()
    return {'salt':salt,'hash':encoded}

def valid_pin(pin,hashinfo):
    try:
        return hmac.compare_digest(digest_pin(pin,hashinfo['salt'])['hash'],hashinfo['hash'])
    except (ValueError,KeyError,TypeError):
        return False

def normalize(v):return v.strip()

def login():
    st.title('📔 서라벌여중: 나의 미래 다이어리')
    st.caption('서라벌여중 · 기술·가정 102~103쪽 · 나만의 생애설계 픽셀 어드벤처')
    st.markdown('**학교 정문에서 시작해 미래마을로 떠나는 자유로운 픽셀 RPG입니다.** 실제 학교를 참고한 외관과 교실에서 탐험을 시작하고, 마을에서는 직업·주거·돌봄·노후를 설계해 보세요.')
    if store_problem:st.error(store_problem+' · 관리자에게 문의하세요. 설정된 Google Sheets가 있을 때 임의로 다른 저장소로 넘어가지 않습니다.')
    with st.form('login-form'):
        a,b,c=st.columns([1,1,1])
        with a:cls=st.text_input('반/학급 코드',placeholder='예: 3-2',max_chars=18)
        with b:sid=st.text_input('학생번호(실명 불필요)',placeholder='예: 07',max_chars=16)
        with c:nick=st.text_input('게임 닉네임',placeholder='예: 별이',max_chars=15)
        pin=st.text_input('개인 이어하기 암호 (8자 이상)',type='password',max_chars=100)
        looks=st.select_slider('캐릭터 모습',options=[1,2,3,4,5,6],value=1)
        restart=st.checkbox('기존 이어하기 대신 새 생애를 시작하기 (이전 기록은 보관됨)')
        submitted=st.form_submit_button('마을 입장 / 이어하기',type='primary',use_container_width=True)
    st.info('결혼·출산 여부로 삶을 평가하지 않습니다. 선택마다 여러 가능성이 있으며, 마을 통계·경제 지표는 실제 국가 통계가 아닌 가상의 수업 모형입니다.')
    if not submitted:return
    cls,sid,nick=map(normalize,[cls,sid,nick])
    if not re.fullmatch(r'[0-9A-Za-z가-힣_-]{1,18}',cls) or not re.fullmatch(r'[0-9A-Za-z_-]{1,16}',sid):
        st.error('반과 학생번호에는 글자·숫자·하이픈만 사용하세요.');return
    if len(pin)<8:st.error('이어하기 암호는 8자 이상 입력하세요.');return
    if store is None:return
    try:old=store.load(cls,sid)
    except Exception as exc:st.error(f'저장 데이터를 불러오지 못했습니다: {exc}');return
    if old and not valid_pin(pin,old.get('auth',{})):
        st.error('기존 학생번호의 암호가 일치하지 않습니다. 다른 기록에 접근할 수 없습니다.');return
    if old and not restart:
        state=old
    else:
        state=new_state(cls,sid,nick or '여행자',looks-1)
        state['auth']=digest_pin(pin)
        try:store.save(state)
        except Exception as exc:st.warning(f'첫 저장이 실패했습니다: {exc}. JSON 백업을 사용하세요.')
    st.session_state['world_state']=state
    st.rerun()

def world():
    state=st.session_state['world_state']
    st.markdown(f"<span style='font-size:1.35rem;font-weight:800'>📔 서라벌여중 <span style='color:#9bcfc0;font-size:.85rem'>내일을 잇는 마을 · {state['nickname']}의 이야기</span></span>",unsafe_allow_html=True)
    with st.sidebar:
        st.subheader('나의 생애 일지')
        st.write(f"**{state['age']}세 · {['청년기','성인기','노년기'][state['stage']]}**")
        st.write(f"필수 사건: {sum(k in state['decisions'] for k in REQUIRED[state['stage']])}/{len(REQUIRED[state['stage']])}")
        st.write(f"경험한 학습 주제: {len(state['concepts'])}/{len(CONCEPTS)}")
        st.caption('지도에서 구역을 터치하면 빠른 이동이 됩니다. 사건 선택 후 저장되며, 이동만으로 저장 요청하지 않습니다.')
        st.markdown('---')
        with st.expander('학습 주제 기록'):
            for key,value in CONCEPTS.items():st.write(('✅ ' if key in state['concepts'] else '▫️ ')+value)
        with st.expander('백업·복원'):
            st.download_button('내 게임 JSON 내려받기',json.dumps(state,ensure_ascii=False,indent=2),file_name=f"sewol_{state['student_id']}.json",mime='application/json')
            upload=st.file_uploader('내가 받은 백업 JSON 복원',type=['json'])
            if upload and st.button('이 백업 복원'):
                try:
                    data=json.loads(upload.getvalue())
                    if data['schema']!=SCHEMA or (data['class_code'],data['student_id'],data['run_id'])!=(state['class_code'],state['student_id'],state['run_id']):
                        raise ValueError('스키마 또는 학생/게임 식별자가 일치하지 않습니다.')
                    if data['revision']<state['revision']:
                        raise ValueError('현재 저장본보다 오래된 버전입니다.')
                    if data.get('auth')!=state.get('auth'):
                        raise ValueError('인증 정보가 일치하지 않습니다.')
                    st.session_state['world_state']=data
                    store.save(data)
                    st.rerun()
                except Exception as exc:st.error(f'복원 거부: {exc}')
        if st.button('다른 학생 입장'):
            del st.session_state['world_state']
            st.rerun()
    # Nonce-based handling avoids duplicate Streamlit iframe message replays.
    result=component(state={k:v for k,v in state.items() if k!='auth'},content=public_content(),
                     notice=st.session_state.get('notice',''),key='sewol_game',default=None)
    if isinstance(result,dict) and result.get('nonce'):
        revised,feedback=apply(state,result)
        if revised['revision']!=state['revision']:
            st.session_state['world_state']=revised
            st.session_state['notice']=feedback
            try:
                store.save(revised)
                st.session_state.pop('save_error',None)
            except Exception as exc:
                st.session_state['save_error']=str(exc)
            st.rerun()
    if st.session_state.get('save_error'):
        st.error('서버 저장이 실패했습니다. 왼쪽의 JSON 내려받기로 백업하세요. '+st.session_state['save_error'])
    if state['ended']:
        st.markdown('### 생애설계 기록 · 학생용 소감문')
        info=recap(state)
        l,r=st.columns(2)
        with l:
            st.write('**내가 선택한 생활**')
            st.write(f"직업: {info['career']} · 주거: {info['housing']} · 정책: {info['policy']}")
            st.write(f"노후 준비: {', '.join(x.removeprefix('ret_') for x in info['retirement'])}")
        with r:st.write('**돌아보기**: '+info['message'])
        st.caption('이 기록은 좋은 삶·나쁜 삶을 나누는 성적표가 아닙니다.')
        with st.form('reflection-form'):
            reflection=st.text_area('소감문 — 무엇을 중요하게 생각했고, 이제 무엇을 준비할까?',value=state.get('reflection',''),height=115)
            save_ref=st.form_submit_button('소감 저장',type='primary')
        if save_ref:
            revised,_=apply(state,{'type':'reflection','text':reflection,'nonce':secrets.token_hex(12)})
            st.session_state['world_state']=revised
            try:store.save(revised)
            except Exception as exc:st.error(f'소감 저장 실패: {exc}')
            st.rerun()

def dashboard():
    st.title('🧑‍🏫 교사 전용 대시보드')
    try:configured=str(st.secrets.get('teacher_password',''))
    except Exception:configured=''
    configured=configured or os.getenv('TEACHER_PASSWORD','')
    if not configured:
        st.warning('교사 암호가 설정되지 않아 대시보드를 사용할 수 없습니다. .streamlit/secrets.toml에 teacher_password를 설정하세요.')
        return
    pw=st.text_input('교사 암호',type='password')
    if not hmac.compare_digest(pw,configured):
        st.info('교사 인증 후 학생별 학습 경험과 마을 선택의 분포를 확인합니다.')
        return
    if store is None:st.error(store_problem);return
    try:data=store.all_latest()
    except Exception as exc:st.error(f'조회 실패: {exc}');return
    classes=sorted({x['class_code'] for x in data})
    target=st.selectbox('학급 필터',['전체']+classes)
    filtered=[x for x in data if target=='전체' or x['class_code']==target]
    done=sum(x.get('ended',False) for x in filtered)
    c1,c2,c3=st.columns(3)
    c1.metric('기록 학생',len(filtered));c2.metric('완료',done);c3.metric('완료 비율',f'{done/max(len(filtered),1)*100:.0f}%')
    policies={}
    for s in filtered:
        p=s.get('flags',{}).get('policy','아직 선택하지 않음')
        policies[p]=policies.get(p,0)+1
    if policies:
        st.subheader('사회적 대응 선택')
        st.bar_chart([{'정책':k,'학생 수':v} for k,v in policies.items()],x='정책',y='학생 수')
    rows=[]
    for x in filtered:
        flags=x.get('flags',{})
        try:
            minutes=max(0,(datetime.fromisoformat(x['last_update'])-datetime.fromisoformat(x['started_at'])).total_seconds()/60)
        except (KeyError,ValueError):
            minutes=0
        rows.append({'학급':x['class_code'],'번호':x['student_id'],'닉네임':x['nickname'],
                     '시기':['청년','성인','노년'][x['stage']],'완료':x.get('ended',False),'경과분(추정)':round(minutes,1),
                     '직업':flags.get('career',''),'주거':flags.get('housing',''),
                     '돌봄':flags.get('care',''),'정책':flags.get('policy',''),
                     '학습주제수':len(x['concepts']),
                     '재무':flags.get('ret_finance',''),'건강':flags.get('ret_health',''),
                     '여가':flags.get('ret_leisure',''),'관계':flags.get('ret_social',''),
                     '소감':x.get('reflection','')})
    st.dataframe(rows,hide_index=True,use_container_width=True)
    buf=io.StringIO();w=csv.DictWriter(buf,fieldnames=list(rows[0]) if rows else ['학급','번호'])
    w.writeheader();w.writerows(rows)
    st.download_button('선택 기록 CSV', '\ufeff'+buf.getvalue(),'sewol_class_summary.csv','text/csv')
    st.caption('경과분은 첫 저장부터 마지막 활동까지의 시각 차이로, 자리 비운 시간도 포함할 수 있는 추정치입니다. 가족 형태나 직업을 성적 기준으로 삼지 않습니다.')

mode=st.query_params.get('mode','game')
if mode=='teacher':dashboard()
elif 'world_state' not in st.session_state:login()
else:world()
