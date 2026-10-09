"""Append-only Google Sheets snapshots or local SQLite fallback.
No keys reach browsers. Local mode is for pilots, not durable Streamlit Cloud storage.
"""
from __future__ import annotations
import json, os, sqlite3, time
from pathlib import Path
from typing import Optional

HEADERS=['event_id','saved_at','class_code','student_id','nickname','run_id','revision','state_json']
DB_PATH=Path(os.getenv('SEWOL_DB','data/sewol_port.sqlite3'))

class StorageError(Exception):
    pass

class LocalStore:
    label='로컬 SQLite (개발용)'
    def __init__(self,path:Path|None=None):
        self.path=path or DB_PATH
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self._connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS saves (event_id TEXT PRIMARY KEY, saved_at REAL, class_code TEXT, student_id TEXT, nickname TEXT, run_id TEXT, revision INTEGER, state_json TEXT)')
            db.execute('CREATE INDEX IF NOT EXISTS by_student ON saves (class_code,student_id,saved_at)')
    def _connection(self):
        db=sqlite3.connect(self.path,timeout=10)
        db.execute('PRAGMA busy_timeout=10000')
        return db
    def load(self,school_class,student_id)->Optional[dict]:
        with self._connection() as db:
            record=db.execute('SELECT state_json FROM saves WHERE class_code=? AND student_id=? ORDER BY saved_at DESC LIMIT 1',(school_class,student_id)).fetchone()
        return json.loads(record[0]) if record else None
    def save(self,state):
        key=f"{state['run_id']}:{state['revision']}"
        with self._connection() as db:
            db.execute('INSERT OR IGNORE INTO saves VALUES (?,?,?,?,?,?,?,?)',(
                key,time.time(),state['class_code'],state['student_id'],state['nickname'],state['run_id'],state['revision'],json.dumps(state,ensure_ascii=False)))
        return key
    def all_latest(self):
        with self._connection() as db:
            rows=db.execute('SELECT state_json FROM saves ORDER BY saved_at DESC').fetchall()
        unique={}
        for (raw,) in rows:
            data=json.loads(raw)
            key=(data['class_code'],data['student_id'])
            unique.setdefault(key,data)
        return list(unique.values())

class SheetsStore:
    label='Google Sheets'
    def __init__(self,settings):
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            scopes=['https://www.googleapis.com/auth/spreadsheets']
            credentials=Credentials.from_service_account_info(dict(settings['gcp_service_account']),scopes=scopes)
            self.book=gspread.authorize(credentials).open_by_key(settings['sheet_id'])
            try:
                self.tab=self.book.worksheet('sewol_port_v1')
            except gspread.WorksheetNotFound:
                self.tab=self.book.add_worksheet('sewol_port_v1',rows=3000,cols=len(HEADERS))
            if not self.tab.row_values(1):
                self.tab.update(range_name='A1:H1',values=[HEADERS],value_input_option='RAW')
            elif self.tab.row_values(1)!=HEADERS:
                raise StorageError('sewol_port_v1 워크시트 헤더가 예상과 다릅니다.')
        except Exception as ex:
            raise StorageError(f'Google Sheets 연결 실패: {ex}') from ex
    def _rows(self):
        try:
            return self.tab.get_all_records(numericise_ignore=['all'])
        except Exception as ex:
            raise StorageError(f'Google Sheets 읽기 실패: {ex}') from ex
    def load(self,school_class,student_id):
        candidates=[r for r in self._rows() if r['class_code']==school_class and r['student_id']==student_id]
        if not candidates:return None
        return json.loads(candidates[-1]['state_json'])
    def save(self,state):
        key=f"{state['run_id']}:{state['revision']}"
        # Sheets append is not transactional; a student should use one device at a time.
        row=[key,str(time.time()),state['class_code'],state['student_id'],state['nickname'],
             state['run_id'],str(state['revision']),json.dumps(state,ensure_ascii=False,separators=(',',':'))]
        try:
            self.tab.append_row(row,value_input_option='RAW')
        except Exception as ex:
            raise StorageError(f'Google Sheets 저장 실패: {ex}') from ex
        return key
    def all_latest(self):
        unique={}
        for row in self._rows():
            try:
                state=json.loads(row['state_json'])
                unique[(state['class_code'],state['student_id'])]=state
            except (KeyError,ValueError,TypeError):
                continue
        return list(unique.values())

def make_store(settings):
    if settings.get('sheet_id') and settings.get('gcp_service_account'):
        return SheetsStore(settings)
    return LocalStore()
