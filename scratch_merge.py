import json
import zipfile
import os
import shutil
import hashlib

# ---------------------------------------------------------------------------
# Низкоуровневые хелперы для сборки блоков Scratch 3
# ---------------------------------------------------------------------------

blocks_by_target = {}
_id_counter = [0]


def new_id():
    _id_counter[0] += 1
    return f"b{_id_counter[0]}"


current_target = [None]


def use_target(name):
    current_target[0] = name
    blocks_by_target.setdefault(name, {})


def mk(opcode, nxt=None, par=None, inp=None, fld=None, top=False, x=0, y=0, shadow=False):
    bid = new_id()
    blocks_by_target[current_target[0]][bid] = {
        "opcode": opcode,
        "next": nxt,
        "parent": par,
        "inputs": inp or {},
        "fields": fld or {},
        "shadow": shadow,
        "topLevel": top,
        "x": x,
        "y": y,
    }
    return bid


def hook(child_id, parent_id):
    """Проставляет parent у уже созданного блока-репортёра."""
    blocks_by_target[current_target[0]][child_id]["parent"] = parent_id
    return child_id


def chain(first, *rest):
    prev = first
    for b in rest:
        blocks_by_target[current_target[0]][prev]["next"] = b
        blocks_by_target[current_target[0]][b]["parent"] = prev
        prev = b
    return first


def var(name, var_id):
    return mk("data_variable", fld={"VARIABLE": [name, var_id]})


def item(list_name, list_id, idx_block_id):
    return mk(
        "data_itemoflist",
        inp={"INDEX": [3, idx_block_id, [7, "1"]]},
        fld={"LIST": [list_name, list_id]},
    )


def length(list_name, list_id):
    return mk("data_lengthoflist", fld={"LIST": [list_name, list_id]})


def n(v):
    return [1, [4, str(v)]]


def s(v):
    return [1, [10, str(v)]]


def lvl(block_id):
    return [3, block_id, [10, ""]]


def cond(block_id):
    return [2, block_id]


# ---------------------------------------------------------------------------
# SVG-ресурсы
# ---------------------------------------------------------------------------

BACKDROP_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1b2a4a"/>
      <stop offset="100%" stop-color="#0d1420"/>
    </linearGradient>
    <linearGradient id="barA" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#4fd1c5"/>
      <stop offset="100%" stop-color="#2b9d94"/>
    </linearGradient>
    <linearGradient id="barB" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#f6ad55"/>
      <stop offset="100%" stop-color="#dd6b20"/>
    </linearGradient>
    <linearGradient id="barR" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#b794f4"/>
      <stop offset="100%" stop-color="#805ad5"/>
    </linearGradient>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="4" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <rect x="0" y="0" width="480" height="360" fill="url(#bg)"/>
  <text x="240" y="40" text-anchor="middle" font-family="Verdana" font-size="18" fill="#e2e8f0" filter="url(#glow)">
    Слияние двух отсортированных массивов
  </text>
  <text x="20" y="100" font-family="Verdana" font-size="14" fill="#4fd1c5">Массив A</text>
  <rect x="20" y="110" width="200" height="18" rx="6" fill="url(#barA)"/>
  <text x="260" y="100" font-family="Verdana" font-size="14" fill="#f6ad55">Массив B</text>
  <rect x="260" y="110" width="200" height="18" rx="6" fill="url(#barB)"/>
  <text x="20" y="190" font-family="Verdana" font-size="14" fill="#b794f4">Результат (Result)</text>
  <rect x="20" y="200" width="440" height="18" rx="6" fill="url(#barR)"/>
  <text x="240" y="300" text-anchor="middle" font-family="Verdana" font-size="13" fill="#a0aec0">
    Для Сч = 1 По a + b Цикл ...
  </text>
</svg>
"""

SPRITE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
  <defs>
    <radialGradient id="body" cx="40%" cy="35%" r="70%">
      <stop offset="0%" stop-color="#9be7ff"/>
      <stop offset="60%" stop-color="#4fa8e0"/>
      <stop offset="100%" stop-color="#1c5d99"/>
    </radialGradient>
    <filter id="spriteGlow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  <circle cx="50" cy="50" r="38" fill="url(#body)" filter="url(#spriteGlow)" stroke="#0d3a63" stroke-width="3"/>
  <path d="M35 45 L50 30 L65 45" stroke="#ffffff" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M35 60 L50 75 L65 60" stroke="#ffffff" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="50" cy="50" r="6" fill="#ffe066"/>
</svg>
"""

