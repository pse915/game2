import unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import new_state,apply,ready,recap,learning_coverage
from content import EVENTS,REQUIRED,CONCEPTS,NPCS,ZONES

class EngineTests(unittest.TestCase):
    def setUp(self):self.state=new_state('3-2','007','학생',2)
    def choose(self,key,choice):
        prev=self.state['revision']
        self.state,text=apply(self.state,{'type':'choose','event_id':key,'choice_id':choice,'nonce':'nonce-'+str(prev+1)})
        self.assertEqual(self.state['revision'],prev+1,text)
    def advance(self):
        prev=self.state['revision']
        self.state,text=apply(self.state,{'type':'advance','nonce':'change-'+str(prev)})
        self.assertEqual(self.state['revision'],prev+1,text)
    def test_every_option_and_concept_defined(self):
        for key,ev in EVENTS.items():
            self.assertTrue(ev['stages'])
            self.assertTrue(ev['choices'])
            for opt in ev['choices'].values():
                self.assertTrue(all(k in CONCEPTS for k in opt['concepts']))
        self.assertEqual(len({n['id'] for n in NPCS}),len(NPCS))
        self.assertEqual(len({z['id'] for z in ZONES}),6)
        self.assertTrue(all(n['event'] in EVENTS for n in NPCS))
    def test_saves_do_not_change_original_and_are_idempotent(self):
        clone,text=apply(self.state,{'type':'choose','event_id':'career','choice_id':'stable','nonce':'abc'})
        self.assertNotIn('career',self.state['decisions'])
        clone2,text2=apply(clone,{'type':'choose','event_id':'career','choice_id':'stable','nonce':'abc'})
        self.assertEqual(clone2,clone)
        self.assertEqual(text2,'이미 반영된 선택입니다.')
    def test_cannot_skip_requirements(self):
        new,msg=apply(self.state,{'type':'advance','nonce':'too-early'})
        self.assertEqual(new['revision'],0)
        self.assertFalse(ready(new))
        new,msg=apply(self.state,{'type':'finish','nonce':'too-early2'})
        self.assertFalse(new['ended'])
    def test_school_playthrough_with_nontraditional_choices(self):
        self.choose('housing','share')
        self.choose('career','flex')
        self.assertTrue(ready(self.state))
        self.advance();self.assertEqual(self.state['age'],43)
        self.choose('worklife','equal')
        self.choose('policy','aging')
        self.choose('care','share')
        self.assertTrue(ready(self.state))
        self.advance();self.assertEqual(self.state['age'],69)
        for k in REQUIRED[2]:self.choose(k,next(iter(EVENTS[k]['choices'])))
        self.assertTrue(ready(self.state))
        self.state,msg=apply(self.state,{'type':'finish','nonce':'completed'})
        self.assertTrue(self.state['ended'])
        self.assertEqual(len(recap(self.state)['retirement']),4)
        self.assertTrue(self.state['flags']['housing']=='공동 주거')
        self.assertTrue(learning_coverage(self.state)['aging'])
    def test_free_exploration_after_ending(self):
        self.choose('career','stable');self.choose('housing','share');self.advance()
        self.choose('care','flex');self.choose('policy','together');self.advance()
        for k in REQUIRED[2]:self.choose(k,next(iter(EVENTS[k]['choices'])))
        self.state,_=apply(self.state,{'type':'finish','nonce':'ending'})
        assert self.state['ended']
        self.state,_=apply(self.state,{'type':'choose','event_id':'festival','choice_id':'safe','nonce':'free-choice'})
        self.assertIn('festival',self.state['decisions'])
        rejected,_=apply(self.state,{'type':'choose','event_id':'career','choice_id':'stable','nonce':'not-free'})
        self.assertEqual(rejected['revision'],self.state['revision'])
    def test_no_negative_real_world_tfr_generated(self):
        self.choose('career','stable')
        self.choose('housing','rent')
        self.advance()
        self.choose('policy','youth')
        # A personal choice never sets or alters national fertility statistics.
        self.assertNotIn('tfr',self.state)
        self.assertNotIn('birthrate',self.state)
    def test_no_double_choice_or_stage_skip(self):
        self.choose('career','stable')
        start=self.state['revision']
        result,_=apply(self.state,{'type':'choose','event_id':'career','choice_id':'venture','nonce':'new-nonce'})
        self.assertEqual(start,result['revision'])
        self.assertEqual(result['flags']['career'],'공공서비스')
    def test_bounds_on_indicators(self):
        self.choose('career','venture')
        self.choose('housing','house')
        self.assertTrue(all(-6<=v<=40 for v in self.state['stats'].values()))
    def test_unknown_event_rejected(self):
        revised,text=apply(self.state,{'type':'choose','event_id':'bogus','choice_id':'x','nonce':'xx'})
        self.assertEqual(revised,self.state)

if __name__=='__main__':unittest.main()
