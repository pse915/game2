"""Google Sheets 저장과 로컬 CSV 비상 백업입니다. 인증 키는 브라우저에 보내지 않습니다."""
import csv, json, threading, time, uuid
from pathlib import Path
from datetime import datetime, timezone
from engine import validate_state, score, ending_code
LOCK=threading.RLock()
LOG_HEADERS=['event_id','saved_at','class_code','student_id','nickname','run_id','event','state_json']
RESULT_HEADERS=['event_id','saved_at','class_code','student_id','nickname','run_id','ending','contribution','final_tfr','happiness','care','minutes','quiz_correct']

class Store:
    def __init__(self,config=None,fallback_path='fallback_logs.csv'):
        self.config=dict(config or {});self.path=Path(fallback_path);self.book=None;self.sheets={};self.error='';self.disabled=False
        self.configured=bool(self.config.get('sheet_id') and self.config.get('gcp_service_account'))
    def connect(self):
        if not self.configured:raise RuntimeError('Google Sheets 미설정: 로컬 CSV로 저장합니다.')
        if self.disabled:raise RuntimeError('Google 권한 오류로 재시도를 중지했어요. 서비스계정과 시트 공유를 확인한 뒤 앱을 재시작하세요.')
        if self.book is None:
            import gspread
            from google.oauth2.service_account import Credentials
            creds=Credentials.from_service_account_info(dict(self.config['gcp_service_account']),scopes=['https://www.googleapis.com/auth/spreadsheets'])
            gc=gspread.authorize(creds);gc.set_timeout(12)
            self.book=gc.open_by_key(self.config['sheet_id'])
        return self.book
    def sheet(self,name,headers):
        if name in self.sheets:return self.sheets[name]
        import gspread
        book=self.connect()
        try:ws=book.worksheet(name)
        except gspread.WorksheetNotFound:
            try:ws=book.add_worksheet(title=name,rows=1000,cols=len(headers))
            except gspread.exceptions.APIError:ws=book.worksheet(name)
        existing=ws.row_values(1)
        if not existing:ws.update([headers],range_name='A1',value_input_option='RAW')
        elif existing!=headers:raise ValueError(name+' 시트의 첫 행이 예시와 달라요. 빈 시트를 쓰거나 헤더를 확인하세요.')
        self.sheets[name]=ws
        return ws
    def failure(self,error):
        # 비밀키나 인증 응답 전문을 학생 화면에 내보내지 않습니다.
        text=str(error).lower()
        if any(t in text for t in ('401','403','permission','insufficient_scope','invalid_grant','forbidden')):
            self.disabled=True;self.error='Google 인증·권한 오류입니다. 서비스계정 키와 시트 편집자 공유를 교사가 확인해야 합니다.'
        elif not self.configured:self.error='Google Sheets가 설정되지 않아 로컬 백업 모드로 동작합니다.'
        else:self.error='Google Sheets 저장·조회에 실패했어요. 네트워크 또는 시트 설정을 확인해 주세요.'
    def read_fallback(self):
        if not self.path.exists():return []
        with LOCK,self.path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
    def append_fallback(self,row):
        with LOCK:
            exists=self.path.exists() and self.path.stat().st_size>0
            self.path.parent.mkdir(parents=True,exist_ok=True)
            with self.path.open('a',encoding='utf-8',newline='') as f:
                writer=csv.writer(f)
                if not exists:writer.writerow(LOG_HEADERS)
                writer.writerow(row)
    def make_log(self,state,event):
        return [str(uuid.uuid4()),datetime.now(timezone.utc).isoformat(),state['class_code'],state['student_id'],state['nickname'],state['run_id'],event,json.dumps(state,ensure_ascii=False,separators=(',',':'))]
    def result_row(self,record):
        s=json.loads(record['state_json']);d,t=score(s)
        return [record['event_id'],record['saved_at'],s['class_code'],s['student_id'],s['nickname'],s['run_id'],ending_code(s),d,t,s['stats']['happiness'],s['stats']['care'],round((s.get('ended_at',s['start_time'])-s['start_time'])/60,1),sum(bool(q.get('correct')) for q in s['quizzes'].values())]
    def save(self,state,event='자동저장'):
        row=self.make_log(state,event);record=dict(zip(LOG_HEADERS,row))
        try:
            self.sheet('logs',LOG_HEADERS).append_row(row,value_input_option='RAW')
            if state['finished']:self.sheet('results',RESULT_HEADERS).append_row(self.result_row(record),value_input_option='RAW')
            self.error='';return 'Google Sheets에 저장했어요.'
        except Exception as e:
            self.failure(e)
            try:self.append_fallback(row);return self.error+' fallback_logs.csv 백업을 완료했어요.'
            except Exception:return self.error+' 로컬 파일 쓰기도 실패했어요. 반드시 개인 저장파일을 내려받아 주세요.'
    def logs(self):
        remote=[]
        try:remote=self.sheet('logs',LOG_HEADERS).get_all_records(numericise_ignore=['all']);self.error=''
        except Exception as e:self.failure(e)
        local=self.read_fallback()
        records={r['event_id']:r for r in remote+local if r.get('event_id')}
        return sorted(records.values(),key=lambda r:r['saved_at'])
    def latest(self,student_id,class_code):
        rows=[r for r in self.logs() if str(r['student_id'])==student_id and str(r['class_code'])==class_code]
        if not rows:return None
        return validate_state(json.loads(rows[-1]['state_json']))
    def results(self):
        # logs를 대신 평균내지 않고 results 시트와 미전송 엔딩 백업만 합칩니다.
        remote=[]
        try:remote=self.sheet('results',RESULT_HEADERS).get_all_records(numericise_ignore=['all']);self.error=''
        except Exception as e:self.failure(e)
        local=[]
        for r in self.read_fallback():
            try:
                if json.loads(r['state_json']).get('finished'):local.append(dict(zip(RESULT_HEADERS,self.result_row(r))))
            except (ValueError,KeyError,TypeError):continue
        # 재저장·동기화로 같은 학생이 중복 집계되지 않도록 학생별 최신 엔딩을 택합니다.
        latest={}
        for r in sorted(remote+local,key=lambda r:r.get('saved_at','')):latest[(r['class_code'],r['student_id'])]=r
        return list(latest.values())
    def sync(self):
        """교사가 명시적으로 실행합니다. 성공한 로컬 행도 감사용으로 보존합니다."""
        rows=self.read_fallback()
        if not rows:return 0
        try:
            logs=self.sheet('logs',LOG_HEADERS);results=self.sheet('results',RESULT_HEADERS)
            ids=set(logs.col_values(1)[1:]);rids=set(results.col_values(1)[1:]);count=0
            for r in rows:
                if r['event_id'] not in ids:
                    logs.append_row([r[h] for h in LOG_HEADERS],value_input_option='RAW');ids.add(r['event_id']);count+=1
                if json.loads(r['state_json']).get('finished') and r['event_id'] not in rids:
                    results.append_row(self.result_row(r),value_input_option='RAW');rids.add(r['event_id'])
            self.error='';return count
        except Exception as e:self.failure(e);raise RuntimeError(self.error) from None
