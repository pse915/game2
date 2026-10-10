"""Original photo-informed pixel environment art for the Sewol Port RPG.
References are user-supplied photographs of the school exterior, classroom, corridor,
and user-provided high-density pixel RPG examples.  Source images are NOT pasted
into the game; all textures and shapes are new, drawn by this script.
The photographed exterior does not establish measured floor counts or a floorplan.
"""
from pathlib import Path
import math, json, random
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]/'frontend'/'assets'
MAN=ROOT/'manifest.json'
manifest=json.loads(MAN.read_text(encoding='utf8'))
assets=manifest['assets']
RAND=random.Random(776204)

def rect(d,xy,c): d.rectangle(tuple(map(int,xy)),fill=c)
def line(d,pts,c,w=1):d.line(pts,fill=c,width=w)
def ellipse(d,box,c):d.ellipse(box,fill=c)
def poly(d,xy,c):d.polygon(xy,fill=c)
def publish(name, im, purpose, source='user school reference / original pixel artwork', scale=2, **kw):
    if scale!=1:im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
    im.save(ROOT/(name+'.png'),optimize=True)
    previous=assets.get(name,{})
    fw=kw.get('frame_width',im.width);fh=kw.get('frame_height',im.height)
    sprite=('avatar_' in name or 'teacher_' in name)
    meta={**previous,'asset_id':name,'path':'assets/'+name+'.png','file':'assets/'+name+'.png',
      'width':im.width,'height':im.height,'purpose':purpose,'source':source,
      'license':'Project-generated original pixels','pixel_scale':scale,
      'type':'sprite_sheet' if sprite else 'background' if name.startswith(('school_hall','school_classroom','school_exterior')) else 'object',
      'frame_width':fw,'frame_height':fh,'frames':list(range(16)) if sprite else [0],
      'animation':{'down':[0,1,2,3],'left':[4,5,6,7],'right':[8,9,10,11],'up':[12,13,14,15]} if sprite else {},
      'collision':'separate_map' if name.startswith('building_') else 'none',
      'layer':'entities' if sprite else 'buildings' if name.startswith('building_') else 'background',
      'anchor':'feet' if sprite else 'bottom-center' if name.startswith(('building_','tree_')) else 'top-left'}
    assets[name]=meta
    print(name,im.size)

