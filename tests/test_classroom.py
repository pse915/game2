"""기존 저장 구조와 수업용 빠른 진행을 확인합니다."""
import unittest
from engine import new_state, handle, public_state, validate_state, CHAPTERS, NPC, MAPS
from collections import deque

class ClassroomTests(unittest.TestCase):
    def event(self,s,kind,**kw):return handle(s,{'kind':kind,**kw})
    def travel(self,s,zone):
        q=deque([(s['zone'],[])]);seen={s['zone']}
        while q:
            z,path=q.popleft()
            if z==zone:
                for portal in path:s,_=self.event(s,'portal',x=portal['x'],y=portal['y'])
                return s
            for portal in MAPS[z]['portals']:
                if portal['to'] not in seen:
                    seen.add(portal['to']);q.append((portal['to'],path+[portal]))
        raise AssertionError('missing path')
    def test_fast_path_and_life_card(self):
        s=new_state('12','3-1','학습자','1234')
        s,ui=self.event(s,'classroom');self.assertTrue(s['flags']['classroom_mode'])
        for ch,code in enumerate('ACCBDA'):
            n=NPC[CHAPTERS[ch]['guide']]
            s=self.travel(s,n['zone'])
            s,ui=self.event(s,'talk',npc=n['id'],x=n['x'],y=n['y']+1)
            self.assertEqual(len(ui['lines']),1)
            s,ui=self.event(s,'quest');self.assertEqual(ui['type'],'choices')
            s,ui=self.event(s,'choose',code=code);self.assertEqual(s['chapter'],ch+1)
            if ch==3:
                s,ui=self.event(s,'policy_menu');self.assertEqual(ui['type'],'policy_menu')
                s,_=self.event(s,'policy_select',code='housing')
                s,_=self.event(s,'policy_select',code='elder')
                with self.assertRaises(ValueError):self.event(s,'policy_select',code='flex')
        s=self.travel(s,NPC['mayor']['zone'])
        n=NPC['mayor'];s,ui=self.event(s,'finish',x=n['x'],y=n['y']+1)
        self.assertTrue(s['finished']);self.assertEqual(len(s['history']),6)
        s,ui=self.event(s,'life_card');self.assertEqual(ui['type'],'life_card')
        self.assertIn('재무',ui['card']['retirement'])
        self.assertEqual(public_state(s)['progress'],100)
        self.assertIs(validate_state(s),s)
    def test_old_state_no_migration(self):
        s=new_state('2','3-2','학생','1234')
        self.assertNotIn('classroom_mode',s['flags'])
        self.assertEqual(validate_state(s)['schema'],1)

if __name__=='__main__':unittest.main()
