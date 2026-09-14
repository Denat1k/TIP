"""Генератор Scratch 3 проекта: слияние двух отсортированных массивов за один цикл.

Запуск:  python3 scratch_merge.py
Результат: merge_sorted_arrays.sb3
"""

import json
import zipfile
import os
import shutil
import hashlib

# ===========================================================================
#  ЯДРО: сборка блоков Scratch 3
# ===========================================================================

blocks_by_target = {}
current_target = [None]
_counter = [0]


def new_id():
    _counter[0] += 1
    return "b%d" % _counter[0]


def use_target(name):
    current_target[0] = name
    blocks_by_target.setdefault(name, {})


def B():
    return blocks_by_target[current_target[0]]


# Обёртки, задающие способ подстановки блока в input
class R(str):
    """репортёр в обычный input -> [3, id, [10, ""]]"""


class RN(str):
    """репортёр в числовой input -> [3, id, [4, "1"]]"""


class RI(str):
    """репортёр в input индекса -> [3, id, [7, "1"]]"""


class C(str):
    """условие или SUBSTACK -> [2, id]"""


class MENU(str):
    """shadow-меню -> [1, id]"""


class MR(tuple):
    """репортёр поверх меню -> [3, ref_id, menu_id]"""


def mk(opcode, inp=None, fld=None, top=False, x=0, y=0, shadow=False):
    bid = new_id()
    blocks = B()
    ins = {}
    for key, val in (inp or {}).items():
        if isinstance(val, R):
            ins[key] = [3, str(val), [10, ""]]
            blocks[str(val)]["parent"] = bid
        elif isinstance(val, RN):
            ins[key] = [3, str(val), [4, "1"]]
            blocks[str(val)]["parent"] = bid
        elif isinstance(val, RI):
            ins[key] = [3, str(val), [7, "1"]]
            blocks[str(val)]["parent"] = bid
        elif isinstance(val, C):
            ins[key] = [2, str(val)]
            blocks[str(val)]["parent"] = bid
        elif isinstance(val, MENU):
            ins[key] = [1, str(val)]
            blocks[str(val)]["parent"] = bid
        elif isinstance(val, MR):
            ins[key] = [3, val[0], val[1]]
            blocks[val[0]]["parent"] = bid
            blocks[val[1]]["parent"] = bid
        else:
            ins[key] = val
    blocks[bid] = {
        "opcode": opcode,
        "next": None,
        "parent": None,
        "inputs": ins,
        "fields": fld or {},
        "shadow": shadow,
        "topLevel": top,
        "x": x,
        "y": y,
    }
    return bid


def chain(first, *rest):
    blocks = B()
    prev = first
    for nxt in rest:
        blocks[prev]["next"] = nxt
        blocks[nxt]["parent"] = prev
        prev = nxt
    return first


def n(v):
    return [1, [4, str(v)]]


def s(v):
    return [1, [10, str(v)]]


# ===========================================================================
#  ИДЕНТИФИКАТОРЫ ПЕРЕМЕННЫХ, СПИСКОВ, СООБЩЕНИЙ
# ===========================================================================

VAR_A = "var_a"
VAR_B = "var_b"
VAR_I = "var_i"
VAR_J = "var_j"
VAR_CNT = "var_cnt"
VAR_SEL_ARR = "var_sel_arr"
VAR_SEL_IDX = "var_sel_idx"
VAR_SLOT = "var_slot"

LIST_A = "list_a"
LIST_B = "list_b"
LIST_R = "list_r"

# локальные переменные спрайта «Плитка»
TV_ARR = "tv_arr"
TV_IDX = "tv_idx"
TV_VAL = "tv_val"
TV_SLOT = "tv_slot"
TV_K = "tv_k"

BC = {
    "сброс": "bc_reset",
    "создать": "bc_build",
    "указатели": "bc_point",
    "сравнить": "bc_cmp",
    "перенести": "bc_move",
    "волна": "bc_wave",
    "салют": "bc_fire",
}

INITIAL_A = [2, 4, 6, 8, 10, 12]
INITIAL_B = [1, 3, 5, 7, 9, 11, 13, 15]

# геометрия сцены (координаты Scratch: центр 0,0)
ROW_A_Y = 58
ROW_B_Y = -14
ROW_R_Y = -82
PTR_A_Y = 86
PTR_B_Y = 12
SLOT_X0 = -210
SLOT_STEP = 30
MAX_SLOTS = 15


# ---------------------------------------------------------------------------
#  Готовые конструкторы блоков
# ---------------------------------------------------------------------------

def V(name, vid):
    return mk("data_variable", fld={"VARIABLE": [name, vid]})


def v_a():
    return V("a", VAR_A)


def v_b():
    return V("b", VAR_B)


def v_i():
    return V("i", VAR_I)


def v_j():
    return V("j", VAR_J)


def v_cnt():
    return V("Сч", VAR_CNT)


def v_sel_arr():
    return V("выбран массив", VAR_SEL_ARR)


def v_sel_idx():
    return V("выбран индекс", VAR_SEL_IDX)


def v_slot():
    return V("слот", VAR_SLOT)


def v_my_arr():
    return V("мой массив", TV_ARR)


def v_my_idx():
    return V("мой индекс", TV_IDX)


def v_my_val():
    return V("моё значение", TV_VAL)


def v_my_slot():
    return V("мой слот", TV_SLOT)


def v_k():
    return V("к", TV_K)


def item_of(list_name, list_id, idx_block):
    return mk("data_itemoflist", inp={"INDEX": RI(idx_block)},
              fld={"LIST": [list_name, list_id]})


