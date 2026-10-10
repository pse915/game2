"""Draw original tiled, photo-informed school RPG environments.
The user's school photographs inform materials, colors and objects, not measured architecture.
Produces real PNGs for the existing 960x608 HTML5 Canvas, preserving map/collision IDs.
"""
from pathlib import Path
import json, random, math
from PIL import Image, ImageDraw
A=Path(__file__).resolve().parents[1]/'frontend'/'assets'
R=random.Random(915102)
S=2
PAL={'shade':'#29293b','dark':'#454354','line':'#716e7b','plaster':'#ece7dc','plaster2':'#dbd7d0',
'floor':'#aaa9a6','grout':'#817f83','floorhi':'#c4c3bd','pink':'#a34f71','pink2':'#d48aa1',
'wood':'#9f7956','wood2':'#d6b58d','wood3':'#e9d9bf','glass':'#93bdc2','glass2':'#cde4da',
'blue':'#4f81a1','chair':'#2f6f92','chairhi':'#74aac6','metal':'#60696c','yellow':'#e5c37c'}

def rect(d,x0,y0,x1,y1,c):d.rectangle((round(x0),round(y0),round(x1),round(y1)),fill=c)
def line(d,p,c,w=1):d.line(p,fill=c,width=w)
def new():return Image.new('RGB',(480,304),PAL['shade'])
def tex(d,x0,y0,x1,y1,base,grain=200):
    rect(d,x0,y0,x1,y1,base)
    colors=['#938f89','#d0ceca','#656867','#c2bcb2']
    for _ in range(grain):
        x=R.randrange(int(x0)+2,int(x1)-1);y=R.randrange(int(y0)+2,int(y1)-1)
        rect(d,x,y,x+R.choice([0,0,1]),y,R.choice(colors))

