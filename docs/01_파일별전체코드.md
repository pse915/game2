# 파일별 전체 코드

실행용 개별 파일 전체를 순서대로 모았습니다. 실행할 때에는 ZIP의 개별 파일을 사용합니다.

## app.py

```python
"""실행: streamlit run app.py"""
import copy, csv, hashlib, hmac, io, json, re, time
from pathlib import Path
import pandas as pd
import streamlit as st
from component import game
from content import TITLE, SUBTITLE, NOTICE, SOURCE, CHAPTERS, NPCS, MAPS, ENDING
from engine import new_state, verify_pin, handle, public_state, validate_state, score, objective
from storage import Store
st.set_page_config(page_title=TITLE,page_icon='🏡',layout='wide',initial_sidebar_state='collapsed')
st.markdown('<style>.block-container{max-width:1140px;padding-top:1.2rem;padding-bottom:1rem}h1{font-size:1.7rem!important}div[data-testid="stMetricValue"]{font-size:1.6rem}</style>',unsafe_allow_html=True)
try:config=st.secrets.to_dict()
except Exception:config={}
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
    st.session_state.ui={'type':'notice','title':'미래마을에 오신 것을 환영해요.','text':NOTICE,'lines':['예상 플레이 시간은 15~20분입니다. 방향키는 게임 화면을 한 번 눌러야 작동합니다. 개인정보 보호를 위해 실명 대신 별명을 쓰세요.'], 'next':objective(s)}
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
payload={'state':public_state(s),'maps':MAPS,'npcs':NPCS,'chapters':CHAPTERS,'notice':NOTICE,'ui':st.session_state.get('ui'),'save_status':st.session_state.get('save_status','')}
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

```

## engine.py

```python
"""화면이나 네트워크에 의존하지 않는 게임 규칙입니다."""
import copy, hashlib, secrets, time, uuid, math
from collections import deque
from content import CHAPTERS, NPCS, MAPS, QUIZZES, CHECKLIST, ENDING, KNOWLEDGE, NOTICE
SCHEMA = 1
NPC = {n['id']:n for n in NPCS}

def pin_hash(pin,salt):
    return hashlib.pbkdf2_hmac('sha256',str(pin).encode(),salt.encode(),120000).hex()

def new_state(student_id,class_code,nickname,pin):
    salt=secrets.token_hex(16)
    return dict(schema=SCHEMA,run_id=str(uuid.uuid4()),student_id=student_id,class_code=class_code,nickname=nickname,
      x=5,y=9,zone=0,chapter=0,age=15,flags={'informed':False},
      stats={'children':0,'village_tfr':1.30,'contribution':0.0,'aging':14.0,'vitality':50,'happiness':50,'care':50,'housing':0,'income':0},
      start_time=time.time(),revision=0,history=[],quizzes={},checklist=[],visited=[],finished=False,
      _pin_salt=salt,_pin_hash=pin_hash(pin,salt))

def verify_pin(state,pin):
    return secrets.compare_digest(state.get('_pin_hash',''),pin_hash(pin,state.get('_pin_salt','')))

def bonuses(s):
    f=s['flags']; items=[]
    if f.get('shared_care'):items.append(('공동육아',.10))
    for label,k in [('휴직 제도','leave'),('어린이집 제도','nursery'),('유연근무 제도','flex')]:
        if f.get(k):items.append((label,.05))
    if f.get('family_learning'):items.append(('가족가치 학습',.05))
    if f.get('solo_care'):items.append(('독박·경력단절',-.10))
    if f.get('unprepared'):items.append(('무준비 부양',-.10))
    if not f.get('informed'):items.append(('정책무지',-.05))
    return items

def score(s):
    b=round(sum(v for _,v in bonuses(s)),2)
    delta=round((s['stats']['children']-1.30)+b,2)
    return delta,round(1.30+delta,2)

def ending_code(s):
    delta,tfr=score(s); st=s['stats']
    if st['happiness']<=30 or st['care']>=80:return 'D'
    if tfr<=.99 or st['aging']>=20:return 'C'
    if tfr>=1.60:return 'A'
    return 'B'

def walkable(zone,x,y):
    if type(zone)!=int or not 0<=zone<len(MAPS) or type(x)!=int or type(y)!=int or not (0<=x<24 and 0<=y<15):return False
    for bx,by,w,h,_ in MAPS[zone]['buildings']:
        if bx<=x<bx+w and by<=y<by+h:return False
    if any(n['zone']==zone and n['x']==x and n['y']==y for n in NPCS):return False
    return True

def reachable(zone,a,b):
    todo=deque([a]); seen={a}
    while todo:
        p=todo.popleft()
        if p==b:return True
        for dx,dy in ((0,1),(0,-1),(1,0),(-1,0)):
            q=(p[0]+dx,p[1]+dy)
            if q not in seen and walkable(zone,*q):seen.add(q);todo.append(q)
    return False

def accept_position(s,event):
    x=event.get('x',s['x']); y=event.get('y',s['y'])
    if walkable(s['zone'],x,y) and reachable(s['zone'],(s['x'],s['y']),(x,y)):
        s['x'],s['y']=x,y

def near(s,npc_id):
    n=NPC.get(npc_id,{})
    return n.get('zone')==s['zone'] and abs(n.get('x',99)-s['x'])+abs(n.get('y',99)-s['y'])<=1

def allowed(s,o):
    key=o.get('require')
    if key=='checklist':return set(s['checklist'])==set(CHECKLIST)
    return not key or bool(s['flags'].get(key))

def apply_effects(s,effects):
    for k,v in effects.items():
        if k in ('housing','income'):s['stats'][k]=v
        else:s['stats'][k]=round(s['stats'].get(k,0)+v,2)
    for k in ('vitality','happiness','care'):s['stats'][k]=max(0,min(100,s['stats'][k]))
    s['stats']['aging']=max(0,min(100,round(s['stats']['aging'],2)))

def refresh(s):
    if s['flags'].get('birth_decided'):
        d,t=score(s);s['stats']['contribution']=d;s['stats']['village_tfr']=t

def choices_ui(s):
    ch=CHAPTERS[s['chapter']]
    options=[]
    for o in ch['options']:
        options.append(dict(code=o['code'],label=o['label'],locked=not allowed(s,o),reason=o.get('reason',''),
                            note=o.get('note',''),effects=o['effects']))
    return dict(type='choices',title=ch['title'],text=ch['prompt'],options=options)

def quiz_ui(s,message=''):
    q=QUIZZES[s['chapter']]
    return dict(type='quiz',title='미래마을 지식 확인',text=q['q'],answers=q['a'],message=message)

def apply_choice(s,code):
    """테스트와 화면에서 공동으로 쓰는 권위 있는 분기 처리입니다."""
    ch=s['chapter']
    if ch>=6:raise ValueError('이미 모든 챕터를 마쳤어요.')
    if not s['quizzes'].get(str(ch),{}).get('correct'):raise ValueError('먼저 이번 퀴즈를 풀어 주세요.')
    option=next((o for o in CHAPTERS[ch]['options'] if o['code']==code),None)
    if option is None:raise ValueError('없는 선택지예요.')
    if not allowed(s,option):raise ValueError(option['reason'])
    before=copy.deepcopy(s['stats']); extra=[]
    apply_effects(s,option['effects']);s['flags'].update(option['flags'])
    if ch==1 and option['code']=='D':extra.append('대학 4년을 보냈어요. 다음 장은 29세입니다. 이후에는 취업 가능 상태로 진행합니다.')
    if ch==2:
        if s['flags'].get('college'):
            s['flags']['employed']=True
            if option['code']!='D':s['stats']['income']=270
            apply_effects(s,{'vitality':4});extra.append('대학 진로 탐색 보너스로 활력이 4 높아졌어요.')
        if option.get('bonus')=='housing' and s['flags'].get('housing_stable'):
            apply_effects(s,{'happiness':4,'care':-3});extra.append('안정 주거 보너스: 행복 +4, 돌봄 부담 -3입니다.')
        if s['flags'].get('partner'):
            jobs=['간호사','공공기관 직원','프리랜서','교사']
            idx=int(hashlib.sha256((s['run_id']+'배우자').encode()).hexdigest(),16)%len(jobs)
            job=jobs[idx];s['flags']['partner_job']=job
            # 직업의 우열을 점수화하지 않고 근무 시간 의논 이벤트만 줍니다.
            extra.append('배우자 직업 사건: '+job+'입니다. 근무 시간과 돌봄 분담을 함께 의논합니다. 직업별 점수 차이는 없습니다.')
    if ch==3:
        s['stats']['children']=option['children'];s['flags']['birth_decided']=True;s['flags']['policy_offer']=True
        extra.append('국가·사회 책임 정책카드를 받았어요. 화면의 정책카드 버튼으로 활성화할 수 있어요.')
    if ch==4:
        if s['stats']['children']==0:
            s['flags'].pop('leave',None);s['flags'].pop('nursery',None)
            extra.append('무자녀 계획이므로 개인의 육아휴직·어린이집 보너스는 적용하지 않아요. 공동 돌봄과 유연근무는 반영해요.')
        stress=3*s['stats']['children']
        if s['flags'].get('policy_card'):stress=max(0,stress-4)
        apply_effects(s,{'happiness':-stress,'care':stress})
        extra.append('양육·교육비 스트레스 사건: 행복 -'+str(stress)+', 돌봄 부담 +'+str(stress)+'입니다. 지원카드는 이 부담을 완화해요.')
    refresh(s)
    s['history'].append({'chapter':ch,'age':CHAPTERS[ch]['age'],'code':code,'label':option['label'],'before':before,'after':copy.deepcopy(s['stats']),'extra':extra})
    s['chapter']+=1;s['age']=CHAPTERS[s['chapter']]['age'] if s['chapter']<6 else 65
    n=NPC[CHAPTERS[ch]['guide']]
    response=n['after'].get(str(ch)+code,'다음 세대와 함께 미래를 준비해요.')
    if ch==3:response+=' '+('학교 유지 불빛이 켜졌어요.' if s['stats']['village_tfr']>=1.0 else '학교의 불빛이 꺼졌어요. 이는 가상 모형의 연출이지 개인에 대한 책임 판정이 아니에요.')
    return dict(type='notice',title='선택이 마을에 반영되었어요.',text=response,lines=extra,next=objective(s))

def objective(s):
    if s['finished']:return '엔딩을 확인하고 수업 성찰을 기록하세요.'
    if s['chapter']>=6:return '실버타운의 온유 미래시장에게 말을 걸어 65세 엔딩을 확인하세요.'
    n=NPC[CHAPTERS[s['chapter']]['guide']]
    return CHAPTERS[s['chapter']]['title']+' · '+MAPS[n['zone']]['name']+'의 '+n['name']+'에게 말을 거세요.'

def talk_ui(s,npc_id):
    n=NPC[npc_id]
    lines=[n['quote'],n['text']]
    for h in s['history']:
        key=str(h['chapter'])+h['code']
        if key in n['after']:lines.append(n['after'][key])
    buttons=[]
    if s['chapter']<6 and CHAPTERS[s['chapter']]['guide']==npc_id:
        buttons.append({'label':'이번 챕터를 진행합니다.','kind':'quest'})
    if npc_id=='scholar':buttons.append({'label':'무료 정책 안내를 받습니다.','kind':'learn'})
    if npc_id=='hr':buttons.append({'label':'고용·제도 상담을 받습니다.','kind':'work_help'})
    if npc_id=='official':
        buttons += [{'label':'인구피라미드를 봅니다.','kind':'pyramid'}, {'label':'주거·돌봄 안전망을 상담합니다.','kind':'housing_help'}]
    if npc_id in ('granny','doctor'):buttons.append({'label':'노후 준비 4영역을 점검합니다.','kind':'check_open'})
    if npc_id=='mayor' and s['chapter']>=6:buttons.append({'label':'65세 엔딩홀에 입장합니다.','kind':'finish'})
    return dict(type='talk',title=n['name'],npc=npc_id,lines=lines,cards=[KNOWLEDGE[i] for i in n['cards']],buttons=buttons)

def handle(state,event):
    s=copy.deepcopy(state);kind=event.get('kind');accept_position(s,event);ui=None
    if s['finished'] and kind not in ('save','book','ending'):
        return s,{'type':'notice','title':'여정이 끝났어요.','text':'엔딩과 선택 기록을 확인해 주세요.'}
    if kind=='portal':
        p=next((p for p in MAPS[s['zone']]['portals'] if p['x']==s['x'] and p['y']==s['y']),None)
        if not p:raise ValueError('포탈 타일 위에서 이동해 주세요.')
        s.update(zone=p['to'],x=p['tx'],y=p['ty'])
    elif kind=='talk':
        nid=event.get('npc')
        if not near(s,nid):raise ValueError('NPC 바로 옆에서 말을 걸어 주세요.')
        if nid not in s['visited']:s['visited'].append(nid)
        ui=talk_ui(s,nid)
    elif kind in ('quest','answer','choose'):
        if s['chapter']>=6:raise ValueError('엔딩홀로 이동해 주세요.')
        guide=CHAPTERS[s['chapter']]['guide']
        if not near(s,guide):raise ValueError('이번 챕터 안내자 옆에서 진행해 주세요.')
        ch=str(s['chapter'])
        if kind=='quest':ui=choices_ui(s) if s['quizzes'].get(ch,{}).get('correct') else quiz_ui(s)
        elif kind=='answer':
            q=QUIZZES[s['chapter']];a=event.get('answer')
            if type(a)!=int or not 0<=a<len(q['a']):raise ValueError('답을 선택해 주세요.')
            prior=s['quizzes'].get(ch,{})
            correct=a==q['correct']
            s['quizzes'][ch]={'correct':bool(prior.get('correct') or correct),'attempts':prior.get('attempts',0)+1}
            ui=choices_ui(s) if correct else quiz_ui(s,'다시 생각해 봐요. '+q['why'])
            if correct:ui['feedback']='정답입니다. '+q['why']
        else:ui=apply_choice(s,event.get('code'))
    elif kind in ('learn','work_help','housing_help'):
        target={'learn':'scholar','work_help':'hr','housing_help':'official'}[kind]
        if not near(s,target):raise ValueError('상담 NPC 옆에서 이용해 주세요.')
        if kind=='learn':s['flags']['informed']=True;message='정보 접근성이 열렸어요. 정책무지 -0.05가 해제됩니다.'
        elif kind=='work_help':s['flags'].update(employed=True,work_support=True);message='고용 연결과 제도 정보가 생겼어요. 직장 지원 선택지가 열립니다.'
        else:s['flags']['housing_stable']=True;message='안정 주거 상담을 마쳤어요. 주거 안전망 분기가 열립니다. 실제 지원 자격은 별도로 확인해요.'
        refresh(s);ui={'type':'notice','title':'상담을 마쳤어요.','text':message}
    elif kind=='pyramid':
        if not near(s,'official'):raise ValueError('시청직원 옆에서 게시판을 열어 주세요.')
        ui={'type':'pyramid','title':'시청 인구피라미드 게시판','text':'설명용 가상 연령·성별 분포입니다. 실제 한국 통계가 아닙니다. 고령화율은 전체 인구 중 65세 이상 비중입니다.'}
    elif kind in ('check_open','check'):
        if not (near(s,'granny') or near(s,'doctor')):raise ValueError('할머니 또는 의사 옆에서 점검해 주세요.')
        if kind=='check':
            checked=event.get('checked',[])
            if not isinstance(checked,list) or not all(k in CHECKLIST for k in checked):raise ValueError('점검 항목이 올바르지 않아요.')
            s['checklist']=list(dict.fromkeys(checked))
        ui={'type':'checklist','title':'노후 준비 4영역','text':'실제로 준비한 자산을 묻는 것이 아니에요. 각 영역의 계획을 읽고 학습 여부를 표시하세요.','items':CHECKLIST,'checked':s['checklist']}
    elif kind=='policy':
        if not s['flags'].get('policy_offer'):raise ValueError('32세 선택 후 정책카드를 받을 수 있어요.')
        if not s['flags'].get('policy_card'):
            s['flags']['policy_card']=True;s['flags']['informed']=True
            apply_effects(s,{'care':-5,'vitality':6,'happiness':4});refresh(s)
        ui={'type':'notice','title':'국가·사회 책임 정책카드','text':'공공 돌봄·양육교육비 문화 개선을 연결했어요. 돌봄 -5, 활력 +6, 행복 +4이며, 양육비 사건의 부담을 4 줄입니다. TFR에 직접 가산하지 않으며, 정책무지 불이익은 해제합니다. 중복 사용은 안 됩니다.'}
    elif kind=='finish':
        if s['chapter']<6 or not near(s,'mayor'):raise ValueError('모든 챕터를 마치고 엔딩홀로 와 주세요.')
        s['finished']=True;s['ended_at']=time.time();s['ending']=ending_code(s);refresh(s);ui={'type':'ending'}
    elif kind=='ending':ui={'type':'ending'}
    elif kind=='book':ui={'type':'book','title':'미래마을 지식 도감','cards':KNOWLEDGE}
    elif kind=='save':pass
    else:raise ValueError('알 수 없는 요청이에요.')
    s['revision']+=1
    return s,ui

def public_state(s):
    data={k:copy.deepcopy(v) for k,v in s.items() if not k.startswith('_')}
    data['objective']=objective(s);data['bonus_items']=bonuses(s)
    if s['finished']:
        code=ending_code(s);delta,tfr=score(s)
        data['ending_info']={**ENDING[code],'code':code,'delta':delta,'tfr':tfr,
          'message':f'당신의 선택이 합계출산율을 {delta:+.2f}만큼 '+('올렸습니다.' if delta>=0 else '내렸습니다.')+f' 최종 TFR {tfr:.2f}'}
    return data

def validate_state(s):
    if not isinstance(s,dict) or s.get('schema')!=SCHEMA:raise ValueError('지원하지 않는 저장파일이에요.')
    for key in ('student_id','class_code','nickname','run_id','_pin_salt','_pin_hash'):
        if not isinstance(s.get(key),str) or not s[key] or len(s[key])>200:raise ValueError('저장 식별 정보가 잘못되었어요.')
    if type(s.get('chapter'))!=int or not 0<=s['chapter']<=6:raise ValueError('챕터 정보가 잘못되었어요.')
    if not walkable(s.get('zone'),s.get('x'),s.get('y')):raise ValueError('이동 좌표가 잘못되었어요.')
    for k in ('children','village_tfr','contribution','aging','vitality','happiness','care','housing','income'):
        v=s.get('stats',{}).get(k)
        if not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>100000:raise ValueError('지표가 잘못되었어요.')
    if s['stats']['children'] not in (0,1,2,3):raise ValueError('자녀 수가 잘못되었어요.')
    for k,t in [('flags',dict),('quizzes',dict),('history',list),('checklist',list),('visited',list)]:
        if not isinstance(s.get(k),t):raise ValueError('진행 기록이 잘못되었어요.')
    for k in ('start_time','revision','age'):
        if not isinstance(s.get(k),(int,float)) or not math.isfinite(s[k]):raise ValueError('시간·버전 정보가 잘못되었어요.')
    if not isinstance(s.get('finished'),bool):raise ValueError('엔딩 상태가 잘못되었어요.')
    if any(k not in CHECKLIST for k in s['checklist']):raise ValueError('노후 준비 항목이 잘못되었어요.')
    return s

```