def len_of(list_name, list_id):
    return mk("data_lengthoflist", fld={"LIST": [list_name, list_id]})


def add_to(list_name, list_id, item_input):
    return mk("data_addtolist", inp={"ITEM": item_input},
              fld={"LIST": [list_name, list_id]})


def del_all(list_name, list_id):
    return mk("data_deletealloflist", fld={"LIST": [list_name, list_id]})


def setv(name, vid, value_input):
    return mk("data_setvariableto", inp={"VALUE": value_input},
              fld={"VARIABLE": [name, vid]})


def changev(name, vid, value_input):
    return mk("data_changevariableby", inp={"VALUE": value_input},
              fld={"VARIABLE": [name, vid]})


def op(opcode, a_key, a_val, b_key, b_val):
    return mk(opcode, inp={a_key: a_val, b_key: b_val})


def add_(x, y):
    return op("operator_add", "NUM1", x, "NUM2", y)


def sub_(x, y):
    return op("operator_subtract", "NUM1", x, "NUM2", y)


def mul_(x, y):
    return op("operator_multiply", "NUM1", x, "NUM2", y)


def gt_(x, y):
    return op("operator_gt", "OPERAND1", x, "OPERAND2", y)


def eq_(x, y):
    return op("operator_equals", "OPERAND1", x, "OPERAND2", y)


def and_(x, y):
    return op("operator_and", "OPERAND1", C(x), "OPERAND2", C(y))


def or_(x, y):
    return op("operator_or", "OPERAND1", C(x), "OPERAND2", C(y))


def not_(x):
    return mk("operator_not", inp={"OPERAND": C(x)})


def join_(x, y):
    return op("operator_join", "STRING1", x, "STRING2", y)


def random_(lo, hi):
    return op("operator_random", "FROM", n(lo), "TO", n(hi))


def wait(secs):
    return mk("control_wait", inp={"DURATION": n(secs)})


def repeat(times_input, body_first):
    return mk("control_repeat", inp={"TIMES": times_input, "SUBSTACK": C(body_first)})


def if_(cond_id, body_first):
    return mk("control_if", inp={"CONDITION": C(cond_id), "SUBSTACK": C(body_first)})


def if_else(cond_id, then_first, else_first):
    return mk("control_if_else", inp={"CONDITION": C(cond_id),
                                      "SUBSTACK": C(then_first),
                                      "SUBSTACK2": C(else_first)})


def goto(x_input, y_input):
    return mk("motion_gotoxy", inp={"X": x_input, "Y": y_input})


def glide(secs, x_input, y_input):
    return mk("motion_glidesecstoxy", inp={"SECS": n(secs), "X": x_input, "Y": y_input})


def set_size(v):
    return mk("looks_setsizeto", inp={"SIZE": n(v)})


def change_size(v):
    return mk("looks_changesizeby", inp={"CHANGE": n(v)})


def change_effect(effect, v):
    return mk("looks_changeeffectby", inp={"CHANGE": n(v)},
              fld={"EFFECT": [effect, None]})


def set_effect(effect, value_input):
    return mk("looks_seteffectto", inp={"VALUE": value_input},
              fld={"EFFECT": [effect, None]})


def clear_effects():
    return mk("looks_cleargraphiceffects")


def show():
    return mk("looks_show")


def hide():
    return mk("looks_hide")


def say_for(text, secs):
    return mk("looks_sayforsecs", inp={"MESSAGE": s(text), "SECS": n(secs)})


def switch_costume(ref_block, default_name):
    menu = mk("looks_costume", fld={"COSTUME": [default_name, None]}, shadow=True)
    return mk("looks_switchcostumeto", inp={"COSTUME": MR((ref_block, menu))})


def switch_backdrop(name):
    menu = mk("looks_backdrops", fld={"BACKDROP": [name, None]}, shadow=True)
    return mk("looks_switchbackdropto", inp={"BACKDROP": MENU(menu)})


def create_clone():
    menu = mk("control_create_clone_of_menu",
              fld={"CLONE_OPTION": ["_myself_", None]}, shadow=True)
    return mk("control_create_clone_of", inp={"CLONE_OPTION": MENU(menu)})


def delete_clone():
    return mk("control_delete_this_clone")


def broadcast_wait(name):
    return mk("event_broadcastandwait",
              inp={"BROADCAST_INPUT": [1, [11, name, BC[name]]]})


def broadcast(name):
    return mk("event_broadcast",
              inp={"BROADCAST_INPUT": [1, [11, name, BC[name]]]})


def when_flag(x=40, y=40):
    return mk("event_whenflagclicked", top=True, x=x, y=y)


def when_bc(name, x=40, y=40):
    return mk("event_whenbroadcastreceived",
              fld={"BROADCAST_OPTION": [name, BC[name]]}, top=True, x=x, y=y)


def when_clone(x=40, y=40):
    return mk("control_start_as_clone", top=True, x=x, y=y)


def slot_x(idx_block):
    """x = -210 + (индекс - 1) * 30"""
    return RN(add_(n(SLOT_X0), RN(mul_(RN(sub_(RN(idx_block), n(1))), n(SLOT_STEP)))))


# ===========================================================================
#  SVG-РЕСУРСЫ
# ===========================================================================

# Scratch рисует SVG средствами браузера, поэтому у шрифта нужен запасной вариант
FONT = "Verdana, &apos;DejaVu Sans&apos;, Geneva, sans-serif"


def with_font(svg):
    return svg.replace('font-family="Verdana"', 'font-family="%s"' % FONT)


