import unittest,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import new_state,apply
from storage import LocalStore

class StoreTests(unittest.TestCase):
    def test_save_restore_and_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'subfolder'/'data.sqlite3';store=LocalStore(file)
            state=new_state('classA','001','별이')
            store.save(state)
            state,_=apply(state,{'type':'choose','event_id':'career','choice_id':'stable','nonce':'one'})
            store.save(state);store.save(state)
            again=LocalStore(file).load('classA','001')
            self.assertEqual(again['revision'],1)
            self.assertEqual(again['flags']['career'],'공공서비스')
            self.assertIsNone(store.load('classB','001'))
            self.assertEqual(len(store.all_latest()),1)

if __name__=='__main__':unittest.main()