## content.py

```python
"""교과서 기반 수업 데이터입니다. 수치는 현실 예측이 아닌 게임 밸런스입니다."""
TITLE = '중3부터 시작하는 미래마을을 구해라!'
SUBTITLE = '생애설계 어드벤처'
SOURCE = '천재교육 기술·가정②, 사용자 제공 p.102–103 스크린샷'
NOTICE = ('결혼·비혼과 자녀 수는 개인의 선택입니다. 가족의 형태나 사람의 가치를 점수로 평가하지 않습니다. '
          'TFR 기여도는 이 수업만의 가상 계산이며, 한 사람의 선택으로 실제 국가 출산율을 계산할 수 없습니다. '
          '전국 비교 기준 1.30은 요청된 가정값이지 현재 전국 실측치가 아닙니다.')
KNOWLEDGE = [
 {'title':'출산 관련 용어', 'text':'저출산=2명 이하 지속, 초저출산=1.3명 이하, 출산율=15~49세 여성 평생 예상 출생아', 'note':'요청된 수업 문구를 그대로 사용합니다. 여기서 출산율은 합계출산율을 뜻합니다. 실제 통계는 해당 연도의 연령별 출산율을 합산한 지표이며 개인의 미래 출생아 수를 예측하는 값은 아닙니다.'},
 {'title':'고령화의 진행 단계', 'text':'고령화사회 65세 7%+, 고령사회 14%+, 초고령사회 20%+', 'note':'전체 인구 중 65세 이상 인구의 비율입니다. 경계값을 포함하며, 가장 높은 해당 단계를 적용합니다.'},
 {'title':'원인A 결혼·출산기피', 'text':'소득·고용불안정, 결혼·출산 가치관 약화, 일·가정 양립 어려움, 육아부담 증가', 'note':'교과서의 원인 분류입니다. 비혼이나 무자녀 개인에게 책임을 돌리는 뜻이 아닙니다.'},
 {'title':'원인B 평균수명 상승', 'text':'영양상태 개선, 의료기술 향상', 'note':'오래 건강하게 사는 것은 성취입니다. 돌봄 체계를 함께 준비해야 합니다.'},
 {'title':'가정생활의 영향 6종', 'text':'노인부양부담↑, 노후생활 불안정, 노인경제활동↑, 노인돌봄부담↑(고령자녀가 초고령부모 부양), 양육·교육비↑, 가족스트레스↑(기대치 상승)', 'note':'사회에는 노동력부족·생산성저하·경기침체·경쟁력약화·복지부담·의료비급증 문제가 생길 수 있습니다. 노인의 경제활동 자체는 부정적인 일이 아닙니다.'},
 {'title':'장기 대비와 단기 대비', 'text':'장기: 가족생활 가치회복, 양성평등, 세대간 이해·협동, 가족친화문화 / 단기: 인식·가치관 교육+정책적 노력', 'note':'개인의 노력과 사회 제도를 함께 바꾸는 방식입니다.'},
 {'title':'저출산 대비 6가지', 'text':'인식교육, 국가·사회책임강화, 청년일자리·신혼주거지원, 고비용양육교육문화개선, 양성평등육아확산, 결혼·출산·육아가치회복', 'note':'선택권을 존중하면서 돌봄을 함께 책임집니다.'},
 {'title':'고령 사회 대비 5가지', 'text':'연금·의료·돌봄확대, 고령친화산업·실버경제, 교통·생활안전, 문화·여가확대, 세대간이해증진', 'note':'고령 친화적인 동네는 모든 세대가 안전한 동네입니다.'},
 {'title':'노후준비지원법', 'text':'노후준비지원법 2015년, 국민연금공단 재무·건강·여가·대인관계 상담·교육', 'note':'게임의 4영역 체크는 계획을 학습했다는 뜻이지 실제 재무 준비를 완료했다는 뜻은 아닙니다.'},
 {'title':'교과서 속 신문 읽기', 'text':'“확 늙어버린 대한민국” — 한국 고령화사회→고령사회 18년, 세계 최고 수준', 'note':'p.103의 2016.9.7 기사에 실린 당시 전망입니다. 2000년→2018년 진입 예상이라는 역사 자료이며 현재 통계로 쓰지 않습니다. 노령화지수는 0~14세 인구 100명당 65세 이상 인구의 수입니다. 기사 수치는 1985년 14.5%, 2015년 95.1%입니다.'}
]
# 좌표는 24×15 타일 기준입니다. 건물은 위쪽, 이동로와 NPC는 아래쪽에 있습니다.
MAPS = [
 {'name':'중학교·청춘거리','color':'#739e6b','buildings':[[1,1,7,4,'미래중학교'],[11,1,5,4,'청춘책방'],[18,1,5,4,'진로교실']], 'sign':'가족 친화 문화의 확산', 'portals':[{'x':22,'y':8,'to':1,'tx':1,'ty':8,'label':'신혼마을'}]},
 {'name':'신혼마을·시청 통계센터','color':'#81a98e','buildings':[[1,1,6,4,'공공주택'],[9,1,7,4,'시청 통계센터'],[18,1,5,4,'청년상점']], 'sign':'고령화 7% / 고령 14% / 초고령 20%', 'portals':[{'x':0,'y':8,'to':0,'tx':21,'ty':8,'label':'중학교'},{'x':23,'y':8,'to':2,'tx':1,'ty':8,'label':'육아지구'},{'x':12,'y':14,'to':3,'tx':12,'ty':12,'label':'직장거리'}]},
 {'name':'육아교육지구','color':'#9bad77','buildings':[[1,1,7,4,'새싹어린이집'],[11,1,7,4,'미래초등학교']], 'sign':'출산·양육에 대한 국가·사회의 책임 강화', 'portals':[{'x':0,'y':8,'to':1,'tx':22,'ty':8,'label':'신혼마을'},{'x':23,'y':8,'to':3,'tx':1,'ty':8,'label':'직장거리'}]},
 {'name':'직장거리','color':'#7e9e93','buildings':[[1,1,7,4,'유연근무 회사'],[11,1,6,4,'직장어린이집'],[19,1,4,4,'청년공방']], 'sign':'양성평등한 육아 문화 확산', 'portals':[{'x':0,'y':8,'to':2,'tx':22,'ty':8,'label':'육아지구'},{'x':12,'y':14,'to':1,'tx':12,'ty':12,'label':'시청'},{'x':23,'y':8,'to':4,'tx':1,'ty':8,'label':'실버타운'}]},
 {'name':'실버타운·미래시청','color':'#8a9b92','buildings':[[1,1,6,4,'마을병원'],[9,1,6,4,'경로당'],[17,1,6,4,'미래시청 엔딩홀']], 'sign':'세대 간 이해 증진', 'portals':[{'x':0,'y':8,'to':3,'tx':22,'ty':8,'label':'직장거리'}]}
]
NPCS = [
 {'id':'teacher','name':'한봄 담임교사','zone':0,'x':5,'y':6,'color':'#c48076','quote':'“가족 친화 문화의 확산”을 함께 실천해 봅시다. 어떤 가족이든 존중받아야 해요.', 'text':'오늘은 중3, 15세입니다. 여러분은 60대까지 살아 보며 개인의 선택과 제도가 어떤 차이를 만드는지 관찰할 거예요.', 'cards':[0,2,5], 'after':{'0A':'가족생활의 가치를 배웠군요. 다른 형태의 가족도 함께 존중해요.','0B':'1인가구의 삶도 존중해요. 필요한 정책을 찾아볼 정보 접근성을 얻었어요.','0C':'관심은 나중에 생겨도 괜찮아요. 척척박사의 무료 정보 안내를 이용하세요.'}},
 {'id':'career','name':'이길 취업상담사','zone':0,'x':19,'y':6,'color':'#d8b261','quote':'“청년 일자리 확대 및 신혼부부 주거 지원”은 삶의 출발을 돕는 정책이에요.', 'text':'20대의 출발점이에요. 바로 취업하거나 대학에서 4년 더 공부할 수 있어요. 주거비와 고용 안정성을 살펴보세요.', 'cards':[2,6], 'after':{'1A':'안정적인 일자리와 지원 주택을 연결했어요.','1B':'불안정한 소득은 개인의 잘못이 아니에요. 공동체 지원을 찾아봐요.','1C':'지역 일자리와 정착 지원을 연결했어요.','1D':'진로를 탐색할 4년을 보냅니다. 29세 시점에는 취업 준비를 마친 상태예요.'}},
 {'id':'scholar','name':'척척박사','zone':0,'x':12,'y':10,'color':'#a396d5','quote':'“저출산·고령 사회에 대비한 정책적 노력”도 필요해요.', 'text':'정책을 모른다면 여기에서 배울 수 있어요. 나의 선택만으로 국가 통계가 정해지는 것은 아니에요. 무료 안내를 누르면 정책무지 플래그가 해제돼요.', 'cards':[0,1,2,3,4,5,6,7,8,9], 'after':{'0C':'지금 정보를 익혀도 늦지 않아요. 무료 정책 안내를 눌러 보세요.'}},
 {'id':'official','name':'나래 시청직원','zone':1,'x':12,'y':6,'color':'#7ab5d5','quote':'“고령 사회: 총인구 중 65세 이상인 고령자의 비율이 14% 이상인 사회”라고 교과서는 설명해요.', 'text':'7%, 14%, 20%를 기억하세요. 인구피라미드는 나이별 인구 구성을 보여 줍니다. 이 게시판의 남녀 분포는 설명용 가상 자료예요. 29세의 관계와 진로를 선택해 보세요.', 'cards':[1,9], 'after':{'2A':'결혼을 선택했군요. 돌봄을 평등하게 나눌 약속도 필요해요.','2B':'동거·사실혼을 선택했군요. 실제 제도마다 지원 대상이 다르니 자격을 확인해야 해요.','2C':'비혼·만혼을 선택했군요. 친구·이웃과 서로 돌보는 연결도 소중해요.','2D':'취직에 집중하기로 했군요. 관계의 선택을 나중에 바꿀 수도 있어요.'}},
 {'id':'owner','name':'도윤 청년사장','zone':1,'x':20,'y':6,'color':'#bf956b','quote':'“노동력 부족과 생산성 저하”는 우리 가게에도 영향을 줄 수 있어요.', 'text':'일할 사람이 줄고 손님도 줄면 영업을 줄이게 돼요. 자동화, 고령 친화 일자리, 청년 정착 지원을 함께 고민해야 해요.', 'cards':[4,6,7], 'after':{'3A':'돌봄 공동체와 일자리 정책도 마을을 지키는 데 필요해요.','3C':'학교의 수요가 늘었어요. 일할 가족의 돌봄 지원도 준비해야겠어요.'}},
 {'id':'director','name':'새봄 어린이집원장','zone':2,'x':5,'y':6,'color':'#df9ab2','quote':'“출산·양육에 대한 국가·사회의 책임 강화”를 기억하세요.', 'text':'32세입니다. 자녀 수는 자유롭게 고릅니다. 현재 관계 유형과 무관한 미래 계획으로 선택할 수 있어요. 실제 입양·출산·지원 자격은 별도 확인이 필요해요. 정책카드를 받으면 양육을 사회가 함께 지원합니다.', 'cards':[0,2,6], 'after':{'3A':'무자녀 계획을 존중해요. 공동육아나 지역 돌봄에는 누구나 참여할 수 있어요.','3B':'한 아이가 자라려면 온 마을의 지원이 필요해요.','3C':'학교 유지 신호가 켜졌어요. 숫자만큼 중요한 것은 아이와 가족의 삶이에요.','3D':'게임에서는 3명+를 정확히 3명으로 계산해요. 충분한 지원망을 함께 준비해요.'}},
 {'id':'solo','name':'지은 독박육아맘','zone':2,'x':16,'y':6,'color':'#b69bbc','quote':'“일·가정 양립의 어려움”과 “육아 부담의 증가”가 겹치니 힘들어요.', 'text':'돌봄이 한 사람에게 몰리면 경력과 건강을 잃을 수 있어요. 양육·교육비가 늘고 자녀에 대한 기대가 커지면 가족 스트레스도 생겨요. 개인을 탓하지 말고 나눌 방법을 찾아요.', 'cards':[2,4,6], 'after':{'4C':'혼자 떠안지 않아도 돼요. 지금부터라도 공적 돌봄과 휴직 제도를 요청하세요.','4A':'돌봄을 나눌 제도가 생겨 한숨 돌렸어요.','4D':'직장에서도 돌봄을 함께 책임지는군요.'}},
 {'id':'working','name':'유진 워킹맘선배','zone':3,'x':5,'y':6,'color':'#78bbc1','quote':'“양성평등한 육아 문화 확산”은 모든 가족 구성원이 함께 돌보는 일이에요.', 'text':'38세의 생활을 설계해 봐요. 무자녀라면 아래 선택을 이웃·가족 돌봄 참여 방식으로 읽어 주세요. 해당하지 않는 개인의 육아휴직은 사용한 것으로 계산하지 않습니다.', 'cards':[4,5,6], 'after':{'4A':'휴직 분담과 공공 돌봄을 연결했어요. 양성평등 배지를 드려요.','4B':'조부모에게 무리한 돌봄이 몰리지 않는지 확인해요.','4C':'돌봄 쏠림은 구조적인 문제예요. 다시 배울 때 다른 지원을 비교해 봐요.','4D':'유연근무와 직장어린이집을 연결했어요. 양성평등 배지를 드려요.'}},
 {'id':'hr','name':'다솜 인사담당자','zone':3,'x':14,'y':6,'color':'#dda879','quote':'“고비용 자녀 양육 및 교육 문화 개선”도 필요해요.', 'text':'이곳에서는 상담만 받아도 유연근무·직장 돌봄 정보를 얻을 수 있어요. 아래 제도 상담을 누르면 직장 지원 선택지가 열립니다.', 'cards':[5,6], 'after':{'4D':'정책이 종이에만 있지 않고 실제로 쓰일 수 있어야 해요.'}},
 {'id':'granny','name':'정애 80대 할머니','zone':4,'x':11,'y':6,'color':'#ad94cc','quote':'“고령의 자녀가 초고령 부모를 돌보는 등 노인 돌봄 부담이 증가한다.”는 이야기가 남의 일이 아니에요.', 'text':'58세의 당신도 부모를 돌보며 자신의 노후를 준비해야 해요. 가족만으로 버티지 말고 연금·의료·돌봄 서비스와 이웃을 연결해요.', 'cards':[4,7,8], 'after':{'5A':'세대가 함께 살면서도 각자의 사생활과 선택을 존중해요.','5B':'무준비로 홀로 버티기보다 공공 상담과 돌봄 지원에 도움을 청해요.','5C':'시설·실버서비스도 존엄한 선택이에요. 서비스 질과 접근성을 확인해요.'}},
 {'id':'doctor','name':'건우 의사','zone':4,'x':4,'y':6,'color':'#dce7e8','quote':'“영양 상태의 개선”과 “의료 기술의 향상”으로 평균 수명이 높아졌어요.', 'text':'장수는 소중한 성취예요. 건강한 노후와 안정적인 의료·돌봄 체계가 함께 필요해요. 재무·건강·여가·대인관계를 모두 살펴보세요.', 'cards':[3,7,8], 'after':{'5A':'네 영역을 균형 있게 준비했군요. 꾸준히 점검해요.','5B':'노후준비 상담은 지금부터 시작할 수 있어요.'}},
 {'id':'mayor','name':'온유 미래시장','zone':4,'x':20,'y':6,'color':'#78aeda','quote':'“세대 간 이해 증진”과 “고령자 문화·여가 기회 확대”를 함께 실천해요.', 'text':'65세의 엔딩홀입니다. 마을의 변화는 사람을 채점하는 결과가 아니라 선택과 정책의 가상 실험이에요. 가족 친화 문화는 모두의 삶을 존중하는 문화예요.', 'cards':[5,7,9], 'after':{'5C':'돌봄 서비스가 마을의 새로운 일자리와 연결되었어요.'}}
]
QUIZZES = [
 {'q':'수업에서 사용하는 초저출산 기준은 무엇일까요?', 'a':['합계출산율 1.3명 이하입니다.','합계출산율 2명 이상입니다.','고령 인구가 7% 이상입니다.'], 'correct':0,'why':'요청된 교과서 수업 기준은 1.3명 이하입니다. 출산율은 이 수업에서 합계출산율을 뜻합니다.'},
 {'q':'초고령 사회는 65세 이상 인구가 몇 % 이상인 사회일까요?', 'a':['7% 이상입니다.','14% 이상입니다.','20% 이상입니다.'], 'correct':2,'why':'고령화사회 7%, 고령사회 14%, 초고령사회 20%입니다.'},
 {'q':'교과서에서 저출산·고령화의 원인을 크게 나눈 두 축은 무엇일까요?', 'a':['결혼·출산의 기피와 평균 수명의 상승입니다.','영양 악화와 의료 기술 후퇴입니다.','인구피라미드와 노령화지수입니다.'], 'correct':0,'why':'첫 축에는 고용 불안정·가치관 변화·일가정 양립·육아 부담, 둘째 축에는 영양 개선·의료 기술 향상이 포함됩니다.'},
 {'q':'노후준비지원법이 마련된 해와 상담·교육 기관은 무엇일까요?', 'a':['2000년, 통계청입니다.','2015년, 국민연금공단입니다.','2025년, 한국은행입니다.'], 'correct':1,'why':'교과서는 2015년과 국민연금공단을 제시합니다. 재무·건강·여가·대인관계 네 영역을 지원합니다.'},
 {'q':'교과서의 기사에서 2015년 노령화지수는 얼마일까요?', 'a':['14.5%입니다.','18.1%입니다.','95.1%입니다.'], 'correct':2,'why':'2015년 노령화지수는 95.1%입니다. 0~14세 인구 100명당 65세 이상 인구가 95.1명이라는 뜻입니다. 18.1은 기사 속 노년부양비로 다른 지표입니다.'},
 {'q':'교과서의 2016년 기사는 한국이 고령화사회에서 고령사회로 가는 데 몇 년을 예상했나요?', 'a':['18년을 예상했습니다.','72년을 예상했습니다.','115년을 예상했습니다.'], 'correct':0,'why':'기사는 2000년부터 2018년까지 18년을 예상했습니다. “확 늙어버린 대한민국”은 당시 기사 제목이며 현재 통계가 아닙니다.'}
]
def opt(code,label,effects=None,flags=None,**extra):
    return dict(code=code,label=label,effects=effects or {},flags=flags or {},**extra)
CHAPTERS = [
 {'age':15,'title':'CH0 · 중3, 나의 가치관','guide':'teacher','prompt':'어떤 수업 활동으로 미래를 탐색할까요?', 'options':[
 opt('A','가족가치 수업에 집중합니다.',{'happiness':4,'vitality':3},{'informed':True,'family_learning':True}),
 opt('B','비혼·1인가구 생활 영상을 봅니다.',{'happiness':4},{'informed':True,'diversity':True}),
 opt('C','아직 관심을 두지 않습니다.',{}, {'informed':False})]},
 {'age':24,'title':'CH1 · 20대, 진로와 주거','guide':'career','prompt':'20대의 진로와 주거 계획을 고르세요.', 'options':[
 opt('A','청년일자리+지원 주택을 선택합니다.',{'vitality':10,'happiness':7,'care':-3,'housing':30,'income':240,'aging':0.5},{'employed':True,'housing_stable':True,'work_support':True},require='informed',reason='척척박사에게 무료 정책 안내를 받으면 선택할 수 있어요.'),
 opt('B','불안정 알바+고시원에서 시작합니다.',{'vitality':-7,'happiness':-8,'care':6,'housing':55,'income':140,'aging':1},{'employed':True}),
 opt('C','지방취업+정착지원금을 선택합니다.',{'vitality':12,'happiness':5,'care':-2,'housing':25,'income':210,'aging':0.5},{'employed':True,'housing_stable':True,'work_support':True}),
 opt('D','대학교 진학으로 취업을 4년 미룹니다.',{'happiness':3,'vitality':2,'care':3,'housing':45,'income':0,'aging':1},{'college':True},note='24세까지 공부하고 29세 시점에는 취업 기회를 얻습니다.') ]},
 {'age':29,'title':'CH2 · 관계와 일의 선택','guide':'official','prompt':'관계와 일 중 지금의 우선순위를 고르세요.', 'options':[
 opt('A','결혼을 선택합니다.',{'happiness':6,'care':3,'aging':1},{'partner':True,'relationship':'결혼'},bonus='housing'),
 opt('B','동거·사실혼을 선택합니다.',{'happiness':6,'care':3,'aging':1},{'partner':True,'relationship':'동거·사실혼'},bonus='housing'),
 opt('C','비혼·만혼을 선택합니다.',{'happiness':6,'care':-2,'aging':1},{'relationship':'비혼·만혼'}),
 opt('D','취직에 집중해 관계를 나중으로 미룹니다.',{'vitality':6,'happiness':1,'care':3,'income':280,'aging':1},{'employed':True,'relationship':'진로 우선'})]},
 {'age':32,'title':'CH3 · 자녀와 국가의 책임','guide':'director','prompt':'나의 미래 자녀 계획을 고르세요. 어떤 선택도 존중받습니다.', 'options':[
 opt('A','0명을 계획합니다.',{'happiness':3,'care':-4,'aging':3},children=0),
 opt('B','1명을 계획합니다.',{'happiness':3,'care':4,'aging':2},children=1),
 opt('C','2명을 계획합니다.',{'happiness':3,'care':8,'aging':1},children=2),
 opt('D','3명 이상을 계획합니다. (계산은 3명)',{'happiness':3,'care':12,'aging':0},children=3,require='housing_stable',reason='안정 주거가 필요해요. 시청에서 주거·돌봄 안전망 상담을 받으세요.') ]},
 {'age':38,'title':'CH4 · 돌봄을 함께 나누기','guide':'working','prompt':'양육 또는 이웃·가족 돌봄을 어떻게 나눌까요?', 'options':[
 opt('A','육아휴직 분담+국공립어린이집을 활용합니다.',{'vitality':9,'happiness':12,'care':-15,'aging':-1},{'shared_care':True,'leave':True,'nursery':True,'equality':True},require='employed',reason='현재 고용 연결이 필요해요. 인사담당자에게 제도 상담을 받으세요.'),
 opt('B','조부모 도움+부분휴직을 활용합니다.',{'happiness':3,'care':5,'aging':0.5},{'leave':True}),
 opt('C','한 사람이 돌봄을 전담하고 경력이 단절됩니다.',{'vitality':-10,'happiness':-16,'care':19,'aging':1.5},{'solo_care':True}),
 opt('D','직장어린이집+유연근무를 활용합니다.',{'vitality':12,'happiness':10,'care':-13,'aging':-1},{'shared_care':True,'nursery':True,'flex':True,'equality':True},require='work_support',reason='직장 지원 정보가 필요해요. 인사담당자에게 제도 상담을 받으세요.') ]},
 {'age':58,'title':'CH5 · 부모 부양과 나의 노후','guide':'granny','prompt':'네 가지 노후 준비를 점검하고 돌봄 계획을 선택하세요.', 'options':[
 opt('A','세대공유주택+연금·돌봄 준비를 연결합니다.',{'vitality':8,'happiness':10,'care':-18,'aging':-0.5},{'retirement_ready':True},require='checklist',reason='재무·건강·여가·대인관계 네 영역을 먼저 점검하세요.'),
 opt('B','준비 없이 홀로 부모를 부양합니다.',{'vitality':-6,'happiness':-17,'care':22,'aging':2},{'unprepared':True}),
 opt('C','시설·실버서비스를 활용합니다.',{'vitality':10,'happiness':7,'care':-12,'aging':0.5},{'silver_service':True}) ]}
]
CHECKLIST = {'finance':'재무: 연금 가입과 생활비·비상자금을 점검합니다.','health':'건강: 운동·건강검진·의료 이용 계획을 세웁니다.','leisure':'여가: 하고 싶은 활동과 배움의 시간을 정합니다.','social':'대인관계: 가족·친구·이웃과 도움을 주고받습니다.'}
ENDING = {
 'A':{'name':'가족친화 마을 · 연대의 축제','advice':['양성평등한 육아 문화를 확산합니다.','세대 간 이해와 협동을 늘립니다.']},
 'B':{'name':'유지 마을 · 함께 만드는 내일','advice':['청년 일자리와 신혼부부 주거 지원을 확대합니다.','고비용 자녀 양육 및 교육 문화를 개선합니다.']},
 'C':{'name':'초고령 위험 마을 · 닫힌 학교의 편지','advice':['연금·의료·돌봄 등 노후 생활 지원을 확대합니다.','고령 친화 산업과 실버 경제를 육성합니다.']},
 'D':{'name':'고립 위험 마을 · 도움을 청할 권리','advice':['출산·양육에 대한 국가·사회의 책임을 강화합니다.','고령자 문화·여가 기회와 세대 간 이해를 확대합니다.']}
}

```