def backdrop_svg(finale=False):
    rows = []
    # три дорожки-жёлоба под плитки
    for cy in (122, 194, 262):
        rows.append(
            '<rect x="14" y="%d" width="452" height="36" rx="18" '
            'fill="#ffffff" fill-opacity="0.05" stroke="#7fa6d8" '
            'stroke-opacity="0.18" stroke-width="1"/>' % (cy - 18)
        )
    # деления слотов
    ticks = []
    for k in range(MAX_SLOTS):
        cx = 30 + k * SLOT_STEP
        for cy in (122, 194, 262):
            ticks.append(
                '<rect x="%d" y="%d" width="26" height="26" rx="8" '
                'fill="#ffffff" fill-opacity="0.04"/>' % (cx - 13, cy - 13)
            )

    finale_layer = ""
    if finale:
        confetti = []
        palette = ["#4fd1c5", "#f6ad55", "#b794f4", "#f687b3", "#68d391", "#63b3ed"]
        spots = [(60, 60), (110, 40), (170, 70), (240, 38), (300, 66), (360, 44),
                 (410, 72), (80, 96), (200, 100), (330, 98), (440, 104), (24, 130),
                 (462, 140), (46, 210), (446, 206), (150, 122), (270, 130)]
        for idx, (cx, cy) in enumerate(spots):
            col = palette[idx % len(palette)]
            if idx % 3 == 0:
                confetti.append(
                    '<circle cx="%d" cy="%d" r="5" fill="%s" fill-opacity="0.85"/>'
                    % (cx, cy, col))
            elif idx % 3 == 1:
                confetti.append(
                    '<rect x="%d" y="%d" width="9" height="9" rx="2" fill="%s" '
                    'fill-opacity="0.8" transform="rotate(25 %d %d)"/>'
                    % (cx, cy, col, cx + 4, cy + 4))
            else:
                confetti.append(
                    '<rect x="%d" y="%d" width="4" height="12" rx="2" fill="%s" '
                    'fill-opacity="0.8" transform="rotate(-20 %d %d)"/>'
                    % (cx, cy, col, cx + 2, cy + 6))
        finale_layer = (
            '<rect x="96" y="146" width="288" height="64" rx="18" fill="#10233f" '
            'fill-opacity="0.93" stroke="#63e6c8" stroke-opacity="0.6" stroke-width="2"/>'
            '<text x="240" y="178" text-anchor="middle" font-family="Verdana" '
            'font-size="26" font-weight="bold" fill="#8ff3dc">ГОТОВО!</text>'
            '<text x="240" y="198" text-anchor="middle" font-family="Verdana" '
            'font-size="11" fill="#bcd6f2">один цикл — один отсортированный массив</text>'
            + "".join(confetti)
        )

    return with_font(
        '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="480" '
        'height="360" viewBox="0 0 480 360">'
        '<defs>'
        '<linearGradient id="sky" gradientUnits="userSpaceOnUse" '
        'x1="0" y1="0" x2="480" y2="360">'
        '<stop offset="0" stop-color="#16294a"/>'
        '<stop offset="0.55" stop-color="#101d36"/>'
        '<stop offset="1" stop-color="#0a1222"/>'
        '</linearGradient>'
        '<linearGradient id="hdr" gradientUnits="userSpaceOnUse" '
        'x1="0" y1="0" x2="480" y2="0">'
        '<stop offset="0" stop-color="#4fd1c5" stop-opacity="0.55"/>'
        '<stop offset="0.5" stop-color="#f6ad55" stop-opacity="0.45"/>'
        '<stop offset="1" stop-color="#b794f4" stop-opacity="0.55"/>'
        '</linearGradient>'
        '<radialGradient id="halo" gradientUnits="userSpaceOnUse" '
        'cx="110" cy="40" r="240">'
        '<stop offset="0" stop-color="#4fd1c5" stop-opacity="0.20"/>'
        '<stop offset="1" stop-color="#4fd1c5" stop-opacity="0"/>'
        '</radialGradient>'
        '</defs>'
        '<rect x="0" y="0" width="480" height="360" fill="url(#sky)"/>'
        '<rect x="0" y="0" width="480" height="360" fill="url(#halo)"/>'
        '<rect x="0" y="0" width="480" height="3" fill="url(#hdr)"/>'
        '<text x="22" y="34" font-family="Verdana" font-size="16" '
        'font-weight="bold" fill="#e8f1ff">Слияние двух отсортированных '
        'массивов</text>'
        '<text x="22" y="54" font-family="Verdana" font-size="11" '
        'fill="#89a7cd">Для Сч = 1 По a + b Цикл — один проход, без '
        'сортировки</text>'
        '<rect x="368" y="2" width="108" height="92" rx="12" fill="#ffffff" '
        'fill-opacity="0.06" stroke="#7fa6d8" stroke-opacity="0.2" '
        'stroke-width="1"/>'
        + "".join(rows) + "".join(ticks) +
        '<text x="22" y="82" font-family="Verdana" font-size="12" '
        'font-weight="bold" fill="#5fe3d0">Массив A</text>'
        '<text x="22" y="154" font-family="Verdana" font-size="12" '
        'font-weight="bold" fill="#ffb066">Массив B</text>'
        '<text x="22" y="232" font-family="Verdana" font-size="12" '
        'font-weight="bold" fill="#c9aeff">Результат — по возрастанию</text>'
        '<rect x="22" y="300" width="250" height="26" rx="13" fill="#ffffff" '
        'fill-opacity="0.05"/>'
        '<circle cx="38" cy="313" r="6" fill="#3fd6c0"/>'
        '<text x="50" y="317" font-family="Verdana" font-size="10" '
        'fill="#bcd6f2">пришло из A</text>'
        '<circle cx="148" cy="313" r="6" fill="#ffb15c"/>'
        '<text x="160" y="317" font-family="Verdana" font-size="10" '
        'fill="#bcd6f2">пришло из B</text>'
        '<text x="22" y="344" font-family="Verdana" font-size="10" '
        'fill="#6f8bb0">i — указатель в A, j — указатель в B, Сч — номер шага'
        '</text>'
        + finale_layer +
        '</svg>'
    )