BACKDROP_ID = hashlib.md5(BACKDROP_SVG.encode("utf-8")).hexdigest()
SPRITE_ID = hashlib.md5(SPRITE_SVG.encode("utf-8")).hexdigest()

# ---------------------------------------------------------------------------
# Переменные и списки (общие, лежат на Stage)
# ---------------------------------------------------------------------------

var_a = "var_a"
var_b = "var_b"
var_i = "var_i"
var_j = "var_j"
var_cnt = "var_cnt"

list_A = "list_A"
list_B = "list_B"
list_R = "list_R"

INITIAL_A = [2, 4, 6, 8, 10, 12]
INITIAL_B = [1, 3, 5, 7, 9, 11, 13, 15]

# ---------------------------------------------------------------------------
# Скрипт спрайта: слияние двух отсортированных массивов за один цикл
# "Для Сч = 1 По a + b Цикл"
# ---------------------------------------------------------------------------

use_target("Merger")

hat = mk("event_whenflagclicked", top=True, x=40, y=40)

del_result = mk("data_deletealloflist", fld={"LIST": ["Result", list_R]})

len_a_rep = length("A", list_A)
set_a = mk("data_setvariableto", inp={"VALUE": lvl(len_a_rep)}, fld={"VARIABLE": ["a", var_a]})
hook(len_a_rep, set_a)

len_b_rep = length("B", list_B)
set_b = mk("data_setvariableto", inp={"VALUE": lvl(len_b_rep)}, fld={"VARIABLE": ["b", var_b]})
hook(len_b_rep, set_b)

set_i = mk("data_setvariableto", inp={"VALUE": n(1)}, fld={"VARIABLE": ["i", var_i]})
set_j = mk("data_setvariableto", inp={"VALUE": n(1)}, fld={"VARIABLE": ["j", var_j]})
set_cnt = mk("data_setvariableto", inp={"VALUE": n(1)}, fld={"VARIABLE": ["Сч", var_cnt]})

clear_fx_start = mk("looks_cleargraphiceffects")
set_size_start = mk("looks_setsizeto", inp={"SIZE": n(100)})
goto_start = mk("motion_gotoxy", inp={"X": n(-200), "Y": n(-40)})

# --- условие: i <= a  И  (j > b  ИЛИ  A[i] <= B[j]) ---

i_rep1 = var("i", var_i)
a_rep1 = var("a", var_a)
gt_i_a = mk("operator_gt", inp={"OPERAND1": lvl(i_rep1), "OPERAND2": lvl(a_rep1)})
hook(i_rep1, gt_i_a)
hook(a_rep1, gt_i_a)
not_gt_i_a = mk("operator_not", inp={"OPERAND": cond(gt_i_a)})
hook(gt_i_a, not_gt_i_a)
# not_gt_i_a  <=>  i <= a

j_rep1 = var("j", var_j)
b_rep1 = var("b", var_b)
gt_j_b = mk("operator_gt", inp={"OPERAND1": lvl(j_rep1), "OPERAND2": lvl(b_rep1)})
hook(j_rep1, gt_j_b)
hook(b_rep1, gt_j_b)
# gt_j_b  <=>  j > b

i_rep2 = var("i", var_i)
Ai = item("A", list_A, i_rep2)
hook(i_rep2, Ai)

j_rep2 = var("j", var_j)
Bj = item("B", list_B, j_rep2)
hook(j_rep2, Bj)

gt_Ai_Bj = mk("operator_gt", inp={"OPERAND1": lvl(Ai), "OPERAND2": lvl(Bj)})
hook(Ai, gt_Ai_Bj)
hook(Bj, gt_Ai_Bj)
not_gt_Ai_Bj = mk("operator_not", inp={"OPERAND": cond(gt_Ai_Bj)})
hook(gt_Ai_Bj, not_gt_Ai_Bj)
# not_gt_Ai_Bj  <=>  A[i] <= B[j]