## storage.py

```python
"""Google Sheets 저장과 로컬 CSV 비상 백업입니다. 인증 키는 브라우저에 보내지 않습니다."""
import csv, json, threading, time, uuid
from pathlib import Path
from datetime import datetime, timezone
from engine import validate_state, score, ending_code
LOCK=threading.RLock()
LOG_HEADERS=['event_id','saved_at','class_code','student_id','nickname','run_id','event','state_json']
RESULT_HEADERS=['event_id','saved_at','class_code','student_id','nickname','run_id','ending','contribution','final_tfr','happiness','care','minutes','quiz_correct']

class Store:
    def __init__(self,config=None,fallback_path='fallback_logs.csv'):
        self.config=dict(config or {});self.path=Path(fallback_path);self.book=None;self.sheets={};self.error='';self.disabled=False
        self.configured=bool(self.config.get('sheet_id') and self.config.get('gcp_service_account'))
    def connect(self):
        if not self.configured:raise RuntimeError('Google Sheets 미설정: 로컬 CSV로 저장합니다.')
        if self.disabled:raise RuntimeError('Google 권한 오류로 재시도를 중지했어요. 서비스계정과 시트 공유를 확인한 뒤 앱을 재시작하세요.')
        if self.book is None:
            import gspread
            from google.oauth2.service_account import Credentials
            creds=Credentials.from_service_account_info(dict(self.config['gcp_service_account']),scopes=['https://www.googleapis.com/auth/spreadsheets'])
            gc=gspread.authorize(creds);gc.set_timeout(12)
            self.book=gc.open_by_key(self.config['sheet_id'])
        return self.book
    def sheet(self,name,headers):
        if name in self.sheets:return self.sheets[name]
        import gspread
        book=self.connect()
        try:ws=book.worksheet(name)
        except gspread.WorksheetNotFound:
            try:ws=book.add_worksheet(title=name,rows=1000,cols=len(headers))
            except gspread.exceptions.APIError:ws=book.worksheet(name)
        existing=ws.row_values(1)
        if not existing:ws.update([headers],range_name='A1',value_input_option='RAW')
        elif existing!=headers:raise ValueError(name+' 시트의 첫 행이 예시와 달라요. 빈 시트를 쓰거나 헤더를 확인하세요.')
        self.sheets[name]=ws
        return ws
    def failure(self,error):
        # 비밀키나 인증 응답 전문을 학생 화면에 내보내지 않습니다.
        text=str(error).lower()
        if any(t in text for t in ('401','403','permission','insufficient_scope','invalid_grant','forbidden')):
            self.disabled=True;self.error='Google 인증·권한 오류입니다. 서비스계정 키와 시트 편집자 공유를 교사가 확인해야 합니다.'
        elif not self.configured:self.error='Google Sheets가 설정되지 않아 로컬 백업 모드로 동작합니다.'
        else:self.error='Google Sheets 저장·조회에 실패했어요. 네트워크 또는 시트 설정을 확인해 주세요.'
    def read_fallback(self):
        if not self.path.exists():return []
        with LOCK,self.path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
    def append_fallback(self,row):
        with LOCK:
            exists=self.path.exists() and self.path.stat().st_size>0
            self.path.parent.mkdir(parents=True,exist_ok=True)
            with self.path.open('a',encoding='utf-8',newline='') as f:
                writer=csv.writer(f)
                if not exists:writer.writerow(LOG_HEADERS)
                writer.writerow(row)
    def make_log(self,state,event):
        return [str(uuid.uuid4()),datetime.now(timezone.utc).isoformat(),state['class_code'],state['student_id'],state['nickname'],state['run_id'],event,json.dumps(state,ensure_ascii=False,separators=(',',':'))]
    def result_row(self,record):
        s=json.loads(record['state_json']);d,t=score(s)
        return [record['event_id'],record['saved_at'],s['class_code'],s['student_id'],s['nickname'],s['run_id'],ending_code(s),d,t,s['stats']['happiness'],s['stats']['care'],round((s.get('ended_at',s['start_time'])-s['start_time'])/60,1),sum(bool(q.get('correct')) for q in s['quizzes'].values())]
    def save(self,state,event='자동저장'):
        row=self.make_log(state,event);record=dict(zip(LOG_HEADERS,row))
        try:
            self.sheet('logs',LOG_HEADERS).append_row(row,value_input_option='RAW')
            if state['finished']:self.sheet('results',RESULT_HEADERS).append_row(self.result_row(record),value_input_option='RAW')
            self.error='';return 'Google Sheets에 저장했어요.'
        except Exception as e:
            self.failure(e)
            try:self.append_fallback(row);return self.error+' fallback_logs.csv 백업을 완료했어요.'
            except Exception:return self.error+' 로컬 파일 쓰기도 실패했어요. 반드시 개인 저장파일을 내려받아 주세요.'
    def logs(self):
        remote=[]
        try:remote=self.sheet('logs',LOG_HEADERS).get_all_records(numericise_ignore=['all']);self.error=''
        except Exception as e:self.failure(e)
        local=self.read_fallback()
        records={r['event_id']:r for r in remote+local if r.get('event_id')}
        return sorted(records.values(),key=lambda r:r['saved_at'])
    def latest(self,student_id,class_code):
        rows=[r for r in self.logs() if str(r['student_id'])==student_id and str(r['class_code'])==class_code]
        if not rows:return None
        return validate_state(json.loads(rows[-1]['state_json']))
    def results(self):
        # logs를 대신 평균내지 않고 results 시트와 미전송 엔딩 백업만 합칩니다.
        remote=[]
        try:remote=self.sheet('results',RESULT_HEADERS).get_all_records(numericise_ignore=['all']);self.error=''
        except Exception as e:self.failure(e)
        local=[]
        for r in self.read_fallback():
            try:
                if json.loads(r['state_json']).get('finished'):local.append(dict(zip(RESULT_HEADERS,self.result_row(r))))
            except (ValueError,KeyError,TypeError):continue
        # 재저장·동기화로 같은 학생이 중복 집계되지 않도록 학생별 최신 엔딩을 택합니다.
        latest={}
        for r in sorted(remote+local,key=lambda r:r.get('saved_at','')):latest[(r['class_code'],r['student_id'])]=r
        return list(latest.values())
    def sync(self):
        """교사가 명시적으로 실행합니다. 성공한 로컬 행도 감사용으로 보존합니다."""
        rows=self.read_fallback()
        if not rows:return 0
        try:
            logs=self.sheet('logs',LOG_HEADERS);results=self.sheet('results',RESULT_HEADERS)
            ids=set(logs.col_values(1)[1:]);rids=set(results.col_values(1)[1:]);count=0
            for r in rows:
                if r['event_id'] not in ids:
                    logs.append_row([r[h] for h in LOG_HEADERS],value_input_option='RAW');ids.add(r['event_id']);count+=1
                if json.loads(r['state_json']).get('finished') and r['event_id'] not in rids:
                    results.append_row(self.result_row(r),value_input_option='RAW');rids.add(r['event_id'])
            self.error='';return count
        except Exception as e:self.failure(e);raise RuntimeError(self.error) from None

```

