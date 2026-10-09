"""Authoritative, deterministic event reducer for the classroom RPG.
Front-end renders and animates; Python alone validates choices and changes state.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
import uuid
from content import EVENTS, REQUIRED, CONCEPTS, STAGES

SCHEMA = 1
LIMITS = {"money":(-6,16), "time":(-6,16), "energy":(-6,16), "bond":(-6,16), "insight":(0,40)}

def new_state(class_code: str, student_id: str, nickname: str, appearance: int = 0) -> dict:
    return {"schema":SCHEMA, "run_id":uuid.uuid4().hex, "revision":0,
            "class_code":class_code,"student_id":student_id,"nickname":nickname,
            "appearance":int(appearance)%6, "stage":0,"age":19,"zone":"square",
            "x":16,"y":13,"flags":{},"decisions":{},"concepts":[],
            "stats":{"money":5,"time":5,"energy":5,"bond":5,"insight":0},
            "journal":[],"nonces":[],"ended":False,"reflection":"",
            "started_at":datetime.now(timezone.utc).isoformat(),"last_update":datetime.now(timezone.utc).isoformat()}

def completed(state:dict)->list[str]:
    return [name for name in REQUIRED[state['stage']] if name in state['decisions']]

def ready(state:dict)->bool:
    return all(name in state['decisions'] for name in REQUIRED[state['stage']])

def learning_coverage(state:dict)->dict[str,bool]:
    seen = set(state.get("concepts",[]))
    return {key: key in seen for key in CONCEPTS}

def recap(state:dict)->dict:
    decisions=state['decisions']; flags=state['flags']
    policy=flags.get('policy','정책 참여 기록 없음')
    ret={k: flags.get(k,"미선택") for k in ("ret_finance","ret_health","ret_leisure","ret_social")}
    return {"career":flags.get('career','미선택'),"housing":flags.get('housing','미선택'),
            "care":flags.get('care','해당 사건에 참여하지 않음'),"policy":policy,
            "retirement":ret,"decisions":len(decisions),"learned":len(state['concepts']),
            "covered":learning_coverage(state),"life":STAGES[state['stage']],
            "message": "한 가지 선택으로 인생이 결정되지 않아요. 개인의 노력과 사회의 지원이 함께 삶을 바꿉니다.",
            "reflection_questions": ["내가 가장 중요하게 여긴 가치는 무엇인가?", "주민의 어려움과 저출산·고령화는 어떻게 연결되는가?", "사회와 나는 앞으로 무엇을 준비할 수 있을까?"]}

def apply(state:dict, message:dict) -> tuple[dict,str]:
    """Return cloned state + user-facing feedback. Unknown/malformed events never mutate."""
    result=deepcopy(state)
    if not isinstance(message,dict):return result,"잘못된 요청입니다."
    nonce = str(message.get('nonce',''))
    if not nonce or len(nonce)>100:return result,"저장 요청 식별자가 없습니다."
    if nonce in result.get('nonces',[]):return result,"이미 반영된 선택입니다."
    kind=message.get('type')
    feedback=""
    if kind=='choose':
        key=message.get('event_id'); option=message.get('choice_id')
        event=EVENTS.get(key)
        if not event or option not in event['choices']:
            return result,"유효하지 않은 선택입니다."
        if (result['ended'] and not event.get('free')) or result['stage'] not in event['stages']:
            return result,"현재 생애 시기에 맞지 않는 사건입니다."
        if key in result['decisions']:
            return result,"이 사건은 이미 경험했습니다."
        data=event['choices'][option]
        for attr,delta in data['effects'].items():
            lo,hi=LIMITS[attr]
            result['stats'][attr]=max(lo,min(hi,result['stats'][attr]+delta))
        result['flags'].update(data['flags'])
        result['decisions'][key]={"option":option,"stage":result['stage'],"label":data['label']}
        result['concepts']=list(dict.fromkeys(result['concepts']+data['concepts']))
        result['journal'].append({"age":result['age'],"event":key,"title":event['title'],"choice":data['label'],"outcome":data['text']})
        feedback=data['text']
    elif kind=='advance':
        if result['ended']:return result,"이미 생애설계를 정리했습니다."
        if not ready(result):return result,"다음 시기로 가기 전에 필요한 사건을 경험해 보세요."
        if result['stage']==2:
            return result,"이제 생애설계 책을 완성할 수 있습니다."
        old_stage=result['stage']
        result['stage']+=1
        result['age']=[19,43,69][result['stage']]
        result['zone']='square' if result['stage']==1 else 'welfare'
        result['x']=16;result['y']=13
        result['journal'].append({"age":result['age'],"event":"transition","title":"시간이 흘렀다", "choice": f"{STAGES[old_stage]}에서 {STAGES[result['stage']]}로", "outcome":"과거 선택의 흔적이 마을에 남았다. 이제 새 계획을 세워 보자."})
        if result['stage']==1:
            result['concepts']=list(dict.fromkeys(result['concepts']+["aging","low_birth"]))
        feedback=f"{STAGES[result['stage']]}에 도착했습니다. 마을과 주민의 변화에 주목해 보세요."
    elif kind=='finish':
        if result['stage']!=2 or not ready(result):
            return result,"노후 준비 네 가지 영역을 모두 경험해야 생애설계 카드를 완성할 수 있습니다."
        result['ended']=True
        result['journal'].append({"age":result['age'],"event":"ending","title":"나의 내일을 잇는 기록","choice":"생애 설계 완성", "outcome":"하나의 정답이 아닌 나만의 계획을 만들었다."})
        feedback="생애설계 기록이 완성됐습니다. 이제 소감문으로 이어가세요."
    elif kind=='reflection':
        value=str(message.get('text',''))[:1500]
        result['reflection']=value
        feedback="소감이 저장되었습니다."
    else:
        return result,"지원하지 않는 요청입니다."
    result['revision']+=1
    result['nonces']=(result.get('nonces',[])+[nonce])[-100:]
    result['last_update']=datetime.now(timezone.utc).isoformat()
    return result,feedback