def token_svg(kind, value):
    if kind == "A":
        c1, c2, edge = "#5ae6cf", "#17907f", "#0d5f54"
    else:
        c1, c2, edge = "#ffc178", "#dd7a16", "#96530a"
    text = str(value)
    size = 16 if len(text) == 1 else 13
    return with_font(
        '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="36" '
        'height="36" viewBox="0 0 36 36">'
        '<defs><linearGradient id="g%s%s" gradientUnits="userSpaceOnUse" '
        'x1="4" y1="4" x2="32" y2="32">'
        '<stop offset="0" stop-color="%s"/>'
        '<stop offset="1" stop-color="%s"/>'
        '</linearGradient></defs>'
        '<rect x="4" y="5" width="28" height="28" rx="9" fill="#000000" '
        'fill-opacity="0.35"/>'
        '<rect x="4" y="4" width="28" height="28" rx="9" fill="url(#g%s%s)" '
        'stroke="%s" stroke-width="1.5"/>'
        '<rect x="7" y="7" width="22" height="9" rx="4.5" fill="#ffffff" '
        'fill-opacity="0.22"/>'
        '<text x="18" y="%s" text-anchor="middle" font-family="Verdana" '
        'font-size="%d" font-weight="bold" fill="#ffffff">%s</text>'
        '</svg>'
        % (kind, text, c1, c2, kind, text, edge,
           "24" if len(text) == 1 else "23.5", size, text)
    )


def pointer_svg(kind):
    if kind == "A":
        c1, c2, edge = "#7ff0dd", "#1fa892", "#0d5f54"
    else:
        c1, c2, edge = "#ffd09a", "#e8871f", "#96530a"
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="28" '
        'height="26" viewBox="0 0 28 26">'
        '<defs><linearGradient id="p%s" gradientUnits="userSpaceOnUse" '
        'x1="14" y1="2" x2="14" y2="24">'
        '<stop offset="0" stop-color="%s"/>'
        '<stop offset="1" stop-color="%s"/>'
        '</linearGradient></defs>'
        '<rect x="10" y="2" width="8" height="8" rx="4" fill="url(#p%s)" '
        'stroke="%s" stroke-width="1"/>'
        '<path d="M5 10 L23 10 L14 24 Z" fill="url(#p%s)" stroke="%s" '
        'stroke-width="1.5" stroke-linejoin="round"/>'
        '</svg>' % (kind, c1, c2, kind, edge, kind, edge)
    )


SPARK_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="28" '
    'height="28" viewBox="0 0 28 28">'
    '<defs><radialGradient id="sp" gradientUnits="userSpaceOnUse" cx="14" '
    'cy="14" r="13">'
    '<stop offset="0" stop-color="#ffffff"/>'
    '<stop offset="0.45" stop-color="#ffe08a"/>'
    '<stop offset="1" stop-color="#ff9f43"/>'
    '</radialGradient></defs>'
    '<path d="M14 0 L17 11 L28 14 L17 17 L14 28 L11 17 L0 14 L11 11 Z" '
    'fill="url(#sp)"/>'
    '<circle cx="14" cy="14" r="3.5" fill="#ffffff"/>'
    '</svg>'
)

MASCOT_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="80" '
    'height="80" viewBox="0 0 80 80">'
    '<defs>'
    '<linearGradient id="mb" gradientUnits="userSpaceOnUse" x1="14" y1="18" '
    'x2="66" y2="70">'
    '<stop offset="0" stop-color="#9fd4ff"/>'
    '<stop offset="1" stop-color="#2f6bb0"/>'
    '</linearGradient>'
    '<linearGradient id="ms" gradientUnits="userSpaceOnUse" x1="22" y1="30" '
    'x2="58" y2="56">'
    '<stop offset="0" stop-color="#0e2743"/>'
    '<stop offset="1" stop-color="#17395f"/>'
    '</linearGradient>'
    '</defs>'
    '<rect x="37" y="6" width="6" height="14" rx="3" fill="#7fb6e8"/>'
    '<circle cx="40" cy="7" r="6" fill="#ffd166"/>'
    '<rect x="12" y="18" width="56" height="48" rx="16" fill="url(#mb)" '
    'stroke="#12395f" stroke-width="2.5"/>'
    '<rect x="20" y="28" width="40" height="26" rx="11" fill="url(#ms)"/>'
    '<circle cx="31" cy="39" r="5" fill="#6ef0d4"/>'
    '<circle cx="49" cy="39" r="5" fill="#6ef0d4"/>'
    '<path d="M30 47 Q40 54 50 47" stroke="#6ef0d4" stroke-width="2.5" '
    'fill="none" stroke-linecap="round"/>'
    '<rect x="26" y="60" width="28" height="5" rx="2.5" fill="#ffffff" '
    'fill-opacity="0.3"/>'
    '<rect x="4" y="34" width="8" height="16" rx="4" fill="#4d8ac4"/>'
    '<rect x="68" y="34" width="8" height="16" rx="4" fill="#4d8ac4"/>'
    '</svg>'
)

# ---------------------------------------------------------------------------
#  Регистрация ресурсов
# ---------------------------------------------------------------------------

ASSETS = {}


def register(svg):
    aid = hashlib.md5(svg.encode("utf-8")).hexdigest()
    ASSETS[aid] = svg
    return aid


