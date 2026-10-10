"""Distinctive original pixel-art interiors for all 13 building types.
Each game background is 960x608 after exact 2x pixel enlargement.
Based on user's reference to detailed JRPG cutaway interiors, NOT copied sprites.
"""
from pathlib import Path
import json, random
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]/'frontend/assets';MP=ROOT/'manifest.json';M=json.loads(MP.read_text(encoding='utf8'))
THEMES={
 'bread':('#f0e1c8','#c8a27c','#986746','빵집'),
 'cafe':('#e7d8c9','#b98e81','#7c6257','카페'),
 'closed':('#dedbd3','#aaa9a0','#74817d','새로운 공간'),
 'hall':('#e5e3dc','#acb9ac','#647f7d','마을회관'),
 'library':('#e7ddc7','#c2a586','#71877d','도서관'),
 'factory':('#d3dada','#b2bab3','#70818b','공방'),
 'office':('#e4e5e3','#acbcc6','#687e9a','사무실'),
 'home':('#f1e2d6','#bea391','#aa8b8c','공동주거'),
 'house':('#e7e2d9','#c9b49b','#9cae9b','주거공간'),
 'clinic':('#e8edeb','#a9c3bf','#609ca3','보건시설'),
 'care':('#eee3dc','#c8b0b2','#b98b8d','돌봄공간'),
 'school':('#e6ded2','#b9a6a0','#719b9c','배움공간'),
 'theater':('#dfd7df','#ab92a5','#886982','극장')}

def R(d,p,c):d.rectangle(p,fill=c)
def L(d,p,c,w=1):d.line(p,fill=c,width=w)
def E(d,p,c):d.ellipse(p,fill=c)
def cabinet(d,x,y,color,side=False):
    R(d,(x,y,x+55,y+83),'#4a4647');R(d,(x+3,y+2,x+52,y+79),color)
    for j in range(3):
        Y=y+5+j*25
        R(d,(x+6,Y,x+49,Y+19),'#554947');R(d,(x+8,Y+1,x+47,Y+17),'#ae906e')
        for i in range(7):
            X=x+9+i*5
            R(d,(X,Y+3,X+3,Y+15),['#c8a678','#8b9d9a','#c1acb4','#e0b698'][i%4])
        R(d,(x+6,Y+18,x+49,Y+20),'#54433c')
    R(d,(x+1,y+79,x+54,y+83),'#5b4c44')

def desk(d,x,y,top='#ede7d6',frame='#66717a',chair='#6399b1'):
    R(d,(x+5,y+17,x+45,y+32),'#56555f')
    R(d,(x+8,y+31,x+12,y+53),frame);R(d,(x+40,y+31,x+44,y+53),frame)
    R(d,(x,y+7,x+51,y+24),'#46565d')
    R(d,(x+2,y+5,x+49,y+19),top)
    R(d,(x+4,y+7,x+47,y+9),'#ffffff')
    R(d,(x+16,y+35,x+40,y+48),'#2d5a6b')
    R(d,(x+19,y+31,x+38,y+44),chair)
    R(d,(x+19,y+49,x+38,y+52),'#617a82')
    R(d,(x+23,y+52,x+25,y+58),'#596b74')
    R(d,(x+34,y+52,x+36,y+58),'#596b74')

def bed(d,x,y,accent):
    R(d,(x+3,y+17,x+114,y+58),'#758789')
    R(d,(x+7,y+11,x+109,y+54),'#faf9f3')
    R(d,(x+10,y+12,x+30,y+48),'#dfe5e1')
    R(d,(x+40,y+17,x+98,y+49),'#c6e2dd')
    R(d,(x+6,y+56,x+13,y+68),'#76898a');R(d,(x+103,y+56,x+110,y+68),'#76898a')
    R(d,(x+103,y+4,x+111,y+57),accent)

def potted(d,x,y):
    E(d,(x-5,y-11,x+15,y+12),'#346950')
    E(d,(x+4,y-14,x+22,y+8),'#5a946d')
    E(d,(x-7,y-16,x+6,y+2),'#7dad7d')
    R(d,(x,y+9,x+15,y+24),'#ac7967')
    R(d,(x+2,y+11,x+13,y+19),'#ba9179')