## component/__init__.py

```python
"""빌드 도구 없이 동작하는 양방향 Streamlit 게임 컴포넌트입니다."""
from pathlib import Path
import streamlit.components.v1 as components
_game=components.declare_component('future_village',path=str(Path(__file__).parent/'frontend'))
def game(data,key='future_village'):
    return _game(data=data,key=key,default=None)

```

## component/frontend/index.html

```html
<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>미래마을 생애설계 어드벤처</title><link rel="stylesheet" href="style.css"></head>
<body><main id="game">
<header><div><span class="tag">미래마을 생애설계 어드벤처</span><h1 id="place">마을을 불러오고 있어요.</h1></div><div id="age"></div></header>
<div id="hud" aria-label="마을의 현재 지표"></div>
<div class="quest"><strong id="objective"></strong><span id="badges"></span></div>
<div id="stage" tabindex="0" aria-label="방향키로 이동합니다. NPC 바로 옆에서 Enter로 말을 겁니다.">
<canvas id="world" width="768" height="480" aria-label="24×15 타일 미래마을 지도"></canvas>
<div id="maplabel"></div><div id="hint" aria-live="polite"></div>
<div id="modal" class="hidden" role="dialog" aria-modal="true" aria-labelledby="dialogtitle"><section id="dialog"></section></div>
</div>
<div id="controls"><div class="pad" aria-label="이동 방향 버튼">
<button data-dir="up" class="up" aria-label="위로 이동합니다.">▲</button><button data-dir="left" class="left" aria-label="왼쪽으로 이동합니다.">◀</button><button data-dir="down" class="down" aria-label="아래로 이동합니다.">▼</button><button data-dir="right" class="right" aria-label="오른쪽으로 이동합니다.">▶</button>
</div><div class="actions"><button id="talk" class="primary">말걸기 · Enter</button><button id="book">지식 도감</button><button id="policy">정책카드</button><button id="save">저장합니다.</button><button id="sound">소리를 켭니다.</button><button id="full">화면을 확대합니다.</button></div></div>
<footer id="status" aria-live="polite">방향키 또는 화면의 방향버튼으로 움직여요. 빛나는 포탈에 들어가면 다른 구역으로 이동해요.</footer>
</main><script src="game.js"></script></body></html>

```