def costume(name, svg, cx, cy, for_stage=False):
    aid = register(svg)
    c = {
        "name": name,
        "assetId": aid,
        "md5ext": "%s.svg" % aid,
        "dataFormat": "svg",
        "rotationCenterX": cx,
        "rotationCenterY": cy,
    }
    if not for_stage:
        c["bitmapResolution"] = 1
    return c


BACKDROP_MAIN = costume("Сцена", backdrop_svg(False), 240, 180, for_stage=True)
BACKDROP_FIN = costume("Финиш", backdrop_svg(True), 240, 180, for_stage=True)

TOKEN_COSTUMES = []
for kind in ("A", "B"):
    for value in range(1, 26):
        TOKEN_COSTUMES.append(
            costume("%s%d" % (kind, value), token_svg(kind, value), 18, 18))

POINTER_A_COSTUME = costume("стрелка A", pointer_svg("A"), 14, 13)
POINTER_B_COSTUME = costume("стрелка B", pointer_svg("B"), 14, 13)
SPARK_COSTUME = costume("искра", SPARK_SVG, 14, 14)
MASCOT_COSTUME = costume("робот", MASCOT_SVG, 40, 40)

# ===========================================================================
#  СПРАЙТ «Плитка» — элементы массивов
# ===========================================================================

use_target("Плитка")

# --- при старте: прячем оригинал ---
t_flag = when_flag(40, 40)
chain(t_flag, hide(), set_size(100), clear_effects())

# --- сброс: клоны исчезают ---
t_reset = when_bc("сброс", 40, 220)
chain(t_reset, delete_clone())

# --- создание клонов по спискам A и B ---
mk_a_body = chain(
    setv("мой массив", TV_ARR, s("A")),
    setv("мой индекс", TV_IDX, R(v_k())),
    setv("моё значение", TV_VAL, R(item_of("A", LIST_A, v_k()))),
    setv("мой слот", TV_SLOT, n(0)),
    create_clone(),
    changev("к", TV_K, n(1)),
    wait(0.07),
)
mk_b_body = chain(
    setv("мой массив", TV_ARR, s("B")),
    setv("мой индекс", TV_IDX, R(v_k())),
    setv("моё значение", TV_VAL, R(item_of("B", LIST_B, v_k()))),
    setv("мой слот", TV_SLOT, n(0)),
    create_clone(),
    changev("к", TV_K, n(1)),
    wait(0.07),
)
t_build = when_bc("создать", 40, 360)
chain(
    t_build,
    hide(),
    setv("к", TV_K, n(1)),
    repeat(R(len_of("A", LIST_A)), mk_a_body),
    setv("к", TV_K, n(1)),
    repeat(R(len_of("B", LIST_B)), mk_b_body),
)

# --- клон появляется на своей полке ---
place_a = goto(slot_x(v_my_idx()), n(ROW_A_Y))
place_b = goto(slot_x(v_my_idx()), n(ROW_B_Y))
pop_body = change_size(10)
t_clone = when_clone(40, 640)
chain(
    t_clone,
    switch_costume(join_(R(v_my_arr()), R(v_my_val())), "A1"),
    if_else(eq_(R(v_my_arr()), s("A")), place_a, place_b),
    clear_effects(),
    set_size(0),
    show(),
    repeat(n(12), pop_body),
    set_size(100),
)

# --- подсветка сравниваемой пары ---
cmp_cond = or_(
    and_(eq_(R(v_my_arr()), s("A")), eq_(R(v_my_idx()), R(v_i()))),
    and_(eq_(R(v_my_arr()), s("B")), eq_(R(v_my_idx()), R(v_j()))),
)
cmp_body = chain(set_size(122), change_effect("BRIGHTNESS", 25), wait(0.16),
                 set_size(100), change_effect("BRIGHTNESS", -25))
t_cmp = when_bc("сравнить", 40, 900)
chain(t_cmp, if_(cmp_cond, cmp_body))

# --- перенос выбранной плитки в результат ---
move_cond = and_(eq_(R(v_my_arr()), R(v_sel_arr())),
                 eq_(R(v_my_idx()), R(v_sel_idx())))
move_body = chain(
    setv("мой слот", TV_SLOT, R(v_slot())),
    mk("looks_gotofrontback", fld={"FRONT_BACK": ["front", None]}),
    set_size(128),
    glide(0.45, slot_x(v_slot()), n(ROW_R_Y)),
    set_size(112),
    wait(0.08),
    set_size(100),
)
t_move = when_bc("перенести", 40, 1160)
chain(t_move, if_(move_cond, move_body))

# --- финальная волна по результату ---
wave_up = chain(change_effect("COLOR", 28), change_size(6), wait(0.03))
wave_dn = chain(change_effect("COLOR", 28), change_size(-6), wait(0.03))
t_wave = when_bc("волна", 40, 1420)
chain(
    t_wave,
    mk("control_wait", inp={"DURATION": RN(mul_(R(v_my_slot()), n(0.05)))}),
    repeat(n(4), wave_up),
    repeat(n(4), wave_dn),
    clear_effects(),
    set_size(100),
)

TOKEN_BLOCKS = blocks_by_target["Плитка"]

# ===========================================================================
#  СПРАЙТ «Указатель i»
# ===========================================================================

use_target("Указатель i")

pa_flag = when_flag(40, 40)
chain(pa_flag, set_size(100), clear_effects(), show(),
      goto(n(SLOT_X0), n(PTR_A_Y)))

pa_reset = when_bc("сброс", 40, 220)
chain(pa_reset, show(), goto(n(SLOT_X0), n(PTR_A_Y)))

