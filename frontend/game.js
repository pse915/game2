/* SEWOL PORT: original, programmatic pixel RPG renderer + tablet input.
 * Python receives choice events and owns every simulated outcome.
 */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const canvas=$('game'), ctx=canvas.getContext('2d',{alpha:false});
  const TILE=32, MW=30, MH=19, W=960, H=608;
  const ZONE_SYMBOL={shop:'☕',square:'✦',work:'⚒',home:'⌂',welfare:'✿',river:'≈'};
  const ICON={money:'◈',time:'◷',energy:'♥',bond:'✦',insight:'◇'};
  const LABEL={money:'생활 여유',time:'내 시간',energy:'건강',bond:'관계',insight:'배움'};
  const LOOKS=[{skin:0,hair:0,outfit:3},{skin:1,hair:3,outfit:2},{skin:2,hair:1,outfit:4},{skin:0,hair:4,outfit:0},{skin:1,hair:2,outfit:5},{skin:2,hair:5,outfit:1}];
  let data=null,state=null,pos={zone:'square',x:16,y:13,dir:'down',moving:false,prevX:16,prevY:13,moveTime:0};
  let latestRevision=-1,lastRun='',pressed=new Set(),lastStep=0,modalOpen=false,audio=false,audioContext=null,
      mapCanvas=null,mapKey='',floatingTime=0,initial=true,notice='',eventsPending=false,walkTick=0;
  const safe = s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const post=(type,extra={})=>window.parent.postMessage({isStreamlitMessage:true,type,...extra},'*');
  function componentReady(){post('streamlit:componentReady',{apiVersion:1});setHeight();}
  function setHeight(){post('streamlit:setFrameHeight',{height:Math.ceil(document.documentElement.scrollHeight+6)});}
  const hash=(x,y,s=0)=>{let n=Math.imul(x*374761393^y*668265263^s*1442695041,1274126177);return ((n^(n>>>13))>>>0)%1000};
  const lc = (...parts)=>parts.filter(Boolean).join(' ');
  function sound(note=520){if(!audio)return;try{audioContext??=new(window.AudioContext||window.webkitAudioContext)();const o=audioContext.createOscillator(),g=audioContext.createGain();o.type='square';o.frequency.setValueAtTime(note,audioContext.currentTime);o.frequency.exponentialRampToValueAtTime(note*.7,audioContext.currentTime+.09);g.gain.setValueAtTime(.04,audioContext.currentTime);g.gain.exponentialRampToValueAtTime(.001,audioContext.currentTime+.12);o.connect(g).connect(audioContext.destination);o.start();o.stop(audioContext.currentTime+.13)}catch(e){}}
  function zoneInfo(){return data?.zones.find(z=>z.id===pos.zone)}
  function readSavedPosition(){try{const p=JSON.parse(sessionStorage.getItem('sewol_location:'+state.run_id+':'+state.stage));if(p&&data.zones.some(z=>z.id===p.zone)&&Number.isInteger(p.x)&&Number.isInteger(p.y)&&p.x>=1&&p.x<29&&p.y>=8&&p.y<18&&!obstacle(p.zone,p.x,p.y))return p;}catch(e){}return null}
  function rememberPosition(){if(!state)return;try{sessionStorage.setItem('sewol_location:'+state.run_id+':'+state.stage,JSON.stringify({zone:pos.zone,x:pos.x,y:pos.y,dir:pos.dir}));}catch(e){}}
  function updateFromPython(args){
    if(!args?.state||!args?.content)return;
    const incoming=args.state;data=args.content;notice=args.notice||'';
    const firstRun=lastRun!==incoming.run_id,phaseChange=!firstRun&&state?.stage!==incoming.stage;
    const newRev=state===null||incoming.revision!==latestRevision;
    state=incoming;
    if(firstRun||phaseChange){pos={zone:state.zone,x:state.x,y:state.y,prevX:state.x,prevY:state.y,dir:'down',moveTime:0,moving:false};const back=readSavedPosition();if(back){Object.assign(pos,back);pos.prevX=pos.x;pos.prevY=pos.y;}mapKey='';lastRun=state.run_id;closeModal();if(phaseChange){
        if(state.stage===1){showModal('시간의 풍경이 바뀌었다','출생아 수 감소와 평균 수명 상승으로 마을의 나이 구성이 달라졌습니다. 일터에는 빈자리가 생기고 어린이집에는 빈 의자가 늘었습니다.','<blockquote>저출산과 고령화는 한 사람의 선택 탓이 아닙니다. 일자리·주거·돌봄·의료 등 생활환경이 서로 연결되어 있습니다.</blockquote>',r=>actions(r,[['변화한 마을 탐험하기',closeModal]]));}
        else {showModal('노년기의 새 페이지','세월이 흘러 이제는 노후의 생활을 직접 설계할 시간입니다.','<blockquote>재무·건강·여가·대인 관계는 함께 준비하며, 과거 선택 한 번으로 남은 삶이 결정되지는 않습니다.</blockquote>',r=>actions(r,[['나의 노년기 시작',closeModal]]));}
        sound(630)
      } }
    if(newRev&&latestRevision>=0&&!phaseChange){if(notice)showToast(notice);sound(650)}
    if(firstRun){showToast('마을을 자유롭게 돌아보세요. 지도 버튼으로 빠르게 이동할 수 있습니다.');}
    latestRevision=incoming.revision;eventsPending=false;refreshUI();setHeight();
  }
  window.addEventListener('message',e=>{if(e.data?.type==='streamlit:render')updateFromPython(e.data.args);});
  function emit(message){if(!state||eventsPending)return;eventsPending=true;message.nonce=typeof crypto!=='undefined'&&crypto.randomUUID?crypto.randomUUID():String(Date.now())+'-'+Math.random();post('streamlit:setComponentValue',{value:message});showToast('선택을 기록하고 있습니다…');}
  function showToast(s){const el=$('toast');el.textContent=s;el.classList.remove('hidden');floatingTime=performance.now()+3300;}
  function closeModal(){modalOpen=false;$('modal-layer').classList.add('hidden');$('modal-content').replaceChildren();}
  function showModal(title,summary,body,creator){const modal=$('modal-layer'),root=$('modal-content');modal.classList.remove('hidden');modalOpen=true;root.innerHTML=`<div class="tag">✦ SEWOL PORT · LIFE EVENT</div><h3>${safe(title)}</h3><p>${safe(summary)}</p>${body||''}`;if(creator)creator(root);setTimeout(setHeight,50);sound(440);}
  function actions(root,choices){const holder=document.createElement('div');holder.className='dialog-actions';for(const [label,handler] of choices){const b=document.createElement('button');b.textContent=label;b.addEventListener('click',handler);holder.appendChild(b)}root.appendChild(holder);}
  function eventOpen(eventId){if(!state||!data)return false;const ev=data.events[eventId];return !!ev&&ev.stages.includes(state.stage)&&!state.decisions[eventId]&&(!state.ended||ev.free);}
  function nearNPC(){const occupants=data.npcs.filter(n=>n.zone===pos.zone);const list=occupants.map(n=>({n,d:Math.abs(n.x-pos.x)+Math.abs(n.y-pos.y)})).filter(x=>x.d<=2).sort((a,b)=>a.d-b.d);return list[0]?.n||null}
  function buildingByDoor(){const blocks=data.buildings[pos.zone]||[];for(const b of blocks){let dx=b[0]+Math.floor(b[2]/2),dy=b[1]+b[3]+1;if(Math.abs(dx-pos.x)+Math.abs(dy-pos.y)<=2)return b;}return null}
  function interact(){if(!state||modalOpen)return;
    if(pos.zone.startsWith('inside:')){interiorInfo();return;}
    const npc=nearNPC();if(npc){const ev=data.events[npc.event];if(eventOpen(npc.event)){openEvent(npc,ev);return;}const why=ev&&ev.stages.includes(state.stage)?'지난번 선택이 마을 사람들의 기억에 남아 있어요.':'지금은 다른 시기의 이야기가 기다리고 있어요.';showModal(npc.name+' · '+npc.role,why,'',r=>actions(r,[['계속 탐험',closeModal]]));return;}
    const door=buildingByDoor();if(door){enterInterior(door);return;}
    showToast('주민 옆에서 말 걸기를 누르세요. 문 앞에서는 건물에 들어갈 수 있어요.');
  }
  function openEvent(npc,ev){const buttons=Object.entries(ev.choices).map(([id,c])=>`<button data-choice="${safe(id)}"><div>${safe(c.label)}</div><div class="option-note">${safe(c.text)}</div></button>`).join('');showModal(ev.title,ev.intro,`<div class="options">${buttons}</div>`,root=>{
    root.querySelectorAll('[data-choice]').forEach(b=>b.addEventListener('click',()=>{emit({type:'choose',event_id:npc.event,choice_id:b.dataset.choice});closeModal();}));actions(root,[['아직 결정하지 않기',closeModal]]);
  });}
  function enterInterior(building){pos={...pos,zone:'inside:'+pos.zone,building:building,prevX:15,prevY:14,x:15,y:14,moving:false};mapKey='';refreshUI();showToast(building[4]+'에 들어왔습니다. 문 앞에서 말 걸기 = 밖으로 나가기');}
  function leaveInterior(){const outer=pos.zone.split(':')[1],b=pos.building||data.buildings[outer][0];pos={zone:outer,x:b[0]+Math.floor(b[2]/2),y:b[1]+b[3]+1,prevX:15,prevY:13,dir:'down',moving:false,moveTime:0};mapKey='';refreshUI();rememberPosition();}
  function interiorInfo(){if(pos.y>=15){leaveInterior();return}showModal('일터와 생활의 현장','책과 도구, 사람이 함께 있는 작은 공간입니다. 이곳에서 삶에 필요한 정보가 오고 갑니다.','',r=>actions(r,[['밖으로 나가기',()=>{closeModal();leaveInterior()}],['계속 둘러보기',closeModal]]));}
  function promptStage(){if(!state||modalOpen)return;const req=data.requirements[state.stage],todo=req.filter(e=>!state.decisions[e]);if(todo.length){showToast('먼저 만나 볼 주민: '+todo.map(e=>data.npcs.find(n=>n.event===e)?.name).join(', '));return}
    if(state.stage===2){showModal('내일로 남기는 생애 기록','세 생애의 경험을 정리하고, 내가 앞으로 준비하고 싶은 것을 생각해 보세요.','<blockquote>정답이 정해진 삶은 없습니다. 선택은 계속 이어집니다.</blockquote>',r=>actions(r,[['내 생애설계 카드 완성',()=>{emit({type:'finish'});closeModal();}],['마을을 더 둘러보기',closeModal]]));}
    else{const t=state.stage===0?'성인기':'노년기';showModal('시간의 문을 통과할까요?','지금까지의 선택이 시간의 흐름과 함께 마을의 새로운 풍경으로 이어집니다.',`<blockquote>다음 이야기: ${t} · 언제든 자유롭게 다시 탐험할 수 있어요.</blockquote>`,r=>actions(r,[['다음 생애로',()=>{emit({type:'advance'});closeModal()}],['아직 둘러보기',closeModal]]));}
  }
  function showMap(){const contents=`<div class="options two-column">${data.zones.map(z=>`<button data-warp="${z.id}"><b>${ZONE_SYMBOL[z.id]} ${safe(z.name)}</b><div class="option-note">${safe(z.blurb)}</div></button>`).join('')}</div><p class="option-note">도착한 뒤에는 자유롭게 움직이며 사건을 찾아보세요. 빠른 이동은 선택 결과에 영향을 주지 않습니다.</p>`;showModal('세월항 여행 지도','여섯 구역은 길로 서로 연결되어 있습니다. 원하는 장소로 바로 이동할 수도 있습니다.',contents,r=>{r.querySelectorAll('[data-warp]').forEach(b=>b.addEventListener('click',()=>{warp(b.dataset.warp);closeModal()}));actions(r,[['닫기',closeModal]]);});}
  function warp(zone){if(!data.zones.some(z=>z.id===zone))return;pos={zone,x:16,y:13,prevX:16,prevY:13,dir:'down',moving:false,moveTime:0};mapKey='';rememberPosition();refreshUI();showToast(data.zones.find(z=>z.id===zone).name+'에 도착했어요.');sound(620);}
  function showJournal(){const arr=state.journal||[],unseen=Object.entries(data.concepts).filter(([k])=>!state.concepts.includes(k)),memory=arr.slice(-12).reverse().map(j=>`<li><b>${j.age}세 · ${safe(j.title)}</b><div>${safe(j.choice)} — ${safe(j.outcome)}</div></li>`).join('');showModal('나의 생애 노트',`경험한 교과서 주제 ${state.concepts.length}/${Object.keys(data.concepts).length} · 선택한 사건 ${Object.keys(state.decisions).length}개`,`<div class="two-column"><div><b>나의 선택</b><ul>${memory||'<li>아직 기록이 없어요.</li>'}</ul></div><div><b>발견한 내용</b><ul>${state.concepts.map(k=>'<li>'+safe(data.concepts[k])+'</li>').join('')||'<li>주민과 이야기해 보세요.</li>'}</ul><hr class="divider"><b>아직 찾지 못한 단서</b><p>${unseen.length}개 남았습니다. 모든 단서를 다 찾아야 엔딩을 볼 수 있는 것은 아닙니다.</p></div></div>`,r=>actions(r,[['하루 시간표 미니게임',showSchedule],['닫기',closeModal]]));}
  function showSchedule(){const activities=['일','휴식','돌봄','여가'];let picks=[];function present(){const content=`<p>오늘 자유롭게 쓸 수 있는 시간은 <b>세 칸</b>입니다. 어떤 활동을 선택하시겠어요? 모두 필요하지만 한 번에 전부 할 수는 없습니다.</p><div class="options two-column">${activities.map(x=>`<button data-act="${x}">${x} ${picks.filter(y=>y===x).length?'✓':''}</button>`).join('')}</div><p><b>시간표: </b>${picks.length?picks.join(' → '):'아직 선택하지 않음'} (${picks.length}/3)</p>`;showModal('하루 시간 조율', '',content,r=>{r.querySelectorAll('[data-act]').forEach(b=>b.addEventListener('click',()=>{if(picks.length<3){picks.push(b.dataset.act);present()}}));actions(r,[['처음부터',()=>{picks=[];present()}],['선택 마무리',()=>{if(picks.length<3){showToast('세 칸을 채워 보세요.');return;}const omitted=activities.filter(a=>!picks.includes(a));closeModal();showModal('선택의 결과',`당신은 ${picks.join('·')}을(를) 골랐어요. 남은 ${omitted.join('·')||'활동'}에도 시간과 지원이 필요할 수 있습니다. 사람마다 중요한 것이 다릅니다.`,'<blockquote>일·가정 양립은 개인의 계획뿐 아니라 직장과 지역사회의 제도가 함께 뒷받침해야 합니다.</blockquote>',r2=>actions(r2,[['마을로',closeModal]]));}]]);});}present();}
  function refreshUI(){if(!state||!data)return;const zone=zoneInfo();const indoor=pos.zone.startsWith('inside:');$('zone-label').innerHTML=`<span class="mini-sun">☀</span> ${safe(indoor?(pos.building?.[4]||'실내'):zone?.name||'마을')}`;
    $('stage-pill').textContent='✧ '+data.stages[state.stage];$('age-pill').textContent=state.age+'세';$('stat-pill').textContent='✦ 관계 '+state.stats.bond;$('season').textContent=['봄','가을','겨울'][state.stage];$('ambient-label').textContent=['☀ 햇살 좋은 오후','❖ 계절이 깊어지는 거리','❄ 긴 시간이 흐른 마을'][state.stage];
    const titles=['어떤 어른이 될까?','함께 살아가는 방법','내 삶을 돌아보는 시간'];const descriptions=['일터지구의 선우, 주거지의 미라와 만나 직업·주거를 직접 선택해 보세요.','돌봄공원의 연주와 중앙광장의 하린을 만나 마을 문제와 정책을 연결해 보세요.','돌봄공원의 유진·태오, 강가의 유리, 광장의 수아에게서 노후 준비 네 분야를 경험하세요.'];
    $('task-title').textContent=state.ended?'완성된 이야기, 새로운 탐험':titles[state.stage];$('task-desc').textContent=state.ended?'생애설계 카드를 완성했습니다. 이제 세대 협력·정원·축제 등 남은 사건을 자유롭게 경험해 보세요.':descriptions[state.stage];const need=data.requirements[state.stage];let done=need.filter(k=>state.decisions[k]).length;$('req-count').textContent=done+' / '+need.length+' 필수 사건';$('learn-count').textContent='학습 단서 '+state.concepts.length+'개';$('progress-bar').style.width=(100*done/need.length)+'%';const next=$('next-stage');next.disabled=done!==need.length||state.ended;next.innerHTML=state.ended?'생애설계 완성 ✦':state.stage===2?'생애설계 카드 완성 <span>✦</span>':'다음 생애로 이동하기 <span>↗</span>';
    $('zone-subtitle').textContent=zone?.blurb||'조용한 실내 풍경';const icons=ZONE_SYMBOL;$('mini-map').innerHTML=data.zones.map(z=>`<button class="zone-cell ${z.id===pos.zone?'active':''}" data-zone="${z.id}"><span class="glyph">${icons[z.id]}</span>${safe(z.name)}</button>`).join('');$('mini-map').querySelectorAll('[data-zone]').forEach(b=>b.addEventListener('click',()=>warp(b.dataset.zone)));
    $('memory-content').innerHTML=state.journal.length?state.journal.slice(-3).reverse().map(j=>`<div class="memory-line"><i>${j.age}세</i>${safe(j.choice)}</div>`).join(''):'<div class="empty-memory">첫 선택이 곧 나의 이야기가 됩니다.</div>';
    $('reflect-prompt').textContent=['나는 어떤 삶을 중요하게 생각할까?','가족 친화 문화는 누가 함께 만들까?','건강·여가·재무·관계를 어떻게 준비할까?'][state.stage];
  }
  function obstacle(zone,x,y){if(x<0||x>=MW||y<0||y>=MH)return false;if(zone.startsWith('inside:'))return y<3||y>=18||x<2||x>=28;
    for(const b of data.buildings[zone]||[]){if(x>=b[0]&&x<b[0]+b[2]&&y>=b[1]&&y<b[1]+b[3])return true}
    if(zone==='river'&&x>=25&&(y<10||y>14))return true;
    if(zone==='square'&&x>=14&&x<=17&&y>=9&&y<=11)return true;
    return false;
  }
  function tryMove(dx,dy,now){if(modalOpen||!state)return;const toX=pos.x+dx,toY=pos.y+dy;pos.dir=dx>0?'right':dx<0?'left':dy>0?'down':'up';
    if(pos.zone.startsWith('inside:')){if(toY>=18){leaveInterior();return;}if(obstacle(pos.zone,toX,toY))return;}
    else if(toX<0||toX>=MW||toY<0||toY>=MH){const here=data.zones.find(z=>z.id===pos.zone);const next=data.zones.find(z=>z.col===here.col+(toX<0?-1:toX>=MW?1:0)&&z.row===here.row+(toY<0?-1:toY>=MH?1:0));if(next){pos.zone=next.id;pos.x=toX<0?29:toX>=MW?0:Math.max(1,Math.min(28,pos.x));pos.y=toY<0?18:toY>=MH?0:Math.max(9,Math.min(16,pos.y));pos.prevX=pos.x;pos.prevY=pos.y;mapKey='';refreshUI();rememberPosition();sound(420);}return;}
    else if(obstacle(pos.zone,toX,toY))return;
    pos.prevX=pos.x;pos.prevY=pos.y;pos.x=toX;pos.y=toY;pos.moveTime=now;pos.moving=true;walkTick++;if(walkTick%6===0)rememberPosition();
    if(pos.zone.startsWith('inside:')&&pos.y>=16)showToast('한 칸 더 내려가면 건물 밖으로 나갑니다.');
  }
  function updateMovement(now){if(now-lastStep<145||modalOpen||!state)return;let dx=0,dy=0;if(pressed.has('left'))dx=-1;else if(pressed.has('right'))dx=1;else if(pressed.has('up'))dy=-1;else if(pressed.has('down'))dy=1;if(dx||dy){tryMove(dx,dy,now);lastStep=now}}
  const keyToDirection={ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right',w:'up',s:'down',a:'left',d:'right',W:'up',S:'down',A:'left',D:'right'};
  window.addEventListener('keydown',e=>{if(e.target.tagName==='TEXTAREA'||e.target.tagName==='INPUT')return;const dir=keyToDirection[e.key];if(dir){e.preventDefault();pressed.add(dir);}else if(e.key==='Enter'||e.key===' '){e.preventDefault();if(modalOpen)return;interact();}else if(e.key.toLowerCase()==='m'){e.preventDefault();showMap();}else if(e.key.toLowerCase()==='j'){e.preventDefault();showJournal();}else if(e.key==='Escape'&&modalOpen)closeModal();});
  window.addEventListener('keyup',e=>{const dir=keyToDirection[e.key];if(dir){pressed.delete(dir);e.preventDefault()}});
  function stopAll(){pressed.clear();document.querySelectorAll('.dpad button').forEach(b=>b.classList.remove('pressed'))}
  window.addEventListener('blur',stopAll);document.addEventListener('visibilitychange',()=>{if(document.hidden)stopAll()});
  document.querySelectorAll('[data-dir]').forEach(el=>{const dir=el.dataset.dir;el.addEventListener('pointerdown',e=>{e.preventDefault();el.setPointerCapture?.(e.pointerId);pressed.add(dir);el.classList.add('pressed');canvas.focus()});const stop=e=>{pressed.delete(dir);el.classList.remove('pressed');e.preventDefault()};['pointerup','pointercancel','lostpointercapture'].forEach(event=>el.addEventListener(event,stop));});
  $('touch-talk').addEventListener('click',interact);$('touch-map').addEventListener('click',showMap);$('map-open').addEventListener('click',showMap);$('journal-open').addEventListener('click',showJournal);$('next-stage').addEventListener('click',promptStage);$('audio-toggle').addEventListener('click',()=>{audio=!audio;$('audio-toggle').textContent=audio?'♪ 켜짐':'♪ 꺼짐';if(audio)sound(510)});
  // --------- Pixel drawing: original geometric assets, never proprietary sprites. -------
  const palette={grass:['#83aa7a','#7ca473','#88af7d','#71996f'],amber:['#bca773','#b6a06d','#c5ad7a','#b8a16c'],stone:['#99aaa0','#92a59c','#a6b6ac','#8c9d95'],green:['#7fba92','#84b69a','#90c39b','#7fb08a'],river:['#91b59b','#8eb6a2','#95baaa','#8aab9c']};
  function rect(c,x,y,w,h,color){c.fillStyle=color;c.fillRect(Math.round(x),Math.round(y),Math.round(w),Math.round(h));}
  function isRoad(z,x,y){const main=y>=10&&y<=14,vertical=x>=14&&x<=17&&y>=8;return main||vertical||z==='square'&&x>=8&&x<=23&&y>=8&&y<=15}
  function drawGrass(c,z,x,y){const seed=hash(x,y,z.length),base=palette[z==='square'?'grass':(zoneInfo()?.theme||'grass')]||palette.grass;const X=x*TILE,Y=y*TILE;rect(c,X,Y,TILE,TILE,base[seed%4]);if(seed%7===0){rect(c,X+4,Y+6,2,5,'#5d936b');rect(c,X+7,Y+8,2,3,'#5b916b');}if(seed%5===0){rect(c,X+21,Y+19,2,2,'#d8dca8');rect(c,X+24,Y+22,2,3,'#477d61');}if(seed%13===0){rect(c,X+10,Y+21,3,3,'#e8cf9a');rect(c,X+12,Y+19,2,2,'#f6e8bf')}}
  function drawRoad(c,z,x,y){const X=x*TILE,Y=y*TILE,stone=z==='square'||z==='work';const base=stone?'#b9baa9':'#ceb99a';rect(c,X,Y,32,32,base);rect(c,X,Y,32,1,'#dbcbb5');rect(c,X+hash(x,y)%16,Y+13,12,1,stone?'#969e99':'#af9c80');rect(c,X+4,Y+26,7,1,'#aa9f8f');if((x+y)%4===0)rect(c,X+19,Y+7,2,2,'#e8d7bb');if(stone){rect(c,X+16,Y,1,32,'#acafa4');rect(c,X,Y+16,32,1,'#a6ada4')}}
  function drawTree(c,x,y,n=0){const X=x*TILE,Y=y*TILE;rect(c,X+13,Y+16,8,22,'#725842');rect(c,X+10,Y+24,14,4,'#574936');rect(c,X+2,Y+11,26,15,'#2d6758');rect(c,X+5,Y+5,22,17,'#3d8469');rect(c,X+9,Y+1,17,14,'#569b75');rect(c,X+4,Y+9,8,8,'#76ae76');rect(c,X+17,Y+6,7,5,'#9dc38e');rect(c,X+18,Y+17,7,5,'#1f5f55');if(state.stage===1){rect(c,X+12,Y+6,5,4,'#e2ad64');rect(c,X+7,Y+13,4,4,'#e8bd77');}if(state.stage===2){rect(c,X+13,Y+5,5,3,'#e5e3dc');rect(c,X+19,Y+18,5,3,'#e4e3dc')}}
  function drawFlowerbed(c,x,y){const X=x*TILE,Y=y*TILE;rect(c,X+3,Y+18,28,13,'#4c7b5b');rect(c,X+2,Y+16,28,3,'#a58b6a');for(let j=0;j<4;j++){let px=X+7+j*7,py=Y+18+(j%2)*6;rect(c,px,py,4,4,j%2?'#efb27f':'#e9cfb0');rect(c,px+1,py+1,2,2,'#f8eac3')}}
  function drawLamp(c,x,y){const X=x*TILE,Y=y*TILE;rect(c,X+14,Y+6,4,29,'#485d55');rect(c,X+9,Y+5,14,3,'#354f4d');rect(c,X+12,Y+7,9,8,'#f6d494');rect(c,X+15,Y+8,4,6,'#fff2ba');rect(c,X+9,Y+2,14,3,'#506661')}
  function drawWater(c,x,y,t){const X=x*TILE,Y=y*TILE,blue=['#4d929f','#579aa7','#599dac','#539ba4'][hash(x,y)%4];rect(c,X,Y,32,32,blue);rect(c,X+3+hash(y,x)%9,Y+9,13,2,'#b4ddd3');rect(c,X+18,Y+24,9,2,'#9cced1');if(Math.sin(t/700+x*3+y)>0.6)rect(c,X+8,Y+17,9,1,'#d5eeee')}
  function drawDecor(c,z,t){for(let x=0;x<MW;x++)for(let y=0;y<MH;y++){if(z==='river'&&x>=25){drawWater(c,x,y,t);if(y>=10&&y<=14){rect(c,x*TILE,y*TILE,32,32,'#bda784');rect(c,x*TILE,y*TILE+3,32,2,'#eee0b1');rect(c,x*TILE,y*TILE+24,32,3,'#826e56')}continue}isRoad(z,x,y)?drawRoad(c,z,x,y):drawGrass(c,z,x,y)}
    // Evergreen silhouettes, flower borders, planters. Dense, but all paths stay clear.
    for(const [x,y] of [[0,1],[1,6],[0,15],[27,8],[27,16],[5,16],[25,16]]){if(z==='river'&&x>24)continue;drawTree(c,x,y,hash(x,y))}
    for(const [x,y] of [[3,15],[8,16],[22,16]])drawFlowerbed(c,x,y);
    for(const [x,y] of [[7,10],[25,11]])drawLamp(c,x,y);
    if(z==='square'){rect(c,14*TILE,9*TILE,4*TILE,3*TILE,'#81999b');rect(c,14*TILE+9,9*TILE+9,4*TILE-18,3*TILE-15,'#5599ab');rect(c,15*TILE+10,9*TILE+3,7,37,'#b9d1c0');rect(c,15*TILE+2,9*TILE+10,25,4,'#dce2d2');rect(c,14*TILE+20,9*TILE+32,7,7,'#e9eee4');}
    if(z==='welfare'&&state.flags.policy==='고령자 지원'){for(const [x,y] of [[4,15],[22,15]]){rect(c,x*TILE,y*TILE+14,26,5,'#b17d55');rect(c,x*TILE+4,y*TILE+19,3,9,'#665b50');rect(c,x*TILE+20,y*TILE+19,3,9,'#665b50')}}
    if(z==='shop'&&state.flags.policy==='세대 협력'){for(let x=4;x<27;x+=3){rect(c,x*TILE,8*TILE+2,17,7,x%2?'#f4dd9d':'#ed9d80');rect(c,x*TILE+8,8*TILE+9,2,2,'#f5ecdb')}}
    (data.buildings[z]||[]).forEach(b=>drawBuilding(c,b,z));
    // Ground-level shadows below props
    for(let x=0;x<MW;x++)if((x+z.length)%9===0){rect(c,x*TILE+4,17*TILE+12,14,2,'#638f76')}
  }
  function drawBuilding(c,b,z){const [x,y,w,h,name,type]=b,X=x*TILE,Y=y*TILE,WW=w*TILE,HH=h*TILE,doorX=X+Math.floor(w/2)*TILE;
    let roof={'school':'#b97760','hall':'#508777','clinic':'#7b9daf','cafe':'#ca8662','theater':'#986c8e','closed':'#757d7c','factory':'#7e8da1','office':'#8b9288','library':'#847fa3','care':'#8f9fb8','house':'#c49076','home':'#b78973','bread':'#cf9d63'}[type]||'#a98270';
    if(type==='closed'&&state.flags.policy==='청년 지원')roof='#639382';
    rect(c,X+1,Y+13,WW,HH-1,'#263f42');rect(c,X+4,Y+20,WW-9,HH-20,'#e8d7b2');rect(c,X+9,Y+29,WW-18,HH-32,'#d4c6a9');
    rect(c,X-4,Y+1,WW+8,15,'#4d534e');rect(c,X-8,Y+3,WW+16,25,roof);rect(c,X-7,Y+6,WW+14,4,'#ffffff29');rect(c,X-6,Y+26,WW+12,6,'#494d4d');
    for(let j=1;j<w-1;j+=2){const winX=X+j*TILE+2;if(winX>doorX-24&&winX<doorX+18)continue;rect(c,winX,Y+41,21,27,'#6e655c');rect(c,winX+3,Y+45,15,20,'#739faa');rect(c,winX+10,Y+45,2,20,'#ead9bb');rect(c,winX+4,Y+49,6,5,'#c8cfa6');rect(c,winX+3,Y+64,15,3,'#d5a76d')}
    rect(c,doorX,Y+47,25,HH-46,'#554d4b');rect(c,doorX+3,Y+50,19,HH-52,'#7e9688');rect(c,doorX+4,Y+52,7,14,'#a8bcb4');rect(c,doorX+19,Y+71,3,3,'#e9d189');
    const signW=Math.min(WW-18,166);rect(c,X+(WW-signW)/2,Y+28,signW,18,'#2c4e55');rect(c,X+(WW-signW)/2+2,Y+30,signW-4,14,'#3a6670');c.textAlign='center';c.textBaseline='middle';c.fillStyle='#fff2ce';c.font='bold 13px sans-serif';let label=name;
    if(type==='closed'&&state.flags.policy==='청년 지원')label='청년 공유공간';
    if(type==='closed'&&state.stage>=1&&state.flags.policy!=='청년 지원')label='임대 문의';
    c.fillText(label,X+WW/2,Y+37,signW-7);
    // Candles, awnings and entrance plants.
    if(type==='cafe'||type==='bread'){for(let j=0;j<5;j++)rect(c,X+9+j*(WW-18)/5,Y+47,(WW-18)/5,6,j%2?'#e8d8ab':'#d17c68')}
    rect(c,doorX-18,Y+HH-14,13,10,'#466d54');rect(c,doorX-17,Y+HH-20,11,10,'#82ab69');rect(c,doorX+27,Y+HH-14,13,10,'#466d54');rect(c,doorX+28,Y+HH-20,11,10,'#83b67b');
  }
  function makeSprite(who,dir='down',frame=0,old=false){const sw=16,sh=24,off=document.createElement('canvas');off.width=sw;off.height=sh;const c=off.getContext('2d');c.imageSmoothingEnabled=false;const skin=['#f1c099','#bb846b','#805a4d'][who.skin%3];const dark=['#674c3a','#3e3936','#2c3037','#bdb5a2','#805a45','#a6a8a4'][who.hair%6];const jacket=['#4c7981','#b76962','#8c7eaa','#c89a5a','#6b9b7b','#c77d7a'][who.outfit%6],pants=['#4c5760','#6c6159','#4a5570'][who.outfit%3];const R=(x,y,w,h,color)=>rect(c,x,y,w,h,color);
    R(5,1,6,2,dark);R(4,3,8,5,dark);R(5,6,6,5,skin);R(4,6,2,3,dark);R(10,6,2,3,dark);
    if(who.hair%6===3){R(3,7,2,8,dark);R(11,7,2,8,dark)}if(who.hair%6===4)R(4,1,8,4,dark);if(who.hair%6===5){R(4,3,8,3,'#b9bab4');R(6,4,5,3,'#dcddcf')}
    if(dir!=='up'){R(7,8,1,1,'#473a34');R(10,8,1,1,'#473a34');if(dir==='right')R(7,8,2,1,skin);}
    R(5,11,7,7,jacket);R(7,12,3,1,'#eff0ce');R(3,12,2,6,jacket);R(12,12,2,6,jacket);R(3,17,2,2,skin);R(12,17,2,2,skin);
    R(5,18,7,3,pants);R(5,21,3,2+(frame?1:0),pants);R(9,21+(frame?1:0),3,2,pants);R(5,23,3,1,'#4b413e');R(9,23,3,1,'#4b413e');
    if(who.outfit%6===0){R(5,12,2,3,'#e0d3b3');R(10,12,2,3,'#e0d3b3')}if(who.outfit%6===2)R(6,12,5,3,'#f0c88f');if(who.outfit%6===4){R(6,13,4,2,'#f2eece');R(5,16,7,1,'#b9dfd2')}
    if(old){R(5,3,6,1,'#b9b6ad');R(9,7,2,1,'#eee4d4');}return off;
  }
  const spriteCache=new Map();function sprite(who,dir,frame,old){const key=[who.skin,who.hair,who.outfit,dir,frame,old].join(':');if(!spriteCache.has(key))spriteCache.set(key,makeSprite(who,dir,frame,old));return spriteCache.get(key)}
  function drawPerson(c,who,x,y,dir='down',frame=0,old=false){rect(c,x-11,y+4,24,5,'#28413b88');c.drawImage(sprite(who,dir,frame,old),Math.round(x-15),Math.round(y-44),30,47)}
  function nameLabel(c,x,y,text,active){c.textAlign='center';c.font='bold 12px sans-serif';const bw=Math.max(40,Math.min(150,c.measureText(text).width+16));rect(c,x-bw/2,y-61,bw,19,active?'#2e5260':'#243a3e');rect(c,x-bw/2,y-61,bw,2,active?'#edc486':'#759893');c.fillStyle=active?'#f9e5af':'#e9e7d1';c.textBaseline='middle';c.fillText(text,x,y-51);if(active){rect(c,x-6,y-86,13,17,'#f4c67b');c.fillStyle='#634b30';c.font='bold 12px sans-serif';c.fillText('!',x,y-77)}}
  function drawInside(c){for(let y=0;y<MH;y++)for(let x=0;x<MW;x++){const X=x*TILE,Y=y*TILE;rect(c,X,Y,32,32,y<3?'#6b7774':(x+y)%2?'#d9c6a0':'#e2d2b0');if(y>=3){rect(c,X+1,Y,31,1,'#cbb48f');rect(c,X,Y+1,1,30,'#cbb48f')}}rect(c,0,0,W,80,'#54717a');rect(c,0,77,W,18,'#475962');rect(c,90,122,170,85,'#8a6a51');rect(c,104,139,142,16,'#d1af75');rect(c,700,122,170,85,'#8a6a51');rect(c,714,139,142,16,'#d1af75');for(let x=320;x<640;x+=100){rect(c,x,140,78,140,'#8d6f56');for(let j=0;j<4;j++){rect(c,x+9,155+j*28,50,13,j%2?'#89a4a3':'#c49b74')}}rect(c,435,340,95,50,'#ad8662');rect(c,452,358,61,15,'#e4c38f');rect(c,456,570,42,24,'#5e7f73');c.textAlign='center';c.fillStyle='#ecf1d9';c.font='bold 25px sans-serif';c.fillText(pos.building?.[4]||'마을 시설',W/2,44);c.font='bold 14px sans-serif';c.fillStyle='#3a5555';c.fillText('문을 통해 나가려면 아래로 이동하세요',W/2,551);drawPerson(c,LOOKS[state.appearance%6],pos.x*TILE+16,pos.y*TILE+28,pos.dir,Math.floor(performance.now()/190)%2,state.stage===2)}
  function cachedLayer(now){const key=pos.zone+'-'+state.stage+'-'+(state.flags.policy||'none');if(mapKey!==key){mapKey=key;mapCanvas=document.createElement('canvas');mapCanvas.width=W;mapCanvas.height=H;const cc=mapCanvas.getContext('2d');drawDecor(cc,pos.zone,now);}}
  function draw(now){ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,W,H);if(!state){rect(ctx,0,0,W,H,'#487666');ctx.textAlign='center';ctx.textBaseline='middle';ctx.font='bold 36px sans-serif';ctx.fillStyle='#ffeed0';ctx.fillText('🌅 세월항 — 내일을 잇는 마을',W/2,H/2);return;}
    if(pos.zone.startsWith('inside:')){drawInside(ctx);return}
    cachedLayer(now);ctx.drawImage(mapCanvas,0,0);const npcList=data.npcs.filter(n=>n.zone===pos.zone);const current=Math.floor(now/450)%2;
    const actors=npcList.map(n=>({kind:'npc',y:n.y,x:n.x,who:n}));actors.push({kind:'player',x:pos.x,y:pos.y});actors.sort((a,b)=>a.y-b.y);
    actors.forEach(a=>{if(a.kind==='npc'){const n=a.who,shift=Math.sin(now/1000+n.x+n.y)*1.2;drawPerson(ctx,n,n.x*TILE+16,n.y*TILE+32+shift,'down',current,state.stage===2&&['grand','bank'].includes(n.id));nameLabel(ctx,n.x*TILE+16,n.y*TILE+32+shift,n.name,eventOpen(n.event));}
      else{const ratio=Math.min(1,(now-pos.moveTime)/145),smooth=ratio*ratio*(3-2*ratio),dx=pos.prevX+(pos.x-pos.prevX)*smooth,dy=pos.prevY+(pos.y-pos.prevY)*smooth;drawPerson(ctx,LOOKS[state.appearance%6],dx*TILE+16,dy*TILE+32,pos.dir,Math.floor(now/170)%2,state.stage===2);rect(ctx,dx*TILE+9,dy*TILE-25,14,2,'#f4e6b0');}
    });
    // Zone changes use a vignette, while leaving the pixels crisp.
    rect(ctx,0,0,W,5,'#213d4880');rect(ctx,0,H-5,W,5,'#213d4880');
    if(modalOpen)return;const neighbor=nearNPC();if(neighbor){rect(ctx,355,H-67,250,32,'#203b42d9');ctx.fillStyle='#f8edc9';ctx.font='bold 14px sans-serif';ctx.textAlign='center';ctx.fillText('✦ '+neighbor.name+' · 말 걸기',W/2,H-46)}else if(buildingByDoor()){rect(ctx,370,H-67,220,32,'#203b42d9');ctx.fillStyle='#f8edc9';ctx.font='bold 14px sans-serif';ctx.textAlign='center';ctx.fillText('⌂ 건물 안으로',W/2,H-46)}
  }
  function loop(now){updateMovement(now);draw(now);if(floatingTime&&now>floatingTime){$('toast').classList.add('hidden');floatingTime=0;}requestAnimationFrame(loop)}
  requestAnimationFrame(loop);
  // Direct static-page opening shows an honest preview (no fake progress/save mode).
  setTimeout(()=>{if(!state&&!window.frameElement){showToast('플레이하려면 상위 폴더에서 streamlit run app.py 를 실행하세요.')};setHeight()},600);
  if('ResizeObserver' in window)new ResizeObserver(()=>setHeight()).observe(document.documentElement);
  componentReady();
})();
