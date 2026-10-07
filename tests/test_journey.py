"""실제 프론트엔드가 보내는 요청 형태로 4개 엔딩 경로를 통합 검사합니다."""
import copy, unittest
from collections import deque
from engine import new_state,handle,NPC,MAPS,CHAPTERS,QUIZZES,CHECKLIST
class JourneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=new_state('001','3-1','모험가','1234')
    def event(self,s,kind,**kwargs):return handle(s,{'kind':kind,**kwargs})[0]
    def travel(self,s,zone):
        todo=deque([(s['zone'],[])]);seen={s['zone']};route=None
        while todo:
            here,path=todo.popleft()
            if here==zone:route=path;break
            for portal in MAPS[here]['portals']:
                if portal['to'] not in seen:seen.add(portal['to']);todo.append((portal['to'],path+[portal]))
        self.assertIsNotNone(route)
        for portal in route:s=self.event(s,'portal',x=portal['x'],y=portal['y'])
        return s
    def approach(self,s,nid):
        n=NPC[nid];s=self.travel(s,n['zone']);return self.event(s,'talk',npc=nid,x=n['x'],y=n['y']+1)
    def run_path(self,path,policy):
        s=copy.deepcopy(self.base)
        for ch,code in enumerate(path):
            guide=CHAPTERS[ch]['guide'];s=self.approach(s,guide)
            s,ui=handle(s,{'kind':'quest'});self.assertEqual(ui['type'],'quiz')
            s,ui=handle(s,{'kind':'answer','answer':QUIZZES[ch]['correct']});self.assertEqual(ui['type'],'choices')
            if ch==5 and code=='A':s=self.event(s,'check',checked=list(CHECKLIST))
            s,ui=handle(s,{'kind':'choose','code':code});self.assertEqual(ui['type'],'notice')
            if ch==3 and policy:s=self.event(s,'policy')
        s=self.approach(s,'mayor');s=self.event(s,'finish')
        self.assertTrue(s['finished']);return s['ending']
    def test_four_full_journeys(self):
        for path,policy,expected in [('ACACDA',True,'A'),('ACCBDA',True,'B'),('BCCADA',True,'C'),('CBDCCB',False,'D')]:
            with self.subTest(path=path):self.assertEqual(self.run_path(path,policy),expected)
    def test_counseling_recovery(self):
        s=copy.deepcopy(self.base);s=self.approach(s,'scholar');s=self.event(s,'learn');self.assertTrue(s['flags']['informed'])
        s=self.approach(s,'official');s=self.event(s,'housing_help');self.assertTrue(s['flags']['housing_stable'])
        s=self.approach(s,'hr');s=self.event(s,'work_help');self.assertTrue(s['flags']['work_support']);self.assertTrue(s['flags']['employed'])
if __name__=='__main__':unittest.main()