pa_hide = hide()
pa_move = chain(show(), glide(0.22, slot_x(v_i()), n(PTR_A_Y)))
pa_point = when_bc("указатели", 40, 380)
chain(pa_point, if_else(gt_(R(v_i()), R(v_a())), pa_hide, pa_move))

POINTER_A_BLOCKS = blocks_by_target["Указатель i"]

# ===========================================================================
#  СПРАЙТ «Указатель j»
# ===========================================================================

use_target("Указатель j")

pb_flag = when_flag(40, 40)
chain(pb_flag, set_size(100), clear_effects(), show(),
      goto(n(SLOT_X0), n(PTR_B_Y)))

pb_reset = when_bc("сброс", 40, 220)
chain(pb_reset, show(), goto(n(SLOT_X0), n(PTR_B_Y)))

pb_hide = hide()
pb_move = chain(show(), glide(0.22, slot_x(v_j()), n(PTR_B_Y)))
pb_point = when_bc("указатели", 40, 380)
chain(pb_point, if_else(gt_(R(v_j()), R(v_b())), pb_hide, pb_move))

POINTER_B_BLOCKS = blocks_by_target["Указатель j"]

# ===========================================================================
#  СПРАЙТ «Искра» — финальный салют
# ===========================================================================

use_target("Искра")

sp_flag = when_flag(40, 40)
chain(sp_flag, hide())

sp_reset = when_bc("сброс", 40, 180)
chain(sp_reset, delete_clone())

sp_spawn_body = chain(create_clone(), wait(0.04))
sp_fire = when_bc("салют", 40, 320)
chain(sp_fire, hide(), repeat(n(28), sp_spawn_body))

sp_fade_body = chain(change_size(6), change_effect("GHOST", 8),
                     change_effect("COLOR", 12), wait(0.03))
sp_clone = when_clone(40, 520)
chain(
    sp_clone,
    goto(RN(random_(-215, 215)), RN(random_(-150, 155))),
    mk("looks_seteffectto", inp={"VALUE": RN(random_(0, 200))},
       fld={"EFFECT": ["COLOR", None]}),
    set_effect("GHOST", n(0)),
    mk("looks_setsizeto", inp={"SIZE": RN(random_(35, 90))}),
    show(),
    repeat(n(12), sp_fade_body),
    delete_clone(),
)

SPARK_BLOCKS = blocks_by_target["Искра"]

# ===========================================================================
#  СПРАЙТ «Алгоритм» — управляющий скрипт (сам алгоритм слияния)
# ===========================================================================

use_target("Алгоритм")

# условие: i <= a И (j > b ИЛИ A[i] <= B[j])
c_i_le_a = not_(gt_(R(v_i()), R(v_a())))
c_j_gt_b = gt_(R(v_j()), R(v_b()))
c_ai_le_bj = not_(gt_(R(item_of("A", LIST_A, v_i())),
                      R(item_of("B", LIST_B, v_j()))))
main_cond = and_(c_i_le_a, or_(c_j_gt_b, c_ai_le_bj))

take_a = chain(
    setv("выбран массив", VAR_SEL_ARR, s("A")),
    setv("выбран индекс", VAR_SEL_IDX, R(v_i())),
    add_to("Result", LIST_R, R(item_of("A", LIST_A, v_i()))),
    changev("i", VAR_I, n(1)),
)
take_b = chain(
    setv("выбран массив", VAR_SEL_ARR, s("B")),
    setv("выбран индекс", VAR_SEL_IDX, R(v_j())),
    add_to("Result", LIST_R, R(item_of("B", LIST_B, v_j()))),
    changev("j", VAR_J, n(1)),
)

loop_body = chain(
    broadcast_wait("сравнить"),
    if_else(main_cond, take_a, take_b),
    setv("слот", VAR_SLOT, R(v_cnt())),
    broadcast_wait("перенести"),
    broadcast_wait("указатели"),
    changev("Сч", VAR_CNT, n(1)),
    wait(0.12),
)

alg_flag = when_flag(40, 40)
chain(
    alg_flag,
    switch_backdrop("Сцена"),
    broadcast_wait("сброс"),
    del_all("Result", LIST_R),
    setv("a", VAR_A, R(len_of("A", LIST_A))),
    setv("b", VAR_B, R(len_of("B", LIST_B))),
    setv("i", VAR_I, n(1)),
    setv("j", VAR_J, n(1)),
    setv("Сч", VAR_CNT, n(1)),
    setv("выбран массив", VAR_SEL_ARR, s("")),
    setv("выбран индекс", VAR_SEL_IDX, n(0)),
    setv("слот", VAR_SLOT, n(0)),
    clear_effects(),
    set_size(70),
    show(),
    goto(n(190), n(-138)),
    say_for("Оба массива уже отсортированы — сливаем их за один проход!", 2.2),
    broadcast_wait("создать"),
    broadcast_wait("указатели"),
    wait(0.4),
    repeat(RN(add_(R(v_a()), R(v_b()))), loop_body),
    say_for("Все a + b шагов сделаны!", 1.2),
    switch_backdrop("Финиш"),
    broadcast("салют"),
    broadcast_wait("волна"),
    say_for("Готово: массивы объединены и отсортированы по возрастанию.", 3),
)

ALG_BLOCKS = blocks_by_target["Алгоритм"]

# ===========================================================================
#  ПРОВЕРКА СТРУКТУРЫ
# ===========================================================================

