"""Contract checks for the revised, still unverified L-shaped school map."""
from collections import deque
import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from school import SCHOOL_FLOORS, ROOM_ORDER, TEACHER_MAP, SPECIAL, STAIRS, SCHOOL_ENTRY, hall_walkable
from content import public_content

class LSchoolLayoutTests(unittest.TestCase):
    def test_layout_is_bent_and_connected(self):
        self.assertTrue(hall_walkable(7,9))
        self.assertTrue(hall_walkable(7,16))
        self.assertTrue(hall_walkable(25,9))
        self.assertFalse(hall_walkable(22,15), 'The bottom-right courtyard is not a passable hallway')
        self.assertFalse(hall_walkable(5,14), 'Students cannot pass through room walls')
        self.assertEqual(SCHOOL_ENTRY,[15,9])
        for stair in STAIRS.values(): self.assertTrue(hall_walkable(*stair))
    def test_every_registered_room_door_is_independently_reachable(self):
        queue=deque([tuple(SCHOOL_ENTRY)]); seen=set(queue)
        while queue:
            x,y=queue.popleft()
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                p=x+dx,y+dy
                if p not in seen and hall_walkable(*p):seen.add(p);queue.append(p)
        for f,rooms in SCHOOL_FLOORS.items():
            self.assertEqual({r['id'] for r in rooms},set(ROOM_ORDER[f]['west']+ROOM_ORDER[f]['north']))
            self.assertEqual(len({tuple(r['door']) for r in rooms}),len(rooms),f)
            for r in rooms:
                with self.subTest(floor=f,room=r['id']):
                    self.assertIn(tuple(r['door']),seen)
                    self.assertEqual(r['floor_id'],int(f))
                    self.assertEqual(r['display_name'],r['name'])
                    self.assertTrue(r['name'].strip())
                    self.assertTrue(r['interior_map_id'].endswith(r['room_id']))
                    self.assertTrue(r['label_position'])
                    self.assertIn(r['kind'],['class','special'])
    def test_all_given_special_rooms_and_17_teachers_are_present(self):
        available={r['id'] for rooms in SCHOOL_FLOORS.values() for r in rooms}
        self.assertTrue(set(SPECIAL).issubset(available))
        self.assertTrue(set(TEACHER_MAP).issubset(available))
        self.assertEqual(len(TEACHER_MAP),17)
        self.assertIn('학습지원실2',[r['name'] for r in SCHOOL_FLOORS['1'] if r['wing']=='west'])
        self.assertIn('Wee클래스',[r['name'] for r in SCHOOL_FLOORS['3']])
        self.assertIn('국어도서관',[r['name'] for r in SCHOOL_FLOORS['4']])
        self.assertEqual(len(available),sum(map(len,SCHOOL_FLOORS.values())))
    def test_public_payload_contains_labels_for_directory_and_canvas(self):
        p=public_content()['school']
        self.assertEqual(p['stairs'],STAIRS)
        self.assertTrue(p['layout_status'])
        for floor,rooms in p['floors'].items():
            for r in rooms: self.assertEqual(len(r['door']),2)

if __name__=='__main__': unittest.main()