def terrazzo(d,x0,y0,x1,y1,phase=0):
    rect(d,x0,y0,x1,y1,PAL['floor'])
    for y in range(y0+phase,y1,16):
        line(d,[(x0,y),(x1,y)],'#87888a')
    for x in range(x0+phase,x1,16):line(d,[(x,y0),(x,y1)],'#87888a')
    for y in range(y0,y1,16):
        for x in range(x0,x1,16):
            for k in range(13):
                a=x+((k*7+y*3+x)%13)+1;b=y+((k*11+x//2+y)%13)+1
                if x0<=a<x1 and y0<=b<y1:
                    rect(d,a,b,a+R.choice([0,0,1]),b,R.choice(['#797b79','#d7d0bd','#c8c7c5','#958f89']))
            if (x//16+y//16)%3==0:rect(d,x+1,y+1,x+5,y+1,'#c7c8c1')

def wall(d,x0,y0,x1,y1):
    rect(d,x0,y0,x1,y1,PAL['plaster']);rect(d,x0,y0,x1,y0+4,'#dbd8d0')
    rect(d,x0,y1-13,x1,y1,'#c8c7c1');rect(d,x0,y1-15,x1,y1-14,'#989598')
    rect(d,x0,y1-4,x1,y1,'#8d8180');line(d,[(x0,y1),(x1,y1)],'#56525a',2)
    for x in range(x0+18,x1,86):rect(d,x,y0+8,x+1,y1-17,'#d2cdc7')

def frame(d,x,y,w,h,inner):
    rect(d,x-4,y-4,x+w+4,y+h+5,'#59515b');rect(d,x-2,y-3,x+w+2,y+h+2,PAL['wood'])
    rect(d,x,y,x+w,y+h,inner);line(d,[(x+w//2,y),(x+w//2,y+h)],PAL['wood2'],2)
    line(d,[(x,y+h//2),(x+w,y+h//2)],PAL['wood2'],2)
    rect(d,x+2,y+2,x+w//2-3,y+6,PAL['glass2'])
    rect(d,x+w//2+2,y+h//2+1,x+w-2,y+h-2,'#618b96')
    rect(d,x-5,y+h+4,x+w+4,y+h+7,'#9c7862')

def door(d,x,y,orient='h',color=None):
    color=color or PAL['wood']
    if orient=='h':
        rect(d,x-12,y-42,x+12,y+2,'#53474a');rect(d,x-10,y-41,x+10,y,color)
        rect(d,x-7,y-36,x+6,y-16,'#658fa3');rect(d,x-6,y-36,x+1,y-32,'#acd3d6')
        rect(d,x+6,y-17,x+8,y-13,PAL['yellow'])
        rect(d,x-14,y+1,x+14,y+4,'#927d70')
    else:
        rect(d,x-4,y-9,x+18,y+9,'#5b4b50');rect(d,x-3,y-8,x+17,y+8,color)
        rect(d,x+2,y-6,x+11,y+5,'#7dabb2');rect(d,x+3,y-6,x+7,y-3,'#bddbdb')
        rect(d,x+12,y,x+14,y+2,PAL['yellow'])

def bulletin(d,x,y,w=38,h=25,kind=0):
    rect(d,x-2,y-2,x+w+2,y+h+2,'#6c5751');rect(d,x,y,x+w,y+h, '#456e6e' if kind==0 else '#c79b72')
    for i in range(6):
        xx=x+3+(i%3)*11;yy=y+3+(i//3)*10
        rect(d,xx,yy,xx+7,yy+7,['#e9e2ca','#f0bdac','#d3e2d7','#dfc3c6'][i%4]);rect(d,xx+1,yy+2,xx+5,yy+2,'#9d9696')

def clock(d,x,y):
    d.ellipse((x-10,y-10,x+10,y+10),fill='#59575b');d.ellipse((x-8,y-8,x+8,y+8),fill='#ebe9e3')
    line(d,[(x,y),(x,y-6)],'#44444c',2);line(d,[(x,y),(x+4,y+3)],'#44444c',1)

def locker(d,x,y,w=17,h=28,color='#9090a1'):
    rect(d,x-2,y-2,x+w+2,y+h+3,'#525465');rect(d,x,y,x+w,y+h,color)
    rect(d,x+2,y+2,x+w-2,y+6,'#b6b5bd');rect(d,x+4,y+10,x+w-4,y+12,'#56576c')
    rect(d,x+w-5,y+16,x+w-3,y+20,'#ded7c7');rect(d,x+2,y+h-3,x+w-1,y+h-2,'#626679')

def plant(d,x,y):
    rect(d,x-6,y+8,x+7,y+21,'#b78a66');rect(d,x-5,y+8,x+6,y+11,'#d0a37d')
    for k in range(11):
        xx=x+round(math.sin(k*2.3)*10);yy=y+round(math.cos(k*2.3)*7)
        d.ellipse((xx-5,yy-3,xx+4,yy+3),fill=['#53745b','#789568','#85a571'][k%3])

def archive(d,x0,y0,x1,y1):
    rect(d,x0,y0,x1,y1,'#343440');rect(d,x0+2,y0+2,x1-2,y1-2,'#ccc4b6')
    for j in range(4):
        xx=x0+8+j*19;locker(d,xx,y0+9,16,33)

def school_hall(f):
    im=new();d=ImageDraw.Draw(im)
    # A playable, photo-inspired cutaway corridor: real walkable arms x=96..144; y=128..176.
    rect(d,0,0,479,303,'#2b2a35')
    # upper classroom facades and hall ceiling shadow
    wall(d,112,31,479,128)
    rect(d,112,26,479,37,'#b8b6b2');rect(d,112,28,479,29,'#efeae1')
    for i in range(7):
        x=133+i*51
        if x>470:break
        frame(d,x,47,34,34,'#85aeb1')
        rect(d,x-8,83,x+42,88,'#e3ddd2')
    # repeating photo-inspired wooden classroom doors at actual data coordinates
    for i in range(9):
        x=160+i*32
        if x>460:break
        door(d,x,126,color='#a87e57')
        rect(d,x-9,72,x+9,76,'#ede7d4')
    # visible architectural feature: bright pink arch around connecting hall, not fictitious floor plan
    for x in (120,288,432):
        rect(d,x-6,95,x+7,129,'#a34e75');rect(d,x-6,95,x+7,100,'#d88ca1')
        rect(d,x-10,125,x+10,130,'#79586a')
    # west/perpendicular structural wing behind corridor
    wall(d,4,105,105,303)
    rect(d,4,106,105,116,'#d3c2ad')
    for y in range(177,272,16):door(d,96,y,'v',color='#9b7c61')
    for y in (146,212,271):
        rect(d,7,y-6,72,y+4,'#d1c9bd');rect(d,7,y+5,74,y+6,'#8f8b8b')
    # far classroom cutaway: shows that areas beyond corridor are ROOM, not a grassy park
    rect(d,144,176,479,303,'#2c2b37')
    for k in range(3):
        xx=150+k*108
        if xx>=480:continue
        rect(d,xx,181,min(479,xx+102),301,'#c4b9ab')
        terrazzo(d,xx+5,184,min(479,xx+100),298)
        rect(d,xx,180,min(479,xx+102),188,'#a69c9b')
        for j in range(2):
            bx=xx+19+j*39
            if bx+24>479:continue
            desk(d,bx,211+38*j,25)
        rect(d,xx+4,185,xx+29,198,'#658a87')
    # dark separating wall below horizontal corridor
    rect(d,144,175,479,182,'#5e5861');rect(d,144,174,479,176,'#cbb9a2')
    # L-corridor from established game logic. Stitch corners, preserve passable tiles.
    terrazzo(d,96,128,144,289)
    terrazzo(d,112,128,448,176)
    rect(d,95,129,97,289,'#8b7780')
    rect(d,143,176,145,302,'#685d68')
    rect(d,112,126,448,128,'#b09f95')
    rect(d,96,284,145,288,'#8c827a')
    # corridor lower-right walls follow actual photo arch color
    rect(d,144,176,448,182,'#6b5a65')
    # pink arched entrance and trim at southwest junction
    rect(d,94,113,99,175,PAL['pink']);rect(d,140,113,146,176,PAL['pink'])
    rect(d,91,112,147,117,PAL['pink2']);rect(d,101,117,139,120,'#d3afaf')
    # wall messageboard and clock off foot traffic
    bulletin(d,181,88,43,26,kind=0)
    bulletin(d,342,86,40,27,kind=1)
    clock(d,245,100)
    # stairwell visible at W foot and far east; footprint matches logical nav
    rect(d,101,277,140,303,'#666772')
    for y in range(279,303,6):rect(d,103,y,138,y+3,'#bfc4c7')
    rect(d,430,154,451,178,'#646a79')
    for y in range(155,179,5):line(d,[(430,y),(448,y)],'#c8c7c3',2)
    # wall water dispenser near upper edge; collectible-like small environmental props
    rect(d,308,112,318,129,'#526872');rect(d,309,109,317,114,'#92d4e5')
    rect(d,311,120,315,124,'#d4eeec');rect(d,313,126,320,129,'#64606a')
    rect(d,270,119,280,126,'#9e7968')
    for i in range(3):rect(d,272+i*2,120,273+i*2,125,['#e5d9b9','#c9dfb9','#a7b2d2'][i])
    # wall subtle shadows, dimensional contact lines
    rect(d,112,127,448,128,'#69646c')
    rect(d,97,129,100,289,'#847779')
    # subtle floor directional marks, unobtrusive and passable
    for x in (170,250,333,415):
        rect(d,x,169,x+8,170,'#c5bfb2')
    if f>1:
        rect(d,280,40,358,43,'#978ba1')
        rect(d,276,46,366,48,'#d5c9c1')
    return im

def desk(d,x,y,w=30):
    # photographed white laminate top, dark navy edge, grey steel legs, chair behind
    rect(d,x-2,y+14,x+3,y+31,'#586069');rect(d,x+w-4,y+14,x+w+1,y+31,'#586069')
    rect(d,x-2,y+6,x+w+1,y+19,'#555963')
    rect(d,x,y+4,x+w-1,y+15,'#eeeae1');rect(d,x+2,y+5,x+w-3,y+6,'#ffffff')
    rect(d,x+9,y+9,x+17,y+10,'#cdc8bb')
    # blue chair back and seat
    rect(d,x+6,y+20,x+w-8,y+28,'#2b6381')
    rect(d,x+8,y+17,x+w-10,y+21,'#71a1bf')
    rect(d,x+7,y+28,x+10,y+33,'#585a63')
    rect(d,x+w-11,y+28,x+w-8,y+33,'#585a63')

def lab_table(d,x,y,w=42):
    rect(d,x,y,x+w,y+13,'#778d91');rect(d,x+3,y+2,x+w-3,y+9,'#d2d8ce')
    rect(d,x+4,y+13,x+7,y+33,'#53646c');rect(d,x+w-8,y+13,x+w-5,y+33,'#53646c')
    for i in range(3):
        xx=x+6+i*11;rect(d,xx,y-4,xx+7,y+3,['#6eacb4','#ddad96','#9ecaa4'][i])

def classroom(special='classroom'):
    im=new();d=ImageDraw.Draw(im)
    terrazzo(d,0,65,479,303)
    wall(d,0,0,479,85)
    rect(d,0,0,479,6,'#d6d2c9')
    # cream storage cabinets from real classroom photo
    for j in range(5):
        x=13+j*32
        rect(d,x,15,x+30,77,'#a3a099');rect(d,x+2,17,x+28,73,'#ebe7d9')
        rect(d,x+26,50,x+28,56,'#767b76')
    bulletin(d,181,23,76,42,kind=1)
    for j in range(2):
        x=326+j*70;frame(d,x,12,52,47,'#8aa5b3')
        for yy in range(21,55,7):rect(d,x+1,yy,x+51,yy+3,'#d2d6cf')
    # bright fluorescent lighting rendered as indirect wall glow, not literal perspective ceiling
    rect(d,160,4,286,7,'#e6e7df');rect(d,184,6,271,8,'#fbf4d7')
    # board corresponds interactive location x9,y5 => x=152 y=80
    rect(d,125,18,295,63,'#b0b0a6');rect(d,129,21,290,58,'#47736a')
    rect(d,132,23,284,26,'#6b9b83')
    for k in range(9):rect(d,147+k*14,43,152+k*14,44,'#b4c7ab')
    rect(d,127,60,292,63,'#7b6d62')
    # photographed white desks and blue chairs aligned in accessible four blocks
    for row in range(3):
        for col in range(4):
            desk(d,39+col*94,126+row*62,48)
    # teacher station x14 y8 game character stands near these, allow visual floor
    rect(d,345,88,418,100,'#6b7574')
    rect(d,351,83,415,95,'#e9e2d6')
    rect(d,354,78,379,85,'#6f8e9b')
    rect(d,358,69,379,77,'#a6c9cb')
    rect(d,352,99,356,127,'#606668');rect(d,410,99,414,127,'#606668')
    rect(d,431,94,457,123,'#bcab94')
    rect(d,435,95,452,113,'#e5e0d3')
    # entrance at floor foot center
    rect(d,217,291,261,303,'#6a746f');rect(d,221,295,256,303,'#a8ae9f')
    if special in ('science','technology','homemaking','computer','music','art','health','library','counsel','office','gym'):
        # overlay distinct, legible furnishings, not same cloned 17-classroom setup
        for row in range(3):
            for col in range(4):
                x=39+col*94;y=126+row*62
                rect(d,x-4,y+2,x+54,y+35,PAL['floor'])
                if special in ('science','technology','homemaking'):
                    lab_table(d,x,y,48)
                elif special=='computer':
                    desk(d,x,y,48);rect(d,x+15,y-7,x+39,y+5,'#3d4e62');rect(d,x+18,y-4,x+36,y+3,'#67a7c0')
                elif special=='music':
                    rect(d,x+6,y+6,x+42,y+12,'#7e5b67');rect(d,x+14,y-8,x+30,y+8,'#e2d7c7')
                    rect(d,x+17,y-1,x+28,y,'#766064')
                elif special=='art':
                    rect(d,x+5,y+3,x+46,y+30,'#b7a395');rect(d,x+19,y-8,x+34,y+9,'#eadbc5');rect(d,x+20,y-6,x+33,y+6,'#95b7ad')
                elif special=='health':
                    rect(d,x,y+2,x+49,y+28,'#f3e7db');rect(d,x+2,y+2,x+16,y+13,'#9ac2c3');rect(d,x+45,y,x+48,y+31,'#9babb5')
                elif special=='library':
                    rect(d,x-2,y-7,x+55,y+25,'#9b7258')
                    for j in range(4):rect(d,x+6+j*12,y-3,x+11+j*12,y+18,['#c7a7af','#8a9eaf','#d9bd83','#92a17e'][j])
                elif special=='counsel':
                    rect(d,x+3,y+4,x+43,y+27,'#9ca6a0');rect(d,x+6,y+5,x+38,y+17,'#c8c1bd')
                elif special=='office':
                    desk(d,x,y,48);rect(d,x+30,y-7,x+45,y+6,'#666c7b')
                elif special=='gym':
                    rect(d,x+7,y,x+43,y+6,'#b1aa9e');rect(d,x+24,y+3,x+27,y+29,'#707f7a')
        colors={'science':'#88bfa9','technology':'#91a8bc','homemaking':'#e2c4a4','computer':'#8ab9d0','music':'#bc9cbc','art':'#d5a69b','health':'#a5d1c5','library':'#b29b7d','counsel':'#c6afa1','office':'#9ea9ac','gym':'#a4b48a'}
        rect(d,126,17,295,19,colors[special])
    return im

for floor in range(1,5):school_hall(floor).resize((960,608),Image.Resampling.NEAREST).save(A/f'school_hall_{floor}.png')
classroom().resize((960,608),Image.Resampling.NEAREST).save(A/'school_classroom.png')
variants=['science','technology','homemaking','computer','music','art','health','library','counsel','office','gym']
for kind in variants:classroom(kind).resize((960,608),Image.Resampling.NEAREST).save(A/f'school_room_{kind}.png')
meta=json.loads((A/'manifest.json').read_text(encoding='utf8'))
for kind in variants:
 key=f'school_room_{kind}'
 meta['assets'][key]={"asset_id":key,"path":f"assets/{key}.png","file":f"assets/{key}.png","width":960,"height":608,"purpose":f"Photo-inspired playable cutaway {kind} classroom","source":"original programmatically drawn pixel art, user photo material reference","license":"Project-generated original pixels","type":"background","frame_width":960,"frame_height":608,"frames":[0],"animation":{},"collision":"separate_map","layer":"background","anchor":"top-left"}
(A/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
print('Refined 4 floors, 1 photographed classroom and 11 unique room styles.')
