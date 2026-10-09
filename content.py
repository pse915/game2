"""Narrative data for the fictional learning world of Sewol Port.
All numeric balances are *fictional game indicators*, not Korean statistics.
"""

STAGES = ["청년기", "성인기", "노년기"]
CONCEPTS = {
    "low_birth": "저출산: 출생아 수 감소와 출산율 저하",
    "aging": "고령화: 평균 수명 상승과 노인 인구 비율 증가",
    "employment": "소득·고용 불안정과 청년 일자리",
    "housing": "청년 주거 지원과 생활비 부담",
    "values": "결혼·출산에 관한 가치관 변화와 다양한 삶",
    "workcare": "일·가정 양립과 양성평등한 돌봄",
    "education_cost": "양육·교육비 부담과 사회적 책임",
    "labor": "노동력 부족과 지역 경제",
    "elder_care": "고령자의 돌봄 수요와 부담",
    "policy": "가족 친화 문화와 사회적·정책적 대응",
    "ret_finance": "노후 준비: 재무",
    "ret_health": "노후 준비: 건강",
    "ret_leisure": "노후 준비: 여가",
    "ret_social": "노후 준비: 대인 관계",
    "generations": "세대 간 이해·협동과 사회 참여",
}

def C(label, text, effects=None, flags=None, concepts=None):
    return {"label": label, "text": text, "effects": effects or {}, "flags": flags or {}, "concepts": concepts or []}

# Each character has a distinctive role, stage context and place in a connected map.
NPCS = [
    {"id":"seon", "name":"선우", "role":"직업 상담사", "zone":"work", "x":15,"y":11,"skin":0,"hair":1,"outfit":0,"event":"career"},
    {"id":"mira", "name":"미라", "role":"공인중개사", "zone":"home", "x":14,"y":11,"skin":1,"hair":3,"outfit":2,"event":"housing"},
    {"id":"jiho", "name":"지호", "role":"카페 사장", "zone":"shop", "x":14,"y":11,"skin":2,"hair":2,"outfit":1,"event":"shop"},
    {"id":"nari", "name":"나리", "role":"진로를 고민하는 청년", "zone":"square", "x":19,"y":12,"skin":0,"hair":0,"outfit":3,"event":"young"},
    {"id":"yeon", "name":"연주", "role":"돌봄센터 직원", "zone":"welfare", "x":10,"y":11,"skin":1,"hair":4,"outfit":4,"event":"care"},
    {"id":"hyeon", "name":"현서", "role":"야간 근무 노동자", "zone":"work", "x":22,"y":12,"skin":2,"hair":1,"outfit":1,"event":"worklife"},
    {"id":"boram", "name":"보람", "role":"어린이집 원장", "zone":"welfare", "x":21,"y":12,"skin":0,"hair":3,"outfit":5,"event":"nursery"},
    {"id":"dojun", "name":"도준", "role":"시장 상인", "zone":"shop", "x":22,"y":12,"skin":2,"hair":0,"outfit":3,"event":"labor"},
    {"id":"mayor", "name":"하린", "role":"마을 협의회장", "zone":"square", "x":11,"y":11,"skin":1,"hair":2,"outfit":5,"event":"policy"},
    {"id":"grand", "name":"정숙", "role":"은퇴한 목공", "zone":"river", "x":16,"y":11,"skin":0,"hair":5,"outfit":2,"event":"generation"},
    {"id":"bank", "name":"유진", "role":"생활 금융 상담사", "zone":"welfare", "x":15,"y":11,"skin":1,"hair":0,"outfit":0,"event":"ret_finance"},
    {"id":"doctor", "name":"태오", "role":"지역 보건사", "zone":"welfare", "x":16,"y":14,"skin":2,"hair":1,"outfit":4,"event":"ret_health"},
    {"id":"artist", "name":"유리", "role":"동네 예술가", "zone":"river", "x":22,"y":12,"skin":0,"hair":4,"outfit":3,"event":"ret_leisure"},
    {"id":"neighbor", "name":"수아", "role":"마을 활동가", "zone":"square", "x":22,"y":14,"skin":1,"hair":3,"outfit":2,"event":"ret_social"},
    {"id":"garden", "name":"은서", "role":"공동정원 관리자", "zone":"home", "x":21,"y":12,"skin":2,"hair":4,"outfit":3,"event":"garden"},
    {"id":"festival", "name":"시온", "role":"축제 기획자", "zone":"shop", "x":19,"y":13,"skin":0,"hair":2,"outfit":5,"event":"festival"},
]