def brick(d,x,y,w,h,base='#984f4d',light='#b26b60'):
    rect(d,(x,y,x+w,y+h),base)
    for j,yy in enumerate(range(y+4,y+h,6)):
        line(d,[(x,yy),(x+w,yy)],'#783f43')
        for xx in range(x+((j%2)*9),x+w,18):
            line(d,[(xx,yy+1),(xx,yy+5)],'#be7564')
            if ((xx*19+yy*11)//9)%5==0:rect(d,(xx+3,yy+2,xx+8,yy+3),light)

def schoolwindow(d,x,y,w=27,h=22):
    rect(d,(x-2,y-3,x+w+3,y+h+4),'#6d5555')
    rect(d,(x-1,y-1,x+w+1,y+h+1),'#ece7db')
    rect(d,(x+2,y+2,x+w-1,y+h-1),'#718d95')
    rect(d,(x+3,y+3,x+w//2-2,y+8),'#b4d2d5')
    rect(d,(x+w//2+2,y+11,x+w-2,y+h-2),'#4d6b78')
    line(d,[(x+w//2,y),(x+w//2,y+h)],'#e6e6d9',2)
    line(d,[(x,y+h//2),(x+w,y+h//2)],'#ede9dc',2)
    rect(d,(x-2,y+h+2,x+w+3,y+h+5),'#c0b2a9')

def roofarc(d,x1,y1,x2,y2,top='#426d91'):
    # curved school metal roof silhouette with distinct long ridgeline
    p=[]
    for x in range(x1,x2+1,3):
        u=(x-x1)/(x2-x1)
        yy=int(y1-10*(math.sin(math.pi*u)**.8)+2*u)
        p.append((x,yy))
    poly(d,p+[(x2,y2),(x1,y2)],'#315573')
    line(d,p,top,3)
    for x in range(x1+13,x2-10,17):
        u=(x-x1)/(x2-x1); yy=int(y1-10*(math.sin(math.pi*u)**.8)+2*u)
        line(d,[(x,yy+3),(x,y2-1)],'#446d91')
    line(d,[(x1,y2),(x2,y2)],'#233849',3)

# EXTERIOR: red brick school wing, curved blue roof, left grey building,
# canopied walkway and dirt playground. L-junction is shown on left.
im=Image.new('RGBA',(480,288),(0,0,0,0));d=ImageDraw.Draw(im)
rect(d,(0,228,479,287),'#b6ada0')
for yy in range(231,288,7):
    for xx in range((yy//7)%2*9,480,23):
        if RAND.random()<.39:rect(d,(xx,yy,xx+2,yy+1),'#aa9f91')
# grey perpendicular wing, photo left
rect(d,(0,51,95,227),'#7c868a')
rect(d,(11,44,107,228),'#a7b0b3')
rect(d,(11,47,109,57),'#4c5359')
rect(d,(10,53,111,61),'#577083')
for yy in (67,101,135,169):
    for xx in (18,50,83):schoolwindow(d,xx,yy,21,25)
    rect(d,(13,yy+29,109,yy+31),'#a1a5a3')
rect(d,(104,66,119,228),'#67787c')
rect(d,(110,62,131,226),'#85878b')
# red main wing with actual photographed three-story face; internal game still has 4 floors
brick(d,128,72,351,154,'#8f4647','#a45951')
rect(d,(126,67,478,79),'#d0b5a9')
roofarc(d,125,56,479,78)
# beige upper window band and vertical bays
rect(d,(129,89,477,121),'#beaaa3')
for xx in range(136,470,35):
    rect(d,(xx+25,93,xx+27,219),'#c8b5ab')
    for yy,h in [(96,24),(140,27),(183,27)]:schoolwindow(d,xx,yy,26,h)
for yy in (130,173,217):rect(d,(130,yy,476,yy+3),'#a87f78')
# upper red-brick school sign zone, decorative insignia without baking Korean text
rect(d,(283,124,418,134),'#6b393b')
rect(d,(293,126,408,127),'#ddc5a8')
ellipse(d,(273,120,285,132),'#e6c6a5')
poly(d,[(279,120),(284,129),(275,127)],'#5a8aa2')
# glass entry vestibule, pillars and portico canopy
rect(d,(243,187,278,235),'#4b6672')
rect(d,(248,188,274,232),'#b9d6d2')
rect(d,(260,190,262,231),'#eef0df')
rect(d,(241,184,281,190),'#e0dbcc')
rect(d,(192,201,333,209),'#353d40')
rect(d,(189,199,336,203),'#475355')
for xx in (193,236,286,332):
    rect(d,(xx,206,xx+5,244),'#36383d')
    rect(d,(xx-2,206,xx+7,210),'#545459')
# benches under sheltered walkway
for xx in (205,252,292):
    rect(d,(xx,231,xx+24,233),'#674f4c')
    rect(d,(xx+3,234,xx+5,243),'#3f4442')
    rect(d,(xx+19,234,xx+21,243),'#3f4442')
# dark-green shrubs on front line
for xx in range(137,473,29):
    ellipses=[(xx-8,222,xx+10,242,'#385e4d'),(xx+2,220,xx+22,237,'#4a7055')]
    for a,b,c,e,col in ellipses:ellipse(d,(a,b,c,e),col)
# small trees, green yard
for xx,yy,s in [(113,203,1),(426,210,1)]:
    rect(d,(xx+8,yy+14,xx+12,yy+40),'#615040')
    for cx,cy,r,shade in [(xx+9,yy,18,'#33584e'),(xx+17,yy+5,14,'#476f50'),(xx+3,yy-5,13,'#648a63')]:ellipse(d,(cx-r//2,cy-r//2,cx+r//2,cy+r//2),shade)
publish('school_exterior',im,'School facade: curved blue metal roof, red brick, grey perpendicular wing, canopied walkway, playground',scale=1)

# detailed corridor tile: real grey speckled terrazzo with warm cream wall and wine-colored arch
W,H=480,304
for floor in range(1,5):
    rnd=random.Random(floor*997+5)
    im=Image.new('RGB',(W,H),'#24272d');d=ImageDraw.Draw(im)
    # background classrooms north and west cut-away; not a passable region
    rect(d,(110,0,479,122),'#dfded8')
    rect(d,(0,111,111,303),'#dedbd4')
    rect(d,(110,0,479,8),'#efeee7')
    # large classroom wall paneling like real photo
    rect(d,(110,8,479,106),'#eee9e0')
    for x in range(119,480,53):
        rect(d,(x,3,x+2,118),'#c4b8ac')
        rect(d,(x+2,4,x+4,119),'#faf5ed')
    # warm timber-framed classroom windows; corridor photo's mullions
    for x in range(120,460,63):
        rect(d,(x,15,x+43,90),'#705642')
        rect(d,(x+3,18,x+40,86),'#caa983')
        for j in range(2):
            xx=x+5+j*17
            rect(d,(xx,20,xx+14,81),'#a3c0bb')
            rect(d,(xx+2,23,xx+12,37),'#d1d9c5')
            rect(d,(xx+2,52,xx+12,76),'#7c989f')
        line(d,[(x+4,50),(x+40,50)],'#d4b48e',3)
        rect(d,(x-3,86,x+46,90),'#886c57')
    # noticeboard, signs between windows
    rect(d,(154,89,191,109),'#815147')
    rect(d,(157,91,188,106),'#69867b')
    for j in range(7):
        px=159+(j*19)%26;py=93+(j*7)%11
        rect(d,(px,py,px+4,py+3),['#fae4c7','#e5d6a9','#e5beb4'][j%3])
    # cut-away L southern classroom wing area and courtyard
    rect(d,(144,179,479,303),'#648876')
    # Natural lawn texture and planting rather than a repeated checkerboard.
    for _ in range(2400):
        px=rnd.randrange(145,479);py=rnd.randrange(180,304)
        col=rnd.choice(('#537b65','#6e9980','#799a80','#a0b199','#51715e'))
        rect(d,(px,py,px+rnd.randrange(1,3),py),col)
    # a curved garden walking path around the back courtyard
    for yy in range(210,304):
        xx=int(370-35*math.sin((yy-210)/86*math.pi))
        rect(d,(xx-17,yy,xx+17,yy),'#aca49a')
        if yy%8==0:line(d,[(xx-17,yy),(xx+17,yy)],'#98968c')
    for tx,ty in ((199,204),(300,240),(445,208)):
        rect(d,(tx+3,ty+5,tx+7,ty+24),'#765f4e')
        ellipse(d,(tx-11,ty-12,tx+23,ty+16),'#3f6d55')
        ellipse(d,(tx-3,ty-19,tx+27,ty+8),'#699577')
        for i in range(9):
            ax=tx+rnd.randrange(-9,19);ay=ty+rnd.randrange(-13,10)
            rect(d,(ax,ay,ax+1,ay+1),'#a3bf8c')
    for tx,ty in ((174,272),(262,284),(430,276)):
        rect(d,(tx-6,ty-2,tx+23,ty+4),'#917b62')
        rect(d,(tx-4,ty-8,tx+21,ty-3),'#ac8e6c')
        for i in range(3):rect(d,(tx+i*9,ty-13,tx+5+i*9,ty-8),rnd.choice(('#b37a8a','#dec1a2','#d3d67f')))
    # photos' terrazzo stone floors; traversable L grid only
    def terrazzo(x,y):
        px=x*16;py=y*16
        base=['#c8c4bb','#d0cec5','#bcbab1','#ccc9bf'][(x*2+y*5+floor)%4]
        rect(d,(px,py,px+15,py+15),base)
        line(d,[(px,py),(px+15,py)],'#8f918a')
        line(d,[(px,py),(px,py+15)],'#a6aaa1')
        for _ in range(21):
            tx=px+rnd.randrange(1,15);ty=py+rnd.randrange(1,15)
            col=rnd.choice(('#7d827d','#a1a49b','#e0dfd4','#b3aaa2'))
            rect(d,(tx,ty,tx,ty),col)
        rect(d,(px+1,py+1,px+13,py+1),'#d9d8cc')
    for x in range(7,28):
        for y in range(8,11):terrazzo(x,y)
    for x in range(6,9):
        for y in range(8,18):terrazzo(x,y)
    # baseboard and upper wall/door threshold visual rules
    rect(d,(112,119,463,124),'#966d70')
    rect(d,(112,123,463,127),'#eee1d1')
    rect(d,(95,124,100,303),'#82545f')
    rect(d,(99,125,103,303),'#e8dbc9')
    # magenta structural arch openings and pillars from corridor photograph
    for x in (137,294,444):
        rect(d,(x,91,x+10,125),'#973a60')
        rect(d,(x-3,91,x+13,99),'#c96e87')
        rect(d,(x+3,100,x+8,122),'#ba5875')
        rect(d,(x-4,124,x+14,129),'#bdafa2')
    # cabinets along west wing and small pictures
    for y in (147,200,253):
        rect(d,(7,y,72,y+27),'#786c60')
        rect(d,(11,y+2,68,y+25),'#e9dfcf')
        rect(d,(15,y+6,62,y+20),'#9aab9d')
        rect(d,(17,y+21,62,y+22),'#e0c9a4')
    # arches/lights corners, real school's distinctive green accents
    rect(d,(100,129,108,163),'#789657')
    rect(d,(100,128,128,132),'#c68b73')
    # stairs and details outside walkable path
    for yy in range(164,274,8):
        rect(d,(2,yy,82,yy+3),'#adb4b4')
        rect(d,(3,yy+4,83,yy+7),'#677781')
    # dynamic labels and doors based on canonical room ordering
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from school import SCHOOL_FLOORS
    for room in SCHOOL_FLOORS[str(floor)]:
        xx,yy=room['door']
        if room['wing']=='north':
            x=xx*16
            rect(d,(x-8,100,x+8,125),'#765548')
            rect(d,(x-6,101,x+5,119),'#b08a6d')
            rect(d,(x-4,103,x+3,118),'#91b4b6')
            rect(d,(x+3,111,x+4,113),'#efcf91')
            rect(d,(x-10,125,x+11,128),'#aa8177')
        else:
            y=yy*16
            rect(d,(78,y-8,97,y+8),'#76564d')
            rect(d,(80,y-5,95,y+6),'#b69175')
            rect(d,(84,y-4,93,y+5),'#a3c6bf')
            rect(d,(95,y-8,99,y+11),'#ab7f7c')
    # wooden framed cork notice board and wall clock
    ellipse(d,(240,88,255,103),'#665e5e')
    ellipse(d,(242,90,253,101),'#f1ebd6')
    line(d,[(247,95),(247,91)],'#4c565d')
    line(d,[(247,95),(251,97)],'#4c565d')
    publish('school_hall_'+str(floor),im,'Photo-inspired L-shaped school corridor '+str(floor)+': cream walls, timber mullions, terrazzo and magenta arches')

# CLASSROOM: furniture choices follow the photo (blue chairs, pale desks, grey legs,
# grey patterned floor, large blinds and storage wall). Gameplay locations unchanged.
im=Image.new('RGB',(480,304),'#d1cdc5');d=ImageDraw.Draw(im)
rect(d,(0,0,479,73),'#e7e2d5')
rect(d,(0,70,479,83),'#c1b3a5')
rect(d,(0,82,479,303),'#c5c2bb')
for x in range(0,480,16):
    line(d,[(x,83),(x,303)],'#aba9a2')
for y in range(82,304,16):line(d,[(0,y),(479,y)],'#afaea8')
for _ in range(2600):
    x=RAND.randrange(480);y=RAND.randrange(82,304)
    rect(d,(x,y,x,y),RAND.choice(['#aaa8a2','#e1ded4','#919390','#d8d7cf']))
# rear classroom storage cabinets and lesson notice board
rect(d,(6,19,151,86),'#9b9388')
for x in range(9,151,27):
    rect(d,(x,21,x+25,81),'#ded9c8')
    rect(d,(x+23,47,x+24,52),'#827f76')
rect(d,(162,15,308,69),'#9da69f')
rect(d,(164,18,305,66),'#e2e2d7')
for i in range(10):
    x=169+(i%5)*25;y=25+(i//5)*15
    rect(d,(x,y,x+15,y+9),['#b2c1c4','#c2b9ae','#b9c9bd'][i%3])
# sunlight, far right large windows with horizontal blinds
for x in (324,399):
    rect(d,(x,8,x+65,84),'#9a9393')
    rect(d,(x+3,12,x+62,77),'#a6b9bc')
    for yy in range(12,77,7):
        rect(d,(x+4,yy,x+61,yy+3),'#d0d0ce')
        line(d,[(x+4,yy+4),(x+61,yy+4)],'#8c999f')
    rect(d,(x,75,x+65,81),'#d0bdae')
# teaching desk + monitor at top-right
rect(d,(343,98,430,112),'#7a8387')
rect(d,(346,94,427,104),'#dbd8c6')
rect(d,(363,77,383,93),'#4b6574')
rect(d,(366,80,380,89),'#91bec3')
for xx in (349,420):rect(d,(xx,110,xx+4,128),'#66717a')
# blue single chairs and white metal-frame desks in three irregular rows
for row,y in enumerate((134,189,244)):
    for col,x in enumerate((38,130,222,310)):
        off=(row%2)*9
        x+=off
        # chair back (the reference photo's iconic blue plastic backrest)
        rect(d,(x+7,y+24,x+27,y+41),'#3c718a')
        rect(d,(x+9,y+23,x+25,y+35),'#4d90aa')
        ellipse(d,(x+13,y+25,x+21,y+28),'#8eb2bd')
        rect(d,(x+11,y+38,x+24,y+42),'#2b697f')
        # desk frame and legs
        for dx in (2,49):
            rect(d,(x+dx,y+9,x+dx+3,y+31),'#666e72')
            rect(d,(x+dx-1,y+29,x+dx+5,y+31),'#4d5b62')
        rect(d,(x,y-2,x+55,y+12),'#58616c')
        rect(d,(x+2,y-5,x+53,y+7),'#f2efe5')
        rect(d,(x+4,y-3,x+50,y-2),'#ffffff')
        if (row*5+col)%3==0:rect(d,(x+22,y-3,x+30,y),'#cfb99d')
# doorway in south
rect(d,(226,290,261,303),'#566e6f')
rect(d,(229,294,258,303),'#9caba3')
publish('school_classroom',im,'Photograph-informed classroom: blue chairs, off-white desks, grey frames, cabinets, roller blinds')

# TOWN BUILDINGS, explicitly different silhouettes and roof profiles per use.
BUILD_COLORS={
 'cafe':('#8a625b','#f2d4bb','#c16c58'), 'bread':('#987a53','#f0dbab','#ce925b'),
 'hall':('#587d75','#d8dfd0','#6da291'),'office':('#68798a','#dce2e2','#7895b8'),
 'home':('#916f7c','#dfcab9','#ae8b9a'),'house':('#87785e','#e8d6b5','#9c8b69'),
 'clinic':('#6d9d9f','#ecf3ee','#7bbaba'),'care':('#b88f94','#f1e4dc','#d19ea2'),
 'factory':('#6e7478','#e3d1bc','#83929b'),'closed':('#7a8284','#d2d1c8','#6c8c83'),
 'library':('#7a718c','#f0e5d1','#8e85a3'),'school':('#6b7c89','#e5dbc5','#bc6e67'),
 'theater':('#805d80','#ecdcc3','#a36c92')}
for kind,(edge,wall,roof) in BUILD_COLORS.items():
    im=Image.new('RGBA',(160,116),(0,0,0,0));d=ImageDraw.Draw(im)
    # drop shadow
    ellipse(d,(10,104,151,115),'#34434477')
    rect(d,(9,23,151,105),edge)
    rect(d,(13,27,147,99),wall)
    # facade segmented wall panels and subtle brick/stone texture
    for yy in range(33,97,9):
        line(d,[(14,yy),(145,yy)],'#c1b6ac')
        for xx in range((yy%2)*7+17,144,22):
            line(d,[(xx,yy+1),(xx,yy+8)],'#d2bfb6')
    # variable roof silhouettes
    if kind in ('house','home'):
        poly(d,[(1,36),(80,0),(158,36),(156,42),(4,42)],roof)
        line(d,[(8,35),(80,5),(152,35)],'#e8bba8',3)
    elif kind=='factory':
        poly(d,[(2,36),(2,10),(37,25),(72,10),(107,25),(145,10),(157,32)],roof)
        rect(d,(123,0,136,24),'#6a7174')
    elif kind=='theater':
        rect(d,(1,21,158,39),roof)
        for x in range(10,150,17):ellipse(d,(x,15,x+9,25),'#e6b7aa')
    else:
        rect(d,(5,10,154,38),roof)
        rect(d,(2,31,157,40),'#4a4e58')
        for xx in range(16,143,23):rect(d,(xx,13,xx+2,30),'#ffffff26')
    # double-height windows
    for xx in (19,116):
        rect(d,(xx-2,48,xx+28,84),'#635e5e')
        rect(d,(xx,50,xx+26,80),'#a5c7c3')
        rect(d,(xx+2,52,xx+11,60),'#cfdfd4')
        rect(d,(xx+13,51,xx+15,80),'#efe9d9')
        rect(d,(xx,64,xx+26,66),'#eee1d3')
        rect(d,(xx-4,81,xx+30,84),'#d3b6a0')
    # shopfront, entrance with glazing and awning per category
    if kind in ('cafe','bread'):
        for j in range(8):rect(d,(7+j*19,40,26+j*19,48),roof if j%2 else '#fae7d1')
        rect(d,(22,85,49,99),'#af775b')
        for x in (26,39):ellipse(d,(x,80,x+8,87),'#e8c995')
    if kind in ('clinic','care'):
        rect(d,(73,11,88,27),'#eef3e5');rect(d,(79,14,83,25),'#779c9b');rect(d,(75,18,86,22),'#779c9b')
    if kind=='library':
        for j in range(4):rect(d,(48+j*6,53,51+j*6,72),['#be907f','#668f98','#9e9d64'][j%3])
    rect(d,(69,61,91,106),'#66575b')
    rect(d,(71,62,88,101),'#89aaa6')
    rect(d,(72,64,78,89),'#c3d7d0')
    rect(d,(85,81,87,83),'#f4d6a3')
    rect(d,(68,102,94,109),'#beb4a5')
    # facade cornice and small signage zone, actual text drawn at runtime
    rect(d,(41,41,115,50),'#3f5960')
    rect(d,(43,42,113,43),'#9dbcb6')
    for x in (6,149):
        rect(d,(x,85,x+5,99),'#715b56')
        rect(d,(x-2,78,x+9,88),'#608d66')
        rect(d,(x+2,73,x+9,85),'#7fa67b')
    publish('building_'+kind,im,kind+' uniquely shaped town building sprite',scale=2)

# Trees (three canopies) use the same shadow orientation as buildings
for idx in range(3):
    rr=random.Random(idx*1123+77)
    im=Image.new('RGBA',(38,47),(0,0,0,0));d=ImageDraw.Draw(im)
    ellipse(d,(8,39,30,45),'#263d3655')
    rect(d,(17,24,22,41),'#745840')
    rect(d,(17,27,18,41),'#aa7958')
    for _ in range(13):
        x=rr.randrange(3,26);y=rr.randrange(3,29);r=rr.randrange(7,12)
        ellipse(d,(x,y,x+r,y+r),['#3a6c54','#457b5f','#5d9470','#75a87e'][rr.randrange(4)])
    for _ in range(17):
        x=rr.randrange(8,29);y=rr.randrange(6,26)
        rect(d,(x,y,x+2,y+1),'#99bd8a')
    publish('tree_'+str(idx),im,'Detailed town tree canopy and trunk',scale=2)

# Avatar and teacher SPRITE SHEETS: 4 directional rows, 4 animation frames.
# 16x24 per original frame -> output 32x48 per frame; 128x192 PNG sheet.
def sprite_sheet(seed, teacher=False):
    rr=random.Random(seed)
    skin=['#e7b48e','#c89478','#98684f'][seed%3]
    hair=['#4d393e','#292c36','#76534b','#b9a07f','#583540','#453e37'][seed%6]
    top=['#4a9e91','#a46f89','#637fa9','#a58b62','#769a78','#865e84'][seed%6]
    pants=['#40566e','#56576c','#554f5e'][seed%3]
    im=Image.new('RGBA',(64,96),(0,0,0,0));d=ImageDraw.Draw(im)
    for row in range(4):
        for frame in range(4):
            ox,oy=frame*16,row*24
            leg=frame%4
            # thick dark silhouette, detailed hair strands, warm face
            rect(d,(ox+4,oy+3,ox+12,oy+11),'#2b2d34')
            rect(d,(ox+5,oy+1,ox+11,oy+7),hair)
            rect(d,(ox+3,oy+6,ox+5,oy+13),hair)
            rect(d,(ox+11,oy+6,ox+13,oy+13),hair)
            rect(d,(ox+5,oy+6,ox+11,oy+12),skin)
            rect(d,(ox+6,oy+7,ox+11,oy+9),'#f1c9a0' if seed%3==0 else skin)
            if row==0: # front
                rect(d,(ox+6,oy+9,ox+6,oy+9),'#283039')
                rect(d,(ox+10,oy+9,ox+10,oy+9),'#283039')
                rect(d,(ox+7,oy+11,ox+9,oy+11),'#b76c69')
            elif row==1: # left
                rect(d,(ox+5,oy+8,ox+5,oy+9),'#283039')
                rect(d,(ox+3,oy+9,ox+4,oy+11),'#9c614b')
            elif row==2: # right
                rect(d,(ox+11,oy+8,ox+11,oy+9),'#283039')
                rect(d,(ox+12,oy+9,ox+13,oy+11),'#9c614b')
            else: # rear, hair over neck
                rect(d,(ox+5,oy+7,ox+11,oy+12),hair)
                rect(d,(ox+6,oy+9,ox+7,oy+11),'#9a7359')
            # shoes and alternating legs
            shoe='#333d45'
            if leg==1:
                rect(d,(ox+5,oy+19,ox+7,oy+23),pants)
                rect(d,(ox+9,oy+19,ox+11,oy+21),pants)
                rect(d,(ox+5,oy+23,ox+8,oy+23),shoe)
                rect(d,(ox+9,oy+21,ox+12,oy+22),shoe)
            elif leg==3:
                rect(d,(ox+5,oy+19,ox+7,oy+21),pants)
                rect(d,(ox+9,oy+19,ox+11,oy+23),pants)
                rect(d,(ox+5,oy+21,ox+8,oy+22),shoe)
                rect(d,(ox+9,oy+23,ox+12,oy+23),shoe)
            else:
                rect(d,(ox+5,oy+19,ox+7,oy+22),pants)
                rect(d,(ox+9,oy+19,ox+11,oy+22),pants)
                rect(d,(ox+5,oy+22,ox+8,oy+23),shoe)
                rect(d,(ox+9,oy+22,ox+12,oy+23),shoe)
            rect(d,(ox+4,oy+13,ox+12,oy+19),top)
            rect(d,(ox+5,oy+13,ox+6,oy+19),'#335f6b')
            rect(d,(ox+7,oy+14,ox+9,oy+16),'#dfbf8c')
            rect(d,(ox+3,oy+13,ox+4,oy+18),top)
            rect(d,(ox+12,oy+13,ox+13,oy+18),top)
            rect(d,(ox+3,oy+18,ox+4,oy+19),skin)
            rect(d,(ox+12,oy+18,ox+13,oy+19),skin)
            if teacher:
                rect(d,(ox+5,oy+16,ox+11,oy+17),'#d6c7b1')
            if seed%3==2:
                rect(d,(ox+4,oy+3,ox+12,oy+4),'#d9aa75')
            if seed%5==0:
                rect(d,(ox+13,oy+10,ox+13,oy+17),'#3e5d65')
    return im
for i in range(6):publish('avatar_'+str(i),sprite_sheet(i),'Original 4-direction, 4-frame player animation',frame_width=32,frame_height=48,frames=16)
for i in range(17):publish('teacher_'+f'{i:02d}',sprite_sheet(i+28,True),'Original teacher sprite with directional walking animation',frame_width=32,frame_height=48,frames=16)
MAN.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print('Assets regenerated:', len(assets))