cond2 = mk("operator_or", inp={"OPERAND1": cond(gt_j_b), "OPERAND2": cond(not_gt_Ai_Bj)})
hook(gt_j_b, cond2)
hook(not_gt_Ai_Bj, cond2)

full_cond = mk("operator_and", inp={"OPERAND1": cond(not_gt_i_a), "OPERAND2": cond(cond2)})
hook(not_gt_i_a, full_cond)
hook(cond2, full_cond)

# --- ветка THEN: берём элемент из A ---

if_block = mk("control_if_else")
hook(full_cond, if_block)

i_rep3 = var("i", var_i)
Ai_take = item("A", list_A, i_rep3)
hook(i_rep3, Ai_take)
add_a = mk(
    "data_addtolist",
    par=if_block,
    inp={"ITEM": lvl(Ai_take)},
    fld={"LIST": ["Result", list_R]},
)
hook(Ai_take, add_a)
inc_i = mk("data_changevariableby", inp={"VALUE": n(1)}, fld={"VARIABLE": ["i", var_i]})
chain(add_a, inc_i)

# --- ветка ELSE: берём элемент из B ---

j_rep3 = var("j", var_j)
Bj_take = item("B", list_B, j_rep3)
hook(j_rep3, Bj_take)
add_b = mk(
    "data_addtolist",
    par=if_block,
    inp={"ITEM": lvl(Bj_take)},
    fld={"LIST": ["Result", list_R]},
)
hook(Bj_take, add_b)
inc_j = mk("data_changevariableby", inp={"VALUE": n(1)}, fld={"VARIABLE": ["j", var_j]})
chain(add_b, inc_j)

blocks_by_target["Merger"][if_block]["inputs"] = {
    "CONDITION": cond(full_cond),
    "SUBSTACK": cond(add_a),
    "SUBSTACK2": cond(add_b),
}

# --- визуальные эффекты и продвижение счётчика на каждой итерации ---

inc_cnt = mk("data_changevariableby", inp={"VALUE": n(1)}, fld={"VARIABLE": ["Сч", var_cnt]})
change_color = mk("looks_changeeffectby", inp={"CHANGE": n(20)}, fld={"EFFECT": ["COLOR", None]})
change_size = mk("looks_changesizeby", inp={"CHANGE": n(3)})

cnt_rep = var("Сч", var_cnt)
mul15 = mk("operator_multiply", inp={"NUM1": lvl(cnt_rep), "NUM2": n(15)})
hook(cnt_rep, mul15)
x_expr = mk("operator_add", inp={"NUM1": n(-200), "NUM2": lvl(mul15)})
hook(mul15, x_expr)

glide_step = mk("motion_glidesecstoxy", inp={"SECS": n(0.3), "X": lvl(x_expr), "Y": n(-40)})
hook(x_expr, glide_step)

wait_step = mk("control_wait", inp={"DURATION": n(0.4)})

chain(if_block, inc_cnt, change_color, change_size, glide_step, wait_step)

# --- сам цикл: "Для Сч = 1 По a + b Цикл" реализован через control_repeat(a+b) ---

a_rep2 = var("a", var_a)
b_rep2 = var("b", var_b)
sum_ab = mk("operator_add", inp={"NUM1": lvl(a_rep2), "NUM2": lvl(b_rep2)})
hook(a_rep2, sum_ab)
hook(b_rep2, sum_ab)

repeat_block = mk("control_repeat", inp={"TIMES": lvl(sum_ab)})
hook(sum_ab, repeat_block)
blocks_by_target["Merger"][repeat_block]["inputs"]["SUBSTACK"] = cond(if_block)
hook(if_block, repeat_block)

# --- финал: салют/вспышка ---

final_size = mk("looks_setsizeto", inp={"SIZE": n(100)})
final_clear_fx = mk("looks_cleargraphiceffects")
final_glide = mk("motion_glidesecstoxy", inp={"SECS": n(0.5), "X": n(0), "Y": n(0)})
final_say = mk(
    "looks_sayforsecs",
    inp={"MESSAGE": s("Готово! Массивы объединены и отсортированы."), "SECS": n(2)},
)

