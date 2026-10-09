"""미래마을 2.0 사건 탐험, 시각 상태, 기존 기록 호환성 회귀검사."""
import copy
import unittest
from content import EVENTS, CHECKLIST, CHAPTERS, MAPS
from engine import (new_state, handle, world_view, life_card, student_digest,
                    validate_state, walkable, reachable, public_state, NPC)

class RenewalTests(unittest.TestCase):
    def new(self):
        s = new_state('001', '3-2', '탐험가', '1234')
        return handle(s, {'kind': 'classroom'})[0]

    def test_events_all_reachable_and_learning_mapped(self):
        self.assertEqual(len(EVENTS), 5)
        for event in EVENTS:
            self.assertTrue(walkable(event['zone'], event['x'], event['y']), event['id'])
            self.assertTrue(reachable(event['zone'], (12, 8), (event['x'], event['y'])), event['id'])
            self.assertEqual(len(event['answers']), 2)
            self.assertTrue(event['lesson'])
            self.assertTrue(event['concept'])

    def test_event_must_be_near_and_records_single_choice(self):
        s=self.new(); event=EVENTS[0]
        with self.assertRaises(ValueError):
            handle(s, {'kind':'investigate','event_id':event['id']})
        s,ui=handle(s,{'kind':'investigate','event_id':event['id'],'x':event['x'],'y':event['y']})
        self.assertEqual(ui['type'],'event')
        old_stats=copy.deepcopy(s['stats'])
        s,ui=handle(s,{'kind':'resolve_event','event_id':event['id'],'code':'housing'})
        self.assertTrue(ui['sparkle'])
        self.assertEqual(s['flags']['investigations'][event['id']],'housing')
        self.assertIn(event['concept'],s['flags']['experience_concepts'])
        self.assertEqual(s['stats'],old_stats)
        again,_=handle(s,{'kind':'resolve_event','event_id':event['id'],'code':'community'})
        self.assertEqual(again['flags']['investigations'][event['id']],'housing')
        self.assertEqual(len(again['flags']['experience_concepts']),1)
        self.assertEqual(public_state(again)['life_card']['incidents'],[event['title']])

    def test_policies_have_visible_and_nonjudgmental_results(self):
        s=self.new()
        s['flags']['policy_offer']=True
        s['stats']['children']=0
        a=world_view(s)
        self.assertEqual(a['shop'],'quiet')
        self.assertEqual(a['nursery'],'quiet')
        self.assertEqual(a['elder'],'alone')
        s,_=handle(s,{'kind':'policy_select','code':'housing'})
        b=world_view(s)
        self.assertEqual(b['shop'],'reviving')
        self.assertEqual(b['housing'],'welcoming')
        self.assertEqual(b['nursery'],'quiet')  # 해결하지 않은 문제는 남아야 합니다.
        s,_=handle(s,{'kind':'policy_select','code':'elder'})
        self.assertEqual(world_view(s)['elder'],'connected')
        with self.assertRaises(ValueError):handle(s,{'kind':'policy_select','code':'flex'})
        zero=world_view(s)
        s['stats']['children']=3
        self.assertEqual(world_view(s),zero)  # 한 사람의 자녀 수로 마을의 우열을 정하지 않습니다.

    def test_six_chapters_time_transitions_and_old_save(self):
        s=self.new()
        assert s['schema']==1
        for ch,code in enumerate('ACCBDA'):
            guide=NPC[CHAPTERS[ch]['guide']]
            # 기존 보안 규칙을 이용해 정확한 동선에서 이동 이벤트를 기록합니다.
            s['zone']=guide['zone'];s['x']=guide['x'];s['y']=guide['y']+1
            s,ui=handle(s,{'kind':'choose','code':code})
            self.assertEqual(ui['travel']['to'],s['age'])
            self.assertEqual(s['chapter'],ch+1)
        self.assertEqual(s['age'],65)
        self.assertEqual(world_view(s)['season'],'autumn')
        s['zone']=NPC['mayor']['zone'];s['x']=NPC['mayor']['x'];s['y']=NPC['mayor']['y']+1
        s,ui=handle(s,{'kind':'finish'})
        self.assertTrue(s['finished'])
        self.assertEqual(validate_state(s)['schema'],1)
        card=life_card(s)
        self.assertEqual(set(card['retirement']),{'재무','건강','여가','대인 관계'})
        self.assertIn('완료',student_digest(s)['완료'])
        self.assertEqual(public_state(s)['progress'],100)

    def test_recover_legacy_no_optional_fields(self):
        s=new_state('3','3-1','기존 학생','1234')
        self.assertNotIn('investigations',s['flags'])
        self.assertNotIn('policy_choices',s['flags'])
        self.assertEqual(world_view(s)['season'],'spring')
        self.assertEqual(life_card(s)['incidents'],[])
        self.assertEqual(student_digest(s)['진행'],'0/6')
        self.assertIs(validate_state(s),s)

if __name__=='__main__':unittest.main()