## component/frontend/style.css

```css
:root{color-scheme:dark;--bg:#101923;--panel:#1b2937;--line:#4a6072;--fg:#f0f5ed;--accent:#b9e695}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.55 Pretendard,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}button{font:inherit;color:inherit;background:#26394a;border:1px solid #60768a;border-radius:5px;cursor:pointer;min-height:42px;padding:7px 12px;touch-action:manipulation}button:hover{background:#3a5266}button:focus-visible,input:focus-visible{outline:3px solid #ffe6a3;outline-offset:2px}button:disabled{opacity:.48;cursor:not-allowed}.primary{background:#426647;border-color:#b9e695}#game{max-width:1000px;margin:auto;padding:10px}header{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #869a80;margin-bottom:8px}.tag{font-size:11px;color:#b9c8ba;letter-spacing:1px}h1{font-size:20px;margin:0 0 6px}#age{font-size:20px;color:#f8df94;font-weight:700}#hud{display:grid;grid-template-columns:repeat(7,1fr);gap:6px}.metric{border:1px solid var(--line);padding:7px;background:var(--panel)}.metric span{display:block;font-size:11px;color:#c3cfda}.metric b{font-size:19px;font-variant-numeric:tabular-nums}.track{height:5px;background:#42505a;margin-top:3px}.fill{height:100%;background:#abd28d}.fill.danger{background:#e7ac84}.quest{padding:7px 0;font-size:12px;min-height:45px}.quest strong{display:block;color:#ffdf8f}#badges{color:#b8d2c9}#stage{position:relative;border:3px solid #9fac88;isolation:isolate}canvas{display:block;width:100%;height:auto;image-rendering:pixelated;touch-action:none}#maplabel{position:absolute;top:8px;left:8px;background:#172333ed;border:1px solid #6d8b80;padding:4px 9px;font-size:11px;pointer-events:none}#hint{position:absolute;bottom:7px;left:50%;transform:translateX(-50%);background:#111d2fee;padding:4px 10px;max-width:95%;text-align:center;font-size:12px;pointer-events:none}#controls{display:flex;justify-content:space-between;gap:15px;padding-top:10px;align-items:center}.pad{display:grid;grid-template-columns:44px 44px 44px;grid-template-rows:40px 40px;gap:4px;flex-shrink:0}.pad button{padding:0;min-height:40px;touch-action:none}.up{grid-column:2}.left{grid-column:1;grid-row:2}.down{grid-column:2;grid-row:2}.right{grid-column:3;grid-row:2}.actions{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}footer{color:#b6c4d0;font-size:11px;margin:8px 0}.hidden{display:none!important}#modal{position:absolute;inset:0;background:#07101bdc;display:flex;align-items:flex-end;z-index:5;padding:12px}#dialog{width:100%;max-height:100%;overflow:auto;background:#172634;border:2px solid #d9d5ad;padding:14px;overscroll-behavior:contain}#dialog h2{font-size:18px;color:#ffdf8f;margin:0 0 8px}#dialog p{margin:6px 0 10px}#dialog .close{float:right;margin-left:10px;font-size:12px;min-height:32px;padding:3px 9px}.dialog-actions{display:flex;flex-direction:column;gap:7px;clear:both;margin-top:10px}.choice{text-align:left}.choice small{display:block;color:#c8d2df;font-size:11px;line-height:1.6}.feedback{border-left:3px solid #b9e695;padding:6px 10px;color:#d4edc6}.card{border:1px solid #607080;margin:8px 0;padding:9px}details{border-top:1px solid #425567;padding:8px 0}summary{cursor:pointer;color:#b9dcfa}.checkrow{display:flex;align-items:flex-start;gap:8px;margin:12px 0}.checkrow input{width:20px;height:20px;flex-shrink:0}.bigscore{font-size:clamp(20px,3vw,30px);color:#ffe7a1;font-weight:bold}.comparison{border:1px solid #698075;padding:10px;margin:12px 0}.bar{height:14px;background:#a9d496;margin:3px 0 7px}.bar.baseline{background:#8093a7}.ending-letter{border-top:1px solid #536471;margin-top:12px;padding-top:10px}.pyramid{display:grid;grid-template-columns:1fr 55px 1fr;gap:7px;align-items:center}.pyramid .men{background:#7fabc9;justify-self:end;height:18px}.pyramid .women{background:#bed5e6;height:18px}.pyramid .label{text-align:center;font-size:11px}#game:fullscreen{overflow:auto;background:var(--bg);max-width:none;padding:12px}#game:fullscreen #stage{max-width:1000px;margin:auto}#game:fullscreen #hud,#game:fullscreen #controls{max-width:1000px;margin:auto}@media(max-width:600px){#game{padding:3px}h1{font-size:15px}.tag{font-size:9px}#hud{grid-template-columns:repeat(4,1fr);gap:3px}.metric{padding:3px 5px}.metric b{font-size:16px}.metric span{font-size:10px}.actions button{padding:4px 8px;font-size:12px;min-height:36px}#controls{gap:6px}#modal{padding:4px}#dialog{padding:9px;font-size:12px}#dialog h2{font-size:15px}.quest{font-size:11px}#maplabel{font-size:9px}#hint{font-size:10px;white-space:nowrap}#dialog button{min-height:38px}}

```

## component/frontend/game.js