EVENTS = {
"career": {"stages":[0],"title":"사라진 구인 공고", "intro":"구인 게시판에 여러 장의 공고가 붙어 있다. 선우가 말한다. ‘급여뿐 아니라 근무시간과 안정성을 함께 봐야 해요.’ 당신은 어떤 일의 방식을 택할까?", "choices": {
    "stable":C("안정적인 공공서비스", "규칙적인 시간이 생겼다. 대신 수입은 조금 천천히 늘어난다.",{"money":2,"time":2},{"career":"공공서비스"},["employment"]),
    "flex":C("유연근무 디자인", "내 일정에 맞춰 일할 수 있다. 수입은 프로젝트마다 달라진다.",{"money":1,"time":3},{"career":"디자이너"},["employment"]),
    "venture":C("동네 가게 창업", "손님과 직접 만나며 시작했다. 운영의 불확실성도 함께 배운다.",{"money":1,"bond":2},{"career":"창업가"},["employment","labor"]),
    "service":C("돌봄·지역 서비스", "이웃의 삶을 가까이에서 돕는다. 감정적 노동에도 휴식이 필요하다.",{"money":1,"bond":2},{"career":"지역 돌봄"},["employment","elder_care"]),
}},
"housing": {"stages":[0],"title":"새집을 찾아서", "intro":"전셋값과 생활비를 계산한 미라가 여러 열쇠를 건넨다. ‘넓이가 전부는 아니죠. 거리, 관계, 비용을 함께 보세요.’", "choices":{
    "rent":C("작고 가까운 임대주택", "주거비를 줄이고 출퇴근 시간을 아꼈다.",{"money":2,"time":1},{"housing":"작은 임대주택"},["housing"]),
    "share":C("이웃과 함께 사는 집", "공간을 함께 쓰며 생활 규칙을 조율한다.",{"money":1,"bond":2},{"housing":"공동 주거"},["housing","values"]),
    "house":C("생활 공간이 넉넉한 집", "공간의 자유가 커졌다. 관리비도 함께 늘었다.",{"money":-1,"energy":1},{"housing":"일반 주택"},["housing"]),
}},
"shop": {"stages":[0,1],"title":"카페에 사람이 없다", "intro":"점심시간인데 카페가 한산하다. 지호는 ‘주변 청년이 이사하고, 가게 인력 구하기도 힘들어요’라며 메뉴판을 내려놓는다.","choices":{
    "help":C("잠깐 일손을 돕는다", "차를 나르고 작은 보수를 받았다. 인력 부족이 가게에 미치는 영향을 느꼈다.",{"money":1,"time":-1,"bond":1},{},["labor"]),
    "talk":C("왜 손님이 줄었는지 조사", "주거비와 일자리 문제가 지역 상권에까지 이어진다는 것을 발견했다.",{"insight":2},{},["labor","housing"]),
    "route":C("지역 장터 행사를 제안", "주민들이 새로운 손님을 만날 통로가 생겼다. 그러나 지속적인 일자리 대책도 필요하다.",{"bond":2},{},["labor","policy"]),
}},
"young": {"stages":[0,1],"title":"떠나는 친구의 편지", "intro":"나리가 이력서를 접어 가방에 넣는다. ‘계속 이곳에서 살고 싶은데, 안정적인 일과 집을 구하기가 어려워.’ 마을의 미래를 고민한다.","choices":{
    "job":C("일자리 정보를 함께 찾는다", "구직과 직업 훈련의 문턱을 확인했다.",{"bond":1,"insight":1},{},["employment"]),
    "home":C("함께 살 공간을 알아본다", "살 곳의 비용이 생애 선택에 얼마나 큰 영향을 주는지 이해했다.",{"bond":1,"insight":1},{},["housing","values"]),
    "listen":C("어떤 삶을 원하는지 듣는다", "누군가의 선택을 평가하지 않고, 다양한 삶의 계획을 존중했다.",{"bond":2},{},["values"]),
}},
"care": {"stages":[1],"title":"비어 버린 돌봄 시간표", "intro":"연주가 돌봄센터 현관에 멈춰 있다. 한 주민이 야간 근무를 하게 되었지만 돌봄서비스는 일찍 끝난다. 이웃의 도움이 필요하다.","choices":{
    "share":C("돌봄을 함께 나누는 당번 제안", "돌봄 책임을 한 사람에게 몰아주지 않을 수 있었다.",{"bond":2,"time":-1},{"care":"공동 돌봄"},["workcare","elder_care"]),
    "flex":C("근무시간 조정을 요청", "일하는 방식이 바뀌어 돌봄 공백을 일부 줄였다.",{"time":2},{"care":"근무 조정"},["workcare"]),
    "service":C("공공 돌봄서비스 신청을 돕는다", "돌봄이 개인의 힘만으로 해결될 수 없음을 경험했다.",{"insight":2},{"care":"공공 서비스"},["elder_care","policy"]),
}},
"worklife": {"stages":[1],"title":"불이 켜진 빈 사무실", "intro":"현서의 컴퓨터는 밤에도 켜져 있다. ‘일을 계속할지, 쉬면서 돌봄을 나눌지 고민이야. 어느 쪽도 쉬운 답은 없어.’", "choices":{
    "hours":C("유연근무와 휴식권을 논의", "장시간 노동 문제는 개인의 의지만으로 풀리지 않는다.",{"time":2,"insight":1},{},["workcare","policy"]),
    "equal":C("함께 맡는 돌봄 계획을 짠다", "성별과 관계없이 돌봄 책임을 함께 나누는 방법을 찾았다.",{"bond":2},{},["workcare"]),
    "support":C("근로자 지원제도를 알아본다", "직장 문화와 제도가 일·가정 양립의 기반임을 알게 됐다.",{"insight":2},{},["workcare","policy"]),
}},
"nursery": {"stages":[1],"title":"닫힐지도 모르는 어린이집", "intro":"보람은 텅 빈 교실의 작은 의자들을 정리한다. ‘아이들이 줄어 문을 닫을 위기예요. 동시에 돌봄이 필요한 주민은 여전히 있어요.’", "choices":{
    "together":C("어린이·어르신 교류 공간 제안", "돌봄 공간을 세대 교류로 연결했다. 운영에는 전문 인력이 필요하다.",{"bond":2},{},["low_birth","generations"]),
    "retrain":C("교직원 전환 교육을 알아본다", "직업 재교육이 인구 구조 변화에 적응하는 방법이 될 수 있다.",{"insight":2},{},["low_birth","labor"]),
    "expense":C("가정의 양육비 부담을 조사", "경제적 부담과 돌봄 여건을 함께 고려해야 함을 알게 됐다.",{"insight":2},{},["education_cost","low_birth"]),
}},
"labor": {"stages":[1],"title":"닫힌 빵집의 셔터", "intro":"도준은 아침 일찍 셔터를 올렸지만 도울 사람이 없다. 고령 주민의 경험은 풍부해도 새로운 근무 환경에 적응할 지원이 부족하다.","choices":{
    "retrain":C("세대별 기술 교육을 연결", "숙련과 새로운 기술이 연결되었다.",{"bond":1,"insight":2},{},["labor","generations"]),
    "hire":C("고령 친화 일자리를 제안", "일할 기회를 넓히면서 건강과 근로조건을 살폈다.",{"bond":2},{},["aging","labor"]),
    "rest":C("안전하고 쉬기 좋은 공간 마련", "노동력 확보와 노동자의 건강 모두 중요했다.",{"energy":2},{},["aging","labor"]),
}},
"policy": {"stages":[1],"title":"마을 협의회의 네 가지 예산안", "intro":"하린이 예산 지도를 펼친다. ‘모든 문제를 한 번에 해결할 자원은 없어요. 어느 분야를 먼저 바꿔 볼까요?’ 선택 후 마을에 변화가 생긴다.","choices":{
    "youth":C("청년 주거·일자리 지원", "공실 건물이 공유 주거와 훈련소로 바뀌었다. 예산이 계속 필요하다.",{"insight":2},{"policy":"청년 지원"},["employment","housing","policy"]),
    "balance":C("돌봄·일가정 양립 지원", "보육·돌봄센터에 야간 이용 시간이 생겼다. 종사자도 충분히 쉬어야 한다.",{"bond":2},{"policy":"일·돌봄 지원"},["workcare","education_cost","policy"]),
    "aging":C("고령자 의료·여가·안전 지원", "강가의 쉼터와 돌봄센터가 새단장됐다. 접근성을 계속 살펴야 한다.",{"energy":2},{"policy":"고령자 지원"},["aging","elder_care","policy"]),
    "together":C("세대 협력·공동체 사업", "정기 장터와 세대 모임이 시작됐다. 참여하지 못하는 주민도 배려해야 한다.",{"bond":2},{"policy":"세대 협력"},["generations","policy"]),
}},
"generation": {"stages":[1,2],"free":True,"title":"강가의 낡은 작업대", "intro":"정숙이 오래된 목공 도구를 닦는다. ‘평균 수명이 길어지며 은퇴 후 삶도 길어졌지. 배우고 일하고 만날 기회가 필요해.’", "choices":{
    "teach":C("청소년에게 목공을 가르치도록 연결", "나이와 관계없이 누구나 지식과 경험을 나누는 일원이 되었다.",{"bond":2},{},["aging","generations"]),
    "safe":C("안전한 강변 보행로 개선 제안", "고령 친화 환경은 여러 세대에게도 유익했다.",{"energy":1,"insight":1},{},["aging","elder_care"]),
    "listen":C("은퇴 후 바람을 들어본다", "노년기에도 새로운 관계와 계획을 세울 수 있음을 배웠다.",{"bond":2},{},["aging","generations"]),
}},
"garden": {"stages":[1,2], "free":True, "title":"세대가 함께 가꾸는 작은 정원", "intro":"은서의 정원에는 어린아이용 장갑과 어르신용 의자가 나란히 놓여 있다. 마을의 주민들이 서로 다른 체력과 시간을 갖고 함께 살아갈 방법을 찾아야 한다.", "choices":{
    "layout":C("그늘과 쉬는 자리 만들기", "누구나 편히 머무를 수 있는 정원을 만들었다.",{"energy":1,"bond":1},{},["aging","generations"]),
    "grow":C("정원 활동의 시간을 나눠 운영", "늦게 퇴근하는 주민과 건강을 돌보는 주민 모두 참여할 여지가 생겼다.",{"bond":2},{},["workcare","generations"]),
    "share":C("수확물을 돌봄센터에 나누기", "혼자 해결하기 어려운 돌봄을 이웃과 함께 생각했다.",{"bond":2},{},["elder_care","generations"]),
}},
"festival": {"stages":[1,2], "free":True, "title":"다른 세대가 함께 만드는 축제", "intro":"시온은 청년 상인, 아이들의 보호자, 퇴직한 주민을 모두 초대하고 싶다. 하지만 시간과 이동 문제 때문에 누구에게나 편한 행사장을 만들기 어렵다.","choices":{
    "access":C("낮과 저녁 행사로 나누기", "서로 다른 생활 시간을 가진 주민에게 참여 기회를 넓혔다.",{"bond":2},{},["workcare","generations"]),
    "safe":C("무장애 길과 쉼터부터 준비", "누구든 이동하기 편한 마을 축제에 한 걸음 다가갔다.",{"energy":1,"insight":1},{},["aging","policy"]),
    "teach":C("세대별 기술·이야기 전시 열기", "노인과 청년을 도움만 받거나 주는 존재가 아닌 동등한 협력자로 만났다.",{"bond":2},{},["generations"]),
}},
"ret_finance": {"stages":[2],"title":"노후의 돈, 선택의 여지", "intro":"유진은 노후 계획표를 보여 준다. ‘재무 준비는 자산만 모으는 일이 아니라 제도와 지출을 이해하는 일이기도 해요.’", "choices":{
    "budget":C("월별 지출과 긴급비용 점검", "우선순위를 다시 정하고 예상 못한 지출에 대비했다.",{"money":2},{"ret_finance":"지출 점검"},["ret_finance"]),
    "pension":C("연금·공적 지원 상담", "개인의 저축과 사회적 제도를 함께 살펴보았다.",{"insight":2},{"ret_finance":"제도 상담"},["ret_finance","policy"]),
    "learn":C("새로운 소득 활동 탐색", "노년기에도 건강과 희망에 맞춰 역할을 설계할 수 있다.",{"bond":1,"money":1},{"ret_finance":"새 일 탐색"},["ret_finance"]),
}},
"ret_health": {"stages":[2],"title":"무리하지 않는 하루", "intro":"태오가 산책길의 벤치를 가리킨다. ‘건강은 생활 습관뿐 아니라 접근 가능한 의료·안전 환경과도 연결돼요.’", "choices":{
    "walk":C("맞춤 걷기와 휴식 계획", "몸 상태에 맞는 활동과 휴식의 균형을 실천했다.",{"energy":2},{"ret_health":"활동·휴식"},["ret_health"]),
    "check":C("건강검진·돌봄 정보 확인", "도움을 요청할 곳을 알아 두어 불확실성을 줄였다.",{"insight":2},{"ret_health":"건강 서비스"},["ret_health","elder_care"]),
    "share":C("동네 건강 동아리 참여", "꾸준한 활동과 이웃과의 관계를 함께 만들었다.",{"energy":1,"bond":1},{"ret_health":"건강 모임"},["ret_health","ret_social"]),
}},
"ret_leisure": {"stages":[2],"title":"다시 켜진 작은 극장", "intro":"유리가 텅 빈 극장에 공연 포스터를 건다. ‘노년의 여가가 단순히 남는 시간이 아니라 삶의 즐거움이 될 수 있지 않을까요?’", "choices":{
    "arts":C("그림·공연을 배우기", "오래 미뤄 둔 취미에 시간을 썼다.",{"energy":1,"bond":1},{"ret_leisure":"문화 활동"},["ret_leisure"]),
    "garden":C("공동 정원을 가꾸기", "새로운 성취와 계절의 변화를 느꼈다.",{"energy":2},{"ret_leisure":"정원 활동"},["ret_leisure"]),
    "teach":C("내 경험으로 새 강좌 열기", "여가 시간이 배움과 사회 참여로 연결되었다.",{"bond":2},{"ret_leisure":"경험 나눔"},["ret_leisure","generations"]),
}},
"ret_social": {"stages":[2],"title":"오래된 친구의 빈 의자", "intro":"수아가 광장 벤치를 정돈한다. ‘관계가 자연스럽게 줄어들 때가 있어요. 새로 만나거나 다시 이어 갈 방법이 필요해요.’", "choices":{
    "friends":C("연락이 뜸한 이웃에게 편지", "관계를 다시 이어 가는 작은 실천을 했다.",{"bond":2},{"ret_social":"옛 관계 잇기"},["ret_social"]),
    "join":C("세대 모임에 정기 참여", "서로 다른 삶의 이야기를 나누었다.",{"bond":2},{"ret_social":"새 모임"},["ret_social","generations"]),
    "mentor":C("청소년의 고민을 들어주기", "도움을 주고받으며 연결감을 얻었다.",{"bond":2},{"ret_social":"멘토링"},["ret_social","generations"]),
}},
}

