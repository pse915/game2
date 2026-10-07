"""실행: python -m unittest discover -s tests -v"""
import copy, itertools, unittest
from engine import *
from content import CHAPTERS, QUIZZES
class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=new_state('0301','3-1','새봄','1234')
    def make(self):return copy.deepcopy(self.base)
    def ready(self,s):
        s['flags'].update(informed=True,housing_stable=True,employed=True,work_support=True)
        s['checklist']=list(CHECKLIST)
        for i in range(6):s['quizzes'][str(i)]={'correct':True,'attempts':1}
    def test_all_2304_paths(self):
        count=0;endings=set()
        for codes in itertools.product(*[[o['code'] for o in c['options']] for c in CHAPTERS]):
            s=self.make()
            for code in codes:
                self.ready(s);apply_choice(s,code)
            self.assertEqual(s['chapter'],6);self.assertEqual(s['age'],65)
            d,t=score(s);self.assertAlmostEqual(t,s['stats']['children']+sum(v for _,v in bonuses(s)),places=2)
            self.assertTrue(all(0<=s['stats'][k]<=100 for k in ('vitality','happiness','care','aging')))
            endings.add(ending_code(s));count+=1
        self.assertEqual(count,2304);self.assertEqual(endings,set('ABCD'))
    def test_thresholds_and_precedence(self):
        s=self.make();s['flags']['informed']=True
        for child,expected in [(0,'C'),(1,'B'),(2,'A'),(3,'A')]:s['stats']['children']=child;self.assertEqual(ending_code(s),expected)
        s['stats']['aging']=20;self.assertEqual(ending_code(s),'C')
        s['stats']['happiness']=30;self.assertEqual(ending_code(s),'D')
        s['stats']['happiness']=50;s['stats']['care']=80;self.assertEqual(ending_code(s),'D')
    def test_bonus_fixed(self):
        s=self.make();s['stats']['children']=2;s['flags'].update(informed=True,shared_care=True,leave=True,nursery=True,flex=True,family_learning=True)
        self.assertEqual(score(s),(1.0,2.3))
        s['flags'].update(informed=False,solo_care=True,unprepared=True)
        self.assertEqual(score(s),(.75,2.05))
    def test_negative_not_clipped(self):
        s=self.make();s['flags'].update(solo_care=True,unprepared=True)
        self.assertEqual(score(s),(-1.55,-.25))
    def test_locks(self):
        s=self.make();s['chapter']=1;s['quizzes']['1']={'correct':True}
        with self.assertRaises(ValueError):apply_choice(s,'A')
        s['flags']['informed']=True;apply_choice(s,'A')
        s['chapter']=3;s['flags']['housing_stable']=False;s['quizzes']['3']={'correct':True}
        with self.assertRaises(ValueError):apply_choice(s,'D')
        s['chapter']=4;s['flags']['work_support']=False;s['quizzes']['4']={'correct':True}
        with self.assertRaises(ValueError):apply_choice(s,'D')
        s['chapter']=5;s['quizzes']['5']={'correct':True}
        with self.assertRaises(ValueError):apply_choice(s,'A')
    def test_quiz_and_proximity(self):
        s=self.make();s['x']=5;s['y']=7
        s,ui=handle(s,{'kind':'quest'});self.assertEqual(ui['type'],'quiz')
        s,ui=handle(s,{'kind':'answer','answer':1});self.assertFalse(s['quizzes']['0']['correct'])
        s,ui=handle(s,{'kind':'answer','answer':0});self.assertEqual(ui['type'],'choices')
        s,ui=handle(s,{'kind':'choose','code':'B'});self.assertEqual(s['chapter'],1)
        with self.assertRaises(ValueError):handle(s,{'kind':'choose','code':'A'})
    def test_portals_and_buildings(self):
        s=self.make();s['x']=22;s['y']=8
        s,_=handle(s,{'kind':'portal'});self.assertEqual((s['zone'],s['x'],s['y']),(1,1,8))
        for zone,m in enumerate(MAPS):
            for bx,by,w,h,_ in m['buildings']:self.assertFalse(walkable(zone,bx,by))
            for p in m['portals']:self.assertTrue(walkable(p['to'],p['tx'],p['ty']))
            for n in [n for n in NPCS if n['zone']==zone]:self.assertTrue(reachable(zone,(1,8),(n['x'],n['y']+1)))
    def test_policy_idempotent(self):
        s=self.make();s['flags'].update(policy_offer=True,birth_decided=True)
        s,_=handle(s,{'kind':'policy'});stats=copy.deepcopy(s['stats']);s,_=handle(s,{'kind':'policy'});self.assertEqual(s['stats'],stats)
    def test_checklist_and_finish(self):
        s=self.make();self.ready(s)
        for code in 'ACAADA':apply_choice(s,code)
        s.update(zone=4,x=20,y=7)
        s,ui=handle(s,{'kind':'finish'});self.assertTrue(s['finished']);self.assertEqual(ui['type'],'ending')
        self.assertNotIn('_pin_hash',public_state(s));self.assertIn('ending_info',public_state(s))
    def test_save_validation_pin(self):
        s=self.make();self.assertTrue(verify_pin(s,'1234'));self.assertFalse(verify_pin(s,'9999'));validate_state(s)
        s['stats']['care']=float('nan')
        with self.assertRaises(ValueError):validate_state(s)
    def test_no_child_no_personal_parental_bonus(self):
        s=self.make();self.ready(s);s['chapter']=4;apply_choice(s,'A')
        self.assertTrue(s['flags']['shared_care']);self.assertFalse(s['flags'].get('leave'));self.assertFalse(s['flags'].get('nursery'))
    def test_all_quiz_keys(self):
        self.assertEqual(len(QUIZZES),6)
        for q in QUIZZES:self.assertTrue(0<=q['correct']<len(q['a']))
if __name__=='__main__':unittest.main()
