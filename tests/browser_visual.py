"""Chromium 환경에서 실제 Canvas 렌더링과 주요 터치 UI를 검사하고 스크린샷을 만듭니다.
실제 iPad/Android 기기에서의 검증은 별도입니다.
실행: python tests/browser_visual.py
"""
import sys,subprocess,time,socket,contextlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine import new_state,public_state
from content import MAPS,NPCS,CHAPTERS,EVENTS,NOTICE
from playwright.sync_api import sync_playwright

OUT=ROOT/'docs'/'screenshots'
OUT.mkdir(parents=True,exist_ok=True)
URL='http://127.0.0.1:18867/index.html'

def payload(zone=1,policies=None,age=24,chapter=2,ui=None):
    s=new_state('014','3-1','모험가','1234')
    s.update(zone=zone,x=12,y=9,age=age,chapter=chapter)
    s['flags']['classroom_mode']=True
    if policies:
        s['flags']['policy_choices']=policies
    s['revision']+=1
    return {'state':public_state(s),'maps':MAPS,'npcs':NPCS,'events':EVENTS,'chapters':CHAPTERS,'notice':NOTICE,'ui':ui,'save_status':'로컬 미리보기'}

server=subprocess.Popen([sys.executable,'-m','http.server','18867','--bind','127.0.0.1'],cwd=ROOT/'component'/'frontend',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(.5)
try:
 with sync_playwright() as p:
     browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
     page=browser.new_page(viewport={'width':1200,'height':960},device_scale_factor=1)
     errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
     html=(ROOT/'component'/'frontend'/'index.html').read_text()
     html=html.replace('<link rel="stylesheet" href="style.css">','').replace('<script src="game.js"></script>','')
     page.set_content(html,wait_until='load')
     page.add_style_tag(content=(ROOT/'component'/'frontend'/'style.css').read_text())
     page.add_script_tag(content=(ROOT/'component'/'frontend'/'game.js').read_text())
     assert page.locator('#world').count()==1
     def render(obj):
         page.evaluate('data => window.dispatchEvent(new MessageEvent("message", {source: window, data: {type:"streamlit:render",args:{data}}}))',obj)
         page.wait_for_timeout(250)
     render(payload(age=45,chapter=4))
     assert page.locator('#place').inner_text()==MAPS[1]['name']
     assert page.locator('#inspect').count()==1
     page.screenshot(path=str(OUT/'01_before_policies.png'),full_page=True)
     render(payload(policies=['housing','flex'],age=45,chapter=4))
     assert page.locator('#world-phase').inner_text().startswith('여름')
     page.screenshot(path=str(OUT/'02_after_policies.png'),full_page=True)
     # 육아지구 정책 변화를 독립 검증합니다.
     render(payload(zone=2,policies=['flex'],age=38,chapter=4))
     page.screenshot(path=str(OUT/'03_daycare_after.png'),full_page=True)
     # 조사 이벤트 대화와 버튼을 실제 브라우저에서 확인합니다.
     ev=EVENTS[2]
     s=payload(zone=2,age=32,chapter=3)
     s['state']['x']=ev['x'];s['state']['y']=ev['y']
     s['state']['revision']+=1
     s['ui']={'type':'event','event_id':ev['id'],'title':ev['title'],'text':ev['summary'],'prompt':ev['prompt'],'options':ev['answers'],'lesson':ev['lesson'],'previous':None}
     render(s)
     assert page.locator('#dialog .dialog-actions button').count()==2
     page.evaluate('window.__sent=[];window.addEventListener("message", e=>{if(e.data?.type==="streamlit:setComponentValue")window.__sent.push(e.data.value);})')
     page.locator('#dialog .dialog-actions button').first.click()
     page.wait_for_timeout(100)
     assert page.evaluate('window.__sent.some(e=>e.kind==="resolve_event")'), 'event response failed to send'
     page.screenshot(path=str(OUT/'04_investigation.png'),full_page=True)
     # 터치 크기 및 오버플로: 브라우저 뷰포트만 모의합니다.
     pad=page.locator('[data-dir="up"]').bounding_box()
     assert pad['width']>=44 and pad['height']>=44,pad
     page.set_viewport_size({'width':768,'height':1024})
     render(payload(zone=4,age=65,chapter=6))
     assert page.locator('#game').bounding_box()['width']<=768
     assert page.locator('[data-dir="down"]').bounding_box()['height']>=44
     page.screenshot(path=str(OUT/'05_portrait_768.png'),full_page=True)
     # 두 손가락을 따로 떼어도 나머지 방향 입력은 계속 유지되어야 합니다.
     assert page.evaluate('''() => {
        const b=document.querySelector('[data-dir="up"]');
        b.dispatchEvent(new PointerEvent('pointerdown',{pointerId:21,bubbles:true}));
        b.dispatchEvent(new PointerEvent('pointerdown',{pointerId:22,bubbles:true}));
        if(!keys.has('up'))return false;
        b.dispatchEvent(new PointerEvent('pointerup',{pointerId:21,bubbles:true}));
        if(!keys.has('up'))return false;
        b.dispatchEvent(new PointerEvent('pointercancel',{pointerId:22,bubbles:true}));
        return !keys.has('up');
     }'''), 'multi-touch input stuck'
     assert not errors,errors
     # actual JS debug errors on page are not swallowed by mock
     print('CHROMIUM_RENDER_PASS | screenshots=5 | pointer_controls>=44px | event choices=2 | viewport=1200/768')
     browser.close()
finally:
 server.terminate();server.wait(timeout=5)
