# -*- coding: utf-8 -*-
"""게임 수치 로직: 효과 적용, TFR 계산, 엔딩 판정, 잠금 분기"""

BASE_BIRTH = 1.30

def init_stats():
    return {
        "birth_village": BASE_BIRTH,
        "aging": 14.0,
        "vitality": 50,
        "happiness": 50,
        "burden": 50,
        "my_children": 0,
        "quiz_bonus": 0,
    }

def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))

def apply_effects(stats, effects):
    s = dict(stats)
    for k, v in (effects or {}).items():
        if k == "birth_village":
            s["birth_village"] = round(s["birth_village"] + v, 2)
        elif k == "aging":
            s["aging"] = round(s["aging"] + v, 1)
        elif k in ("vitality", "happiness", "burden"):
            s[k] = clamp(s[k] + v)
    return s

def calc_tfr(stats, flags):
    """기여도 delta = (내자녀수 - 1.30) + 보너스합"""
    flags = set(flags or [])
    bonus = 0.0
    if "가족가치학습" in flags:
        bonus += 0.05
    if "공동육아" in flags:
        bonus += 0.10
    # 제도활용 보너스: 최대 +0.15
    sys_flags = {"제도활용", "주거안정", "세대협동", "실버활용", "노후준비", "지방정착", "다자녀", "결혼", "정보탐색"}
    bonus += min(0.15, 0.05 * len(flags & sys_flags))
    if "독박" in flags:
        bonus -= 0.10
    if "무준비" in flags:
        bonus -= 0.10
    if "정책무지" in flags:
        bonus -= 0.05
    bonus += stats.get("quiz_bonus", 0)
    delta = round((stats.get("my_children", 0) - BASE_BIRTH) + bonus, 2)
    final = round(BASE_BIRTH + delta, 2)
    return final, delta, round(bonus, 2)

def determine_ending(stats, flags):
    final, delta, bonus = calc_tfr(stats, flags)
    h, b, a = stats["happiness"], stats["burden"], stats["aging"]
    if h <= 30 or b >= 80:
        return "D", final, delta, bonus
    if final >= 1.60:
        return "A", final, delta, bonus
    if final <= 0.99 or a >= 20.0:
        return "C", final, delta, bonus
    return "B", final, delta, bonus

def is_locked(chapter_id, cid, flags, history):
    """숨은 잠금: CH2-D는 CH1-B 필요"""
    chosen = {h["choice_id"] for h in (history or [])}
    if cid == "CH2-D" and "CH1-B" not in chosen:
        return True, "CH1-B(불안정 알바)를 경험해야 해금됩니다."
    return False, ""

def school_status(stats):
    if stats["birth_village"] <= 0.99:
        return "🏚️ 폐교 (출산율 0.99 이하)"
    if stats["birth_village"] >= 1.60:
        return "🏫 신설! 활기찬 학교"
    return "🏫 유지 중"
