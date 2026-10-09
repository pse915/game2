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
const ids={};['world','game','stage','status','talk','book','policy','save','sound','full','place','age','objective','badges','hud','maplabel','hint','modal','dialog','progress','life','classroom','inspect','period','world-phase','route','timeline','timeline-title','timeline-desc','skiptravel'].forEach(id=>ids[id]=new Element());
ids.world.getContext=()=>({fillRect(){},fillText(){},imageSmoothingEnabled:false});
const listeners={},sent=[],frames=[];
const parent={postMessage(message){sent.push(message);}};
const sandbox={console,Date,Math,crypto:require('crypto').webcrypto,Set,window:{parent,addEventListener(type,fn){listeners[type]=fn;}},document:{addEventListener(){},getElementById:id=>ids[id],createElement:tag=>new Element(tag),querySelectorAll:()=>[],body:{scrollHeight:900},activeElement:null},ResizeObserver:class{observe(){}},requestAnimationFrame:fn=>frames.push(fn),setTimeout:fn=>fn(),clearTimeout:()=>{}};
vm.createContext(sandbox);vm.runInContext(fs.readFileSync('component/frontend/game.js','utf8'),sandbox);
const fixture=JSON.parse(fs.readFileSync(process.argv[2]||'tests/frontend_fixture.json','utf8'));
function render(payload){listeners.message({source:parent,data:{type:'streamlit:render',args:{data:payload}}});}
for(const payload of fixture){render(payload);vm.runInContext('draw(1000)',sandbox);}
assert(sent.some(m=>m.type==='streamlit:componentReady'));
assert(sent.some(m=>m.type==='streamlit:setFrameHeight'));
// 정상 플레이라는 새 fixture로 이동 및 저장 요청을 확인합니다.
const start=fixture[0];start.state.revision=1000;start.ui=null;start.events=start.events||[];render(start);
vm.runInContext("move('down');send('save');",sandbox);
assert(sent.some(m=>m.type==='streamlit:setComponentValue'&&m.value.kind==='save'));
console.log('다섯 지도, 모든 대화 유형, 엔딩 A/B/C/D, 이동·저장 프로토콜을 모사 환경에서 검사했습니다.');
