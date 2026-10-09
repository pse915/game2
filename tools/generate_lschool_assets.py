"""Create L-shaped *fictional approximation* of school assets from the textual brief.
The source floor plan was not attached; do not claim measured architectural accuracy.
Original pixels and geometry: this generator, no external copyrighted sprites.
Run from repo root: python tools/generate_lschool_assets.py
"""
from pathlib import Path
import sys, json, random
from PIL import Image, ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from school import SCHOOL_FLOORS
OUT=Path(__file__).resolve().parents[1]/'frontend'/'assets'
R=random.Random(1196)

def r(d,xy,c):d.rectangle(xy,fill=c)
def brick(d,x,y,w,h,base='#b66d5b'):
    r(d,(x,y,x+w-1,y+h-1),base)
    for row,yy in enumerate(range(y+5,y+h,9)):
        d.line((x,yy,x+w-1,yy), fill='#945649',width=2)
        for xx in range(x+(row%2)*15,x+w,30):d.line((xx,yy+1,xx,yy+8),fill='#ce8b72',width=2)
def window(d,x,y,w=17,h=15):
    r(d,(x-2,y-2,x+w+2,y+h+3),'#e8d9c3')
    r(d,(x,y,x+w,y+h),'#597e89')
    r(d,(x+2,y+2,x+w//2,y+h//2),'#a3c8c5')
    d.line((x+w//2,y,x+w//2,y+h),fill='#f4ebd8',width=2)
    d.line((x,y+h//2,x+w,y+h//2),fill='#f4ebd8',width=2)
    r(d,(x-3,y+h+2,x+w+3,y+h+5),'#dbc1a1')

# Redesigned school exterior: a long main block with the left wing projecting at 90 degrees.
im=Image.new('RGBA',(320,224),(0,0,0,0));d=ImageDraw.Draw(im)
r(d,(2,182,318,219),'#779a73');r(d,(55,156,306,185),'#b1b0a0')
brick(d,68,37,244,118)
r(d,(66,30,313,41),'#765454');r(d,(67,31,311,37),'#c38b76');r(d,(68,153,311,164),'#765a53')
for yy in [46,72,98,124]:
    for x in range(84,307,22):
        if yy==124 and x in [172,194]:continue
        window(d,x,yy,13,14)
    r(d,(68,yy+20,312,yy+22),'#d9ab8a')
# Perspective side / perpendicular left wing.
d.polygon([(42,25),(89,38),(89,175),(24,185),(24,46)],fill='#915448')
d.polygon([(24,36),(43,21),(94,36),(87,47),(22,49)],fill='#744944')
d.polygon([(24,49),(44,43),(44,168),(24,184)],fill='#b97461')
d.polygon([(44,43),(89,47),(89,173),(44,169)],fill='#b66e5d')
for row, yy in enumerate([55,80,105,130]):
    for x in (52,69):window(d,x,yy,9,13)
    d.line((43,yy+20,88,yy+20),fill='#df9d7d',width=2)
# The ground-floor glass entrance and canopy.
r(d,(171,131,212,174),'#4b787d');r(d,(176,137,207,166),'#8caeb0')
for x in (187,198):d.line((x,137,x,167),fill='#ede5d3',width=2)
r(d,(161,126,221,133),'#526c69');r(d,(158,121,225,128),'#b0bcb0')
r(d,(181,175,204,179),'#eee0c8')
for t in range(3):r(d,(171-t*5,179+t*3,214+t*5,182+t*3),'#d0c3ad')
# Surrounding trees / flowerbeds and iron gate.
for x,y in [(12,139),(295,151)]:
    r(d,(x+11,y+9,x+17,y+42),'#775640')
    for cx,cy,rad,col in [(x+8,y+3,16,'#345f51'),(x+19,y-1,18,'#487a59'),(x+15,y-13,13,'#70a17a')]:d.ellipse((cx-rad,cy-rad,cx+rad,cy+rad),fill=col)
for x in range(1,126,8):
    r(d,(x,199,x+3,220),'#3f7955')
    d.polygon([(x-2,200),(x+1,194),(x+5,200)],fill='#4c8b63')
for x in range(251,320,8):
    r(d,(x,199,x+3,220),'#3f7955')
    d.polygon([(x-2,200),(x+1,194),(x+5,200)],fill='#4c8b63')
r(d,(122,195,130,222),'#365f48');r(d,(247,195,255,222),'#365f48')
for x,y in [(106,170),(137,169),(225,169)]:
    r(d,(x,y,x+27,y+13),'#456b50');r(d,(x+2,y+2,x+24,y+8),'#85a778')
    for dx in range(5,24,6):r(d,(x+dx,y+1,x+dx+2,y+3),'#efd0b1')
im.save(OUT/'school_exterior.png',optimize=True)

# Tile layout is 30x19 logic tiles; render half-size first for deliberately crisp pixels.
FLOOR_COLORS={'1':'#cbb8a3','2':'#d5c0ad','3':'#d2bbad','4':'#cbb8b6'}
for floor,rooms in SCHOOL_FLOORS.items():
    im=Image.new('RGB',(480,304),'#263b3c'); d=ImageDraw.Draw(im)
    # Courtyard visible beyond the L-shaped building. Explicitly not walkable.
    r(d,(144,179,479,303),'#6c947a')
    for px,py in [(180,214),(300,242),(401,202),(464,286)]:
        r(d,(px+8,py+9,px+13,py+32),'#6c5d49');d.ellipse((px-6,py-8,px+30,py+23),fill='#497660');d.ellipse((px+3,py-12,px+24,py+15),fill='#7baf82')
    r(d,(157,183,466,187),'#b3c1a8')
    # Upper classroom wing horizontal, left classroom wing vertical.
    r(d,(110,0,479,129),'#efd6bf')
    r(d,(0,112,112,303),'#ecd3b8')
    for x in range(110,480,26):
        d.line((x,9,x,126),fill='#dec1a7',width=1)
        for y in (20,63,106):r(d,(x+2,y,x+4,y+3),'#e5b38f')
    for y in range(123,304,24):d.line((4,y,105,y),fill='#d8baa0',width=1)
    r(d,(110,125,479,128),'#886f68');r(d,(94,112,108,303),'#947971')
    # Top indoor windows, trim, notice boards and wall lights.
    for x in range(125,475,56):
        r(d,(x,12,x+31,51),'#88796c');r(d,(x+3,15,x+28,47),'#91b8bb')
        r(d,(x+5,16,x+14,25),'#cee0d0');d.line((x+17,15,x+17,47),fill='#f9eee0',width=2)
        r(d,(x+1,51,x+32,54),'#c39c82')
    for y in (133,190,249):
        r(d,(8,y,48,y+20),'#869c95');r(d,(10,y+2,46,y+17),'#d3c5a2')
        r(d,(15,y+5,41,y+6),'#a2856d')
    # Hall's traversable L: entire tile walkable inside these strips.
    def tile(x,y):
        px=x*16;py=y*16;seed=(x*11+y*7+int(floor)*3)%4
        pal=[FLOOR_COLORS[floor],'#daccba','#ead9c4','#cbb6a5']
        r(d,(px,py,px+15,py+15),pal[seed]);d.line((px,py,px+15,py),fill='#f7e9d4',width=1);d.line((px,py,px,py+15),fill='#bdac9a',width=1)
        if (x+y)%6==0:r(d,(px+8,py+9,px+9,py+10),'#baaaa0')
    for x in range(7,28):
        for y in range(8,11):tile(x,y)
    for x in range(6,9):
        for y in range(8,18):tile(x,y)
    d.line((112,128,447,128),fill='#f9ebd8',width=2)
    d.line((95,130,95,286),fill='#f7e9d1',width=2)
    # Door thresholds and corridor furniture are tied to the authoritative layout data.
    for room in rooms:
        dx,dy=room['door']
        if room['wing']=='north':
            x=dx*16
            r(d,(x-6,107,x+7,128),'#735d57');r(d,(x-4,109,x+5,123),'#8aada5');r(d,(x-2,111,x+3,114),'#c8dfd4')
            r(d,(x-7,125,x+8,128),'#b6a083')
        else:
            y=dy*16
            r(d,(80,y-6,98,y+7),'#725e56');r(d,(84,y-4,94,y+5),'#8cb5a5');r(d,(95,y-2,99,y+3),'#b2c0ad')
    # Scene-specific signage texture; text is overlaid at runtime, not baked into images.
    for x in (135,241,351,433):
        r(d,(x,72,x+20,79),'#576f70');r(d,(x+2,73,x+18,75),'#e3cb98')
    # Corner floor marker emphasizes actual bend.
    r(d,(113,131,139,134),'#789f8e');r(d,(116,134,120,154),'#789f8e')
    im.resize((960,608),Image.Resampling.NEAREST).save(OUT/f'school_hall_{floor}.png',optimize=True)
manifest_file=OUT/'manifest.json'; m=json.loads(manifest_file.read_text(encoding='utf8'))
for name in ['school_exterior']+[f'school_hall_{i}' for i in range(1,5)]:
    with Image.open(OUT/f'{name}.png') as art:
        e=m['assets'][name];e.update({'width':art.width,'height':art.height,
          'source':'Original procedural pixels; text brief L-shape approximation; actual floor plan unavailable',
          'license':'Project-generated'})
manifest_file.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8')
print('Rebuilt:',', '.join(['school_exterior']+[f'school_hall_{i}' for i in range(1,5)]))