flash_change = mk("looks_changeeffectby", inp={"CHANGE": n(30)}, fld={"EFFECT": ["COLOR", None]})
flash_wait = mk("control_wait", inp={"DURATION": n(0.1)})
chain(flash_change, flash_wait)
flash_repeat = mk("control_repeat", inp={"TIMES": n(8)})
blocks_by_target["Merger"][flash_repeat]["inputs"]["SUBSTACK"] = cond(flash_change)
hook(flash_change, flash_repeat)

finale_clear = mk("looks_cleargraphiceffects")

chain(
    repeat_block,
    final_size,
    final_clear_fx,
    final_glide,
    final_say,
    flash_repeat,
    finale_clear,
)

chain(
    hat,
    del_result,
    set_a,
    set_b,
    set_i,
    set_j,
    set_cnt,
    clear_fx_start,
    set_size_start,
    goto_start,
    repeat_block,
)

merger_blocks = blocks_by_target["Merger"]

# ---------------------------------------------------------------------------
# Самопроверка структуры блоков перед сборкой project.json
# ---------------------------------------------------------------------------


def validate_blocks(blocks):
    for bid, b in blocks.items():
        if b["topLevel"]:
            assert b["parent"] is None, f"{bid}: hat-блок должен иметь parent=None"
        for name, val in b["inputs"].items():
            if val[0] in (2, 3):
                ref = val[1]
                assert ref in blocks, f"{bid}: input {name} ссылается на несуществующий блок {ref}"
        if b["opcode"] in ("control_if", "control_if_else"):
            assert "CONDITION" in b["inputs"], f"{bid}: нет CONDITION"
            cond_id = b["inputs"]["CONDITION"][1]
            assert blocks[cond_id]["parent"] == bid, f"{bid}: CONDITION-блок имеет неверный parent"
            for key in ("SUBSTACK", "SUBSTACK2"):
                if key in b["inputs"]:
                    sub_id = b["inputs"][key][1]
                    assert blocks[sub_id]["parent"] == bid, f"{bid}: {key}-блок имеет неверный parent"
        if b["opcode"] == "control_repeat":
            if "SUBSTACK" in b["inputs"]:
                sub_id = b["inputs"]["SUBSTACK"][1]
                assert blocks[sub_id]["parent"] == bid, f"{bid}: SUBSTACK control_repeat имеет неверный parent"


validate_blocks(merger_blocks)

# ---------------------------------------------------------------------------
# Сборка project.json
# ---------------------------------------------------------------------------

stage_target = {
    "isStage": True,
    "name": "Stage",
    "variables": {
        var_a: ["a", 0],
        var_b: ["b", 0],
        var_i: ["i", 1],
        var_j: ["j", 1],
        var_cnt: ["Сч", 1],
    },
    "lists": {
        list_A: ["A", INITIAL_A],
        list_B: ["B", INITIAL_B],
        list_R: ["Result", []],
    },
    "broadcasts": {},
    "blocks": {},
    "comments": {},
    "currentCostume": 0,
    "costumes": [
        {
            "name": "backdrop1",
            "assetId": BACKDROP_ID,
            "md5ext": f"{BACKDROP_ID}.svg",
            "dataFormat": "svg",
            "rotationCenterX": 0,
            "rotationCenterY": 0,
        }
    ],
    "sounds": [],
    "volume": 100,
    "layerOrder": 0,
    "tempo": 60,
    "videoTransparency": 50,
    "videoState": "off",
    "textToSpeechLanguage": None,
}

sprite_target = {
    "isStage": False,
    "name": "Merger",
    "variables": {},
    "lists": {},
    "broadcasts": {},
    "blocks": merger_blocks,
    "comments": {},
    "currentCostume": 0,
    "costumes": [
        {
            "name": "merger",
            "assetId": SPRITE_ID,
            "md5ext": f"{SPRITE_ID}.svg",
            "dataFormat": "svg",
            "rotationCenterX": 50,
            "rotationCenterY": 50,
            "bitmapResolution": 1,
        }
    ],
    "sounds": [],
    "volume": 100,
    "layerOrder": 1,
    "visible": True,
    "x": -200,
    "y": -40,
    "size": 100,
    "direction": 90,
    "draggable": False,
    "rotationStyle": "all around",
}