def chair(d,x,y,c):
    R(d,(x+1,y+13,x+27,y+35),'#514b4c')
    R(d,(x+4,y+6,x+24,y+27),c)
    R(d,(x+6,y+7,x+22,y+9),'#d9bbb0')
    R(d,(x+3,y+34,x+7,y+42),'#544c4c')
    R(d,(x+21,y+34,x+25,y+42),'#544c4c')

for kind,(wall,floor,accent,label) in THEMES.items():
    rand=random.Random(sum(map(ord,kind))*23)
    im=Image.new('RGB',(480,304),wall);d=ImageDraw.Draw(im)
    R(d,(0,0,479,110),wall)
    R(d,(0,109,479,303),floor)
    R(d,(0,100,479,110),'#756e6c')
    R(d,(0,105,479,110),'#c2aea0')
    # world-consistent panel seams and bevelled wall columns
    for x in range(0,480,60):
        R(d,(x,2,x+1,97),'#e9dfd6')
        R(d,(x+2,2,x+3,99),'#c9bdb1')
    # floors: parquet for shops and homes, tile for institutions
    for y in range(112,304,16):
        L(d,[(0,y),(479,y)],'#a99589' if kind in ('bread','cafe','home','house','library','theater') else '#9da9a5')
        for x in range((y//16)%2*12,480,24):
            L(d,[(x,y),(x,y+15)],'#b8aaa0')
            if rand.random()<.25:R(d,(x+7,y+6,x+9,y+7),'#ded6c5')
    # decorative framed windows for upper wall, dynamic cutaway room aesthetics
    for x in (14,396):
        R(d,(x,12,x+67,92),'#75695e')
        R(d,(x+4,16,x+63,86),'#dcd4c7')
        R(d,(x+6,18,x+61,83),'#96b4b3')
        for t in range(3):
            R(d,(x+7,18+t*19,x+60,22+t*19),'#e8ded1')
        R(d,(x+6,79,x+61,83),'#c4ad8c')
        L(d,[(x+34,18),(x+34,80)],'#e7e0d1',2)
    # back-wall feature adapted for each kind
    R(d,(109,11,375,93),'#514d4c')
    R(d,(113,15,371,88),accent)
    if kind in ('bread','cafe'):
        R(d,(120,22,362,80),'#5d534e')
        for j in range(5):
            xx=131+j*47
            R(d,(xx,36,xx+33,55),'#d0a47d')
            for k in range(3):
                E(d,(xx+2+k*9,30,xx+12+k*9,39),['#f3d19a','#e7b582','#dfaa78'][k])
            R(d,(xx+2,58,xx+29,63),'#ebd1a8')
        R(d,(120,76,363,82),'#8c715e')
    elif kind in ('library','school'):
        for xx in (120,180,240,300):cabinet(d,xx,17,'#906a56')
    elif kind in ('clinic','care'):
        R(d,(130,23,349,72),'#f7f5eb')
        for j in range(4):
            xx=149+j*44
            R(d,(xx,27,xx+34,32),'#90b2b2')
            R(d,(xx+3,37,xx+22,58),'#cddada')
            R(d,(xx+9,39,xx+14,54),'#679c91')
    elif kind in ('office','factory'):
        R(d,(122,19,361,70),'#b8c2c1')
        for xx in (131,183,235,287,339):
            R(d,(xx,27,xx+30,55),'#4b6570')
            R(d,(xx+3,30,xx+27,50),'#a0bec1')
    elif kind=='theater':
        R(d,(128,19,353,86),'#443851')
        R(d,(132,22,348,83),'#bda2ae')
        for i in range(3):R(d,(137+i*70,26,144+i*70,78),'#884d6e')
    else:
        R(d,(129,27,351,63),'#ead8bb')
        R(d,(134,31,345,59),'#a6bbad')
        for xx in range(150,340,42):R(d,(xx,38,xx+22,42),'#f0eadd')
    # perspective furniture arranged around playable three interaction hotspots
    if kind in ('bread','cafe'):
        R(d,(33,157,450,173),'#4e5759')
        R(d,(36,149,447,163),'#d1a77e')
        for xx in (66,164,266,363):
            R(d,(xx,180,xx+61,199),'#5c4b46')
            R(d,(xx+3,176,xx+58,188),'#efceab')
            for j in range(3):E(d,(xx+8+j*15,179,xx+17+j*15,186),'#d39d69' if kind=='bread' else '#eddfc8')
            chair(d,xx+10,207,'#8a8876')
        R(d,(186,130,210,146),'#849e9d')
        R(d,(192,114,204,130),'#54575c')
        R(d,(194,115,202,125),'#d5e0d4')
    elif kind in ('library','school'):
        for xx in (41,207,373):cabinet(d,xx,150,'#93715c')
        desk(d,119,202,'#d9c5a0','#756e6b','#859c89')
        desk(d,279,202,'#d9c5a0','#756e6b','#859c89')
    elif kind in ('clinic','care'):
        bed(d,39,153,accent);bed(d,315,153,accent)
        R(d,(210,164,263,196),'#6d9897')
        R(d,(214,168,259,191),'#e4e9df')
        chair(d,218,214,'#8eab9c')
    elif kind in ('home','house'):
        R(d,(26,174,161,210),'#725e5a')
        R(d,(29,170,158,195),'#d8bca2')
        for xx in (42,112):R(d,(xx,167,xx+35,186),'#9b9b81')
        R(d,(325,166,447,207),'#7f716a')
        R(d,(330,170,442,201),'#efe3d6')
        R(d,(346,179,372,197),'#9fa59c')
        R(d,(193,224,283,244),'#88796b')
        R(d,(200,218,275,234),'#dbb698')
        chair(d,199,251,'#8a8b8a')
    elif kind in ('factory','office'):
        for xx in (40,207,370):
            desk(d,xx,175,'#b7c6c2','#67797c','#708b9c')
            R(d,(xx+12,149,xx+42,174),'#505d69')
            R(d,(xx+15,151,xx+39,169),'#8cb5b9')
            R(d,(xx+20,175,xx+32,177),'#77858d')
    elif kind=='theater':
        R(d,(51,123,425,175),'#625466')
        R(d,(58,129,418,166),'#a18aa8')
        for xx in (60,140,220,300,380):
            for yy in (203,255):chair(d,xx,yy,'#9a6c8c')
    elif kind=='hall':
        R(d,(40,166,440,181),'#7c7567')
        R(d,(44,161,436,176),'#d4bd9a')
        for xx in range(68,440,56):chair(d,xx,199,'#719c9a')
    else: # unfinished community space
        for xx in (53,212,373):
            R(d,(xx,180,xx+87,236),'#a4a7a0')
            R(d,(xx+3,183,xx+83,232),'#d2c6b6')
            for yy in (191,207):R(d,(xx+13,yy,xx+73,yy+2),'#bab2a2')
    for xx in (14,456):potted(d,xx,132)
    R(d,(220,282,262,303),'#647e80')
    R(d,(224,286,258,303),'#a3b8b2')
    im=im.resize((960,608),Image.Resampling.NEAREST)
    fn=ROOT/f'interior_{kind}.png';im.save(fn,optimize=True)
    base=M['assets'].get('interior_'+kind,{})
    base.update({'file':f'assets/interior_{kind}.png','path':f'assets/interior_{kind}.png','asset_id':'interior_'+kind,
        'width':960,'height':608,'frame_width':960,'frame_height':608,'frames':[0],
        'purpose':label+' distinctive photo-inspired RPG interior','source':'Original pixel environment designed for this game','license':'Project-generated',
        'type':'background','animation':{},'collision':'separate_map','layer':'background','anchor':'top-left'})
    M['assets']['interior_'+kind]=base
    print(kind,fn.stat().st_size)
MP.write_text(json.dumps(M,ensure_ascii=False,indent=2),encoding='utf8')