GLOBAL_VARS = {
    VAR_A: ["a", 0],
    VAR_B: ["b", 0],
    VAR_I: ["i", 1],
    VAR_J: ["j", 1],
    VAR_CNT: ["Сч", 1],
    VAR_SEL_ARR: ["выбран массив", ""],
    VAR_SEL_IDX: ["выбран индекс", 0],
    VAR_SLOT: ["слот", 0],
}
GLOBAL_LISTS = {
    LIST_A: ["A", INITIAL_A],
    LIST_B: ["B", INITIAL_B],
    LIST_R: ["Result", []],
}
TOKEN_VARS = {
    TV_ARR: ["мой массив", ""],
    TV_IDX: ["мой индекс", 0],
    TV_VAL: ["моё значение", 0],
    TV_SLOT: ["мой слот", 0],
    TV_K: ["к", 1],
}

HAT_OPCODES = {"event_whenflagclicked", "event_whenbroadcastreceived",
               "control_start_as_clone"}

# все опкоды, которые проект имеет право использовать
KNOWN_OPCODES = {
    "event_whenflagclicked", "event_whenbroadcastreceived", "event_broadcast",
    "event_broadcastandwait",
    "control_start_as_clone", "control_create_clone_of",
    "control_create_clone_of_menu", "control_delete_this_clone",
    "control_wait", "control_repeat", "control_if", "control_if_else",
    "motion_gotoxy", "motion_glidesecstoxy",
    "looks_show", "looks_hide", "looks_setsizeto", "looks_changesizeby",
    "looks_changeeffectby", "looks_seteffectto", "looks_cleargraphiceffects",
    "looks_sayforsecs", "looks_switchcostumeto", "looks_costume",
    "looks_switchbackdropto", "looks_backdrops", "looks_gotofrontback",
    "data_variable", "data_setvariableto", "data_changevariableby",
    "data_itemoflist", "data_lengthoflist", "data_addtolist",
    "data_deletealloflist",
    "operator_add", "operator_subtract", "operator_multiply", "operator_gt",
    "operator_equals", "operator_and", "operator_or", "operator_not",
    "operator_join", "operator_random",
}


def validate(target_name, blocks, local_vars, costume_names):
    known_vars = dict(GLOBAL_VARS)
    known_vars.update(local_vars)
    for bid, blk in blocks.items():
        assert blk["opcode"] in KNOWN_OPCODES, \
            "%s/%s: неизвестный opcode %s" % (target_name, bid, blk["opcode"])
        if blk["opcode"] in HAT_OPCODES:
            assert blk["topLevel"], "%s/%s: hat без topLevel" % (target_name, bid)
            assert blk["parent"] is None, "%s/%s: у hat есть parent" % (target_name, bid)
        else:
            assert not blk["topLevel"], "%s/%s: не-hat помечен topLevel" % (target_name, bid)
        for key, val in blk["inputs"].items():
            if val[0] in (2, 3):
                ref = val[1]
                assert isinstance(ref, str), \
                    "%s/%s: input %s без id блока" % (target_name, bid, key)
                assert ref in blocks, \
                    "%s/%s: input %s ссылается на отсутствующий %s" % (target_name, bid, key, ref)
                assert blocks[ref]["parent"] == bid, \
                    "%s/%s: у блока %s неверный parent" % (target_name, bid, ref)
                if val[0] == 3 and isinstance(val[2], str):
                    assert val[2] in blocks, \
                        "%s/%s: shadow-меню %s отсутствует" % (target_name, bid, val[2])
            if val[0] == 1 and isinstance(val[1], str):
                assert val[1] in blocks, \
                    "%s/%s: shadow %s отсутствует" % (target_name, bid, val[1])
        if blk["opcode"] in ("control_if", "control_if_else"):
            assert "CONDITION" in blk["inputs"] and "SUBSTACK" in blk["inputs"], \
                "%s/%s: у if нет CONDITION/SUBSTACK" % (target_name, bid)
        if blk["opcode"] == "control_if_else":
            assert "SUBSTACK2" in blk["inputs"], "%s/%s: у if-else нет SUBSTACK2" % (target_name, bid)
        if blk["opcode"] == "control_repeat":
            assert "TIMES" in blk["inputs"] and "SUBSTACK" in blk["inputs"], \
                "%s/%s: у repeat нет TIMES/SUBSTACK" % (target_name, bid)
        if "VARIABLE" in blk["fields"]:
            name, vid = blk["fields"]["VARIABLE"]
            assert vid in known_vars and known_vars[vid][0] == name, \
                "%s/%s: неизвестная переменная %s/%s" % (target_name, bid, name, vid)
        if "LIST" in blk["fields"]:
            name, lid = blk["fields"]["LIST"]
            assert lid in GLOBAL_LISTS and GLOBAL_LISTS[lid][0] == name, \
                "%s/%s: неизвестный список %s/%s" % (target_name, bid, name, lid)
        if "BROADCAST_OPTION" in blk["fields"]:
            name, cid = blk["fields"]["BROADCAST_OPTION"]
            assert BC.get(name) == cid, "%s/%s: неизвестное сообщение %s" % (target_name, bid, name)
        if blk["opcode"] == "looks_costume":
            assert blk["fields"]["COSTUME"][0] in costume_names, \
                "%s/%s: нет костюма %s" % (target_name, bid, blk["fields"]["COSTUME"][0])
        if blk["opcode"] == "looks_backdrops":
            assert blk["fields"]["BACKDROP"][0] in ("Сцена", "Финиш"), \
                "%s/%s: нет фона %s" % (target_name, bid, blk["fields"]["BACKDROP"][0])
        for val in blk["inputs"].values():
            if val[0] == 1 and isinstance(val[1], list) and val[1][0] == 11:
                assert BC.get(val[1][1]) == val[1][2], \
                    "%s/%s: сообщение %s не объявлено" % (target_name, bid, val[1][1])
        # запрещённые формы подстановки переменных/списков напрямую
        for val in blk["inputs"].values():
            if isinstance(val[1], list):
                assert val[1][0] not in (12, 13), \
                    "%s/%s: запрещённая подстановка %s" % (target_name, bid, val[1][0])