monitors = [
    {
        "id": list_A,
        "mode": "list",
        "opcode": "data_listcontents",
        "params": {"LIST": "A"},
        "spriteName": None,
        "value": [],
        "width": 0,
        "height": 0,
        "x": 5,
        "y": 5,
        "visible": True,
    },
    {
        "id": list_B,
        "mode": "list",
        "opcode": "data_listcontents",
        "params": {"LIST": "B"},
        "spriteName": None,
        "value": [],
        "width": 0,
        "height": 0,
        "x": 130,
        "y": 5,
        "visible": True,
    },
    {
        "id": list_R,
        "mode": "list",
        "opcode": "data_listcontents",
        "params": {"LIST": "Result"},
        "spriteName": None,
        "value": [],
        "width": 0,
        "height": 0,
        "x": 255,
        "y": 5,
        "visible": True,
    },
    {
        "id": var_a,
        "mode": "default",
        "opcode": "data_variable",
        "params": {"VARIABLE": "a"},
        "spriteName": None,
        "value": 0,
        "width": 0,
        "height": 0,
        "x": 5,
        "y": 150,
        "visible": True,
        "sliderMin": 0,
        "sliderMax": 100,
        "isDiscrete": True,
    },
    {
        "id": var_b,
        "mode": "default",
        "opcode": "data_variable",
        "params": {"VARIABLE": "b"},
        "spriteName": None,
        "value": 0,
        "width": 0,
        "height": 0,
        "x": 5,
        "y": 175,
        "visible": True,
        "sliderMin": 0,
        "sliderMax": 100,
        "isDiscrete": True,
    },
    {
        "id": var_i,
        "mode": "default",
        "opcode": "data_variable",
        "params": {"VARIABLE": "i"},
        "spriteName": None,
        "value": 1,
        "width": 0,
        "height": 0,
        "x": 5,
        "y": 200,
        "visible": True,
        "sliderMin": 0,
        "sliderMax": 100,
        "isDiscrete": True,
    },
    {
        "id": var_j,
        "mode": "default",
        "opcode": "data_variable",
        "params": {"VARIABLE": "j"},
        "spriteName": None,
        "value": 1,
        "width": 0,
        "height": 0,
        "x": 5,
        "y": 225,
        "visible": True,
        "sliderMin": 0,
        "sliderMax": 100,
        "isDiscrete": True,
    },
    {
        "id": var_cnt,
        "mode": "default",
        "opcode": "data_variable",
        "params": {"VARIABLE": "Сч"},
        "spriteName": None,
        "value": 1,
        "width": 0,
        "height": 0,
        "x": 5,
        "y": 250,
        "visible": True,
        "sliderMin": 0,
        "sliderMax": 100,
        "isDiscrete": True,
    },
]

project = {
    "targets": [stage_target, sprite_target],
    "monitors": monitors,
    "extensions": [],
    "meta": {"semver": "3.0.0", "vm": "0.2.0", "agent": "generator"},
}

# ---------------------------------------------------------------------------
# Упаковка в .sb3
# ---------------------------------------------------------------------------

BUILD = "_build"
if os.path.isdir(BUILD):
    shutil.rmtree(BUILD)
os.makedirs(BUILD)

with open(f"{BUILD}/project.json", "w", encoding="utf-8") as f:
    json.dump(project, f, ensure_ascii=False, indent=2)

with open(f"{BUILD}/{BACKDROP_ID}.svg", "w", encoding="utf-8") as f:
    f.write(BACKDROP_SVG)
with open(f"{BUILD}/{SPRITE_ID}.svg", "w", encoding="utf-8") as f:
    f.write(SPRITE_SVG)

OUTPUT_NAME = "merge_sorted_arrays.sb3"

with zipfile.ZipFile(OUTPUT_NAME, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(f"{BUILD}/project.json", "project.json")
    z.write(f"{BUILD}/{BACKDROP_ID}.svg", f"{BACKDROP_ID}.svg")
    z.write(f"{BUILD}/{SPRITE_ID}.svg", f"{SPRITE_ID}.svg")

shutil.rmtree(BUILD)
print(f"OK: {OUTPUT_NAME}")
