# -*- coding: utf-8 -*-
"""미래마을을 구해라! 생애설계 어드벤처 (Streamlit + GitHub + Google Sheets)"""
import time
import streamlit as st

import game_data as GD
import logic as LG
import sheets as SH

st.set_page_config(page_title="미래마을을 구해라!", page_icon="🏘️", layout="wide")

# ---------- 세션 초기화 ----------
def init_state():
    d = {"authed": False, "student_id": "", "class_code": "", "nickname": "",
         "zone": 0, "px": 4, "py": 7, "chapter_idx": 0, "stats": LG.init_stats(),
         "flags": [], "history": [], "quiz_idx": 0, "quiz_score": 0,
         "quiz_done": False, "ended": False, "ending": None, "start_time": time.time(),
         "talk_npc": None, "save_msg": ""}
    for k, v in d.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
S = st.session_state

# ---------- 스타일 ----------
st.markdown("""
<style>
.map-grid {font-size:26px; line-height:1.15; letter-spacing:2px;}
.hud {background:#f0f7ff; padding:10px 14px; border-radius:12px; border:1px solid #cfe3ff;}
.talk {background:#fffbe6; padding:10px 14px; border-radius:12px; border:1px solid #ffe58f;}
.ending-big {font-size:30px; font-weight:800; color:#1a56db; text-align:center;}
</style>
""", unsafe_allow_html=True)

