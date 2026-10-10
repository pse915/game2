"""Original four-way 4-frame, 32x48 sprite sheets for student and teachers.
All characters are fictional depictions, NOT likenesses of actual school teachers.
"""
from PIL import Image,ImageDraw
from pathlib import Path
import json, random
A=Path(__file__).resolve().parents[1]/'frontend'/'assets'
SKIN=['#e8b59d','#b98065','#f2c7ad','#b7937b','#d9a080','#e6a6a4']
HAIR=['#332a37','#644343','#272d3c','#9d6b45','#474a55','#77534d','#bd9765','#4a3032','#81716d']
OUTFITS=[('#76b3a7','#316b74'),('#b48dab','#694e7d'),('#9db49a','#53775f'),('#d59c80','#865a68'),('#6f94bd','#4f617f'),('#d2af79','#8b7460'),('#7699a3','#395d71'),('#b999b9','#65527c')]
DARK='#302c3b';G='#ffffff'
def fill(d,box,c):d.rectangle(box,fill=c)
def ell(d,box,c):d.ellipse(box,fill=c)
def one(d,ox,oy,seed,direction,frame,teacher):
 r=random.Random(9353+seed*51)
 skin=SKIN[seed%len(SKIN)];hair=HAIR[(seed//2+seed%3)%len(HAIR)]
 coat,trim=OUTFITS[(seed+ (2 if teacher else 0))%len(OUTFITS)]
 trouser=['#384e63','#665775','#4f5a5c','#4d5d6d'][seed%4]
 style=seed%7;move=((-2,0,2,0)[frame]);s=(direction==0)
 # soft contact shadow under foot
 ell(d,(ox+7,oy+43,ox+26,oy+47),'#655e6570')
 # shoes & trouser legs; running cycles varied by frame while preserving baseline
 feet=[(11+move,34,15+move,43),(18-move,34,22-move,43)]
 if direction in (1,2):feet=[(11+move//2,34,15+move//2,43),(18-move//2,34,22-move//2,43)]
 for i,(x0,y0,x1,y1) in enumerate(feet):
  fill(d,(ox+x0-1,oy+y0,ox+x1+1,oy+y1),DARK)
  fill(d,(ox+x0,oy+y0+1,ox+x1,oy+y1-1),trouser)
  fill(d,(ox+x0-1,oy+y1,ox+x1+2,oy+y1+2),'#363342')
  fill(d,(ox+x0,oy+y1,ox+x1+1,oy+y1),'#e5c4a1' if not teacher else '#766675')
 # arms behind body swing
 for a,shift in ((8,move//2),(24,-move//2)):
  fill(d,(ox+a-3+shift,oy+23,ox+a+2+shift,oy+33),DARK)
  fill(d,(ox+a-2+shift,oy+24,ox+a+1+shift,oy+30),coat)
  fill(d,(ox+a-1+shift,oy+31,ox+a+1+shift,oy+33),skin)
 # torso silhouette and cuffs, button, scarf, bag
 fill(d,(ox+9,oy+21,ox+24,oy+36),DARK)
 fill(d,(ox+10,oy+22,ox+23,oy+33),coat)
 fill(d,(ox+11,oy+33,ox+22,oy+35),trim)
 fill(d,(ox+15,oy+23,ox+17,oy+31),'#d7d2c9' if teacher else '#dfcba3')
 fill(d,(ox+16,oy+24,ox+16,oy+28),trim)
 if seed%4==0:fill(d,(ox+21,oy+25,ox+24,oy+32),'#b5d4c4')
 if seed%5==1:fill(d,(ox+9,oy+27,ox+11,oy+32),'#e7b77a')
 # hair silhouette behind head: different shape per student and each teacher
 if style in (0,3,5):
  fill(d,(ox+7,oy+9,ox+25,oy+25),DARK)
  fill(d,(ox+8,oy+10,ox+24,oy+24),hair)
 if style==2:
  fill(d,(ox+22,oy+14,ox+28,oy+29),DARK);fill(d,(ox+23,oy+16,ox+27,oy+27),hair)
 if style==4:ell(d,(ox+18,oy+3,ox+27,oy+11),hair)
 # neck + head
 fill(d,(ox+14,oy+18,ox+19,oy+24),skin)
 fill(d,(ox+9,oy+8,ox+24,oy+21),DARK)
 fill(d,(ox+10,oy+9,ox+23,oy+20),skin)
 # ear light and cheeks
 if direction!=3:
  fill(d,(ox+9,oy+15,ox+11,oy+18),'#d89683')
  fill(d,(ox+22,oy+15,ox+24,oy+18),'#d89683')
 if direction==0:
  fill(d,(ox+12,oy+15,ox+13,oy+16),DARK)
  fill(d,(ox+20,oy+15,ox+21,oy+16),DARK)
  fill(d,(ox+15,oy+19,ox+18,oy+19),'#a96d70')
  fill(d,(ox+10,oy+17,ox+11,oy+17),'#de978b');fill(d,(ox+22,oy+17,ox+23,oy+17),'#de978b')
 if direction in (1,2):
  eye=12 if direction==1 else 21
  fill(d,(ox+eye,oy+15,ox+eye+1,oy+16),DARK)
  fill(d,(ox+eye,oy+19,ox+eye+1,oy+19),'#b8867f')
 if direction==3:
  fill(d,(ox+10,oy+10,ox+24,oy+20),hair)
  for v in range(4):fill(d,(ox+11+v*3,oy+13,ox+12+v*3,oy+17),['#625357','#49414d','#766062','#53424a'][v])
 # top hair with natural pixel glints, eyebrows covered and variant cuts
 if direction!=3:
  ell(d,(ox+8,oy+5,ox+25,oy+15),DARK)
  ell(d,(ox+9,oy+5,ox+24,oy+13),hair)
  fill(d,(ox+10,oy+9,ox+13,oy+13),hair)
  if style in (1,2,6):fill(d,(ox+13,oy+8,ox+22,oy+11),hair)
  if style==6:fill(d,(ox+21,oy+12,ox+24,oy+20),hair)
  if style==5:fill(d,(ox+8,oy+11,ox+11,oy+22),hair)
  if seed%2==0:fill(d,(ox+12,oy+6,ox+18,oy+7),'#99877b' if hair=='#272d3c' else '#b18c76')
 if teacher and seed%4==1 and direction==0:
  # small spectacles
  fill(d,(ox+11,oy+14,ox+15,oy+16),'#6d6464')
  fill(d,(ox+19,oy+14,ox+23,oy+16),'#6d6464')
  fill(d,(ox+15,oy+14,ox+19,oy+14),'#6d6464')
 if (not teacher) and seed%3==2:
  fill(d,(ox+12,oy+5,ox+18,oy+6),'#efc79e')
 if teacher and seed%3==0:fill(d,(ox+11,oy+23,ox+13,oy+28),'#f2d7a0')

for prefix,count in [('avatar',6),('teacher',17)]:
 for i in range(count):
  sheet=Image.new('RGBA',(128,192),(0,0,0,0));d=ImageDraw.Draw(sheet)
  for direction in range(4):
   for frame in range(4):
    one(d,frame*32,direction*48,i+(8 if prefix=='teacher' else 0),direction,frame,prefix=='teacher')
  name=f'{prefix}_{i:02d}' if prefix=='teacher' else f'{prefix}_{i}'
  sheet.save(A/f'{name}.png',optimize=True)
print('Generated',6+17,'original detailed sprite sheets, each 4 directions × 4 walking frames.')
