/* 외부 이미지·라이브러리 없이 그리는 원본 픽셀 마을입니다. */
'use strict';
let data=null, state=null, position={x:5,y:9}, revision=-1, pending=false, modalOpen=false;
let direction='down', lastMove=0, moved=false, lastSave=Date.now(), sound=false, audio=null;
let pendingSince=0, idleSince=Date.now(), visual={x:5,y:9}, previousZone=-1;
let effectUntil=0,lastFrame=0,lastHintKey='',travelTimer=null;
const $=id=>document.getElementById(id);
const canvas=$('world'),ctx=canvas.getContext('2d');
ctx.imageSmoothingEnabled=false;
const keys=new Set();
const keyboardDirs=new Set();
const touchDirs=new Map();
function syncKeys(){keys.clear();keyboardDirs.forEach(v=>keys.add(v));touchDirs.forEach(v=>keys.add(v));}
function releaseInputs(){keyboardDirs.clear();touchDirs.clear();keys.clear();}
const text=(tag,content,cls)=>{const el=document.createElement(tag);el.textContent=content;if(cls)el.className=cls;return el;};
function post(type,extra={}){window.parent.postMessage({isStreamlitMessage:true,type,...extra},'*');}
function height(){post('streamlit:setFrameHeight',{height:Math.ceil(document.body.scrollHeight+8)});}
function send(kind,extra={}){
  if(!state||pending)return;
  pending=true;pendingSince=Date.now();releaseInputs();
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
    if(data.ui?.sparkle)effectUntil=Date.now()+1800;
    if(data.ui?.travel)showTravel(data.ui.travel);
    $('status').textContent=data.save_status||'방향버튼으로 움직여 NPC를 만나 보세요.';
  }
  height();
});
post('streamlit:componentReady',{apiVersion:1});
window.addEventListener('resize',height);
new ResizeObserver(height).observe($('game'));
function currentMap(){return data.maps[state.zone];}
function npcNear(){return data.npcs.find(n=>n.zone===state.zone&&Math.abs(n.x-position.x)+Math.abs(n.y-position.y)<=1);}
function eventNear(){return (data.events||[]).find(e=>e.zone===state.zone&&Math.abs(e.x-position.x)+Math.abs(e.y-position.y)<=1);}
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
  if(canWalk(x,y)){position={x,y};moved=true;idleSince=Date.now();const portal=currentMap().portals.find(p=>p.x===x&&p.y===y);if(portal){beep(660);send('portal');}}
}
function talk(){if(!state||pending||modalOpen)return;if(state.finished){send('ending');return;}const n=npcNear();if(n){beep(520);send('talk',{npc:n.id});}else{$('status').textContent='주민 바로 옆으로 한 칸 더 가까이 가 주세요.';}}
function inspect(){if(!state||pending||modalOpen)return;const e=eventNear();if(e){beep(670);send('investigate',{event_id:e.id});}else $('status').textContent='반짝이는 조사 표시 옆으로 이동해 주세요.';}
const keyDir={ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right',w:'up',s:'down',a:'left',d:'right'};
window.addEventListener('keydown',e=>{
  if(e.target.matches('input,textarea,select'))return;
  if(modalOpen){if(e.key==='Escape'){e.preventDefault();closeDialog();}if(e.key==='Tab'){const b=[...$('dialog').querySelectorAll('button:not(:disabled),input,summary')];if(b.length){const first=b[0],last=b[b.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}}return;}
  if(keyDir[e.key]){e.preventDefault();keyboardDirs.add(keyDir[e.key]);syncKeys();move(keyDir[e.key]);}
  if(e.key==='Enter'&&!e.target.matches('button')){e.preventDefault();talk();}
  if((e.code==='Space'||e.key===' ')&&!e.target.matches('button')){e.preventDefault();inspect();}
});
window.addEventListener('keyup',e=>{keyboardDirs.delete(keyDir[e.key]);syncKeys();});
window.addEventListener('blur',releaseInputs);
window.addEventListener('pointercancel',releaseInputs);
document.addEventListener('visibilitychange',()=>{if(document.hidden)releaseInputs();});
document.querySelectorAll('[data-dir]').forEach(b=>{
  b.addEventListener('pointerdown',e=>{e.preventDefault();try{b.setPointerCapture(e.pointerId);}catch(err){}touchDirs.set(e.pointerId,b.dataset.dir);syncKeys();move(b.dataset.dir);});
  ['pointerup','pointercancel','lostpointercapture'].forEach(type=>b.addEventListener(type,e=>{touchDirs.delete(e.pointerId);syncKeys();}));
});
$('talk').onclick=talk;$('inspect').onclick=inspect;$('book').onclick=()=>send('book');$('policy').onclick=()=>send('policy_menu');$('life').onclick=()=>send('life_card');$('classroom').onclick=()=>send('classroom');$('save').onclick=()=>send('save');
$('sound').onclick=()=>{sound=!sound;$('sound').textContent=sound?'소리를 끕니다.':'소리를 켭니다.';beep();};
$('full').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await $('game').requestFullscreen();}catch(e){$('status').textContent='이 환경은 전체화면을 지원하지 않아요. 브라우저 확대 기능을 사용해 주세요.';}height();};
function updateHud(){
  const s=state.stats;
  $('place').textContent=currentMap().name;$('age').textContent=state.age+'세';$('objective').textContent=state.objective;
  $('period').textContent=state.age<29?'청년기':state.age<58?'성인기':'노년기';
  const world=state.world_view||{};const names={spring:'봄 · 시작',summer:'여름 · 성장',autumn:'가을 · 성찰'};
  $('world-phase').textContent=names[world.season]||'마을의 하루';
  $('badges').textContent='만난 주민 '+state.visited.length+'/'+data.npcs.length+'명 · 지식 확인 '+Object.values(state.quizzes).filter(q=>q.correct).length+'/6개'+(state.flags.equality?' · 양성평등 배지를 얻었어요.':'');
  $('hud').replaceChildren();
  const rows=[['내 자녀수',s.children+'명',s.children/3],['TFR 기여도',(s.contribution>=0?'+':'')+s.contribution.toFixed(2),(s.contribution+2)/5],['마을출산율',s.village_tfr.toFixed(2),s.village_tfr/3.5],['고령화율',s.aging.toFixed(1)+'%',s.aging/30],['마을활력',s.vitality+'/100',s.vitality/100],['가족행복',s.happiness+'/100',s.happiness/100],['돌봄부담',s.care+'/100',s.care/100]];
  rows.forEach(([label,value,ratio],i)=>{const box=text('div','','metric');box.append(text('span',label),text('b',value));const tr=text('div','','track'),fill=text('div','','fill'+((i===3||i===6)?' danger':''));fill.style.width=Math.max(0,Math.min(100,ratio*100))+'%';tr.append(fill);box.append(tr);$('hud').append(box);});
  $('policy').disabled=!state.flags.policy_offer||state.finished;
  $('policy').textContent='🏛 정책회의';
  $('progress').textContent=state.progress+'% 진행 · '+(6-state.chapter)+'장 남음';
  $('maplabel').textContent='이동: 방향키 / WASD · 주민: Enter · 사건: Space';
}
function showTravel(transition){
  const overlay=$('timeline');if(!overlay)return;
  clearTimeout(travelTimer);
  $('timeline-title').textContent=transition.from+'세 → '+transition.to+'세';
  $('timeline-desc').textContent='몇 해가 흘렀습니다. 나의 선택과 마을의 변화가 이어집니다.';
  overlay.classList.remove('hidden');
  const hide=()=>{overlay.classList.add('hidden');clearTimeout(travelTimer);};
  $('skiptravel').onclick=hide;
  travelTimer=setTimeout(hide,1550);
}
function closeDialog(){modalOpen=false;releaseInputs();$('modal').classList.add('hidden');$('stage').focus({preventScroll:true});height();}
function button(label,handler,cls=''){const b=text('button',label,cls);b.onclick=()=>{beep();handler();};return b;}
function showCards(cards,container){cards.forEach(c=>{const d=document.createElement('details');d.append(text('summary',c.title),text('p',c.text),text('p',c.note));container.append(d);});}
function showDialog(ui){
  modalOpen=true;releaseInputs();$('modal').classList.remove('hidden');const box=$('dialog');box.replaceChildren();
  const close=button('닫습니다. · Esc',closeDialog,'close');box.append(close,text('h2',ui.title||'65세, 미래마을의 기록'));
  box.querySelector('h2').id='dialogtitle';
  if(ui.text)box.append(text('p',ui.text));
  (ui.lines||[]).forEach(line=>box.append(text('p',line)));
  if(ui.feedback)box.append(text('p',ui.feedback,'feedback'));
  if(ui.message)box.append(text('p',ui.message,'feedback'));
  const actions=text('div','','dialog-actions');
  if(ui.type==='event'){
    box.append(text('div','🔎 마을 현장 조사 · '+(ui.previous?'다시 살펴보기':'새로운 단서'),'dialog-kicker'));
    box.append(text('p',ui.prompt,'event-box'));
    if(ui.previous){box.append(text('p','이 사건은 이미 조사했어요. 다시 읽을 수 있습니다.'));
      box.append(text('p',ui.lesson,'feedback'));
    }else{
      ui.options.forEach(o=>actions.append(button(o.label,()=>send('resolve_event',{event_id:ui.event_id,code:o.code}),'choice')));
      box.append(actions);
    }
  }else   if(ui.type==='talk'){
    ui.buttons.forEach(b=>actions.append(button(b.label,()=>send(b.kind,{npc:ui.npc}),'primary')));
    box.append(actions);if(ui.cards?.length){const more=document.createElement('details');more.append(text('summary','관련 도감 더 보기'));showCards(ui.cards,more);box.append(more);}
  }else if(ui.type==='policy_menu'){
    const available=[['housing','청년 주거 지원','일자리·주거 불안을 줄여요. 대상과 예산에 한계가 있어요.'],['flex','유연근무와 평등한 돌봄','일·가정 양립을 도와요. 사업장의 협력이 필요해요.'],['elder','노인 돌봄과 세대 교류','돌봄과 고립을 줄여요. 서비스 인력이 필요해요.']];
    available.forEach(([code,name,note])=>{const b=button(name,()=>send('policy_select',{code}),'choice');b.disabled=ui.selected.includes(code)||ui.selected.length>=2;b.append(text('small',note));actions.append(b);});box.append(actions,text('p','선택한 정책: '+ui.selected.length+'/2 · 교육용 시뮬레이션입니다.'));
  }else if(ui.type==='life_card'){
    const c=ui.card;box.append(text('p','🌿 내가 직접 살아 본 미래의 기록','dialog-kicker'));[['청년기',c.youth],['일과 삶',c.balance],['관계',c.relationships],['내가 탐색한 가치',c.values],['마을 정책',c.policies.join(', ')||'아직 선택하지 않음']].forEach(([a,b])=>box.append(text('p',a+' · '+b)));
    Object.entries(c.retirement).forEach(([a,b])=>box.append(text('p',a+' · '+b)));
    if(c.incidents?.length)box.append(text('p','내가 발견한 마을 사건 · '+c.incidents.join(' / ')));
    if(c.important_choice)box.append(text('p','마지막 생애 선택 · '+c.important_choice));
    const w=c.policy_effects||{};if(w.policy_count)box.append(text('p','마을에 반영된 정책 '+w.policy_count+'개 · 정책이 모든 문제를 해결하지는 못합니다.'));
    box.append(text('p',c.next_step),text('p',c.reality));
    box.append(button('카드 내용을 복사하기',()=>{const result=box.innerText||c.youth+' / '+c.balance+' / '+c.relationships;navigator.clipboard?.writeText(result);},'primary'));
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
    if(state.flags.classroom_mode){
      box.append(text('p','가상 수치보다 중요한 것은 내가 내린 선택과 주민들의 이야기를 연결해 보는 일이에요. 개인의 삶은 다양하며 돌봄·일자리·주거는 함께 풀어야 할 과제입니다.'));
      box.append(text('p','내가 조사한 사건: '+(state.life_card?.incidents?.join(' / ')||'마을 곳곳에 남아 있는 문제를 돌아보세요.')));
      box.append(button('나의 생애설계 카드 확인',()=>send('life_card'),'primary'));
      box.append(text('p','소감문: ① 기억에 남는 마을 문제 ② 선택한 해결책과 이유 ③ 개인·사회의 준비 ④ 나의 첫 실천을 적어 보세요.'));
      return;
    }
    const chart=text('div','','comparison');chart.append(text('p','전국 기준과 비교합니다. 두 값 모두 수업용이며 전국 기준 1.30은 가정값입니다.'));
    [['전국 비교 기준',1.30,'baseline'],['나의 최종 가상 TFR',e.tfr,'']].forEach(([label,value,cls])=>{chart.append(text('div',label+' '+value.toFixed(2)));const b=text('div','','bar '+cls);b.style.width=Math.min(100,Math.max(0,value)/3.5*100)+'%';chart.append(b);});
    if(e.tfr<0)chart.append(text('p','음수는 고정 계산식의 결과입니다. 실제 합계출산율에는 음수가 없으며 그래프 막대만 0에서 시작합니다. 숫자는 보정하지 않았습니다.'));
    box.append(chart,text('p','계산: (내 자녀 수 − 1.30) + 보너스합 = 기여도입니다. 최종 가상 TFR은 1.30 + 기여도입니다.'));
    state.bonus_items.forEach(([label,value])=>box.append(text('div',label+' '+(value>=0?'+':'')+value.toFixed(2))));
    if(!state.bonus_items.length)box.append(text('div','적용된 보너스가 없습니다.'));
    box.append(text('p','p.103에서 찾은 마을의 다음 약속','ending-letter'));
    e.advice.forEach(a=>box.append(text('p',a)));
    if(e.code==='C')box.append(text('p','신문 아카이브: “확 늙어버린 대한민국” — 2016.9.7 당시 전망입니다. 현재 뉴스가 아닙니다.'));
    box.append(button('나의 생애설계 카드 확인',()=>send('life_card'),'primary'));
    box.append(text('p','소감문: ① 기억에 남는 마을 문제 ② 선택한 해결책과 이유 ③ 개인·사회의 준비 ④ 나의 첫 실천을 적어 보세요.'));
    box.append(text('p','이 엔딩은 행복한 가족의 자격이나 개인의 도덕성을 판정하지 않습니다. 무자녀 공동 돌봄도 존중받습니다.'),text('p','게임 아래의 개인 저장파일과 결과 기록을 내려받고 성찰 활동을 해 주세요.'));
  }else if(ui.type==='notice'){
    if(ui.next)box.append(text('p',ui.next,'feedback'));
    box.append(button('마을로 돌아갑니다.',closeDialog,'primary'));
  }
  setTimeout(()=>{const focus=box.querySelector('.dialog-actions button:not(:disabled)')||close;focus.focus({preventScroll:true});height();},20);
}
/* 미래마을 2.0 오리지널 픽셀 그래픽. 타일맵/충돌 좌표는 변경하지 않습니다. */
const TILE=32;
const PALETTES={spring:{grass:'#7bad7e',shade:'#619873',light:'#95bd81',tree:'#386e61',leaf:'#579473',road:'#d4c6a3',edge:'#abac86',petal:'#f9dc9f'},summer:{grass:'#75a783',shade:'#5c927a',light:'#8cb49b',tree:'#396e65',leaf:'#519080',road:'#cec4a7',edge:'#a5a88f',petal:'#ffcf8c'},autumn:{grass:'#96a07b',shade:'#7f9675',light:'#b7b28a',tree:'#667756',leaf:'#b28a62',road:'#c6bba5',edge:'#a0a08e',petal:'#edb976'}};
function rect(x,y,w,h,color){ctx.fillStyle=color;ctx.fillRect(Math.round(x),Math.round(y),Math.ceil(w),Math.ceil(h));}
function label(s,x,y,color='#253c44',size=11){ctx.font='bold '+size+'px sans-serif';ctx.textAlign='center';ctx.fillStyle=color;ctx.fillText(s,Math.round(x),Math.round(y));}
function palette(){return PALETTES[state.world_view?.season]||PALETTES.spring;}
function tile(x,y,col,alt){const xx=x*TILE,yy=y*TILE;rect(xx,yy,32,32,col);rect(xx+1,yy+1,30,1,alt);}
function grassTile(x,y,pa){tile(x,y,(x*7+y*11)%4===0?pa.shade:pa.grass,pa.light);const xx=x*32,yy=y*32;
  if((x*17+y*13)%5===1){rect(xx+7,yy+19,2,4,pa.light);rect(xx+9,yy+16,2,4,pa.light);rect(xx+14,yy+22,2,3,pa.shade);}
  if((x*23+y*19)%17===2){rect(xx+23,yy+19,4,4,'#ffe3b6');rect(xx+25,yy+17,2,2,'#d7778c');}
}
function roadTile(x,y,pa){tile(x,y,(x+y)%3===0?'#c9bc9e':pa.road,'#ddd0b5');const xx=x*32,yy=y*32;
  if(y===7||y===9){rect(xx,yy+(y===7?0:29),32,2,pa.edge);}
  if((x+y)%4===1){rect(xx+4,yy+12,12,1,'#b3ab95');rect(xx+22,yy+25,7,1,'#e6dac0');}
}
function plant(x,y,pa,flower=false){rect(x+5,y+5,12,12,pa.shade);rect(x+3,y+3,12,10,pa.leaf);rect(x+8,y,6,7,pa.light);
 if(flower){rect(x+10,y+2,3,3,'#f5d586');rect(x+18,y+10,4,4,'#f2a1a5');}}
