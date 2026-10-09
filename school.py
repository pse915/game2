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

# These spaces are taken from the provided renovation brief, NOT a verified architectural plan.
# Reuse legacy room IDs so saved school_records keep working after the map update.
SPECIAL = {
    'student_space': ('학생자치공간', '학생들의 의견이 학교생활을 어떻게 바꿀 수 있을까요?', 'generations'),
    'resources': ('자료실', '사회 변화에 관한 자료를 찾아보고 출처를 확인해 봐요.', 'low_birth'),
    'health': ('보건실', '건강한 노후를 위해 지금부터 준비할 일을 찾아봐요.', 'ret_health'),
    'support1': ('학습지원실1', '서로 다른 배움의 필요를 존중하는 학교를 떠올려 봐요.', 'generations'),
    'admin_archive': ('행정자료실', '학교의 기록이 어떻게 우리 생활을 돕는지 살펴봐요.', 'policy'),
    'support2': ('학습지원실2', '배움의 속도와 방법은 모두 달라도 괜찮아요.', 'values'),
    'principal': ('교장실', '다양한 학생을 위한 학교 정책을 제안해 봐요.', 'policy'),
    'office': ('행정실', '학교의 공적 지원과 공동체의 역할을 살펴봐요.', 'policy'),
    'lobby': ('중앙현관', '서로를 배려하는 학교 안내와 이동 동선을 살펴봐요.', 'generations'),
    'broadcast': ('방송실', '미래사회 관련 알림을 쉽고 공정하게 전달하려면?', 'low_birth'),
    'staff': ('교육공무직원 공간', '학교를 움직이는 다양한 일과 역할을 찾아봐요.', 'labor'),
    'science_staff': ('과학교과연구실', '의료 기술 발전과 기대수명 증가를 살펴봐요.', 'aging'),
    'science1': ('과학실1', '기대수명 증가와 건강한 삶의 조건을 조사해요.', 'aging'),
    'science2': ('과학실2', '인구 구조 변화를 보여 주는 자료의 연도를 확인해요.', 'aging'),
    'science3': ('과학실3', '의료·돌봄 기술은 삶에 어떤 기회를 줄까요?', 'elder_care'),
    'gym': ('체력단련실', '활기찬 생활을 위한 몸과 마음의 활동을 선택해 봐요.', 'ret_health'),
    'english': ('영어활동실', '다른 나라의 일·생활 균형 지원 사례를 찾아봐요.', 'workcare'),
    'year1_office': ('1학년 교무실', '협업하고 도와주는 학교의 여러 역할을 살펴봐요.', 'generations'),
    'teacher_center': ('교무센터', '학생 지원을 위한 의사소통을 설계해 봐요.', 'policy'),
    'art': ('미술실', '내가 꿈꾸는 미래의 생활 모습을 표현해 봐요.', 'values'),
    'art_staff': ('미술교과연구실', '여가와 자기표현이 삶에 주는 의미를 찾아봐요.', 'ret_leisure'),
    'it_staff': ('정보교과연구실', '다양한 직업과 기술의 변화를 비교해 봐요.', 'labor'),
    'technology': ('기술실', '미래 일자리와 직업 역량을 탐색해 봐요.', 'labor'),
    'homemaking': ('가정실', '가계 예산과 돌봄 시간을 함께 계획해 봐요.', 'workcare'),
    'multi': ('다목적실', '세대 간 협력으로 함께 사용하는 공간을 생각해 봐요.', 'generations'),
    'computer': ('컴퓨터실', '고령화 통계의 조사 연도와 기준을 비교해 봐요.', 'low_birth'),
    'math_support': ('수학교과지원실', '주거비와 월별 저축 목표를 계산해 봐요.', 'ret_finance'),
    'year2_office': ('2학년 교무실', '내 미래를 위한 학교의 지원을 찾아봐요.', 'policy'),
    'career': ('진로상담실', '직업을 정할 때 어떤 가치를 먼저 고려할까요?', 'values'),
    'self_learning': ('자기주도배움터', '나만의 학습·휴식 시간표를 설계해 봐요.', 'workcare'),
    'counsel': ('Wee클래스', '마음 건강과 건강한 대인 관계도 미래 준비예요.', 'ret_social'),
    'music': ('음악실1', '나이가 들어서도 이어 가고 싶은 여가를 생각해 봐요.', 'ret_leisure'),
    'music2': ('음악실2', '함께 음악을 즐기며 세대 간 관계를 맺어 봐요.', 'ret_social'),
    'music_staff': ('음악교과연구실', '평생 즐길 수 있는 예술·여가를 고민해 봐요.', 'ret_leisure'),
    'year3_office': ('3학년 교무실', '각자의 진로를 준비하는 과정에서 필요한 지원을 찾아봐요.', 'policy'),
    'korean_staff': ('국어교과공간', '다른 세대의 이야기를 듣고 글로 표현해 봐요.', 'generations'),
    'korean_library': ('국어도서관', '다양한 가족·세대의 삶을 담은 이야기를 탐색해 봐요.', 'elder_care'),
}
# The left segment is rotated 90° from the learning-support-room-2 corner.
# Room order and precise dimensions remain APPROXIMATE until an actual floor plan is supplied.
ROOM_ORDER = {
    '1': {
        'west': ['support2', 'admin_archive', 'support1', 'health', 'resources', 'student_space'],
        'north': ['principal', 'office', 'lobby', 'broadcast', 'staff', 'science_staff', 'science1', 'science2', 'science3']},
    '2': {
        'west': ['gym', '1-5', '1-4', '1-3', '1-2'],
        'north': ['1-1', 'english', 'year1_office', 'teacher_center', 'art', 'art_staff', 'it_staff', 'technology', 'homemaking']},
    '3': {
        'west': ['multi', 'computer', 'math_support', '2-1', '2-2'],
        'north': ['2-3', '2-4', '2-5', '2-6', 'year2_office', 'career', 'self_learning', 'counsel']},
    '4': {
        'west': ['music', 'music2', 'music_staff', '3-1', '3-2'],
        'north': ['3-3', '3-4', '3-5', '3-6', 'year3_office', 'korean_staff', 'korean_library']},
}
# All coordinates are logical tiles in the original 30x19 canvas.
STAIRS = {'west':[8,17], 'east':[27,10]}
SCHOOL_ENTRY = [15,9]