# Stage requirements, rather than forcing one NPC visitation order.
REQUIRED = {0:["career","housing"],1:["care","policy"],2:["ret_finance","ret_health","ret_leisure","ret_social"]}

ZONES = [
    {"id":"shop", "name":"노을 상점가", "col":0,"row":0,"theme":"amber", "blurb":"일자리를 찾는 간판과 장터의 온기가 공존한다."},
    {"id":"square", "name":"별빛 중앙광장", "col":1,"row":0,"theme":"grass", "blurb":"마을의 시간이 모이는 광장"},
    {"id":"work", "name":"새길 일터지구", "col":2,"row":0,"theme":"stone", "blurb":"일과 배움이 만나는 거리"},
    {"id":"home", "name":"달맞이 주거지", "col":0,"row":1,"theme":"grass", "blurb":"삶의 공간과 이웃을 선택하는 골목"},
    {"id":"welfare", "name":"온기 돌봄공원", "col":1,"row":1,"theme":"green", "blurb":"돌봄과 건강, 새로운 노후 계획"},
    {"id":"river", "name":"푸른 강변", "col":2,"row":1,"theme":"river", "blurb":"세대의 이야기가 흐르는 산책로"},
]

BUILDINGS = {
 "shop":[[3,3,6,5,"베이커리","bread"],[12,2,7,6,"노을카페","cafe"],[22,3,5,5,"빈 점포","closed"]],
 "square":[[2,1,10,7,"서라벌여중","school"],[12,2,7,5,"마을회관","hall"],[23,3,5,5,"도서관","library"]],
 "work":[[3,3,7,5,"창업공방","factory"],[14,2,7,6,"직업교육소","school"],[24,3,4,5,"공유사무실","office"]],
 "home":[[3,3,6,5,"공동주거","home"],[13,2,7,6,"임대주택","house"],[23,3,5,5,"작은 집","home"]],
 "welfare":[[3,3,7,5,"마을 보건소","clinic"],[13,2,7,6,"돌봄센터","care"],[23,3,5,5,"어린이집","school"]],
 "river":[[3,3,7,5,"강변 극장","theater"],[14,3,7,5,"목공방","factory"],[24,3,4,5,"쉼터","home"]],
}

def public_content():
    from school import school_content
    return {"stages": STAGES, "concepts": CONCEPTS, "npcs": NPCS,
            "events": EVENTS, "requirements": REQUIRED, "zones": ZONES, "buildings": BUILDINGS, "school": school_content()}
