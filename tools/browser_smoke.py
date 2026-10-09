"""Canvas browser smoke check WITHOUT local network/file access.
Embeds source and assets into a blank Playwright page for isolated testing.
Does NOT verify Streamlit, device browsers, or remote Google Sheets.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json,sys,base64
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from content import public_content
from engine import new_state

state=new_state('2-3','07','체험 학생',1)
payload={'type':'streamlit:render','args':{'state':state,'content':public_content()}}
assets={path.stem:'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode() for path in (ROOT/'frontend'/'assets').glob('*.png')}
html=(ROOT/'frontend'/'index.html').read_text(encoding='utf8').replace('<link rel="stylesheet" href="style.css">','').replace('<script src="game.js" defer></script>','')
js=(ROOT/'frontend'/'game.js').read_text(encoding='utf8').replace("im.src='assets/'+name+'.png'",'im.src=window.TEST_ASSETS[name]')
js=js.replace('  componentReady();', '  window.__smoke={position:()=>({...pos}),hall:(f)=>enterSchoolHall(f),room:(id)=>enterSchoolRoom(id),move:(x,y)=>{pos.x=x;pos.y=y;pos.prevX=x;pos.prevY=y;}, blocked:(x,y)=>obstacle(pos.zone,x,y), route:(x,y)=>{pathNextStep(pos.x,pos.y,x,y,pos.zone);return routeMemo.route||[];}, interact:()=>schoolInteract()}; componentReady();')
css=(ROOT/'frontend'/'style.css').read_text(encoding='utf8')
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-gpu'])
    page=browser.new_page(viewport={'width':1320,'height':950},device_scale_factor=1)
    errs=[];page.on('pageerror',lambda exc:errs.append(str(exc)))
    page.set_content(html)
    page.add_style_tag(content=css)
    page.evaluate('(assets) => {window.TEST_ASSETS=assets;}',assets)
    page.add_script_tag(content=js)
    page.evaluate('(payload) => window.postMessage(JSON.parse(payload),"*")',json.dumps(payload,ensure_ascii=False))
    page.wait_for_timeout(450)
    assert page.locator('#stage-pill').inner_text().strip()=='✧ 청년기'
    assert '별빛' in page.locator('#zone-label').inner_text()
    page.screenshot(path=str(ROOT/'docs'/'업데이트_마을_스크린샷.png'),full_page=True)
    # A fresh game starts directly in front of the school gate.
    assert page.evaluate('window.__smoke.position()')["x"]==7
    page.keyboard.press('Enter')
    page.wait_for_timeout(180)
    school_text=page.locator('#zone-label').inner_text()
    print('school label:',school_text)
    assert '서라벌여중' in school_text
    page.screenshot(path=str(ROOT/'docs'/'업데이트_학교복도_스크린샷.png'),full_page=True)
    # Browser graph test: each room's door has a navigable route through the L, no wall crossing.
    doors=public_content()['school']['floors']
    for f,rooms in doors.items():
        page.evaluate('(f)=>window.__smoke.hall(Number(f))',f)
        for room in rooms:
            route=page.evaluate('(door)=>window.__smoke.route(door[0],door[1])',room['door'])
            assert all(page.evaluate('(p)=>!window.__smoke.blocked(p[0],p[1])',point) for point in route),room
            assert (route or abs(room['door'][0]-15)+abs(room['door'][1]-9)<=1),room
        page.screenshot(path=str(ROOT/'docs'/f'학교_{f}층_ㄱ자복도.png'),full_page=True)
    page.evaluate('window.__smoke.hall(1)')
    # Explicitly verify a path around the 90-degree bend.
    page.evaluate('window.__smoke.move(21,9)')
    around=page.evaluate('window.__smoke.route(7,16)')
    assert any(x<=8 and y>=10 for x,y in around), around
    # Enter and exit through the correct L-wing room door.
    page.evaluate('window.__smoke.hall(1)')
    page.evaluate('window.__smoke.move(7,11)')
    page.evaluate('window.__smoke.interact()')
    assert '학습지원실2' in page.locator('#zone-label').inner_text()
    page.evaluate('window.__smoke.move(15,16)')
    page.evaluate('window.__smoke.interact()')
    back=page.evaluate('window.__smoke.position()')
    assert back['zone']=='school:hall:1' and (back['x'],back['y'])==(7,11), back
    # Floor transitions use named stairways, not a teleporter anywhere in the hall.
    page.evaluate('window.__smoke.move(27,10)')
    page.evaluate('window.__smoke.interact()')
    assert page.locator('#modal-content').inner_text().find('3층으로 이동')>=0
    page.get_by_role('button',name='3층으로 이동').click()
    assert page.evaluate('window.__smoke.position().zone')=='school:hall:3'
    page.evaluate('window.__smoke.hall(1)')
    print('L-wing door entry/return and staircase floor changes verified')
    print('L-shaped bent corridor routing and every room door verified')
    page.locator('#touch-map').click()
    assert page.locator('#modal-content .school-directory').count()==1
    page.locator('[data-room="1-2"]').click()
    assert 'hidden' in page.locator('#modal-layer').get_attribute('class')
    print('school directory selection verified')
    page.evaluate('window.__smoke.room("1-2")')
    page.wait_for_timeout(200)
    assert '1-2 교실' in page.locator('#zone-label').inner_text()
    page.screenshot(path=str(ROOT/'docs'/'업데이트_교실_스크린샷.png'),full_page=True)
    page.evaluate('window.__smoke.move(14,10)')
    page.evaluate('window.__testMessages=[];window.addEventListener("message",e=>{if(e.data?.type==="streamlit:setComponentValue")window.__testMessages.push(e.data.value)})')
    page.keyboard.press('Enter')
    assert page.locator('#modal-content').inner_text().find('이원희')>=0
    page.locator('#modal-content .dialog-actions button').first.click()
    page.wait_for_timeout(150)
    emitted=page.evaluate('window.__testMessages[0]')
    print('school activity emitted:',{k:emitted[k] for k in ('type','room_id','object_id','choice_id')})
    assert emitted['type']=='school_activity' and emitted['room_id']=='1-2'
    from engine import apply
    updated,msg=apply(state,emitted)
    assert updated['revision']==1 and '1-2:teacher' in updated['school_records']
    # Re-render from server proves school data stays consistent after save.
    page.evaluate('(payload)=>window.postMessage(JSON.parse(payload),"*")',json.dumps({'type':'streamlit:render','args':{'state':updated,'content':public_content()}},ensure_ascii=False))
    page.wait_for_timeout(200)
    assert not errs,errs
    print('school activity save and restore verified')
    page.set_viewport_size({'width':810,'height':1100})
    page.evaluate('window.__smoke.hall(2)')
    page.wait_for_timeout(150)
    page.screenshot(path=str(ROOT/'docs'/'업데이트_태블릿_화면.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':800})
    pads=page.locator('.dpad button')
    sizes=[b.bounding_box() for b in pads.all()]
    assert all(size['width']>=44 and size['height']>=44 for size in sizes),sizes
    page.screenshot(path=str(ROOT/'docs'/'업데이트_모바일_화면.png'),full_page=True)
    start=page.evaluate('window.__smoke.position()')
    pad=page.locator('[data-dir="left"]')
    bounds=pad.bounding_box()
    page.mouse.move(bounds['x']+bounds['width']/2,bounds['y']+bounds['height']/2)
    page.mouse.down()
    page.wait_for_timeout(340)
    page.mouse.up()
    finish=page.evaluate('window.__smoke.position()')
    assert finish['x'] < start['x'], (start,finish)
    print('Virtual tablet direction-pad sustained pointer movement verified')
    print('tablet/phone layout and minimum 44px input sizes verified (simulated browser)')
    print('console errors:',errs)
    assert not errs
    browser.close()