validate("Плитка", TOKEN_BLOCKS, TOKEN_VARS, {c["name"] for c in TOKEN_COSTUMES})
validate("Указатель i", POINTER_A_BLOCKS, {}, {POINTER_A_COSTUME["name"]})
validate("Указатель j", POINTER_B_BLOCKS, {}, {POINTER_B_COSTUME["name"]})
validate("Искра", SPARK_BLOCKS, {}, {SPARK_COSTUME["name"]})
validate("Алгоритм", ALG_BLOCKS, {}, {MASCOT_COSTUME["name"]})

# ===========================================================================
#  СБОРКА project.json
# ===========================================================================

def sprite(name, blocks, costumes, x, y, layer, visible=True, size=100,
           local_vars=None):
    return {
        "isStage": False,
        "name": name,
        "variables": local_vars or {},
        "lists": {},
        "broadcasts": {},
        "blocks": blocks,
        "comments": {},
        "currentCostume": 0,
        "costumes": costumes,
        "sounds": [],
        "volume": 100,
        "layerOrder": layer,
        "visible": visible,
        "x": x,
        "y": y,
        "size": size,
        "direction": 90,
        "draggable": False,
        "rotationStyle": "don't rotate",
    }


stage = {
    "isStage": True,
    "name": "Stage",
    "variables": GLOBAL_VARS,
    "lists": GLOBAL_LISTS,
    "broadcasts": {bid: name for name, bid in BC.items()},
    "blocks": {},
    "comments": {},
    "currentCostume": 0,
    "costumes": [BACKDROP_MAIN, BACKDROP_FIN],
    "sounds": [],
    "volume": 100,
    "layerOrder": 0,
    "tempo": 60,
    "videoTransparency": 50,
    "videoState": "off",
    "textToSpeechLanguage": None,
}

targets = [
    stage,
    sprite("Плитка", TOKEN_BLOCKS, TOKEN_COSTUMES, 0, 0, 1, visible=False,
           local_vars=TOKEN_VARS),
    sprite("Указатель i", POINTER_A_BLOCKS, [POINTER_A_COSTUME],
           SLOT_X0, PTR_A_Y, 2),
    sprite("Указатель j", POINTER_B_BLOCKS, [POINTER_B_COSTUME],
           SLOT_X0, PTR_B_Y, 3),
    sprite("Искра", SPARK_BLOCKS, [SPARK_COSTUME], 0, 0, 4, visible=False),
    sprite("Алгоритм", ALG_BLOCKS, [MASCOT_COSTUME], 190, -138, 5, size=70),
]


def var_monitor(vid, name, value, mx, my, visible=True):
    return {
        "id": vid,
        "mode": "default",
        "opcode": "data_variable",
        "params": {"VARIABLE": name},
        "spriteName": None,
        "value": value,
        "width": 0,
        "height": 0,
        "x": mx,
        "y": my,
        "visible": visible,
        "sliderMin": 0,
        "sliderMax": 100,
        "isDiscrete": True,
    }


def list_monitor(lid, name, mx, my, w, h, visible=False):
    return {
        "id": lid,
        "mode": "list",
        "opcode": "data_listcontents",
        "params": {"LIST": name},
        "spriteName": None,
        "value": [],
        "width": w,
        "height": h,
        "x": mx,
        "y": my,
        "visible": visible,
    }


monitors = [
    var_monitor(VAR_I, "i", 1, 376, 8),
    var_monitor(VAR_J, "j", 1, 376, 34),
    var_monitor(VAR_CNT, "Сч", 1, 376, 60),
    var_monitor(VAR_A, "a", 0, 376, 120, visible=False),
    var_monitor(VAR_B, "b", 0, 376, 146, visible=False),
    var_monitor(VAR_SEL_ARR, "выбран массив", "", 240, 120, visible=False),
    var_monitor(VAR_SEL_IDX, "выбран индекс", 0, 240, 146, visible=False),
    var_monitor(VAR_SLOT, "слот", 0, 240, 172, visible=False),
    list_monitor(LIST_A, "A", 10, 10, 120, 140),
    list_monitor(LIST_B, "B", 140, 10, 120, 140),
    list_monitor(LIST_R, "Result", 270, 10, 130, 160),
]

project = {
    "targets": targets,
    "monitors": monitors,
    "extensions": [],
    "meta": {"semver": "3.0.0", "vm": "0.2.0", "agent": "generator"},
}

# ===========================================================================
#  УПАКОВКА
# ===========================================================================

BUILD = "_build"
OUTPUT_NAME = "merge_sorted_arrays.sb3"

if os.path.isdir(BUILD):
    shutil.rmtree(BUILD)
os.makedirs(BUILD)

with open(os.path.join(BUILD, "project.json"), "w", encoding="utf-8") as f:
    json.dump(project, f, ensure_ascii=False, indent=2)

for asset_id, svg in ASSETS.items():
    with open(os.path.join(BUILD, "%s.svg" % asset_id), "w", encoding="utf-8") as f:
        f.write(svg)

with zipfile.ZipFile(OUTPUT_NAME, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(BUILD, "project.json"), "project.json")
    for asset_id in ASSETS:
        z.write(os.path.join(BUILD, "%s.svg" % asset_id), "%s.svg" % asset_id)

shutil.rmtree(BUILD)
print("OK: %s" % OUTPUT_NAME)
