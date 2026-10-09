import json,struct,sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from school import SCHOOL_FLOORS,TEACHER_MAP,validate_school_interaction,CLASS_OBJECTS, SPECIAL_OBJECTS,concept_for
from content import BUILDINGS,CONCEPTS,public_content
from engine import new_state,apply

class SchoolExpansionTests(unittest.TestCase):
    def test_exact_homerooms_and_floor_assignments(self):
        self.assertEqual(len(TEACHER_MAP),17)
        for prefix, floor, count in ((1,'2',5),(2,'3',6),(3,'4',6)):
            self.assertEqual(len([r for r in SCHOOL_FLOORS[floor] if r['kind']=='class']),count)
            for j in range(1,count+1):
                code=f'{prefix}-{j}'
                self.assertEqual(TEACHER_MAP[code]['homeroom'],code)
                self.assertIn(code,[r['id'] for r in SCHOOL_FLOORS[floor]])
                self.assertIn(concept_for(code),CONCEPTS)
        self.assertEqual(TEACHER_MAP['1-2']['name'],'이원희')
        self.assertEqual(TEACHER_MAP['3-6']['name'],'변지희')
    def test_every_enterable_room_has_valid_interactions(self):
        rooms=[r for floor in SCHOOL_FLOORS.values() for r in floor]
        self.assertEqual(len({r['id'] for r in rooms}),len(rooms))
        for r in rooms:
            objs=CLASS_OBJECTS if r['kind']=='class' else SPECIAL_OBJECTS
            self.assertGreaterEqual(len(objs),5 if r['kind']=='class' else 3)
            for o in objs:
                self.assertTrue(validate_school_interaction(r['id'],o,'investigate'))
                self.assertTrue(validate_school_interaction(r['id'],o,'discuss'))
        self.assertFalse(validate_school_interaction('5-9','teacher','investigate'))
        self.assertFalse(validate_school_interaction('office','teacher','discuss'))
    def test_school_choices_persist_without_disrupting_life(self):
        state=new_state('2-2','13','학생')
        event={'type':'school_activity','room_id':'1-2','object_id':'teacher','choice_id':'investigate','nonce':'s-a'}
        new,msg=apply(state,event)
        self.assertEqual(new['revision'],1)
        self.assertIn('housing',new['concepts'])
        self.assertIn('1-2:teacher',new['school_records'])
        self.assertEqual(new['stage'],0)
        self.assertEqual(new['decisions'],{})
        old,ignored=apply(new,event)
        self.assertEqual(old,new)
        newer,_=apply(new,{**event,'nonce':'s-b'})
        self.assertEqual(newer,new)
    def test_backward_compatibility_old_save(self):
        s=new_state('2-2','13','학생')
        s.pop('school_records');s.pop('building_records');s.pop('guide_mode')
        result,_=apply(s,{'type':'school_activity','room_id':'3-5','object_id':'teacher','choice_id':'discuss','nonce':'compat'})
        self.assertEqual(result['school_records']['3-5:teacher']['choice'],'discuss')
        self.assertEqual(result['revision'],1)
    def test_real_building_activities_and_invalid_reject(self):
        state=new_state('2-2','13','학생')
        result,_=apply(state,{'type':'building_activity','building_id':'shop:12:2','object_id':'notice','choice_id':'help','nonce':'b-1'})
        self.assertIn('shop:12:2:notice',result['building_records'])
        self.assertIn('labor',result['concepts'])
        wrong,_=apply(result,{'type':'building_activity','building_id':'shop:12:10','object_id':'notice','choice_id':'help','nonce':'b-2'})
        self.assertEqual(wrong,result)
        self.assertEqual(len(BUILDINGS),6)
    def test_guide_mode_server_saved(self):
        s=new_state('2-2','13','학생')
        t,_=apply(s,{'type':'guide_setting','mode':'free','nonce':'g1'})
        self.assertEqual(t['guide_mode'],'free')
        u,_=apply(t,{'type':'guide_setting','mode':'invalid','nonce':'g2'})
        self.assertEqual(u,t)
    def test_png_manifest_matches_actual_files(self):
        manifest=json.loads((ROOT/'frontend/assets/manifest.json').read_text(encoding='utf8'))
        self.assertGreaterEqual(len(manifest['assets']),30)
        self.assertIn('school_exterior',manifest['assets'])
        for name,entry in manifest['assets'].items():
            data=(ROOT/'frontend'/entry['file']).read_bytes()
            self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
            w,h=struct.unpack('>II',data[16:24])
            self.assertEqual((w,h),(entry['width'],entry['height']))
            if name.startswith('teacher_'):
                self.assertEqual((w,h),(128,192))
    def test_public_content_includes_school(self):
        p=public_content()
        self.assertIn('school',p)
        self.assertEqual(len(p['school']['teachers']),17)

if __name__=='__main__':unittest.main()
