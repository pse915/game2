import copy, json, tempfile, unittest
from pathlib import Path
from engine import new_state
from storage import Store, LOG_HEADERS, RESULT_HEADERS
class FakeWorksheet:
    def __init__(self,headers):self.headers=headers;self.rows=[]
    def append_row(self,row,**kwargs):self.rows.append(list(row))
    def get_all_records(self,**kwargs):return [dict(zip(self.headers,r)) for r in self.rows]
    def col_values(self,index):return [self.headers[index-1]]+[r[index-1] for r in self.rows]
class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Store(fallback_path=Path(self.tmp.name)/'fallback_logs.csv');self.s=new_state('001','3-1','별명','1234')
    def tearDown(self):self.tmp.cleanup()
    def test_offline_roundtrip_latest_and_class(self):
        self.assertIn('백업',self.store.save(self.s));self.s['chapter']=1;self.store.save(self.s)
        result=self.store.latest('001','3-1');self.assertEqual(result['chapter'],1);self.assertEqual(result['student_id'],'001');self.assertIsNone(self.store.latest('001','3-2'))
    def test_results_latest_only(self):
        self.s['finished']=True;self.s['ended_at']=self.s['start_time']+600;self.store.save(self.s)
        self.s['stats']['children']=2;self.store.save(self.s)
        rows=self.store.results();self.assertEqual(len(rows),1);self.assertAlmostEqual(float(rows[0]['final_tfr']),1.95)
    def test_sync_idempotent(self):
        self.s['finished']=True;self.store.save(self.s)
        sheets={'logs':FakeWorksheet(LOG_HEADERS),'results':FakeWorksheet(RESULT_HEADERS)}
        self.store.sheet=lambda name,headers:sheets[name]
        self.assertEqual(self.store.sync(),1);self.assertEqual(self.store.sync(),0)
        self.assertEqual(len(sheets['logs'].rows),1);self.assertEqual(len(sheets['results'].rows),1)
    def test_partial_write_repaired(self):
        sheets={'logs':FakeWorksheet(LOG_HEADERS),'results':FakeWorksheet(RESULT_HEADERS)}
        def failed(row,**kwargs):raise RuntimeError('일시적인 쓰기 실패')
        sheets['results'].append_row=failed;self.store.sheet=lambda name,headers:sheets[name]
        self.s['finished']=True;self.store.save(self.s)
        self.assertEqual(len(sheets['logs'].rows),1);self.assertTrue(self.store.path.exists())
        sheets['results']=FakeWorksheet(RESULT_HEADERS);self.store.sync()
        self.assertEqual(len(sheets['logs'].rows),1);self.assertEqual(len(sheets['results'].rows),1)
    def test_auth_error_stops_connection_retry(self):
        self.store.failure(RuntimeError('403 permission denied'));self.assertTrue(self.store.disabled)
if __name__=='__main__':unittest.main()