# ---------- HUD ----------
def hud():
    s = S.stats
    final, delta, bonus = LG.calc_tfr(s, S.flags)
    sign = "+" if delta >= 0 else ""
    st.markdown(f"""<div class="hud">
    <b>🏘️ {GD.ZONES[S.zone]['name']}</b> | 👤 {S.class_code} {S.student_id} {S.nickname} |
    👶 내 자녀 {s['my_children']}명 | 📈 TFR 기여도 <b>{sign}{delta}</b> (최종 {final}) |
    🏫 학교: {LG.school_status(s)}
    </div>""", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("마을출산율", f"{s['birth_village']:.2f}", help="시작 1.30")
    c2.metric("고령화율", f"{s['aging']:.1f}%", help="14% 고령사회, 20% 초고령")
    c3.progress(min(100, max(0, s["vitality"])) / 100, f"활력 {s['vitality']}")
    c4.progress(min(100, max(0, s["happiness"])) / 100, f"행복 {s['happiness']}")
    c5.progress(min(100, max(0, s["burden"])) / 100, f"돌봄부담 {s['burden']}")

def current_npcs():
    return [n for n in GD.NPCS if n["zone"] == S.zone]

def render_map():
    z = GD.ZONES[S.zone]
    w, h = z["w"], z["h"]
    npcs = {(n["x"], n["y"]): n for n in current_npcs()}
    # 포탈 위치 표시
    portals = {(x, y): tgt for (zz, x, y), tgt in GD.PORTALS.items() if zz == S.zone}
    rows = []
    for y in range(h):
        row = ""
        for x in range(w):
            if x == S.px and y == S.py:
                row += "🧑‍🎓"
            elif (x, y) in npcs:
                row += npcs[(x, y)]["emoji"]
            elif (x, y) in portals:
                row += "🌀"
            elif y == 0 and x in (3, 4, 5):
                # 구역 상징 건물
                sym = {"0": "🏫", "1": "🏛️", "2": "🧸", "3": "🏢", "4": "🏥"}[str(S.zone)]
                row += sym
            elif y == 4 and (x == 0 or x == w - 1):
                row += "🌀"
            else:
                row += "🟩" if (x + y) % 2 == 0 else "⬜"
        rows.append(row)
    st.markdown('<div class="map-grid">' + "<br>".join(rows) + "</div>", unsafe_allow_html=True)
    st.caption(f"{z['name']} - {z['desc']} | 🌀 포탈: 맵 가장자리로 이동하면 옆 마을로 이동. 키보드보다 아래 방향 버튼(태블릿용)을 사용하세요.")

def move(dx, dy):
    z = GD.ZONES[S.zone]
    nx, ny = S.px + dx, S.py + dy
    # 포탈 체크
    if (S.zone, nx, ny) in GD.PORTALS:
        S.zone = GD.PORTALS[(S.zone, nx, ny)]
        nz = GD.ZONES[S.zone]
        S.px, S.py = nz["spawn"][0], nz["spawn"][1]
        S.talk_npc = None
        return
    if 0 <= nx < z["w"] and 0 <= ny < z["h"]:
        S.px, S.py = nx, ny

def nearby_npc():
    for n in current_npcs():
        if abs(n["x"] - S.px) + abs(n["y"] - S.py) <= 1:
            return n
    return None

# ---------- 로그인 ----------
if not S.authed:
    st.title("🏘️ 미래마을을 구해라! 생애설계 어드벤처")
    st.write("중3(15세)부터 60대까지, 너의 선택이 마을의 합계출산율과 초고령화를 바꾼다. (기술·가정② p.102-103)")
    st.info("포켓몬 골드+ZEP식 탑다운: 방향 버튼으로 이동 → NPC 옆에서 [말걸기] → 챕터 선택지 결정 → 지표 변화 확인")
    with st.form("login"):
        c1, c2, c3 = st.columns(3)
        sid = c1.text_input("학번 (예: 30101)", max_chars=10)
        cls = c2.text_input("반 코드 (예: 3-1)", max_chars=10)
        nick = c3.text_input("닉네임", max_chars=12)
        col_a, col_b = st.columns(2)
        new_btn = col_a.form_submit_button("🆕 새로 시작", use_container_width=True)
        cont_btn = col_b.form_submit_button("📂 이어하기 (학번으로 불러오기)", use_container_width=True)
        if new_btn or cont_btn:
            if not sid.strip() or not nick.strip():
                st.error("학번과 닉네임은 필수입니다.")
            else:
                S.student_id, S.class_code, S.nickname = sid.strip(), cls.strip(), nick.strip()
                if cont_btn:
                    try:
                        with st.spinner("구글시트에서 불러오는 중..."):
                            data = SH.load_progress(S.student_id)
                    except Exception as e:
                        st.error(f"불러오기 실패(시트 연결 확인): {e}")
                        data = None
                    if data:
                        S.stats, S.flags, S.history = data["stats"], data["flags"], data["history"]
                        # 다음 챕터 인덱스 복원
                        if data["next_chapter"] is None:
                            S.chapter_idx = len(GD.CHAPTERS)
                        else:
                            ids = [c["id"] for c in GD.CHAPTERS]
                            S.chapter_idx = ids.index(data["next_chapter"])
                        ch = GD.CHAPTERS[min(S.chapter_idx, len(GD.CHAPTERS) - 1)]
                        S.zone = ch["zone"]
                        S.start_time = time.time()
                        S.authed = True
                        st.success(f"불러오기 성공! {data['count']}개 기록, {data['next_chapter']}부터 계속.")
                        st.rerun()
                    else:
                        st.warning("해당 학번 기록이 없습니다. 새로 시작합니다.")
                        S.stats, S.flags, S.history = LG.init_stats(), [], []
                        S.chapter_idx, S.start_time = 0, time.time()
                        S.authed = True
                        st.rerun()
                else:
                    S.stats, S.flags, S.history = LG.init_stats(), [], []
                    S.chapter_idx, S.start_time = 0, time.time()
                    S.authed = True
                    st.rerun()
    st.stop()

# ---------- 메인 ----------
hud()
tab_game, tab_quiz, tab_teacher = st.tabs(["🎮 게임", "📝 퀴즈 (6문제)", "👩‍🏫 교사 대시보드"])

with tab_game:
    left, right = st.columns([1.1, 1.4])
    with left:
        st.subheader(f"🗺️ {GD.ZONES[S.zone]['name']}")
        render_map()
        m1, m2, m3 = st.columns(3)
        with m1:
            st.button("⬆️", use_container_width=True, on_click=move, args=(0, -1))
        with m2:
            pass
        with m3:
            pass
        b1, b2, b3, b4 = st.columns(4)
        b1.button("⬅️", use_container_width=True, on_click=move, args=(-1, 0))
        b2.button("⬇️", use_container_width=True, on_click=move, args=(0, 1))
        b3.button("➡️", use_container_width=True, on_click=move, args=(1, 0))
        b4.button("🌀 포탈", use_container_width=True, help="맵 가장자리 🌀로 가면 자동 이동",
                  on_click=lambda: None)
        # 포탈 수동 이동 버튼 (모바일 편의)
        pz = st.selectbox("포탈 이동", [GD.ZONES[i]["name"] for i in range(5)], index=S.zone)
        if st.button("해당 마을로 이동"):
            S.zone = [GD.ZONES[i]["name"] for i in range(5)].index(pz)
            S.px, S.py = GD.ZONES[S.zone]["spawn"]
            st.rerun()
        st.divider()
        npc = nearby_npc()
        if npc:
            st.markdown(f"<div class='talk'><b>{npc['emoji']} {npc['name']}</b><br>{npc['dialogue'].replace(chr(10), '<br>')}<br><i>💡 {npc['hint']}</i></div>", unsafe_allow_html=True)
        else:
            st.caption("NPC 옆(상하좌우 1칸)으로 이동하면 대화가 표시됩니다.")
        st.write("**이 마을 NPC 목록**")
        for n in current_npcs():
            st.write(f"{n['emoji']} {n['name']} ({n['x']},{n['y']})")

    with right:
        # 종료 후 엔딩
        if S.ended and S.ending:
            e, final, delta, bonus = S.ending
            info = GD.ENDING_INFO[e]
            sign = "+" if delta >= 0 else ""
            st.markdown(f"<div class='ending-big'>당신의 선택이 합계출산율을 {sign}{delta}만큼 {'올렸습니다' if delta>=0 else '내렸습니다'}!<br>최종 TFR {final:.2f}</div>", unsafe_allow_html=True)
            st.success(f"{info['title']} ({info['cond']}) — {info['desc']}")
            st.bar_chart({"나의 TFR": final, "시작값": 1.30, "전국 참고": 0.72})
            st.write(f"보너스 합계 {bonus:+.2f} | 내 자녀 {S.stats['my_children']}명 | 고령화율 {S.stats['aging']:.1f}% | 플래그: {', '.join(S.flags) if S.flags else '없음'}")
            st.write("**내 선택 경로:** " + (" → ".join([h['choice_id'] for h in S.history]) if S.history else "-"))
            if st.button("🔄 처음부터 다시"):
                for k in ("chapter_idx", "ended", "ending", "quiz_done", "quiz_score", "quiz_idx"):
                    S[k] = 0 if "idx" in k or "score" in k else (False if isinstance(S[k], bool) else None)
                S.stats, S.flags, S.history = LG.init_stats(), [], []
                S.chapter_idx, S.ended, S.ending = 0, False, None
                S.start_time = time.time()
                S.zone, S.px, S.py = 0, 4, 7
                st.rerun()
        elif S.chapter_idx >= len(GD.CHAPTERS):
            st.info("모든 챕터를 완료했습니다. 퀴즈 탭을 풀고 아래 버튼으로 엔딩을 확인하세요.")
            if st.button("🏁 엔딩 확정 + 결과 저장", type="primary", use_container_width=True):
                e, final, delta, bonus = LG.determine_ending(S.stats, S.flags)
                S.ending, S.ended = (e, final, delta, bonus), True
                play_sec = int(time.time() - S.start_time)
                summary = " → ".join([h["choice_id"] for h in S.history]) + f" | flags:{','.join(S.flags)}"
                ok, msg = SH.save_result(S.student_id, S.class_code, S.nickname, e, final, delta, S.stats["aging"], play_sec, summary)
                S.save_msg = msg
                st.success(msg)
                st.rerun()
            if S.save_msg:
                st.caption(S.save_msg)
        else:
            ch = GD.CHAPTERS[S.chapter_idx]
            # 챕터 구역 자동 안내 (이동 강제 아님)
            st.subheader(ch["title"])
            st.write(f"*{ch['age']} · 현재 {S.chapter_idx+1}/{len(GD.CHAPTERS)}*")
            st.write(ch["story"])
            if S.zone != ch["zone"]:
                st.warning(f"이 챕터 추천 마을: {GD.ZONES[ch['zone']]['name']} — 왼쪽 포탈로 이동하면 몰입도가 높아집니다.")
            for c in ch["choices"]:
                locked, reason = LG.is_locked(ch["id"], c["cid"], S.flags, S.history)
                if locked:
                    st.button(f"🔒 {c['text']} — {reason}", disabled=True, key=c["cid"], use_container_width=True)
                    continue
                if st.button(c["text"], key=c["cid"], use_container_width=True):
                    S.stats = LG.apply_effects(S.stats, c.get("effects", {}))
                    if "my_children" in c:
                        S.stats["my_children"] = c["my_children"]
                    for f in c.get("flags", []):
                        if f not in S.flags:
                            S.flags.append(f)
                    S.history.append({"chapter": ch["id"], "choice_id": c["cid"], "choice_text": c["text"]})
                    final, delta, _ = LG.calc_tfr(S.stats, S.flags)
                    ok, msg = SH.save_choice(S.student_id, S.class_code, S.nickname, ch["id"], c["cid"], c["text"], S.stats, delta)
                    S.save_msg = msg
                    st.toast(f"{c['feedback']} ({msg})")
                    # 다음 챕터로
                    S.chapter_idx += 1
                    if S.chapter_idx < len(GD.CHAPTERS):
                        S.zone = GD.CHAPTERS[S.chapter_idx]["zone"]
                        S.px, S.py = GD.ZONES[S.zone]["spawn"]
                    st.rerun()
            if S.save_msg:
                st.caption(f"💾 {S.save_msg}")
            st.divider()
            st.write("**진행 기록**")
            for h in S.history:
                st.write(f"- {h['chapter']}: {h['choice_text']}")

with tab_quiz:
    st.subheader("📝 교과서 퀴즈 6문제 (맞히면 TFR 보너스 +0.02/문제)")
    if S.quiz_done:
        st.success(f"완료! 점수 {S.quiz_score}/6 — 보너스 {S.stats.get('quiz_bonus',0):+.2f}가 최종 TFR에 반영됩니다.")
        if st.button("퀴즈 다시 풀기"):
            S.quiz_idx, S.quiz_score, S.quiz_done = 0, 0, False
            S.stats["quiz_bonus"] = 0
            st.rerun()
    else:
        q = GD.QUIZZES[S.quiz_idx]
        st.write(f"**Q{S.quiz_idx+1}. {q['q']}**")
        for i, o in enumerate(q["opts"]):
            if st.button(o, key=f"q{S.quiz_idx}_{i}", use_container_width=True):
                if i == q["answer"]:
                    st.success(f"정답! {q['explain']}")
                    S.quiz_score += 1
                    S.stats["quiz_bonus"] = round(S.stats.get("quiz_bonus", 0) + 0.02, 2)
                else:
                    st.error(f"오답. {q['explain']}")
                S.quiz_idx += 1
                if S.quiz_idx >= len(GD.QUIZZES):
                    S.quiz_done = True
                st.rerun()

with tab_teacher:
    st.subheader("👩‍🏫 교사 대시보드 (results 시트)")
    st.caption("results 워크시트의 반별 평균 TFR 기여도를 보여줍니다. 시트 연결 실패 시 빈 화면.")
    try:
        df = SH.read_results_df()
        if df.empty:
            st.info("아직 저장된 결과가 없습니다. 학생들이 엔딩까지 완료하면 표시됩니다.")
        else:
            st.dataframe(df.tail(50), use_container_width=True)
            if "tfr_delta" in df.columns and "class_code" in df.columns:
                import pandas as pd
                df["tfr_delta"] = pd.to_numeric(df["tfr_delta"], errors="coerce")
                st.bar_chart(df.groupby("class_code")["tfr_delta"].mean())
            if "ending_type" in df.columns:
                st.bar_chart(df["ending_type"].value_counts())
    except Exception as e:
        st.error(f"시트 읽기 실패: {e}")

# 사이드바
with st.sidebar:
    st.write("💾 저장 상태")
    st.write(S.save_msg or "아직 저장 전")
    if st.button("로그아웃"):
        S.authed = False
        st.rerun()
