"""Generate original pixel-art school artwork from geometric pixel motifs.
The attached school photograph is a *reference*, not copied into the artwork.
Run: python tools/generate_school_assets.py
"""
from pathlib import Path
from PIL import Image, ImageDraw
import json, random
R = random.Random(20261010)
OUT = Path(__file__).resolve().parents[1]/'frontend'/'assets'
OUT.mkdir(parents=True,exist_ok=True)
manifest={}

def publish(img,name,purpose,scale=2):
    img=img.resize((img.width*scale,img.height*scale),Image.Resampling.NEAREST)
    dest=OUT/(name+'.png');img.save(dest,optimize=True)
    manifest[name]={'file':'assets/'+name+'.png','width':img.width,'height':img.height,'purpose':purpose,'source':'Original pixel-art; reference: user-provided exterior photo; not reproduced','license':'Project-generated','pixel_scale':scale}
    print(dest, img.size)

def rect(d,xy,fill,outline=None): d.rectangle(xy,fill,outline)

def brick(d,x,y,w,h):
    rect(d,(x,y,x+w,y+h),'#bd795e')
    for r,yy in enumerate(range(y+2,y+h,5)):
        for xx in range(x+(r%2)*5,x+w-3,11):
            d.line((xx,yy,xx+7,yy),fill='#a95e4d',width=1)
            if (xx+yy)%3==0: d.point((xx+3,yy+3),fill='#d38c71')