```javascript
/* 외부 이미지·라이브러리 없이 그리는 원본 픽셀 마을입니다. */
'use strict';
let data=null, state=null, position={x:5,y:9}, revision=-1, pending=false, modalOpen=false;
let direction='down', lastMove=0, moved=false, lastSave=Date.now(), sound=false, audio=null;
let pendingSince=0, visual={x:5,y:9}, previousZone=-1;
const $=id=>document.getElementById(id);
const canvas=$('world'),ctx=canvas.getContext('2d');
ctx.imageSmoothingEnabled=false;
const keys=new Set();
const text=(tag,content,cls)=>{const el=document.createElement(tag);el.textContent=content;if(cls)el.className=cls;return el;};
function post(type,extra={}){window.parent.postMessage({isStreamlitMessage:true,type,...extra},'*');}
function height(){post('streamlit:setFrameHeight',{height:Math.ceil(document.body.scrollHeight+8)});}
function send(kind,extra={}){
  if(!state||pending)return;
  pending=true;pendingSince=Date.now();keys.clear();
  $('status').textContent='선택을 반영하고 저장하고 있어요.';
  post('streamlit:setComponentValue',{value:{id:(crypto.randomUUID?crypto.randomUUID():Date.now()+'-'+Math.random()),kind,x:position.x,y:position.y,...extra},dataType:'json'});
}
function beep(note=440){
  if(!sound)return;
  try{audio=audio||new (window.AudioContext||window.webkitAudioContext)();audio.resume();const o=audio.createOscillator(),g=audio.createGain();o.type='square';o.frequency.value=note;g.gain.value=.025;o.connect(g);g.connect(audio.destination);o.start();g.gain.exponentialRampToValueAtTime(.001,audio.currentTime+.08);o.stop(audio.currentTime+.09);}catch(e){sound=false;}
}
window.addEventListener('message',event=>{
  if(event.source!==window.parent||event.data?.type!=='streamlit:render')return;
  const incoming=event.data.args.data;
  if(!incoming?.state)return;
  data=incoming;
  if(!state||incoming.state.revision!==revision||incoming.state.run_id!==state.run_id){
    state=incoming.state;revision=state.revision;position={x:state.x,y:state.y};
    if(previousZone!==state.zone){visual={...position};previousZone=state.zone;}
    pending=false;moved=false;lastSave=Date.now();
    updateHud();
    if(data.ui)showDialog(data.ui);else closeDialog();
    $('status').textContent=data.save_status||'방향버튼으로 움직여 NPC를 만나 보세요.';
  }
  height();
});
post('streamlit:componentReady',{apiVersion:1});
window.addEventListener('resize',height);
new ResizeObserver(height).observe($('game'));
function currentMap(){return data.maps[state.zone];}
function npcNear(){return data.npcs.find(n=>n.zone===state.zone&&Math.abs(n.x-position.x)+Math.abs(n.y-position.y)<=1);}
function canWalk(x,y){
  if(x<0||x>=24||y<0||y>=15)return false;
  if(currentMap().buildings.some(([bx,by,w,h])=>x>=bx&&x<bx+w&&y>=by&&y<by+h))return false;
  return !data.npcs.some(n=>n.zone===state.zone&&n.x===x&&n.y===y);
}
function move(dir){
  if(!state||pending||modalOpen||state.finished||Date.now()-lastMove<125)return;
  lastMove=Date.now();direction=dir;
  const [dx,dy]={up:[0,-1],down:[0,1],left:[-1,0],right:[1,0]}[dir];
  const x=position.x+dx,y=position.y+dy;
  if(canWalk(x,y)){position={x,y};moved=true;const portal=currentMap().portals.find(p=>p.x===x&&p.y===y);if(portal){beep(660);send('portal');}}
}
function talk(){if(!state||pending)return;if(state.finished){send('ending');return;}const n=npcNear();if(n){beep(520);send('talk',{npc:n.id});}else{$('status').textContent='사람 바로 옆으로 한 칸 더 가까이 가 주세요.';}}
const keyDir={ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right',w:'up',s:'down',a:'left',d:'right'};
window.addEventListener('keydown',e=>{
  if(e.target.matches('input,textarea,select'))return;
  if(modalOpen){if(e.key==='Escape'){e.preventDefault();closeDialog();}if(e.key==='Tab'){const b=[...$('dialog').querySelectorAll('button:not(:disabled),input,summary')];if(b.length){const first=b[0],last=b[b.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}}return;}
  if(keyDir[e.key]){e.preventDefault();keys.add(keyDir[e.key]);move(keyDir[e.key]);}
  if(e.key==='Enter'&&!e.target.matches('button')){e.preventDefault();talk();}
});
window.addEventListener('keyup',e=>keys.delete(keyDir[e.key]));
window.addEventListener('blur',()=>keys.clear());
document.querySelectorAll('[data-dir]').forEach(b=>{
  b.addEventListener('pointerdown',e=>{e.preventDefault();b.setPointerCapture(e.pointerId);keys.add(b.dataset.dir);move(b.dataset.dir);});
  ['pointerup','pointercancel','lostpointercapture'].forEach(type=>b.addEventListener(type,()=>keys.delete(b.dataset.dir)));
});
$('talk').onclick=talk;$('book').onclick=()=>send('book');$('policy').onclick=()=>send('policy');$('save').onclick=()=>send('save');
$('sound').onclick=()=>{sound=!sound;$('sound').textContent=sound?'소리를 끕니다.':'소리를 켭니다.';beep();};
$('full').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await $('game').requestFullscreen();}catch(e){$('status').textContent='이 환경은 전체화면을 지원하지 않아요. 브라우저 확대 기능을 사용해 주세요.';}height();};
function updateHud(){
  const s=state.stats;
  $('place').textContent=currentMap().name;$('age').textContent=state.age+'세';$('objective').textContent=state.objective;
  $('badges').textContent='만난 주민 '+state.visited.length+'/'+data.npcs.length+'명 · 지식 확인 '+Object.values(state.quizzes).filter(q=>q.correct).length+'/6개'+(state.flags.equality?' · 양성평등 배지를 얻었어요.':'');
  $('hud').replaceChildren();
  const rows=[['내 자녀수',s.children+'명',s.children/3],['TFR 기여도',(s.contribution>=0?'+':'')+s.contribution.toFixed(2),(s.contribution+2)/5],['마을출산율',s.village_tfr.toFixed(2),s.village_tfr/3.5],['고령화율',s.aging.toFixed(1)+'%',s.aging/30],['마을활력',s.vitality+'/100',s.vitality/100],['가족행복',s.happiness+'/100',s.happiness/100],['돌봄부담',s.care+'/100',s.care/100]];
  rows.forEach(([label,value,ratio],i)=>{const box=text('div','','metric');box.append(text('span',label),text('b',value));const tr=text('div','','track'),fill=text('div','','fill'+((i===3||i===6)?' danger':''));fill.style.width=Math.max(0,Math.min(100,ratio*100))+'%';tr.append(fill);box.append(tr);$('hud').append(box);});
  $('policy').disabled=!state.flags.policy_offer||state.finished;
  $('policy').textContent=state.flags.policy_card?'정책카드 확인':'정책카드';
  $('maplabel').textContent='방향키 / WASD / 화면 방향버튼 · 빛나는 타일은 포탈입니다.';
}
function closeDialog(){modalOpen=false;$('modal').classList.add('hidden');$('stage').focus({preventScroll:true});height();}
function button(label,handler,cls=''){const b=text('button',label,cls);b.onclick=()=>{beep();handler();};return b;}
function showCards(cards,container){cards.forEach(c=>{const d=document.createElement('details');d.append(text('summary',c.title),text('p',c.text),text('p',c.note));container.append(d);});}
function showDialog(ui){
  modalOpen=true;keys.clear();$('modal').classList.remove('hidden');const box=$('dialog');box.replaceChildren();
  const close=button('닫습니다. · Esc',closeDialog,'close');box.append(close,text('h2',ui.title||'65세, 미래마을의 기록'));
  box.querySelector('h2').id='dialogtitle';
  if(ui.text)box.append(text('p',ui.text));
  (ui.lines||[]).forEach(line=>box.append(text('p',line)));
  if(ui.feedback)box.append(text('p',ui.feedback,'feedback'));
  if(ui.message)box.append(text('p',ui.message,'feedback'));
  const actions=text('div','','dialog-actions');
  if(ui.type==='talk'){
    ui.buttons.forEach(b=>actions.append(button(b.label,()=>send(b.kind,{npc:ui.npc}),'primary')));
    box.append(actions);showCards(ui.cards,box);
  }else if(ui.type==='quiz'){
    ui.answers.forEach((a,i)=>actions.append(button(a,()=>send('answer',{answer:i}),'choice')));box.append(actions);
  }else if(ui.type==='choices'){
    const labels={happiness:'행복',vitality:'활력',care:'돌봄 부담',aging:'고령화율',housing:'월 주거비',income:'월 소득'};
    ui.options.forEach(o=>{
      const b=button(o.code+'. '+o.label,()=>send('choose',{code:o.code}),'choice');b.disabled=o.locked;
      const effects=Object.entries(o.effects).map(([k,v])=>(labels[k]||k)+' '+((k==='housing'||k==='income')?v+'만원':(v>=0?'+':'')+v+(k==='aging'?'%p':''))).join(' · ');
      b.append(text('small',effects));if(o.note)b.append(text('small',o.note));actions.append(b);
      if(o.locked)actions.append(text('small','잠겨 있어요. '+o.reason));
    });box.append(actions,text('p','위 수치는 정책 효과의 실제 추정값이 아닌 게임 밸런스입니다.'));
  }else if(ui.type==='checklist'){
    Object.entries(ui.items).forEach(([key,label])=>{const row=text('label','','checkrow'),input=document.createElement('input');input.type='checkbox';input.value=key;input.checked=ui.checked.includes(key);row.append(input,text('span',label));box.append(row);});
    box.append(button('점검을 저장합니다.',()=>send('check',{checked:[...box.querySelectorAll('input:checked')].map(i=>i.value)}),'primary'));
  }else if(ui.type==='book'){showCards(ui.cards,box);box.append(text('p',data.notice));}
  else if(ui.type==='pyramid'){
    const aged=state.stats.aging,young=Math.max(6,16+(state.stats.village_tfr-1.3)*4),adult=100-aged-young;
    const table=document.createElement('table');table.style.width='100%';table.innerHTML='<caption>가상 인구피라미드: 각 값은 전체 인구 대비 비중입니다.</caption><thead><tr><th>연령</th><th>남성</th><th>여성</th></tr></thead>';
    const grid=text('div','','pyramid');
    [[65+'세 이상',aged],[15+'~64세',adult],['0~14세',young]].forEach(([label,v])=>{const men=text('div','','men'),women=text('div','','women');men.style.width=(v/2)+'%';women.style.width=(v/2)+'%';grid.append(men,text('div',label,'label'),women);const tr=document.createElement('tr');[label,(v/2).toFixed(1)+'%',(v/2).toFixed(1)+'%'].forEach(value=>tr.append(text('td',value)));table.append(tr);});
    box.append(grid,table,text('p','좌측은 남성, 우측은 여성입니다. 모양 설명을 위해 남녀를 같은 비중으로 가정했습니다.'));
  }else if(ui.type==='ending'){
    const e=state.ending_info;if(!e){box.append(text('p','모든 챕터를 마친 뒤 미래시장을 만나세요.'));return;}
    box.append(text('p',e.code+' · '+e.name),text('p',e.message,'bigscore'));
    const chart=text('div','','comparison');chart.append(text('p','전국 기준과 비교합니다. 두 값 모두 수업용이며 전국 기준 1.30은 가정값입니다.'));
    [['전국 비교 기준',1.30,'baseline'],['나의 최종 가상 TFR',e.tfr,'']].forEach(([label,value,cls])=>{chart.append(text('div',label+' '+value.toFixed(2)));const b=text('div','','bar '+cls);b.style.width=Math.min(100,Math.max(0,value)/3.5*100)+'%';chart.append(b);});
    if(e.tfr<0)chart.append(text('p','음수는 고정 계산식의 결과입니다. 실제 합계출산율에는 음수가 없으며 그래프 막대만 0에서 시작합니다. 숫자는 보정하지 않았습니다.'));
    box.append(chart,text('p','계산: (내 자녀 수 − 1.30) + 보너스합 = 기여도입니다. 최종 가상 TFR은 1.30 + 기여도입니다.'));
    state.bonus_items.forEach(([label,value])=>box.append(text('div',label+' '+(value>=0?'+':'')+value.toFixed(2))));
    if(!state.bonus_items.length)box.append(text('div','적용된 보너스가 없습니다.'));
    box.append(text('p','p.103에서 찾은 마을의 다음 약속','ending-letter'));
    e.advice.forEach(a=>box.append(text('p',a)));
    if(e.code==='C')box.append(text('p','신문 아카이브: “확 늙어버린 대한민국” — 2016.9.7 당시 전망입니다. 현재 뉴스가 아닙니다.'));
    box.append(text('p','이 엔딩은 행복한 가족의 자격이나 개인의 도덕성을 판정하지 않습니다. 무자녀 공동 돌봄도 존중받습니다.'),text('p','게임 아래의 개인 저장파일과 결과 기록을 내려받고 성찰 활동을 해 주세요.'));
  }else if(ui.type==='notice'){
    if(ui.next)box.append(text('p',ui.next,'feedback'));
    box.append(button('마을로 돌아갑니다.',closeDialog,'primary'));
  }
  setTimeout(()=>{const focus=box.querySelector('.dialog-actions button:not(:disabled)')||close;focus.focus({preventScroll:true});height();},20);
}
/* 픽셀 도형은 모두 이 파일에서 직접 만든 것으로 외부 게임 자산을 사용하지 않습니다. */
function rect(x,y,w,h,color){ctx.fillStyle=color;ctx.fillRect(Math.round(x),Math.round(y),w,h);}
function label(s,x,y,color='#18262e',size=11){ctx.font='bold '+size+'px sans-serif';ctx.textAlign='center';ctx.fillStyle=color;ctx.fillText(s,x,y);}
function tree(x,y){rect(x+12,y+15,7,17,'#735b41');rect(x+3,y+5,26,18,'#3e694b');rect(x+7,y,18,25,'#528358');rect(x+10,y+3,10,4,'#78a469');}
function person(x,y,color,elder=false,player=false,phase=0){
  const px=x*32,py=y*32;rect(px+7,py+27,18,4,'#557464');
  const step=player&&moved?Math.sin(phase/80)*2:0;
  rect(px+10,py+21,5,9+Math.round(step),'#364052');rect(px+18,py+21,5,9-Math.round(step),'#364052');
  rect(px+7,py+13,20,12,color);rect(px+5,py+16,4,9,'#e8bf94');rect(px+25,py+16,4,9,'#e8bf94');
  rect(px+10,py+3,15,13,'#edc39e');rect(px+9,py,17,6,elder?'#d6d7d1':'#4c3934');rect(px+9,py+4,3,7,elder?'#d6d7d1':'#4c3934');
  if(direction!=='up'||!player){rect(px+14,py+8,2,2,'#1a242b');rect(px+21,py+8,2,2,'#1a242b');}
  if(player){rect(px+8,py,19,4,'#e0b556');rect(px+6,py+3,22,3,'#f4ce6f');rect(px+12,py+14,9,4,'#eed8a5');}
  if(elder){rect(px+28,py+20,2,12,'#735b41');rect(px+14,py+8,10,1,'#596471');}
}
function building(b,index){
  const [bx,by,w,h,name]=b,x=bx*32,y=by*32,W=w*32,H=h*32;
  const poor=state.flags.birth_decided&&state.stats.village_tfr<1.3;
  const school=name==='미래초등학교';const closed=school&&state.flags.birth_decided&&(state.stats.village_tfr<1||state.ending_info?.code==='C');
  const shop=name.includes('상점')||name.includes('책방')||name.includes('공방');const off=closed||(shop&&poor);
  rect(x+4,y+6,W-4,H,'#50685c');rect(x,y+16,W,H-16,closed?'#8b8c80':'#e6d6b1');
  rect(x-3,y+9,W+6,21,closed?'#65756d':index%2?'#688da0':'#b67f66');rect(x+6,y+3,W-12,13,closed?'#7d8779':index%2?'#83a6b2':'#d69a7d');
  for(let xx=14;xx<W-25;xx+=43){rect(x+xx,y+47,28,27,'#52616a');rect(x+xx+3,y+50,22,21,off?'#303e44':'#d8e8b9');rect(x+xx+13,y+49,3,24,'#667c77');}
  rect(x+W/2-12,y+H-34,24,34,'#55636c');rect(x+W/2-8,y+H-29,16,29,off?'#3b4146':'#93ac9c');
  rect(x+8,y+30,W-16,17,'#f2e9d2');label(closed?'폐교 · 지원을 기다려요.':name,x+W/2,y+43,'#29373d',Math.min(11,W/11));
  if(closed){rect(x+W/2-18,y+H-25,36,5,'#8f6d48');rect(x+8,y+H-10,10,12,'#728950');label('학교 문이 닫혔어요.',x+W/2,y+H+13,'#203637',10);}
  if(shop&&poor)label('영업을 줄였어요.',x+W/2,y+H+13,'#263b3b',10);
}
function draw(ts){
  requestAnimationFrame(draw);
  if(!state)return;
  if(keys.size)move([...keys][0]);
  visual.x+=(position.x-visual.x)*.32;visual.y+=(position.y-visual.y)*.32;
  const map=currentMap();rect(0,0,768,480,map.color);
  for(let y=0;y<15;y++)for(let x=0;x<24;x++){
    const road=(y>=7&&y<=9)||(x>=10&&x<=13&&y>=5)||(y===6);
    if(road){rect(x*32,y*32,32,32,(x+y)%2?'#c0b79a':'#c6bfa4');rect(x*32+3,y*32+28,24,1,'#a6a68c');}
    else if((x*13+y*7)%6===0){rect(x*32+8,y*32+18,2,4,'#bdd19a');rect(x*32+11,y*32+21,3,1,'#668760');}
  }
  [[1,11],[3,12],[7,11],[17,12],[21,11],[23,12],[0,0],[8,1],[16,0]].forEach(([x,y])=>tree(x*32,y*32));
  map.buildings.forEach(building);
  rect(2*32,10*32,160,30,'#7a654b');rect(2*32+4,10*32+4,152,22,'#ebdfba');label(map.sign,2*32+80,10*32+18,'#293b3d',8);
  for(const p of map.portals){const pulse=Math.floor(ts/450)%2;rect(p.x*32+2,p.y*32+2,28,28,pulse?'#b3d8c5':'#89b8ac');rect(p.x*32+7,p.y*32+7,18,18,'#5e8a8b');label('↔',p.x*32+16,p.y*32+23,'#f0f3ce',18);const lx=Math.max(44,Math.min(724,p.x*32+16));label(p.label,lx,p.y*32-4,'#1a3735',10);}
  const low=state.flags.birth_decided&&state.stats.village_tfr<1.3;
  const elderCount=low?6:2;
  for(let i=0;i<elderCount;i++){const x=[2,7,15,18,21,5][i],y=[10,12,10,12,10,13][i];person(x,y,['#c4baa6','#a8b9ae','#b5a6c0'][i%3],true,false,ts);}
  for(const n of data.npcs.filter(n=>n.zone===state.zone)){
    person(n.x,n.y,n.color,n.id==='granny');label(n.name,n.x*32+16,n.y*32-6,'#192e32',9);
    const current=state.chapter<6&&data.chapters[state.chapter].guide===n.id||state.chapter>=6&&n.id==='mayor';
    if(current){rect(n.x*32+11,n.y*32-27,12,15,'#f5dd7d');label('!',n.x*32+17,n.y*32-15,'#654c35',13);}
  }
  person(visual.x,visual.y,'#698cbd',state.age>=58,true,ts);
  label(state.nickname,visual.x*32+16,visual.y*32-5,'#1a2c34',10);
  if(state.finished&&state.ending_info.code==='A'){
    const colors=['#f3d878','#92c3b0','#d9a5a0'];for(let i=0;i<35;i++){const xx=(i*97)%760,yy=((ts/25+i*29)%420);rect(xx,yy,4,6,colors[i%3]);}
  }
  const n=npcNear();$('hint').textContent=n?'['+n.name+'] 옆이에요. 말걸기 버튼을 누르세요.':'현재 위치 '+position.x+', '+position.y+' · 노란 ! 표시가 이번 챕터 안내자예요.';
  $('talk').disabled=pending||(!n&&!state.finished);
  if(moved&&!pending&&!modalOpen&&Date.now()-lastSave>25000)send('save');
  if(pending&&Date.now()-pendingSince>20000)$('status').textContent='저장이 지연되고 있어요. 잠시 기다리거나 아래의 개인 저장파일을 내려받아 주세요. 새로고침 전에는 저장 여부를 확인하세요.';
}
requestAnimationFrame(draw);

```

