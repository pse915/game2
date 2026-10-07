# -*- coding: utf-8 -*-
"""구글시트 연동: 저장 + 불러오기 + fallback"""
import csv
import datetime
import os

LOGS_HEADER = ["timestamp", "학번", "class_code", "nickname", "chapter",
               "choice_id", "choice_text", "my_children", "tfr_delta",
               "vitality", "happiness", "burden"]
RESULTS_HEADER = ["timestamp", "학번", "class_code", "nickname", "ending_type",
                  "final_tfr", "tfr_delta", "final_aging", "play_time_sec",
                  "full_path_summary"]

def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_sheet(ws_name):
    import streamlit as st
    import gspread
    creds = dict(st.secrets["gcp_service_account"])
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open_by_url(st.secrets["SHEET_URL"])
    try:
        ws = sh.worksheet(ws_name)
    except Exception:
        ws = sh.add_worksheet(title=ws_name, rows=1000, cols=20)
        ws.append_row(LOGS_HEADER if ws_name == "logs" else RESULTS_HEADER)
    # 헤더가 비어 있으면 추가
    try:
        if not ws.row_values(1):
            ws.append_row(LOGS_HEADER if ws_name == "logs" else RESULTS_HEADER)
    except Exception:
        pass
    return ws

def _fallback(row, fname="fallback_logs.csv"):
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, fname)
    new = not os.path.exists(path)
    with open(path, "a", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(LOGS_HEADER)
        w.writerow(row)
    return path

def save_choice(student_id, class_code, nickname, chapter, choice_id,
                choice_text, stats, tfr_delta):
    row = [_now(), student_id, class_code, nickname, chapter, choice_id,
           choice_text, stats.get("my_children", 0), tfr_delta,
           stats.get("vitality", 0), stats.get("happiness", 0), stats.get("burden", 0)]
    try:
        get_sheet("logs").append_row(row)
        return True, "시트 저장 완료"
    except Exception as e:
        path = _fallback(row)
        return False, f"시트 실패 → 로컬 백업({path}): {e}"

def save_result(student_id, class_code, nickname, ending_type, final_tfr,
                tfr_delta, final_aging, play_time_sec, summary):
    row = [_now(), student_id, class_code, nickname, ending_type, final_tfr,
           tfr_delta, final_aging, play_time_sec, summary]
    try:
        get_sheet("results").append_row(row)
        return True, "결과 저장 완료"
    except Exception as e:
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "fallback_results.csv")
        new = not os.path.exists(path)
        with open(path, "a", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(RESULTS_HEADER)
            w.writerow(row)
        return False, f"시트 실패 → 로컬 백업: {e}"

def load_progress(student_id):
    """학번으로 최신 로그들을 가져와 상태 복원. 반환: dict 또는 None"""
    import game_data as GD
    import logic as LG
    ws = get_sheet("logs")
    records = ws.get_all_records()
    mine = [r for r in records if str(r.get("학번", "")) == str(student_id)]
    if not mine:
        return None
    # timestamp 순 정렬 (문자열 정렬로 충분)
    mine.sort(key=lambda r: str(r.get("timestamp", "")))
    stats = LG.init_stats()
    flags, history = [], []
    # choice_id로 효과 재적용
    cmap = {}
    for ch in GD.CHAPTERS:
        for c in ch["choices"]:
            cmap[c["cid"]] = (ch, c)
    for r in mine:
        cid = str(r.get("choice_id", ""))
        if cid in cmap:
            ch, c = cmap[cid]
            stats = LG.apply_effects(stats, c.get("effects", {}))
            if "my_children" in c:
                stats["my_children"] = c["my_children"]
            for f in c.get("flags", []):
                if f not in flags:
                    flags.append(f)
            history.append({"chapter": ch["id"], "choice_id": cid,
                            "choice_text": c["text"]})
    # 현재 챕터 = 다음 미완료 챕터
    done = {h["chapter"] for h in history}
    next_ch = None
    for ch in GD.CHAPTERS:
        if ch["id"] not in done:
            next_ch = ch["id"]
            break
    last = mine[-1]
    return {"stats": stats, "flags": flags, "history": history,
            "next_chapter": next_ch, "nickname": last.get("nickname", ""),
            "class_code": last.get("class_code", ""), "count": len(mine)}

def read_results_df():
    import pandas as pd
    try:
        ws = get_sheet("results")
        rec = ws.get_all_records()
        return pd.DataFrame(rec)
    except Exception:
        return pd.DataFrame()