def hall_walkable(x: int, y: int) -> bool:
    return (6 <= x <= 8 and 8 <= y <= 17) or (7 <= x <= 27 and 8 <= y <= 10)

def build_floors():
    floors={}
    for floor,sides in ROOM_ORDER.items():
        rooms=[]
        for wing, ids in sides.items():
            for index,room_id in enumerate(ids):
                if room_id in TEACHER_MAP:
                    name=f'{room_id} 교실';kind='class'
                else:
                    name=SPECIAL[room_id][0];kind='special'
                door = [7,11+index] if wing=='west' else [10+index*2,8]
                # North wing two-tile spacing provides readable index plaques.
                sign = [5,11+index] if wing=='west' else [door[0],7]
                rooms.append({'id':room_id,'room_id':room_id,'name':name,'display_name':name,
                              'kind':kind,'floor_id':int(floor),'wing':wing,
                              'door':door,'door_position':door,'label_position':sign,
                              'interior_map_id':'school:room:'+room_id})
        floors[floor]=rooms
    return floors

SCHOOL_FLOORS=build_floors()
CLASS_OBJECTS=['teacher','board','bulletin','desk','locker']
SPECIAL_OBJECTS=['board','desk','locker']
OBJECT_LABELS={'teacher':'담임 선생님','board':'칠판','bulletin':'게시판','desk':'책상','locker':'자료함'}
OBJECT_POINTS={'teacher':[14,8],'board':[9,5],'bulletin':[24,5],'desk':[11,12],'locker':[23,12]}

def school_content():
    return {'teachers':TEACHER_MAP, 'floors':SCHOOL_FLOORS,
            'special':{k:{'name':v[0],'prompt':v[1],'concept':v[2]} for k,v in SPECIAL.items()},
            'objects':OBJECT_LABELS,'points':OBJECT_POINTS,
            'stairs':STAIRS,'entry':SCHOOL_ENTRY,
            'layout_status':'교실배치도 미첨부 — ㄱ자형 구조 및 실별 위치는 검증 전 게임용 배치'}

def validate_school_interaction(room: str, obj: str, choice: str):
    allowed_rooms={item['id']:item for rooms in SCHOOL_FLOORS.values() for item in rooms}
    r=allowed_rooms.get(room)
    return bool(r and choice in ('investigate','discuss') and obj in (CLASS_OBJECTS if r['kind']=='class' else SPECIAL_OBJECTS))

def concept_for(room: str):
    return TEACHER_MAP[room]['concept'] if room in TEACHER_MAP else SPECIAL[room][2]