## requirements.txt

```text
streamlit>=1.41,<2
gspread>=6.1,<7
google-auth>=2.36,<3
pandas>=2.2,<3

```

## .streamlit/secrets.toml.example

```toml
# 이 파일을 secrets.toml로 복사하고 실제 값은 GitHub에 올리지 마세요.
sheet_id = "구글시트_URL의_d와_edit_사이에_있는_ID"
teacher_password = "교사용_충분히_긴_무작위_비밀번호로_교체"
[gcp_service_account]
type = "service_account"
project_id = "프로젝트_ID"
private_key_id = "키_ID"
private_key = """-----BEGIN PRIVATE KEY-----
여기에_JSON_키의_private_key_내용을_넣으세요
-----END PRIVATE KEY-----
"""
client_email = "서비스계정@프로젝트_ID.iam.gserviceaccount.com"
client_id = "클라이언트_ID"
token_uri = "https://oauth2.googleapis.com/token"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"

```

## .streamlit/config.toml

```toml
[theme]
base = "dark"
primaryColor = "#8fdcb1"
backgroundColor = "#101923"
secondaryBackgroundColor = "#1b2937"
textColor = "#f0f5ed"
[server]
maxUploadSize = 2

```

## .gitignore

```text
.streamlit/secrets.toml
.env
__pycache__/
*.py[cod]
.venv/
fallback_logs.csv
fallback_logs.csv.*
*.local.json
.DS_Store

```

## tests/test_engine.py

