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
    if s['flags'].get('classroom_mode'):return True
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
    if not s['flags'].get('classroom_mode') and not s['quizzes'].get(str(ch),{}).get('correct'):raise ValueError('먼저 이번 퀴즈를 풀어 주세요.')
    option=next((o for o in CHAPTERS[ch]['options'] if o['code']==code),None)
    if option is None:raise ValueError('없는 선택지예요.')
    if not allowed(s,option):raise ValueError(option['reason'])
    before=copy.deepcopy(s['stats']); extra=[]
    if s['flags'].get('classroom_mode') and not s['quizzes'].get(str(ch),{}).get('correct'):
        s['flags'].setdefault('concepts_seen',[]).append(ch)
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
        if s['flags'].get('classroom_mode') and not s['flags'].get('policy_card'):
            s['flags']['policy_offer']=True
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
    if s['flags'].get('classroom_mode'):
        response+=' '+LESSONS[ch]
    if ch==3:response+=' '+('학교 유지 불빛이 켜졌어요.' if s['stats']['village_tfr']>=1.0 else '학교의 불빛이 꺼졌어요. 이는 가상 모형의 연출이지 개인에 대한 책임 판정이 아니에요.')
    return dict(type='notice',title='선택이 마을에 반영되었어요.',text=response,lines=extra,next=objective(s))

LESSONS = [
 '가족 친화 문화는 서로 다른 삶과 가족을 존중합니다.',
 '청년의 일자리와 주거 안정은 미래 계획을 세우는 데 도움이 됩니다.',
 '고용 불안과 가치관 변화, 양육 부담이 인구 변화와 연결됩니다.',
 '자녀 계획은 개인의 선택이며 돌봄은 사회가 함께 책임져야 합니다.',
 '일·가정 양립과 양성평등한 돌봄 문화가 부담을 줄입니다.',
 '노후에는 재무·건강·여가·대인 관계를 함께 준비합니다.'
]

def life_card(s):
    chapters={h['chapter']:h['label'] for h in s['history']}
    areas=['재무','건강','여가','대인 관계']
    policies=s['flags'].get('policy_choices',[])
    return {'youth':chapters.get(1,'아직 선택하지 않음'),'balance':chapters.get(4,'아직 선택하지 않음'),
      'relationships':chapters.get(2,'아직 선택하지 않음'),
      'retirement':{name:('점검함' if key in s['checklist'] else '앞으로 준비할 영역') for key,name in zip(CHECKLIST,areas)},
      'values':chapters.get(0,'다양한 삶을 존중하기'),
      'policies':policies,'next_step':'나에게 중요한 영역을 골라 현실적인 첫 걸음을 적어 보세요.',
      'reality':'게임 수치와 인생 선택은 학습용 가정이며 실제 삶의 결과를 예측하지 않습니다.'}

def objective(s):
    if s['finished']:return '엔딩을 확인하고 수업 성찰을 기록하세요.'
    if s['chapter']>=6:return '실버타운의 온유 미래시장에게 말을 걸어 65세 엔딩을 확인하세요.'
    n=NPC[CHAPTERS[s['chapter']]['guide']]
    return f"{s['chapter']+1}/6 · {n['name']} 만나기 ({MAPS[n['zone']]['name']})"

