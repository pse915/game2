/* 외부 이미지·라이브러리 없이 그리는 원본 픽셀 마을입니다. */
'use strict';
let data=null, state=null, position={x:5,y:9}, revision=-1, pending=false, modalOpen=false;
let direction='down', lastMove=0, moved=false, lastSave=Date.now(), sound=false, audio=null;
let pendingSince=0, idleSince=Date.now(), visual={x:5,y:9}, previousZone=-1;
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
  if(canWalk(x,y)){position={x,y};moved=true;idleSince=Date.now();const portal=currentMap().portals.find(p=>p.x===x&&p.y===y);if(portal){beep(660);send('portal');}}
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
window.addEventListener('pointercancel',()=>keys.clear());
document.addEventListener('visibilitychange',()=>{if(document.hidden)keys.clear();});
document.querySelectorAll('[data-dir]').forEach(b=>{
  b.addEventListener('pointerdown',e=>{e.preventDefault();b.setPointerCapture(e.pointerId);keys.add(b.dataset.dir);move(b.dataset.dir);});
  ['pointerup','pointercancel','lostpointercapture'].forEach(type=>b.addEventListener(type,()=>keys.delete(b.dataset.dir)));
});
$('talk').onclick=talk;$('book').onclick=()=>send('book');$('policy').onclick=()=>send('policy_menu');$('life').onclick=()=>send('life_card');$('classroom').onclick=()=>send('classroom');$('save').onclick=()=>send('save');
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
  $('policy').textContent='마을 정책 회의';
  $('progress').textContent=state.progress+'% 진행 · '+(6-state.chapter)+'장 남음';
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
    box.append(actions);if(ui.cards?.length){const more=document.createElement('details');more.append(text('summary','관련 도감 더 보기'));showCards(ui.cards,more);box.append(more);}
  }else if(ui.type==='policy_menu'){
    const available=[['housing','청년 주거 지원','일자리·주거 불안을 줄여요. 대상과 예산에 한계가 있어요.'],['flex','유연근무와 평등한 돌봄','일·가정 양립을 도와요. 사업장의 협력이 필요해요.'],['elder','노인 돌봄과 세대 교류','돌봄과 고립을 줄여요. 서비스 인력이 필요해요.']];
    available.forEach(([code,name,note])=>{const b=button(name,()=>send('policy_select',{code}),'choice');b.disabled=ui.selected.includes(code)||ui.selected.length>=2;b.append(text('small',note));actions.append(b);});box.append(actions,text('p','선택한 정책: '+ui.selected.length+'/2 · 교육용 시뮬레이션입니다.'));
  }else if(ui.type==='life_card'){
    const c=ui.card;[['청년기',c.youth],['일과 삶',c.balance],['관계',c.relationships],['내가 탐색한 가치',c.values],['마을 정책',c.policies.join(', ')||'아직 선택하지 않음']].forEach(([a,b])=>box.append(text('p',a+' · '+b)));
    Object.entries(c.retirement).forEach(([a,b])=>box.append(text('p',a+' · '+b)));box.append(text('p',c.next_step),text('p',c.reality));
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
      box.append(text('p','가상 인구 수치보다 중요한 것은 개인의 선택을 존중하고 마을의 돌봄·일자리·주거 조건을 함께 바꾸는 일이에요.'));
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
  if(!modalOpen&&!pending&&Date.now()-idleSince>45000&&state.chapter<6)$('hint').textContent='길을 잃었나요? 노란 ! 표시의 주민을 만나 보세요. '+state.objective;
  if(moved&&!pending&&!modalOpen&&Date.now()-lastSave>25000)send('save');
  if(pending&&Date.now()-pendingSince>20000)$('status').textContent='저장이 지연되고 있어요. 잠시 기다리거나 아래의 개인 저장파일을 내려받아 주세요. 새로고침 전에는 저장 여부를 확인하세요.';
}
requestAnimationFrame(draw);