```python
"""실행: python -m unittest discover -s tests -v"""
import copy, itertools, unittest
from engine import *
from content import CHAPTERS, QUIZZES
class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=new_state('0301','3-1','새봄','1234')
    def make(self):return copy.deepcopy(self.base)
    def ready(self,s):
        s['flags'].update(informed=True,housing_stable=True,employed=True,work_support=True)
        s['checklist']=list(CHECKLIST)
        for i in range(6):s['quizzes'][str(i)]={'correct':True,'attempts':1}
    def test_all_2304_paths(self):
        count=0;endings=set()
        for codes in itertools.product(*[[o['code'] for o in c['options']] for c in CHAPTERS]):
            s=self.make()
            for code in codes:
                self.ready(s);apply_choice(s,code)
            self.assertEqual(s['chapter'],6);self.assertEqual(s['age'],65)
            d,t=score(s);self.assertAlmostEqual(t,s['stats']['children']+sum(v for _,v in bonuses(s)),places=2)
            self.assertTrue(all(0<=s['stats'][k]<=100 for k in ('vitality','happiness','care','aging')))
            endings.add(ending_code(s));count+=1
        self.assertEqual(count,2304);self.assertEqual(endings,set('ABCD'))
    def test_thresholds_and_precedence(self):
        s=self.make();s['flags']['informed']=True
        for child,expected in [(0,'C'),(1,'B'),(2,'A'),(3,'A')]:s['stats']['children']=child;self.assertEqual(ending_code(s),expected)
        s['stats']['aging']=20;self.assertEqual(ending_code(s),'C')
        s['stats']['happiness']=30;self.assertEqual(ending_code(s),'D')
        s['stats']['happiness']=50;s['stats']['care']=80;self.assertEqual(ending_code(s),'D')
    def test_bonus_fixed(self):
        s=self.make();s['stats']['children']=2;s['flags'].update(informed=True,shared_care=True,leave=True,nursery=True,flex=True,family_learning=True)
        self.assertEqual(score(s),(1.0,2.3))
        s['flags'].update(informed=False,solo_care=True,unprepared=True)
        self.assertEqual(score(s),(.75,2.05))
    def test_negative_not_clipped(self):
        s=self.make();s['flags'].update(solo_care=True,unprepared=True)
        self.assertEqual(score(s),(-1.55,-.25))
    def test_locks(self):
        s=self.make();s['chapter']=1;s['quizzes']['1']={'correct':True}
        with self.assertRaises(ValueError):apply_choice(s,'A')
        s['flags']['informed']=True;apply_choice(s,'A')
        s['chapter']=3;s['flags']['housing_stable']=False;s['quizzes']['3']={'correct':True}
        with self.assertRaises(ValueError):apply_choice(s,'D')
        s['chapter']=4;s['flags']['work_support']=False;s['quizzes']['4']={'correct':True}
        with self.assertRaises(ValueError):apply_choice(s,'D')
        s['chapter']=5;s['quizzes']['5']={'correct':True}
        with self.assertRaises(ValueError):apply_choice(s,'A')
    def test_quiz_and_proximity(self):
        s=self.make();s['x']=5;s['y']=7
        s,ui=handle(s,{'kind':'quest'});self.assertEqual(ui['type'],'quiz')
        s,ui=handle(s,{'kind':'answer','answer':1});self.assertFalse(s['quizzes']['0']['correct'])
        s,ui=handle(s,{'kind':'answer','answer':0});self.assertEqual(ui['type'],'choices')
        s,ui=handle(s,{'kind':'choose','code':'B'});self.assertEqual(s['chapter'],1)
        with self.assertRaises(ValueError):handle(s,{'kind':'choose','code':'A'})
    def test_portals_and_buildings(self):
        s=self.make();s['x']=22;s['y']=8
        s,_=handle(s,{'kind':'portal'});self.assertEqual((s['zone'],s['x'],s['y']),(1,1,8))
        for zone,m in enumerate(MAPS):
            for bx,by,w,h,_ in m['buildings']:self.assertFalse(walkable(zone,bx,by))
            for p in m['portals']:self.assertTrue(walkable(p['to'],p['tx'],p['ty']))
            for n in [n for n in NPCS if n['zone']==zone]:self.assertTrue(reachable(zone,(1,8),(n['x'],n['y']+1)))
    def test_policy_idempotent(self):
        s=self.make();s['flags'].update(policy_offer=True,birth_decided=True)
        s,_=handle(s,{'kind':'policy'});stats=copy.deepcopy(s['stats']);s,_=handle(s,{'kind':'policy'});self.assertEqual(s['stats'],stats)
    def test_checklist_and_finish(self):
        s=self.make();self.ready(s)
        for code in 'ACAADA':apply_choice(s,code)
        s.update(zone=4,x=20,y=7)
        s,ui=handle(s,{'kind':'finish'});self.assertTrue(s['finished']);self.assertEqual(ui['type'],'ending')
        self.assertNotIn('_pin_hash',public_state(s));self.assertIn('ending_info',public_state(s))
    def test_save_validation_pin(self):
        s=self.make();self.assertTrue(verify_pin(s,'1234'));self.assertFalse(verify_pin(s,'9999'));validate_state(s)
        s['stats']['care']=float('nan')
        with self.assertRaises(ValueError):validate_state(s)
    def test_no_child_no_personal_parental_bonus(self):
        s=self.make();self.ready(s);s['chapter']=4;apply_choice(s,'A')
        self.assertTrue(s['flags']['shared_care']);self.assertFalse(s['flags'].get('leave'));self.assertFalse(s['flags'].get('nursery'))
    def test_all_quiz_keys(self):
        self.assertEqual(len(QUIZZES),6)
        for q in QUIZZES:self.assertTrue(0<=q['correct']<len(q['a']))
if __name__=='__main__':unittest.main()

```

## tests/test_storage.py

```python
import copy, json, tempfile, unittest
from pathlib import Path
from engine import new_state
from storage import Store, LOG_HEADERS, RESULT_HEADERS
class FakeWorksheet:
    def __init__(self,headers):self.headers=headers;self.rows=[]
    def append_row(self,row,**kwargs):self.rows.append(list(row))
    def get_all_records(self,**kwargs):return [dict(zip(self.headers,r)) for r in self.rows]
    def col_values(self,index):return [self.headers[index-1]]+[r[index-1] for r in self.rows]
class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Store(fallback_path=Path(self.tmp.name)/'fallback_logs.csv');self.s=new_state('001','3-1','별명','1234')
    def tearDown(self):self.tmp.cleanup()
    def test_offline_roundtrip_latest_and_class(self):
        self.assertIn('백업',self.store.save(self.s));self.s['chapter']=1;self.store.save(self.s)
        result=self.store.latest('001','3-1');self.assertEqual(result['chapter'],1);self.assertEqual(result['student_id'],'001');self.assertIsNone(self.store.latest('001','3-2'))
    def test_results_latest_only(self):
        self.s['finished']=True;self.s['ended_at']=self.s['start_time']+600;self.store.save(self.s)
        self.s['stats']['children']=2;self.store.save(self.s)
        rows=self.store.results();self.assertEqual(len(rows),1);self.assertAlmostEqual(float(rows[0]['final_tfr']),1.95)
    def test_sync_idempotent(self):
        self.s['finished']=True;self.store.save(self.s)
        sheets={'logs':FakeWorksheet(LOG_HEADERS),'results':FakeWorksheet(RESULT_HEADERS)}
        self.store.sheet=lambda name,headers:sheets[name]
        self.assertEqual(self.store.sync(),1);self.assertEqual(self.store.sync(),0)
        self.assertEqual(len(sheets['logs'].rows),1);self.assertEqual(len(sheets['results'].rows),1)
    def test_partial_write_repaired(self):
        sheets={'logs':FakeWorksheet(LOG_HEADERS),'results':FakeWorksheet(RESULT_HEADERS)}
        def failed(row,**kwargs):raise RuntimeError('일시적인 쓰기 실패')
        sheets['results'].append_row=failed;self.store.sheet=lambda name,headers:sheets[name]
        self.s['finished']=True;self.store.save(self.s)
        self.assertEqual(len(sheets['logs'].rows),1);self.assertTrue(self.store.path.exists())
        sheets['results']=FakeWorksheet(RESULT_HEADERS);self.store.sync()
        self.assertEqual(len(sheets['logs'].rows),1);self.assertEqual(len(sheets['results'].rows),1)
    def test_auth_error_stops_connection_retry(self):
        self.store.failure(RuntimeError('403 permission denied'));self.assertTrue(self.store.disabled)
if __name__=='__main__':unittest.main()

```

## tests/test_journey.py

```python
"""실제 프론트엔드가 보내는 요청 형태로 4개 엔딩 경로를 통합 검사합니다."""
import copy, unittest
from collections import deque
from engine import new_state,handle,NPC,MAPS,CHAPTERS,QUIZZES,CHECKLIST
class JourneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=new_state('001','3-1','모험가','1234')
    def event(self,s,kind,**kwargs):return handle(s,{'kind':kind,**kwargs})[0]
    def travel(self,s,zone):
        todo=deque([(s['zone'],[])]);seen={s['zone']};route=None
        while todo:
            here,path=todo.popleft()
            if here==zone:route=path;break
            for portal in MAPS[here]['portals']:
                if portal['to'] not in seen:seen.add(portal['to']);todo.append((portal['to'],path+[portal]))
        self.assertIsNotNone(route)
        for portal in route:s=self.event(s,'portal',x=portal['x'],y=portal['y'])
        return s
    def approach(self,s,nid):
        n=NPC[nid];s=self.travel(s,n['zone']);return self.event(s,'talk',npc=nid,x=n['x'],y=n['y']+1)
    def run_path(self,path,policy):
        s=copy.deepcopy(self.base)
        for ch,code in enumerate(path):
            guide=CHAPTERS[ch]['guide'];s=self.approach(s,guide)
            s,ui=handle(s,{'kind':'quest'});self.assertEqual(ui['type'],'quiz')
            s,ui=handle(s,{'kind':'answer','answer':QUIZZES[ch]['correct']});self.assertEqual(ui['type'],'choices')
            if ch==5 and code=='A':s=self.event(s,'check',checked=list(CHECKLIST))
            s,ui=handle(s,{'kind':'choose','code':code});self.assertEqual(ui['type'],'notice')
            if ch==3 and policy:s=self.event(s,'policy')
        s=self.approach(s,'mayor');s=self.event(s,'finish')
        self.assertTrue(s['finished']);return s['ending']
    def test_four_full_journeys(self):
        for path,policy,expected in [('ACACDA',True,'A'),('ACCBDA',True,'B'),('BCCADA',True,'C'),('CBDCCB',False,'D')]:
            with self.subTest(path=path):self.assertEqual(self.run_path(path,policy),expected)
    def test_counseling_recovery(self):
        s=copy.deepcopy(self.base);s=self.approach(s,'scholar');s=self.event(s,'learn');self.assertTrue(s['flags']['informed'])
        s=self.approach(s,'official');s=self.event(s,'housing_help');self.assertTrue(s['flags']['housing_stable'])
        s=self.approach(s,'hr');s=self.event(s,'work_help');self.assertTrue(s['flags']['work_support']);self.assertTrue(s['flags']['employed'])
if __name__=='__main__':unittest.main()

```

## tests/frontend_smoke.cjs

```javascript
/* Node 내장 기능만 사용합니다. 실제 브라우저 렌더링 검사를 대신하지 않습니다. */
const fs=require('fs'),vm=require('vm'),assert=require('assert');
class Element {
  constructor(tag='div'){this.tag=tag;this.children=[];this.style={};this.dataset={};this.disabled=false;this.className='';this.value='';this.checked=false;this.classList={add(){},remove(){}};}
  append(...items){this.children.push(...items);}
  replaceChildren(...items){this.children=[...items];}
  addEventListener(){}
  focus(){}
  setPointerCapture(){}
  matches(){return false;}
  querySelector(selector){if(selector==='h2')return this.children.find(x=>x.tag==='h2')||new Element('h2');return new Element('button');}
  querySelectorAll(){return [];}
}
const ids={};['world','game','stage','status','talk','book','policy','save','sound','full','place','age','objective','badges','hud','maplabel','hint','modal','dialog'].forEach(id=>ids[id]=new Element());
ids.world.getContext=()=>({fillRect(){},fillText(){},imageSmoothingEnabled:false});
const listeners={},sent=[],frames=[];
const parent={postMessage(message){sent.push(message);}};
const sandbox={console,Date,Math,crypto:require('crypto').webcrypto,Set,window:{parent,addEventListener(type,fn){listeners[type]=fn;}},document:{getElementById:id=>ids[id],createElement:tag=>new Element(tag),querySelectorAll:()=>[],body:{scrollHeight:900},activeElement:null},ResizeObserver:class{observe(){}},requestAnimationFrame:fn=>frames.push(fn),setTimeout:fn=>fn()};
vm.createContext(sandbox);vm.runInContext(fs.readFileSync('component/frontend/game.js','utf8'),sandbox);
const fixture=JSON.parse(fs.readFileSync(process.argv[2]||'tests/frontend_fixture.json','utf8'));
function render(payload){listeners.message({source:parent,data:{type:'streamlit:render',args:{data:payload}}});}
for(const payload of fixture){render(payload);vm.runInContext('draw(1000)',sandbox);}
assert(sent.some(m=>m.type==='streamlit:componentReady'));
assert(sent.some(m=>m.type==='streamlit:setFrameHeight'));
// 정상 플레이라는 새 fixture로 이동 및 저장 요청을 확인합니다.
const start=fixture[0];start.state.revision=1000;start.ui=null;render(start);
vm.runInContext("move('down');send('save');",sandbox);
assert(sent.some(m=>m.type==='streamlit:setComponentValue'&&m.value.kind==='save'));
console.log('다섯 지도, 모든 대화 유형, 엔딩 A/B/C/D, 이동·저장 프로토콜을 모사 환경에서 검사했습니다.');

```