def talk_ui(s,npc_id):
    n=NPC[npc_id]
    lines=[n['quote']] if s['flags'].get('classroom_mode') else [n['quote'],n['text']]
    for h in ([] if s['flags'].get('classroom_mode') else s['history']):
        key=str(h['chapter'])+h['code']
        if key in n['after']:lines.append(n['after'][key])
    buttons=[]
    if s['chapter']<6 and CHAPTERS[s['chapter']]['guide']==npc_id:
        buttons.append({'label':'이야기 선택하기','kind':'quest'})
    if npc_id=='scholar':buttons.append({'label':'무료 정책 안내를 받습니다.','kind':'learn'})
    if npc_id=='hr':buttons.append({'label':'고용·제도 상담을 받습니다.','kind':'work_help'})
    if npc_id=='official':
        buttons += [{'label':'인구피라미드를 봅니다.','kind':'pyramid'}, {'label':'주거·돌봄 안전망을 상담합니다.','kind':'housing_help'}]
    if npc_id in ('granny','doctor'):buttons.append({'label':'노후 준비 4영역을 점검합니다.','kind':'check_open'})
    if npc_id=='mayor' and s['chapter']>=6:buttons.append({'label':'65세 엔딩홀에 입장합니다.','kind':'finish'})
    return dict(type='talk',title=n['name'],npc=npc_id,lines=lines,cards=[] if s['flags'].get('classroom_mode') else [KNOWLEDGE[i] for i in n['cards']],buttons=buttons)

def handle(state,event):
    s=copy.deepcopy(state);kind=event.get('kind');accept_position(s,event);ui=None
    if s['finished'] and kind not in ('save','book','ending','life_card'):
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
    elif kind=='classroom':
        s['flags']['classroom_mode']=True
        s['flags']['informed']=True
        s['flags']['employed']=True
        s['flags']['work_support']=True
        s['flags']['housing_stable']=True
        ui={'type':'notice','title':'20분 수업 모드','text':'필수 퀴즈와 상담 잠금을 생략합니다. 탐험, 인생 선택, 정책과 엔딩은 그대로 경험해요. 퀴즈는 도감에서 선택해 학습할 수 있어요.','next':objective(s)}
    elif kind in ('quest','answer','choose'):
        if s['chapter']>=6:raise ValueError('엔딩홀로 이동해 주세요.')
        guide=CHAPTERS[s['chapter']]['guide']
        if not near(s,guide):raise ValueError('이번 챕터 안내자 옆에서 진행해 주세요.')
        ch=str(s['chapter'])
        if kind=='quest':ui=choices_ui(s) if s['flags'].get('classroom_mode') or s['quizzes'].get(ch,{}).get('correct') else quiz_ui(s)
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
    elif kind=='policy_select':
        if not s['flags'].get('policy_offer'):raise ValueError('먼저 어린이집에서 생애 선택을 완료하세요.')
        options={'housing':('청년 주거 지원',{'vitality':5,'happiness':3}),
                 'flex':('유연근무·양성평등 돌봄',{'care':-7,'happiness':3}),
                 'elder':('고령자 돌봄·세대 교류',{'care':-6,'vitality':4})}
        key=event.get('code')
        if key not in options:raise ValueError('정책을 선택하세요.')
        selected=s['flags'].setdefault('policy_choices',[])
        if key in selected:raise ValueError('이미 실행한 정책입니다.')
        if len(selected)>=2:raise ValueError('마을 예산으로는 두 정책까지만 선택할 수 있어요.')
        selected.append(key);name,effects=options[key];apply_effects(s,effects);s['flags']['informed']=True
        ui={'type':'notice','title':'마을 정책이 바뀌었어요!','text':name+' 정책을 실행했습니다. 한정된 예산 때문에 다른 지원의 우선순위도 함께 고민해 보세요.'}
    elif kind=='policy_menu':
        if not s['flags'].get('policy_offer'):raise ValueError('어린이집 이야기를 먼저 진행하세요.')
        ui={'type':'policy_menu','title':'미래마을 정책 회의','text':'마을 예산으로 세 정책 중 두 개까지 고를 수 있어요. 각 정책에는 혜택과 예산의 한계가 있습니다.', 'selected':s['flags'].get('policy_choices',[])}
    elif kind=='life_card':ui={'type':'life_card','title':'나의 생애설계 카드','card':life_card(s)}
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
    data['objective']=objective(s);data['bonus_items']=bonuses(s);data['life_card']=life_card(s);data['progress']=round(100*s['chapter']/6)
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
