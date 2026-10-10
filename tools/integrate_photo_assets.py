"""Connect new original pixel art to existing Canvas code without changing progress keys."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'frontend/game.js'
s=p.read_text(encoding='utf8')
needle="...['bread','cafe','closed','hall','library','factory','office','home','house','clinic','care','school','theater'].map(k=>'interior_'+k)"
assert needle in s
s=s.replace(needle,needle+",...['bread','cafe','closed','hall','library','factory','office','home','house','clinic','care','school','theater'].map(k=>'building_'+k),...Array.from({length:6},(_,i)=>'avatar_'+i),...Array.from({length:3},(_,i)=>'tree_'+i)")
old="function drawTree(c,x,y,n=0){const X=x*TILE,Y=y*TILE;"
assert old in s
s=s.replace(old,"function drawTree(c,x,y,n=0){const key='tree_'+(Math.abs(n)%3);if(imgReady(key)){c.drawImage(art[key],x*TILE-11,y*TILE-37,53,66);return;}const X=x*TILE,Y=y*TILE;")
needle="if(type==='school'&&art.school_exterior.complete&&art.school_exterior.naturalWidth){c.drawImage(art.school_exterior,X,Y,WW,HH);c.font='bold 13px sans-serif';c.textAlign='center';c.textBaseline='middle';rect(c,X+WW*.25,Y+13,WW*.5,23,'#3d5f59');c.fillStyle='#f8e9c7';c.fillText('서라벌여중',X+WW/2,Y+27);return;}"
assert needle in s
s=s.replace(needle,needle+"\n    if(imgReady('building_'+type)){c.drawImage(art['building_'+type],X-3,Y-3,WW+6,HH+6);const signW=Math.min(WW-24,150);rect(c,X+(WW-signW)/2,Y+HH*.34,signW,21,'#35525add');c.font='bold 12px sans-serif';c.textAlign='center';c.textBaseline='middle';c.fillStyle='#f9edcf';const buildingLabel=type==='closed'&&state.flags.policy==='청년 지원'?'청년 공유공간':type==='closed'&&state.stage>=1?'임대 문의':name;c.fillText(buildingLabel,X+WW/2,Y+HH*.34+11,signW-6);return;}\n   ")
needle="function drawPerson(c,who,x,y,dir='down',frame=0,old=false){rect(c,x-11,y+4,24,5,'#28413b88');c.drawImage(sprite(who,dir,frame,old),Math.round(x-15),Math.round(y-44),30,47)}"
assert needle in s
s=s.replace(needle,"function drawPerson(c,who,x,y,dir='down',frame=0,old=false){rect(c,x-11,y+4,24,5,'#28413b88');const idx=Math.abs((who.skin||0)*5+(who.hair||0)*7+(who.outfit||0)*11)%6,key='avatar_'+idx;if(imgReady(key)){const row={down:0,left:1,right:2,up:3}[dir]??0,fr=Math.abs(frame)%4;c.drawImage(art[key],fr*32,row*48,32,48,Math.round(x-16),Math.round(y-46),32,50);if(old){rect(c,x-6,y-40,12,3,'#e7e6dbaa');}return;}c.drawImage(sprite(who,dir,frame,old),Math.round(x-15),Math.round(y-44),30,47)}")
s=s.replace("if(imgReady(path))c.drawImage(art[path],0,0,32,48,14*TILE-7,8*TILE-45,44,64);","if(imgReady(path))c.drawImage(art[path],Math.floor(now/350)%4*32,0,32,48,14*TILE-7,8*TILE-45,44,64);")
s=s.replace('Math.floor(now/200)%2','Math.floor(now/200)%4').replace('Math.floor(performance.now()/190)%2','Math.floor(performance.now()/190)%4').replace('Math.floor(now/170)%2','Math.floor(now/170)%4')
s=s.replace("const current=Math.floor(now/450)%2;","const current=Math.floor(now/350)%4;")
s=s.replace("'SEWOL PORT · 봄'","'서라벌여중 · 미래마을'")
p.write_text(s,encoding='utf8')
print('Updated game.js with new player/NPC animation, buildings, vegetation.')
