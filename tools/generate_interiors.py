"""Procedurally authored original interior PNGs; no external assets required."""
from pathlib import Path
import json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]/'frontend'/'assets'
manifest_path=ROOT/'manifest.json'; manifest=json.loads(manifest_path.read_text(encoding='utf8'))
THEMES={
'bread':('#fff0d6','#c7a27c','#a76a58','빵집'),
'cafe':('#eee0d6','#b98d7f','#70666e','카페'),
'closed':('#ded8cc','#afaaa0','#7e968e','새로운 공간'),
'hall':('#e8e4db','#9db8b0','#8a978c','마을회관'),
'library':('#f1e4d0','#ae9981','#709483','도서관'),
'factory':('#d9e1dd','#9cafa6','#737f89','공방'),
'office':('#e4e7ea','#9aaec2','#818ea8','사무실'),
'home':('#f7e7db','#c3a68b','#ae968d','공동주거'),
'house':('#efe2d7','#ccb48e','#8ba698','주거공간'),
'clinic':('#e3f2ed','#abc9c4','#699eab','보건시설'),
'care':('#f8eadf','#c7b1b0','#8ea39f','돌봄공간'),
'school':('#e9e0cc','#b7a0b6','#7fa1a2','배움공간'),
'theater':('#e6d3dd','#b08c9d','#775873','작은 극장'),
}
for kind,(wall,floor,accent,category) in THEMES.items():
    im=Image.new('RGB',(480,304),wall);d=ImageDraw.Draw(im)
    def R(box,c): d.rectangle(box,fill=c)
    R((0,106,479,303),floor);R((0,100,479,111),'#827d75')
    for y in range(112,304,16):
        d.line((0,y,479,y),fill='#ffffff55' if False else '#c1b3ac')
    for x in range(0,480,32): d.line((x,112,x,303),fill='#bbaea7')
    # Interior windows / trim, central display.
    for x in (32,398):
        R((x,17,x+44,85),'#e9dec7');R((x+4,21,x+40,81),'#8bb9c1');R((x+22,21,x+24,81),'#ecece6');d.line((x+4,53,x+40,53),fill='#f3ead8',width=3)
    R((133,20,346,89),accent);R((139,27,340,84),'#e9e6d8')
    for j in range(12):
        x=148+j*14
        R((x,48,x+8,51),['#9cbaaa','#ceac98','#c7c2a0'][j%3])
    # Kind-specific detailed furnishings made with pixel primitives.
    if kind in ('bread','cafe'):
        for x in (60,195,325):
            R((x,168,x+92,197),'#866a5c');R((x+4,153,x+88,174),'#d4ae83');
            for k in range(4):
                d.ellipse((x+12+k*18,151,x+24+k*18,164),fill='#e8c38e' if kind=='bread' else '#e5d4bc')
        R((15,110,85,139),accent)
    elif kind in ('library','school'):
        for x in (24,185,345):
            R((x,129,x+95,241),'#927863')
            for yy in (144,172,200):
                R((x+4,yy,x+91,yy+6),'#715b54')
                for k in range(12):R((x+8+k*7,yy+7,x+12+k*7,yy+24),['#7a9c95','#c5b88e','#a792b5'][k%3])
    elif kind in ('clinic','care'):
        for x in (40,190,340):
            R((x,158,x+100,215),'#a6babb');R((x+10,161,x+95,194),'#e3e1ce');R((x+15,159,x+45,179),'#f3eeee')
            R((x+5,213,x+12,238),'#7c8b90');R((x+89,213,x+96,238),'#7c8b90')
    elif kind in ('home','house'):
        for x in (35,190,344):
            R((x,172,x+90,216),'#a58c7a');R((x+5,179,x+85,204),'#ead4b9');R((x+8,212,x+82,218),'#857b77')
        R((200,123,265,144),'#8c796e')
    elif kind=='theater':
        R((100,125,380,235),'#574f65');R((115,133,365,226),'#c1a3c2')
        for j in range(5):R((131+j*50,250,167+j*50,278),'#8b677b')
    elif kind in ('factory','office'):
        for x in (46,196,346):
            R((x,164,x+83,199),'#667d81');R((x+5,151,x+70,171),'#b2bec0')
            R((x+14,130,x+61,158),'#445e68')
            R((x+19,134,x+56,154),'#a2c4c8')
    elif kind=='hall':
        R((60,152,420,174),'#bb9b7a')
        for j in range(7):R((78+j*48,198,106+j*48,235),'#6f8993')
    elif kind=='closed':
        for x in (60,195,330): R((x,148,x+92,206),'#a2a79d')
    R((210,283,270,303),'#678b82')
    im=im.resize((960,608),Image.Resampling.NEAREST)
    im.save(ROOT/f'interior_{kind}.png',optimize=True)
    manifest['assets'][f'interior_{kind}']={'file':f'assets/interior_{kind}.png','width':960,'height':608,'purpose':category+' bespoke interior background','source':'Original Python-generated pixel art','license':'Project-generated'}
    print(kind)
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