def window(d,x,y,w=9,h=11):
    rect(d,(x-1,y-1,x+w+1,y+h+1),'#7b5e59')
    rect(d,(x,y,x+w,y+h),'#f4ead5')
    rect(d,(x+1,y+1,x+w-1,y+h-1),'#8db6c0')
    rect(d,(x+2,y+1,x+3,y+4),'#b9d5d5')
    rect(d,(x+w-2,y+3,x+w-1,y+7),'#b5d7da')
    d.line((x+w//2,y+1,x+w//2,y+h-1),fill='#ede8df',width=1)
    d.line((x+1,y+h//2,x+w-1,y+h//2),fill='#f7f1df',width=1)
    d.line((x-2,y+h+2,x+w+2,y+h+2),fill='#dfbc9c',width=2)

# Canvas 160 x 112, exported as 320 x 224 px.
im=Image.new('RGBA',(160,112),(0,0,0,0));d=ImageDraw.Draw(im)
# Sky reflection in glazing & dark brick wing.
rect(d,(5,17,152,92),'#725b59');rect(d,(4,13,148,86),'#b77a63')
brick(d,6,13,139,74)
rect(d,(4,10,149,13),'#e8c9ac')
d.polygon([(130,5),(150,0),(157,12),(157,88),(133,86)],fill='#a65e51')
d.line((132,9,132,86),fill='#744a44',width=2)
# Distinctively long facade with 4 stacked rows of repeated windows.
for floor, yy in enumerate([18,35,52,69]):
    for i in range(11):
        x=10+i*11
        if floor==3 and i in [5,6]: continue
        window(d,x,yy,7,10)
    d.line((6,yy+14,129,yy+14),fill='#d39679',width=1)
# Right side of the building in perspective
for yy in [15,33,51,69]: window(d,137,yy,10,10)
for x in [33,67,101,129]: d.line((x,14,x,84),fill='#e2ad91',width=1)
# Front center vestibule with canopy, the photo's identifying covered entrance.
rect(d,(61,72,88,98),'#d2c6af');rect(d,(64,75,85,95),'#608d95')
for x in [69,77]: d.line((x,76,x,94),fill='#edeee4',width=2)
d.line((63,85,86,85),fill='#e5e6db',width=1)
rect(d,(54,70,97,75),'#526568');rect(d,(53,68,97,71),'#a1b7ad')
for x in [56,93]: rect(d,(x,73,x+2,93),'#d3cdc0')
rect(d,(65,95,84,98),'#d1c7b7')
# Steps and stone path.
for k in range(3): rect(d,(60-k*4,98+k*4,91+k*4,100+k*4),'#c9c5b5' if k%2==0 else '#aeaaa1')
# Front evergreen planter garden & characteristic large trees.
for x in [10,20,104,116]:
    rect(d,(x,90,x+5,96),'#8e7561');rect(d,(x-3,87,x+8,92),'#537f57');rect(d,(x,83,x+7,89),'#7dac77');rect(d,(x+4,84,x+6,86),'#b6d09b')
for x,y in [(0,54),(146,53)]:
    rect(d,(x+5,y+15,x+9,y+43),'#765b47')
    for cx,cy,r,color in [(x+5,y+7,13,'#426f56'),(x+14,y+5,13,'#477f5f'),(x+7,y-5,12,'#5a9568'),(x-4,y+9,8,'#679d6e')]: d.ellipse((cx-r//2,cy-r//2,cx+r,cy+r),fill=color)
# Famous green entry fence and gate set in the foreground.
rect(d,(0,100,52,102),'#437b57');rect(d,(103,100,159,102),'#437b57')
for x in list(range(2,52,6))+list(range(105,159,6)):
    rect(d,(x,96,x+2,110),'#3d8056');d.polygon([(x-1,97),(x+1,94),(x+3,97)],fill='#508b60')
    d.line((x,103,x+5,109),fill='#57916a',width=1)
rect(d,(47,92,52,112),'#3d7854');d.ellipse((46,89,53,96),fill='#61a275')
rect(d,(103,92,108,112),'#3d7854');d.ellipse((102,89,109,96),fill='#61a275')
publish(im,'school_exterior','Pixel art depiction of long red-brick school facade, glass windows, canopy and green fence')

# Hallway floor backgrounds across four levels.
for level in range(1,5):
    im=Image.new('RGBA',(480,304),'#ddcbb4'); d=ImageDraw.Draw(im)
    rect(d,(0,0,479,101),'#eedac9')
    rect(d,(0,88,479,112),'#ad937e')
    for x in range(0,480,16):
        d.line((x,113,x,303),fill='#cfb9a5')
    for y in range(113,304,16):d.line((0,y,479,y),fill='#cfb9a5')
    rect(d,(0,109,479,115),'#738f8d')
    # Bright classroom door bays with green chalkboard-style number signs.
    for idx in range(7):
        x=(3+4*idx)*16-10
        rect(d,(x-12,37,x+16,111),'#b99e8e')
        rect(d,(x-9,39,x+13,108),'#e7d6ba')
        rect(d,(x-7,45,x+11,106),'#9bb8ba')
        rect(d,(x-7,82,x+11,107),'#c49f7d')
        d.ellipse((x+7,94,x+9,96),fill='#f6ebc4')
        rect(d,(x-11,26,x+15,38),'#527773')
        rect(d,(x-9,28,x+13,36),'#d7e8cd')
    # Display cabinet, noticeboards and bright high windows.
    for x in [27,143,255,371]:
        rect(d,(x,8,x+35,22),'#8badae');rect(d,(x+3,11,x+32,20),'#c2dadd')
    for x in [46,198,330]:
        rect(d,(x,119,x+24,131),'#e4d7b1')
        for t in range(5): d.line((x+3+t*5,122,x+4+t*5,128),fill=['#aa93a7','#83aca0','#d3a97e'][t%3])
    # Tiles/path highlights under the player.
    for yy in range(134,303,32): rect(d,(0,yy,479,yy+1),'#ebdcc6')
    publish(im,f'school_hall_{level}',f'School hallway background, floor {level}')

im=Image.new('RGBA',(480,304),'#dfc8ac');d=ImageDraw.Draw(im)
rect(d,(0,0,479,107),'#f4e5d2')
rect(d,(0,104,479,111),'#a6a99c')
for y in range(112,304,16):
    d.line((0,y,479,y),fill='#c7b39e')
    for x in range((y//16)%2*16,480,32):d.line((x,y,x,y+16),fill='#cbb8a7')
# windows
for x in [46,95,337,388]:
    rect(d,(x,13,x+34,69),'#c1ada1');rect(d,(x+3,16,x+31,65),'#8fb6c1');rect(d,(x+17,16,x+19,65),'#ebece0');d.line((x+4,41,x+31,41),fill='#edf0e7',width=3)
# whiteboard
rect(d,(137,15,334,94),'#7e9a87');rect(d,(142,20,329,88),'#527a71')
for x,y in [(180,52),(198,40),(260,61)]:d.line((x,y,x+9,y+3),fill='#d5e2c5',width=2)
rect(d,(141,91,330,95),'#c6ad84')
# bookcase and cubbies
for x in [12,425]:
    rect(d,(x,138,x+35,230),'#99765f')
    for j in range(3):
        yy=145+j*29;rect(d,(x+4,yy,x+31,yy+4),'#6f5046')
        for k in range(5): rect(d,(x+5+k*5,yy+5,x+8+k*5,yy+19),['#a7b9ac','#e8bf9a','#b5a6c8'][k%3])
# tables 3 x 3 rows
for y in [148,190,232]:
    for x in [104,232,340]:
        rect(d,(x-15,y+6,x+35,y+17),'#8aafae')
        rect(d,(x-12,y+1,x+32,y+11),'#d0aa82')
        rect(d,(x-9,y+2,x+28,y+4),'#ebc7a1')
        rect(d,(x-6,y+16,x+19,y+26),'#8da0a6')
# entrance marker
rect(d,(229,282,258,303),'#668d88')
publish(im,'school_classroom','Shared classroom art with windows, chalkboard, desks, bookcases')

# Teacher/pupil pixel sprites. 16x24 base, 4x3 grid of poses/directions per sheet; varied originals.
for i in range(19):
    im=Image.new('RGBA',(16*4,24*4),(0,0,0,0));d=ImageDraw.Draw(im)
    skin=['#e9b98f','#c59275','#8d6253'][i%3]; hair=['#604b4e','#352d3f','#795545','#bba58b','#303949'][i%5]
    jacket=['#6a94a6','#bb888e','#8e82b3','#829c7b','#c4a071','#8c93a7'][i%6]
    for di in range(4):
        for frame in range(4):
            xx=di*16;yy=frame*24
            rect(d,(xx+4,yy+1,xx+11,yy+7),hair)
            rect(d,(xx+5,yy+6,xx+10,yy+11),skin)
            if i%4==0: rect(d,(xx+3,yy+7,xx+4,yy+15),hair)
            if di!=3:
                rect(d,(xx+6,yy+8,xx+6,yy+8),'#433b3c'); rect(d,(xx+10,yy+8,xx+10,yy+8),'#433b3c')
            rect(d,(xx+4,yy+12,xx+11,yy+18),jacket)
            rect(d,(xx+2,yy+13,xx+3,yy+18),jacket);rect(d,(xx+12,yy+13,xx+13,yy+18),jacket)
            rect(d,(xx+5,yy+19,xx+7,yy+22-(frame%2)),'#454f61')
            rect(d,(xx+9,yy+19+(frame%2),xx+11,yy+22),'#454f61')
            rect(d,(xx+5,yy+23,xx+7,yy+23),'#39363d');rect(d,(xx+9,yy+23,xx+11,yy+23),'#39363d')
    publish(im,f'teacher_{i:02d}',f'Original teacher sprite {i}, 4 directions x 4 walking frames',scale=2)

(OUT/'manifest.json').write_text(json.dumps({'tile_size':32,'assets':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
