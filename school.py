"""Source-of-truth school mapping, inspired by the provided renovation brief.
Floor layouts are *gameplay approximations*; a verified floor plan was not uploaded.
All teacher dialogue in the game is fiction, not an actual quotation.
"""
from __future__ import annotations

TEACHERS = [
    ('1-1','백선영','일본어/진로활동','미래에 하고 싶은 일을 떠올릴 때, 무엇을 가장 소중히 여기나요?','values'),
    ('1-2','이원희','기술가정','내 삶의 목표와 주거·시간·비용은 어떻게 연결될까요?','housing'),
    ('1-3','김평강','음악','바쁜 날에도 내가 좋아하는 활동을 이어 갈 방법을 찾아봐요.','ret_leisure'),
    ('1-4','한주희','수학','한 달 예산에서 꼭 필요한 지출과 선택 가능한 지출을 나눠 볼까요?','ret_finance'),
    ('1-5','이상은','과학','오래 살아가는 시대에 건강과 돌봄을 어떻게 준비할까요?','aging'),
    ('2-1','김은숙','한문','오래된 말 속의 배움과 지금의 생활은 어떻게 이어질까요?','generations'),
    ('2-2','권선희','수학','집을 고를 때 임대료뿐 아니라 통학과 이동시간도 계산해요.','housing'),
    ('2-3','이은영','과학','수명이 늘어나면 건강 관리와 의료 접근성이 더욱 중요해져요.','aging'),
    ('2-4','오영제','역사','시대가 바뀌면 가족의 형태와 일하는 방식도 달라질 수 있어요.','values'),
    ('2-5','전혜정','국어','서로 다른 미래를 그린 친구들의 이야기를 존중하며 들어 봐요.','values'),
    ('2-6','한지윤','음악/스포츠','운동과 여가를 일상에 넣으면 어떤 변화가 생길까요?','ret_health'),
    ('3-1','조혜령','국어','서로 다른 세대의 마음을 담은 편지를 써 볼까요?','generations'),
    ('3-2','정은진','영어','다양한 나라에서 일과 돌봄을 지원하는 방법을 찾아봐요.','workcare'),
    ('3-3','장성은','사회/역사','어떤 사회적 조건이 인구와 가족생활의 변화에 영향을 줄까요?','low_birth'),
    ('3-4','이일형','수학','청년기부터 노년기까지 균형 있는 소비 계획을 만들어 봐요.','ret_finance'),
    ('3-5','정은주','사회','청년 지원·돌봄·고령자 복지 가운데 어떤 정책부터 준비할까요?','policy'),
    ('3-6','변지희','도덕','선택이 서로 다르더라도 존중받을 수 있는 사회를 생각해요.','values'),
]
TEACHER_MAP={homeroom:{'homeroom':homeroom,'name':name,'subject':subject,'prompt':prompt,'concept':concept,'sprite_id':f'teacher_{i:02d}'} for i,(homeroom,name,subject,prompt,concept) in enumerate(TEACHERS)}

SPECIAL = {
    'office':('행정실','학교에서 도움이 필요할 때 어디에 문의할지 찾아봐요.','policy'),
    'health':('보건실','건강한 삶을 위해 예방과 휴식을 어떻게 실천할까요?','ret_health'),
    'science1':('과학실 1','수명의 증가가 우리 생활에 미치는 영향을 조사해요.','aging'),
    'science2':('과학실 2','인구구조의 변화와 기술을 연결해 봐요.','aging'),
    'science3':('과학실 3','의료와 돌봄에서 과학기술이 할 수 있는 일을 찾아봐요.','elder_care'),
    'counsel':('상담실','마음 건강과 관계를 돌보는 방법도 미래 준비에 포함돼요.','ret_social'),
    'homemaking':('기술·가정실','가계 예산과 돌봄 시간을 함께 짜 볼까요?','workcare'),
    'computer':('컴퓨터실','사회 문제를 설명하는 통계는 기준 연도와 출처도 중요해요.','low_birth'),
    'music':('음악실','나이가 들어서도 이어갈 여가와 배움이 있어요.','ret_leisure'),
}
SCHOOL_FLOORS={
    '1':[{'id':key,'name':SPECIAL[key][0],'kind':'special'} for key in ['office','health','science1','science2','science3','counsel']],
    '2':[{'id':str(i)+'-'+str(j),'name':str(i)+'-'+str(j)+' 교실','kind':'class'} for i in [1] for j in range(1,6)]+[{'id':'homemaking','name':'기술·가정실','kind':'special'}],
    '3':[{'id':str(i)+'-'+str(j),'name':str(i)+'-'+str(j)+' 교실','kind':'class'} for i in [2] for j in range(1,7)]+[{'id':'computer','name':'컴퓨터실','kind':'special'}],
    '4':[{'id':str(i)+'-'+str(j),'name':str(i)+'-'+str(j)+' 교실','kind':'class'} for i in [3] for j in range(1,7)]+[{'id':'music','name':'음악실','kind':'special'}],
}
CLASS_OBJECTS = ['teacher','board','bulletin','desk','locker']
SPECIAL_OBJECTS = ['board','desk','locker']
OBJECT_LABELS = {'teacher':'담임 선생님','board':'칠판','bulletin':'게시판','desk':'책상','locker':'자료함'}
OBJECT_POINTS = {'teacher':[14,8],'board':[9,5],'bulletin':[24,5],'desk':[11,12],'locker':[23,12]}

def school_content():
    return {'teachers':TEACHER_MAP, 'floors':SCHOOL_FLOORS,
            'special':{k:{'name':v[0],'prompt':v[1],'concept':v[2]} for k,v in SPECIAL.items()},
            'objects':OBJECT_LABELS,'points':OBJECT_POINTS}

def validate_school_interaction(room: str, obj: str, choice: str):
    allowed_rooms={item['id']:item for rooms in SCHOOL_FLOORS.values() for item in rooms}
    r=allowed_rooms.get(room)
    return bool(r and choice in ('investigate','discuss') and obj in (CLASS_OBJECTS if r['kind']=='class' else SPECIAL_OBJECTS))

def concept_for(room: str):
    return TEACHER_MAP[room]['concept'] if room in TEACHER_MAP else SPECIAL[room][2]