function tree(x,y,pa){rect(x+13,y+18,7,14,'#644d39');rect(x+15,y+18,3,14,'#896f48');
 rect(x+3,y+7,26,17,pa.tree);rect(x+7,y+1,20,20,pa.leaf);rect(x+10,y+0,12,6,pa.light);rect(x+5,y+15,22,5,pa.tree);
 rect(x+12,y+5,5,2,'#a2b784');rect(x+23,y+15,3,4,pa.shade);
}
function lamp(x,y){rect(x+10,y+9,3,21,'#4a5559');rect(x+6,y+5,11,7,'#344b51');rect(x+8,y+7,7,5,'#ffe2a1');rect(x+4,y+29,15,3,'#566f68');}
function bench(x,y){rect(x+1,y+18,28,3,'#72533f');rect(x+2,y+21,27,3,'#a87853');rect(x+3,y+24,3,7,'#58655b');rect(x+25,y+24,3,7,'#58655b');}
function worldFloor(pa){for(let y=0;y<15;y++)for(let x=0;x<24;x++){const road=(y>=7&&y<=9)||(x>=10&&x<=13&&y>=5)||(y===6);if(road)roadTile(x,y,pa);else grassTile(x,y,pa);}
  // 마을을 읽기 쉽게 만드는 반복되지 않는 환경 디테일
  [[1,11],[3,12],[7,11],[17,12],[21,11],[23,12],[0,0],[8,1],[16,0]].forEach(([x,y])=>tree(x*32,y*32,pa));
  [[1,10],[8,13],[19,11],[22,13],[16,13]].forEach(([x,y],i)=>plant(x*32,y*32,pa,i%2===0));
  [[8,6],[18,6]].forEach(([x,y])=>lamp(x*32,y*32));bench(8*32,11*32);
}
const houseKinds=[{roof:'#ad6d68',trim:'#e8c59d',wall:'#e3d5b9'},{roof:'#587f9e',trim:'#c2dfe0',wall:'#e7decb'},{roof:'#80946d',trim:'#d6d7aa',wall:'#e5d6bd'}];
function building(b,index){const [bx,by,w,h,name]=b,x=bx*32,y=by*32,W=w*32,H=h*32;
  const view=state.world_view||{},shop=/상점|책방|공방/.test(name),child=/어린이집|초등학교/.test(name),elder=/경로당|병원/.test(name),office=/시청/.test(name);
  const revitalized=shop&&view.shop==='reviving'||child&&view.nursery==='supported'||elder&&view.elder==='connected'||name==='공공주택'&&view.housing==='welcoming';
  const quiet=shop&&view.shop==='quiet'||child&&view.nursery==='quiet';
  const p=houseKinds[index%3];const roof=office?'#65849d':child?'#a87985':elder?'#749489':p.roof;
  // foundation, sidewall, roof tiles, cornice
  rect(x+3,y+24,W,H-24,'#415c5e');rect(x,y+29,W-5,H-31,p.wall);rect(x+1,y+29,7,H-29,'#b8aa97');
  rect(x-4,y+15,W+8,21,'#435e5c');rect(x-5,y+10,W+10,20,roof);rect(x+1,y+4,W-2,11,roof);rect(x+7,y+1,W-14,5,'#f1d7b3');
  for(let k=9;k<W-7;k+=16){rect(x+k,y+12,9,2,'#faf0d0');rect(x+k+4,y+24,9,2,'#3d5961');}
  rect(x-5,y+29,W+10,4,p.trim);
  for(let xx=14;xx<W-25;xx+=43){const wx=x+xx;rect(wx,y+49,29,30,'#51666e');rect(wx+3,y+52,23,24,quiet?'#566d70':'#9fcbd0');rect(wx+4,y+54,21,21,quiet?'#46565d':'#c9e4d2');rect(wx+13,y+52,3,24,'#8d8875');rect(wx+3,y+63,23,3,'#8c897b');if(revitalized){rect(wx+6,y+55,5,9,'#f6d9a4');rect(wx+18,y+55,4,8,'#f8dea7');}}
  const door=x+W/2-14;rect(door-3,y+H-38,34,38,'#5e5d52');rect(door,y+H-34,28,34,quiet?'#546b6c':'#80aa95');rect(door+4,y+H-29,20,29,quiet?'#607174':'#a8c5ad');rect(door+22,y+H-20,2,3,'#f0d498');
  rect(x+8,y+35,W-16,17,'#f5e9c9');rect(x+8,y+51,W-16,2,'#7a8880');label(name,x+W/2,y+47,'#30474b',Math.min(11,Math.max(8,W/11)));
  if(child){rect(x+W-37,y+H-20,11,11,'#f0c77d');rect(x+W-25,y+H-14,8,8,'#d58a89');}
  if(shop){rect(x+9,y+H-15,13,13,revitalized?'#89b778':'#8e978e');rect(x+23,y+H-14,12,12,'#bc8c66');}
  if(quiet){rect(x+W-62,y+H-17,46,12,'#514e4d');label('잠시 조용해요',x+W-39,y+H-8,'#eed7a4',8);}
  if(revitalized){rect(x+W-42,y+30,32,7,'#a3d39f');rect(x+W-38,y+30,24,3,'#d2f2a9');}
}
function person(x,y,color,elder=false,player=false,phase=0,id=''){const xx=Math.round(x*32),yy=Math.round(y*32);
  const walking=player&&moved;const step=walking?Math.round(Math.sin(phase/85)*2):0;const hair=elder?'#d8dcce':id==='doctor'?'#566477':id==='owner'?'#72513e':id==='teacher'?'#734e54':id==='director'?'#63485a':'#3d4a51';
  // 이동/대화 방향과 NPC별 실루엣
  rect(xx+6,yy+28,21,3,'#4d7169');rect(xx+10,yy+21,6,9+step,'#455467');rect(xx+18,yy+21,6,9-step,'#455467');
  rect(xx+7,yy+12,20,13,'#263e48');rect(xx+9,yy+14,16,10,color);rect(xx+6,yy+17,4,8,'#e4b998');rect(xx+24,yy+17,4,8,'#e4b998');
  rect(xx+11,yy+2,14,14,'#e9bd98');rect(xx+9,yy+1,18,6,hair);rect(xx+10,yy+4,3,8,hair);
  const facing=player?direction:'down';
  if(facing!=='up'){rect(xx+14,yy+9,2,2,'#303844');rect(xx+21,yy+9,2,2,'#303844');rect(xx+17,yy+12,3,1,'#bf877d');}
  else rect(xx+10,yy+6,16,7,hair);
  if(player){rect(xx+8,yy,20,5,'#e3ae5a');rect(xx+6,yy+4,22,3,'#f3d484');rect(xx+13,yy+16,8,3,'#e4d39f');}
  if(elder){rect(xx+28,yy+18,2,14,'#7c6956');rect(xx+9,yy+11,4,1,'#72828a');}
  if(id==='doctor'){rect(xx+8,yy+14,4,10,'#f4f1dc');rect(xx+23,yy+14,4,10,'#f4f1dc');rect(xx+16,yy+17,3,3,'#c7dce5');}
  if(id==='owner'){rect(xx+9,yy+14,17,3,'#eee2ae');rect(xx+9,yy+0,17,3,'#695440');}
  if(id==='official'||id==='mayor'){rect(xx+10,yy+17,14,2,'#efdb95');}
  if(id==='director'){rect(xx+11,yy+4,13,4,'#68515f');}
}
function eventMarker(ev,ts){const px=ev.x*32,py=ev.y*32,found=!!state.flags.investigations?.[ev.id],pulse=Math.round(Math.sin(ts/240)*2);
  // 줍고 살펴볼 수 있는 픽셀 현장 단서
  rect(px+3,py+21,26,6,'#4c6a65');rect(px+7,py+12,18,12,found?'#6e9292':'#cfb477');rect(px+9,py+13,14,8,found?'#9bc9b9':'#f6e6b3');rect(px+15,py+14,2,9,'#6d8a85');
  rect(px+9,py+2+pulse,14,11,found?'#d3dcb2':'#ffe59b');label(found?'✓':'!',px+16,py+11+pulse,found?'#3b7565':'#80553a',11);
}
function draw(ts){requestAnimationFrame(draw);if(!state)return;if(ts-lastFrame<27)return;lastFrame=ts;
  if(keys.size)move([...keys][0]);visual.x+=(position.x-visual.x)*.34;visual.y+=(position.y-visual.y)*.34;
  const map=currentMap(),pa=palette();worldFloor(pa);
  map.buildings.forEach(building);
  // 텍스트 표지판은 원본 좌표를 그대로 사용합니다.
  rect(2*32,10*32,160,31,'#765f48');rect(2*32+3,10*32+3,154,23,'#e6d7a7');label(map.sign,2*32+80,10*32+18,'#3a5053',8);
  // 정책이 게임 월드에 실제로 반영되는 시각적 변화
  const w=state.world_view||{};
  if(state.zone===1){
    if(w.housing==='welcoming'){for(let i=0;i<3;i++){rect(76+i*21,163,13,12,'#ffe4a5');rect(78+i*21,165,9,8,'#bce4bf');}label('청년들이 돌아오는 거리',126,185,'#244e46',10);}
    if(w.shop==='reviving'){for(let i=0;i<4;i++)plant(19*32+i*18,6*32,pa,true);label('영업 재개!',656,187,'#295b4a',11);}
  }
  if(state.zone===2&&w.nursery==='supported'){for(let i=0;i<5;i++){rect(2*32+i*28,5*32+4,18,5,['#f7b69b','#e7cf73','#96d5b7'][i%3]);}label('함께 돌보는 새싹반',155,188,'#315f4f',11);}
  if(state.zone===3&&w.work==='balanced'){rect(2*32,5*32,188,8,'#83b29d');label('퇴근 후 삶을 지켜요',161,188,'#285745',11);}
  if(state.zone===4&&w.elder==='connected'){for(let i=0;i<4;i++)plant((8+i*2)*32,11*32,pa,true);label('함께 걷는 공원',490,410,'#2a594c',11);}
  for(const p of map.portals){const pulse=Math.floor(ts/460)%2;rect(p.x*32+2,p.y*32+2,28,28,pulse?'#d9e1bf':'#9ec9b0');rect(p.x*32+7,p.y*32+7,18,18,'#5c9890');label('↔',p.x*32+16,p.y*32+22,'#f8f4d1',16);const lx=Math.max(40,Math.min(728,p.x*32+16));label(p.label,lx,p.y*32-4,'#274444',10);}
  (data.events||[]).filter(e=>e.zone===state.zone).forEach(ev=>eventMarker(ev,ts));
  const elders=w.elder==='connected'?2:3;for(let i=0;i<elders;i++){const x=[2,7,18][i],y=[11,12,11][i];person(x,y,['#acb89f','#c5aeb7','#aebabb'][i],true,false,ts);}
  if(state.zone===4&&w.elder==='connected')for(let i=0;i<2;i++)person(15+i*2,11,['#87bdb9','#dbad88'][i],false,false,ts);
  if(state.zone===1&&w.shop==='reviving')for(let i=0;i<2;i++)person(17+i*2,11,['#78b2b7','#e0b67c'][i],false,false,ts);
  const npcs=data.npcs.filter(n=>n.zone===state.zone);
  for(const n of npcs){person(n.x,n.y,n.color,n.id==='granny'||(state.age>=58&&['career','owner','teacher'].includes(n.id)),false,ts,n.id);label(n.name,n.x*32+16,n.y*32-6,'#152e37',10);
    const current=state.chapter<6&&data.chapters[state.chapter].guide===n.id||state.chapter>=6&&n.id==='mayor';
    if(current){const d=Math.round(Math.sin(ts/260)*2);rect(n.x*32+10,n.y*32-27+d,14,15,'#f6dd8b');label('!',n.x*32+17,n.y*32-15+d,'#6f5032',14);}}
  person(visual.x,visual.y,'#5e98b8',state.age>=58,true,ts);label(state.nickname,visual.x*32+16,visual.y*32-5,'#182e34',11);
  if(Date.now()<effectUntil)for(let i=0;i<23;i++){const xx=(i*149+Math.floor(ts/22)*3)%768,yy=(i*79+Math.floor(ts/15)*2)%470;rect(xx,yy,4,4,['#f8d28c','#beeab7','#f4ada6'][i%3]);}
  const n=npcNear(),ev=eventNear();$('talk').disabled=pending||(!n&&!state.finished);$('inspect').disabled=pending||!ev||!!state.finished;
  const hint=ev?'🔎 '+ev.title+' · 조사하기':n?'💬 '+n.name+' · 말걸기':'빛나는 느낌표는 대화, 작은 조사 표시는 사건의 단서입니다.';
  const hintKey=position.x+','+position.y+':'+state.zone+':'+hint;
  if(hintKey!==lastHintKey){$('hint').textContent=hint;lastHintKey=hintKey;}
  const focus={1:'job_board',2:'closed_shop',3:'empty_classroom',4:'work_schedule',5:'elder_letter'}[state.chapter];
  const eventTarget=state.flags.classroom_mode&&focus&&!state.flags.investigations?.[focus]?(data.events||[]).find(e=>e.id===focus):null;
  const guideId=state.chapter>=6?'mayor':data.chapters[state.chapter].guide;
  const routeTarget=eventTarget||data.npcs.find(e=>e.id===guideId);
  if(routeTarget)$('route').textContent=routeTarget.zone===state.zone?'목표 · '+(routeTarget.title||routeTarget.name):'이동 · '+data.maps[routeTarget.zone].name;
  else $('route').textContent='우리 마을을 탐험해요';
  if(!modalOpen&&!pending&&Date.now()-idleSince>45000&&state.chapter<6)$('hint').textContent='힌트: '+state.objective;
  if(moved&&!pending&&!modalOpen&&Date.now()-lastSave>25000)send('save');
  if(pending&&Date.now()-pendingSince>20000)$('status').textContent='저장이 지연됩니다. 개인 저장파일을 백업하고 다음에 다시 시도할 수 있어요.';
}
requestAnimationFrame(draw);
