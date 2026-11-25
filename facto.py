import json
import random
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="팩토 창의사고력 수학", page_icon="📐", layout="wide")

ACTIVITY_OPTIONS = [
    "모양 맞춰넣기",
    "모양 나누기",
    "모양 겹치기",
]

LEVEL_OPTIONS_SIMPLE = ["하", "중", "상"]
LEVEL_OPTIONS_OVERLAP = ["하 (초2~초3)", "중 (초3~4)", "상 (초4~6)"]


def level_key_from_label(label: str) -> str:
    if label.startswith("하"):
        return "하"
    if label.startswith("중"):
        return "중"
    return "상"


def norm(coords):
    mr = min(r for r, c in coords)
    mc = min(c for r, c in coords)
    return sorted([(r - mr, c - mc) for r, c in coords])


def rot90(coords):
    return norm([(c, -r) for r, c in coords])


def flip(coords):
    return norm([(r, -c) for r, c in coords])


def all_orientations(coords, allow_flip=True):
    seen = set()
    res = []
    cur = norm(coords)
    for _ in range(4):
        t = tuple(cur)
        if t not in seen:
            seen.add(t)
            res.append(cur)
        cur = rot90(cur)
    if allow_flip:
        cur = flip(norm(coords))
        for _ in range(4):
            t = tuple(cur)
            if t not in seen:
                seen.add(t)
                res.append(cur)
            cur = rot90(cur)
    return res


def canonical_shape(coords, allow_flip=True):
    if not coords:
        return ()
    return min(tuple(o) for o in all_orientations(coords, allow_flip=allow_flip))


def is_connected(cells):
    if len(cells) <= 1:
        return True
    cset = set(tuple(x) for x in cells)
    start = next(iter(cset))
    visited = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nxt = (r + dr, c + dc)
            if nxt in cset and nxt not in visited:
                visited.add(nxt)
                stack.append(nxt)
    return len(visited) == len(cset)


# =========================================================
# 1. 모양 맞춰넣기 (우봉고) 데이터 및 생성기
# =========================================================
UBONGO_BOARDS = {
    "하": [
        [(0, 0), (0, 1), (1, 1), (1, 2), (2, 1), (2, 2), (2, 3), (1, 3)],
        [(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2), (2, 3), (0, 2)],
        [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1), (2, 3)],
        [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2), (2, 3), (0, 2), (0, 3), (2, 1)],
    ],
    "중": [
        [(r, c) for r in range(3) for c in range(4) if (r, c) != (1, 1)],
        [(0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (0, 3), (2, 3)],
        [(0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 2), (2, 3), (2, 4)],
        [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (0, 3), (1, 3), (2, 0), (2, 1)],
    ],
    "상": [
        [(r, c) for r in range(4) for c in range(4) if (r, c) not in {(1, 1), (2, 2)}],
        [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (2, 4), (3, 0), (3, 2), (3, 4)],
        [(0, 0), (0, 1), (1, 1), (1, 2), (1, 3), (2, 0), (2, 2), (2, 3), (2, 4), (3, 0), (3, 1), (3, 3), (0, 3)],
        [(r, c) for r in range(4) for c in range(4) if (r, c) not in {(1, 2), (2, 1)}],
    ],
}

PALETTE = [
    ("빨강", "#FF595E"),
    ("파랑", "#1982C4"),
    ("노랑", "#FFCA3A"),
    ("초록", "#8AC926"),
    ("보라", "#9B5DE5"),
    ("주황", "#FF924C"),
]


def shape_complexity(coords):
    cset = set(coords)
    if len(coords) <= 2:
        return 0
    turns = 0
    for r, c in coords:
        adj_h = ((r, c - 1) in cset) + ((r, c + 1) in cset)
        adj_v = ((r - 1, c) in cset) + ((r + 1, c) in cset)
        if adj_h >= 1 and adj_v >= 1:
            turns += 1
    return turns


def gen_ubongo(level_key):
    if level_key == "하":
        sizes_pool = [2, 3, 3, 4]
        min_pieces, max_pieces = 3, 4
    elif level_key == "중":
        sizes_pool = [2, 3, 4, 4, 5]
        min_pieces, max_pieces = 3, 5
    else:
        sizes_pool = [3, 4, 4, 5, 5]
        min_pieces, max_pieces = 4, 6

    while True:
        mask = norm(random.choice(UBONGO_BOARDS[level_key]))
        for _ in range(random.randint(0, 3)):
            mask = rot90(mask)
        if random.choice([True, False]):
            mask = flip(mask)

        rows = max(r for r, c in mask) + 1
        cols = max(c for r, c in mask) + 1
        mask_set = set(mask)

        rem = set(mask_set)
        parts = []
        ok = True

        while rem:
            cur = [random.choice(list(rem))]
            rem.remove(cur[0])
            goal = random.choice(sizes_pool)

            while len(cur) < goal:
                candidates = []
                for cr, cc in cur:
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nxt = (cr + dr, cc + dc)
                        if nxt in rem and nxt not in candidates:
                            same_dir = (cr - dr, cc - dc) in cur
                            weight = 3 if same_dir else 1
                            candidates.extend([nxt] * weight)
                if not candidates:
                    break
                pick = random.choice(candidates)
                cur.append(pick)
                rem.remove(pick)

            if len(cur) < 2:
                ok = False
                break
            parts.append(cur)

        if not ok or not (min_pieces <= len(parts) <= max_pieces):
            continue

        union_cells = {pt for g in parts for pt in g}
        if union_cells != mask_set:
            continue

        complex_count = sum(1 for g in parts if shape_complexity(g) >= 1)
        if complex_count < max(1, len(parts) // 2):
            continue

        random.shuffle(parts)
        shuffled_palette = PALETTE[:]
        random.shuffle(shuffled_palette)

        pieces = []
        for i, g in enumerate(parts):
            s = norm(g)
            for _ in range(random.randint(0, 3)):
                s = rot90(s)
            if random.choice([True, False]):
                s = flip(s)
            cname, chex = shuffled_palette[i % len(shuffled_palette)]
            pieces.append({
                "id": f"p_{i}",
                "name": f"{cname} ({len(s)}칸)",
                "color": chex,
                "coords": s,
                "sol": sorted(g),
            })
        return rows, cols, sorted(list(mask_set)), pieces


def render_make_activity():
    st.subheader("🧩 모양 만들기 (드래그 앤 드롭 우봉고)")

    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        level_label = st.selectbox("난이도", LEVEL_OPTIONS_SIMPLE, key="make_lv_select")
    with c2:
        st.write("")
        new_q = st.button("🎲 새 문제", use_container_width=True, key="make_new_q")
    with c3:
        st.write("")
        reset_q = st.button("🧹 보드 비우기", use_container_width=True, key="make_reset_q")

    level_key = level_key_from_label(level_label)

    if "make_lv" not in st.session_state or st.session_state.make_lv != level_key or new_q:
        r, c, mlist, plist = gen_ubongo(level_key)
        st.session_state.make_lv = level_key
        st.session_state.make_rows = r
        st.session_state.make_cols = c
        st.session_state.make_mask = mlist
        st.session_state.make_pieces = plist
        st.session_state.make_seed = random.randint(1, 999999)

    if reset_q:
        st.session_state.make_seed = random.randint(1, 999999)

    payload = json.dumps({
        "rows": st.session_state.make_rows,
        "cols": st.session_state.make_cols,
        "mask": st.session_state.make_mask,
        "pieces": st.session_state.make_pieces,
        "seed": st.session_state.make_seed,
    })

    html_template = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
  * { box-sizing: border-box; user-select: none; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  body { margin: 0; padding: 8px; background: transparent; }
  .wrap { display: flex; gap: 28px; align-items: flex-start; flex-wrap: wrap; }
  .panel { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 18px; box-shadow: 0 4px 14px rgba(15,23,42,0.06); }
  .panel-title { font-size: 17px; font-weight: 800; color: #0f172a; margin-bottom: 10px; }
  .sub-note { font-size: 13px; color: #64748b; margin-bottom: 12px; }

  .tray { display: flex; flex-direction: column; gap: 12px; min-width: 240px; }
  .piece-row {
    display: flex; align-items: center; justify-content: space-between; gap: 10px;
    padding: 10px 12px; border-radius: 12px; border: 2px solid #e2e8f0; background: #f8fafc;
    cursor: grab; transition: transform 0.12s ease, border-color 0.12s ease;
  }
  .piece-row.selected { border-color: #0f172a; background: #ffffff; box-shadow: 0 4px 12px rgba(15,23,42,0.1); }
  .piece-row.placed { opacity: 0.55; }
  .piece-row:active { cursor: grabbing; }
  .piece-label { font-size: 13px; font-weight: 800; color: #0f172a; margin-bottom: 4px; }
  .mini-btns { display: flex; gap: 6px; }
  .mini-btns button {
    border: 1px solid #cbd5e1; background: #ffffff; color: #0f172a;
    border-radius: 7px; padding: 5px 8px; font-size: 12px; font-weight: 700; cursor: pointer;
  }
  .mini-btns button:hover { background: #f1f5f9; }

  .board-box { display: flex; flex-direction: column; align-items: center; }
  .status-bar {
    margin-top: 12px; width: 100%; display: flex; justify-content: space-between; align-items: center;
    font-size: 14px; font-weight: 800; color: #0f172a;
  }
  .action-row { margin-top: 10px; display: flex; gap: 8px; width: 100%; }
  .action-row button {
    flex: 1; padding: 9px 12px; border-radius: 10px; border: 1px solid #cbd5e1;
    background: #f8fafc; color: #0f172a; font-weight: 800; font-size: 13px; cursor: pointer;
  }
  .action-row button:hover { background: #e2e8f0; }
  .check-banner {
    margin-top: 10px; width: 100%; padding: 11px 14px; border-radius: 10px;
    font-weight: 800; font-size: 14px; display: none;
  }
  .check-banner.ok { background: #dcfce7; color: #166534; display: block; }
  .check-banner.no { background: #fee2e2; color: #991b1b; display: block; }
  .msg-warn {
    margin-top: 8px; font-size: 13px; font-weight: 700; color: #dc2626; min-height: 18px;
  }
</style>
</head>
<body>
<div class="wrap">
  <div class="panel tray">
    <div class="panel-title">1. 조각 상자 (드래그해서 놓기)</div>
    <div class="sub-note">조각을 마우스로 끌면 조각 모양 이미지가 함께 따라갑니다.</div>
    <div id="makeTrayList"></div>
  </div>

  <div class="panel board-box">
    <div class="panel-title">2. 연결된 퍼즐 보드</div>
    <div class="sub-note">틀 전체가 하나의 연결된 모양입니다. 보드 위 조각을 클릭하면 회수됩니다.</div>
    <svg id="makeBoardSvg"></svg>
    <div class="msg-warn" id="makeWarnText"></div>
    <div class="status-bar">
      <span id="makeProgressText">0 / 0 칸 채움</span>
      <span id="makeSelectedText">선택: -</span>
    </div>
    <div class="action-row">
      <button onclick="makeRotateSelected()">↻ 선택 회전</button>
      <button onclick="makeFlipSelected()">⇄ 선택 뒤집기</button>
      <button onclick="makeCheckAnswer()">✅ 정답 확인</button>
    </div>
    <div class="check-banner" id="makeCheckBanner"></div>
  </div>
</div>

<script>
const MAKE_DATA = __PAYLOAD_JSON__;
const MAKE_CELL = 54;
const MAKE_PAD = 16;

let makePieces = JSON.parse(JSON.stringify(MAKE_DATA.pieces));
let makeSelectedId = makePieces[0].id;
let makeDraggingId = null;
let makePlaced = {};
let makeHoverAnchor = null;

const makeMaskSet = new Set(MAKE_DATA.mask.map(pt => `${pt[0]},${pt[1]}`));

function makeClearCheckBanner() {
  const el = document.getElementById("makeCheckBanner");
  el.className = "check-banner";
  el.style.display = "none";
  el.innerText = "";
}

function makeNorm(coords) {
  const minR = Math.min(...coords.map(p => p[0]));
  const minC = Math.min(...coords.map(p => p[1]));
  return coords.map(p => [p[0] - minR, p[1] - minC]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
}

function makeRotateCoords(coords) {
  return makeNorm(coords.map(([r, c]) => [c, -r]));
}

function makeFlipCoords(coords) {
  return makeNorm(coords.map(([r, c]) => [r, -c]));
}

function makeGetPiece(id) {
  return makePieces.find(p => p.id === id);
}

function makeIsPiecePlaced(id) {
  return Object.values(makePlaced).includes(id);
}

function makeRemovePieceFromBoard(id) {
  for (const k of Object.keys(makePlaced)) {
    if (makePlaced[k] === id) delete makePlaced[k];
  }
}

function makeCanPlace(piece, anchorR, anchorC) {
  const [ar, ac] = piece.coords[0];
  for (const [dr, dc] of piece.coords) {
    const tr = anchorR + (dr - ar);
    const tc = anchorC + (dc - ac);
    const key = `${tr},${tc}`;
    if (!makeMaskSet.has(key)) return false;
    const occ = makePlaced[key];
    if (occ && occ !== piece.id) return false;
  }
  return true;
}

function makePlacePiece(piece, anchorR, anchorC) {
  if (!makeCanPlace(piece, anchorR, anchorC)) {
    document.getElementById("makeWarnText").innerText = "틀 밖으로 나가거나 다른 조각과 겹치는 위치예요!";
    return false;
  }
  document.getElementById("makeWarnText").innerText = "";
  makeClearCheckBanner();
  makeRemovePieceFromBoard(piece.id);
  const [ar, ac] = piece.coords[0];
  for (const [dr, dc] of piece.coords) {
    const tr = anchorR + (dr - ar);
    const tc = anchorC + (dc - ac);
    makePlaced[`${tr},${tc}`] = piece.id;
  }
  makeRenderAll();
  return true;
}

function makeCreateDragImage(piece, cellSize = 44) {
  const set = new Set(piece.coords.map(([r, c]) => `${r},${c}`));
  const maxR = Math.max(...piece.coords.map(p => p[0])) + 1;
  const maxC = Math.max(...piece.coords.map(p => p[1])) + 1;
  const pad = 8;

  const canvas = document.createElement("canvas");
  canvas.width = maxC * cellSize + pad * 2;
  canvas.height = maxR * cellSize + pad * 2;
  const ctx = canvas.getContext("2d");

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = piece.color;

  for (const [r, c] of piece.coords) {
    const x = pad + c * cellSize;
    const y = pad + r * cellSize;
    ctx.fillRect(x, y, cellSize, cellSize);
    if (set.has(`${r - 1},${c}`)) ctx.fillRect(x + 1, y - 3, cellSize - 2, 6);
    if (set.has(`${r + 1},${c}`)) ctx.fillRect(x + 1, y + cellSize - 3, cellSize - 2, 6);
    if (set.has(`${r},${c - 1}`)) ctx.fillRect(x - 3, y + 1, 6, cellSize - 2);
    if (set.has(`${r},${c + 1}`)) ctx.fillRect(x + cellSize - 3, y + 1, 6, cellSize - 2);
  }

  ctx.strokeStyle = "#0f172a";
  ctx.lineWidth = 3;
  ctx.lineCap = "round";
  for (const [r, c] of piece.coords) {
    const x = pad + c * cellSize;
    const y = pad + r * cellSize;
    if (!set.has(`${r - 1},${c}`)) {
      ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + cellSize, y); ctx.stroke();
    }
    if (!set.has(`${r + 1},${c}`)) {
      ctx.beginPath(); ctx.moveTo(x, y + cellSize); ctx.lineTo(x + cellSize, y + cellSize); ctx.stroke();
    }
    if (!set.has(`${r},${c - 1}`)) {
      ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y + cellSize); ctx.stroke();
    }
    if (!set.has(`${r},${c + 1}`)) {
      ctx.beginPath(); ctx.moveTo(x + cellSize, y); ctx.lineTo(x + cellSize, y + cellSize); ctx.stroke();
    }
  }

  const [ar, ac] = piece.coords[0];
  const offsetX = pad + ac * cellSize + cellSize / 2;
  const offsetY = pad + ar * cellSize + cellSize / 2;
  return { canvas, offsetX, offsetY };
}

function makeBuildUnifiedShapeSVG(coords, fillColor, strokeColor, cellSize, pad, bgRect = false, totalRows = 0, totalCols = 0, ghost = false) {
  const set = new Set(coords.map(([r, c]) => `${r},${c}`));
  const maxR = totalRows || (Math.max(...coords.map(p => p[0])) + 1);
  const maxC = totalCols || (Math.max(...coords.map(p => p[1])) + 1);
  const w = maxC * cellSize + pad * 2;
  const h = maxR * cellSize + pad * 2;

  const parts = [];
  if (bgRect) {
    parts.push(`<rect x="0" y="0" width="${w}" height="${h}" rx="16" fill="#0f172a" />`);
  }

  const opAttr = ghost ? ' opacity="0.45"' : "";

  for (const [r, c] of coords) {
    const x = pad + c * cellSize;
    const y = pad + r * cellSize;
    parts.push(`<rect x="${x}" y="${y}" width="${cellSize}" height="${cellSize}" rx="5" fill="${fillColor}"${opAttr} />`);
    if (set.has(`${r - 1},${c}`)) {
      parts.push(`<rect x="${x + 1}" y="${y - 3}" width="${cellSize - 2}" height="6" fill="${fillColor}"${opAttr} />`);
    }
    if (set.has(`${r + 1},${c}`)) {
      parts.push(`<rect x="${x + 1}" y="${y + cellSize - 3}" width="${cellSize - 2}" height="6" fill="${fillColor}"${opAttr} />`);
    }
    if (set.has(`${r},${c - 1}`)) {
      parts.push(`<rect x="${x - 3}" y="${y + 1}" width="6" height="${cellSize - 2}" fill="${fillColor}"${opAttr} />`);
    }
    if (set.has(`${r},${c + 1}`)) {
      parts.push(`<rect x="${x + cellSize - 3}" y="${y + 1}" width="6" height="${cellSize - 2}" fill="${fillColor}"${opAttr} />`);
    }
  }

  for (const [r, c] of coords) {
    const x = pad + c * cellSize;
    const y = pad + r * cellSize;
    if (!set.has(`${r - 1},${c}`)) {
      parts.push(`<line x1="${x + 1}" y1="${y}" x2="${x + cellSize - 1}" y2="${y}" stroke="${strokeColor}" stroke-width="2.5" stroke-linecap="round"${opAttr} />`);
    }
    if (!set.has(`${r + 1},${c}`)) {
      parts.push(`<line x1="${x + 1}" y1="${y + cellSize}" x2="${x + cellSize - 1}" y2="${y + cellSize}" stroke="${strokeColor}" stroke-width="2.5" stroke-linecap="round"${opAttr} />`);
    }
    if (!set.has(`${r},${c - 1}`)) {
      parts.push(`<line x1="${x}" y1="${y + 1}" x2="${x}" y2="${y + cellSize - 1}" stroke="${strokeColor}" stroke-width="2.5" stroke-linecap="round"${opAttr} />`);
    }
    if (!set.has(`${r},${c + 1}`)) {
      parts.push(`<line x1="${x + cellSize}" y1="${y + 1}" x2="${x + cellSize}" y2="${y + cellSize - 1}" stroke="${strokeColor}" stroke-width="2.5" stroke-linecap="round"${opAttr} />`);
    }
  }

  return { svgInner: parts.join(""), w, h };
}

function makeRenderTray() {
  const container = document.getElementById("makeTrayList");
  container.innerHTML = "";
  for (const p of makePieces) {
    const row = document.createElement("div");
    const isSel = p.id === makeSelectedId;
    const isPl = makeIsPiecePlaced(p.id);
    row.className = `piece-row ${isSel ? "selected" : ""} ${isPl ? "placed" : ""}`;
    row.draggable = true;

    row.addEventListener("click", () => {
      makeSelectedId = p.id;
      document.getElementById("makeWarnText").innerText = "";
      makeRenderAll();
    });

    row.addEventListener("dragstart", (e) => {
      makeSelectedId = p.id;
      makeDraggingId = p.id;
      e.dataTransfer.effectAllowed = "move";
      try { e.dataTransfer.setData("text/plain", p.id); } catch (_) {}
      if (e.dataTransfer.setDragImage) {
        const img = makeCreateDragImage(p, 44);
        e.dataTransfer.setDragImage(img.canvas, img.offsetX, img.offsetY);
      }
    });

    row.addEventListener("dragend", () => {
      makeDraggingId = null;
      makeHoverAnchor = null;
      makeRenderBoard();
    });

    const maxR = Math.max(...p.coords.map(x => x[0])) + 1;
    const maxC = Math.max(...p.coords.map(x => x[1])) + 1;
    const built = makeBuildUnifiedShapeSVG(p.coords, p.color, "#0f172a", 26, 4, false, maxR, maxC, false);

    const leftDiv = document.createElement("div");
    leftDiv.innerHTML = `
      <div class="piece-label">${p.name} ${isPl ? "(배치됨)" : ""}</div>
      <svg width="${built.w}" height="${built.h}" viewBox="0 0 ${built.w} ${built.h}">${built.svgInner}</svg>
    `;

    const rightDiv = document.createElement("div");
    rightDiv.className = "mini-btns";

    const rotBtn = document.createElement("button");
    rotBtn.innerText = "↻";
    rotBtn.title = "90도 회전";
    rotBtn.onclick = (ev) => {
      ev.stopPropagation();
      makeSelectedId = p.id;
      makeRemovePieceFromBoard(p.id);
      p.coords = makeRotateCoords(p.coords);
      makeClearCheckBanner();
      makeRenderAll();
    };

    const flipBtn = document.createElement("button");
    flipBtn.innerText = "⇄";
    flipBtn.title = "좌우 뒤집기";
    flipBtn.onclick = (ev) => {
      ev.stopPropagation();
      makeSelectedId = p.id;
      makeRemovePieceFromBoard(p.id);
      p.coords = makeFlipCoords(p.coords);
      makeClearCheckBanner();
      makeRenderAll();
    };

    rightDiv.appendChild(rotBtn);
    rightDiv.appendChild(flipBtn);
    row.appendChild(leftDiv);
    row.appendChild(rightDiv);
    container.appendChild(row);
  }
}

function makeRenderBoard() {
  const svg = document.getElementById("makeBoardSvg");
  const w = MAKE_DATA.cols * MAKE_CELL + MAKE_PAD * 2;
  const h = MAKE_DATA.rows * MAKE_CELL + MAKE_PAD * 2;
  svg.setAttribute("width", w);
  svg.setAttribute("height", h);
  svg.setAttribute("viewBox", `0 0 ${w} ${h}`);

  let html = `<rect x="0" y="0" width="${w}" height="${h}" rx="16" fill="#0f172a" />`;

  const frameBuilt = makeBuildUnifiedShapeSVG(MAKE_DATA.mask, "#1e293b", "#64748b", MAKE_CELL, MAKE_PAD, false, MAKE_DATA.rows, MAKE_DATA.cols, false);
  html += frameBuilt.svgInner;

  for (const p of makePieces) {
    const pCoords = [];
    for (const [k, pid] of Object.entries(makePlaced)) {
      if (pid === p.id) {
        const [r, c] = k.split(",").map(Number);
        pCoords.push([r, c]);
      }
    }
    if (pCoords.length > 0) {
      const pBuilt = makeBuildUnifiedShapeSVG(pCoords, p.color, "#0f172a", MAKE_CELL, MAKE_PAD, false, MAKE_DATA.rows, MAKE_DATA.cols, false);
      html += pBuilt.svgInner;
    }
  }

  const activeId = makeDraggingId || makeSelectedId;
  if (makeHoverAnchor && activeId) {
    const selP = makeGetPiece(activeId);
    if (selP) {
      const [ar, ac] = selP.coords[0];
      const ghostPts = selP.coords.map(([dr, dc]) => [makeHoverAnchor[0] + (dr - ar), makeHoverAnchor[1] + (dc - ac)]);
      const ok = makeCanPlace(selP, makeHoverAnchor[0], makeHoverAnchor[1]);
      const gBuilt = makeBuildUnifiedShapeSVG(
        ghostPts,
        ok ? selP.color : "#ef4444",
        ok ? "#ffffff" : "#fca5a5",
        MAKE_CELL,
        MAKE_PAD,
        false,
        MAKE_DATA.rows,
        MAKE_DATA.cols,
        true
      );
      html += gBuilt.svgInner;
    }
  }

  for (const [r, c] of MAKE_DATA.mask) {
    const x = MAKE_PAD + c * MAKE_CELL;
    const y = MAKE_PAD + r * MAKE_CELL;
    html += `<rect data-r="${r}" data-c="${c}" x="${x}" y="${y}" width="${MAKE_CELL}" height="${MAKE_CELL}" fill="transparent" style="cursor:pointer;" />`;
  }

  svg.innerHTML = html;

  svg.querySelectorAll("rect[data-r]").forEach(rect => {
    const r = Number(rect.getAttribute("data-r"));
    const c = Number(rect.getAttribute("data-c"));

    rect.addEventListener("dragover", (e) => {
      e.preventDefault();
      if (!makeHoverAnchor || makeHoverAnchor[0] !== r || makeHoverAnchor[1] !== c) {
        makeHoverAnchor = [r, c];
        makeRenderBoard();
      }
    });

    rect.addEventListener("drop", (e) => {
      e.preventDefault();
      let pid = makeDraggingId || makeSelectedId;
      try {
        const dtId = e.dataTransfer.getData("text/plain");
        if (dtId) pid = dtId;
      } catch (_) {}
      makeDraggingId = null;
      makeHoverAnchor = null;
      const p = makeGetPiece(pid);
      if (p) {
        makeSelectedId = p.id;
        makePlacePiece(p, r, c);
      }
    });

    rect.addEventListener("click", () => {
      const occId = makePlaced[`${r},${c}`];
      const selP = makeGetPiece(makeSelectedId);
      if (occId && (!selP || occId === selP.id)) {
        makeRemovePieceFromBoard(occId);
        document.getElementById("makeWarnText").innerText = "";
        makeClearCheckBanner();
        makeRenderAll();
        return;
      }
      if (selP) {
        makePlacePiece(selP, r, c);
      }
    });
  });

  const filled = Object.keys(makePlaced).length;
  const total = MAKE_DATA.mask.length;
  document.getElementById("makeProgressText").innerText = `${filled} / ${total} 칸 채움`;
  const curP = makeGetPiece(makeSelectedId);
  document.getElementById("makeSelectedText").innerText = `선택: ${curP ? curP.name : "-"}`;
}

function makeCheckAnswer() {
  const filled = Object.keys(makePlaced).length;
  const total = MAKE_DATA.mask.length;
  const unplaced = makePieces.filter(p => !makeIsPiecePlaced(p.id));
  const banner = document.getElementById("makeCheckBanner");

  if (filled === total && unplaced.length === 0) {
    banner.className = "check-banner ok";
    banner.style.display = "block";
    banner.innerText = "⭕ 맞아요! 빈칸 없이 모든 조각을 정확히 맞췄습니다.";
  } else {
    const reasons = [];
    if (unplaced.length > 0) reasons.push(`안 놓인 조각 ${unplaced.length}개`);
    if (filled < total) reasons.push(`빈칸 ${total - filled}칸 남음`);
    banner.className = "check-banner no";
    banner.style.display = "block";
    banner.innerText = `❌ 다시 생각해볼까요? (${reasons.join(", ")})`;
  }
}

function makeRotateSelected() {
  const p = makeGetPiece(makeSelectedId);
  if (!p) return;
  makeRemovePieceFromBoard(p.id);
  p.coords = makeRotateCoords(p.coords);
  makeClearCheckBanner();
  makeRenderAll();
}

function makeFlipSelected() {
  const p = makeGetPiece(makeSelectedId);
  if (!p) return;
  makeRemovePieceFromBoard(p.id);
  p.coords = makeFlipCoords(p.coords);
  makeClearCheckBanner();
  makeRenderAll();
}

function makeRenderAll() {
  makeRenderTray();
  makeRenderBoard();
}

makeRenderAll();
</script>
</body>
</html>
"""

    html_code = html_template.replace("__PAYLOAD_JSON__", payload)
    components.html(html_code, height=620, scrolling=True)


# =========================================================
# 2. 모양 나누기 데이터 및 생성기
# =========================================================
BASE_SHAPES = {
    "하": [
        [(0, 0), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (0, 2)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(0, 1), (1, 0), (1, 1), (1, 2)],
    ],
    "중": [
        [(0, 0), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(0, 1), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 1), (2, 2)],
        [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
    ],
    "상": [
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(0, 1), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 1), (2, 2)],
        [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 1), (3, 1)],
        [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
    ],
}

DIVERSE_DOT_BOARDS = {
    "하": [
        {"cells": [(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 2)], "group_sizes": [2, 3]},
        {"cells": [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)], "group_sizes": [2, 3]},
        {"cells": [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 1)], "group_sizes": [3]},
        {"cells": [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (2, 2), (2, 3), (1, 3)], "group_sizes": [2, 4]},
    ],
    "중": [
        {"cells": [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2), (2, 3), (0, 2), (1, 3)], "group_sizes": [3]},
        {"cells": [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)], "group_sizes": [2, 4]},
        {"cells": [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (0, 2), (1, 0), (2, 1)], "group_sizes": [3]},
        {"cells": [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1), (2, 2)], "group_sizes": [2, 4]},
    ],
    "상": [
        {"cells": [(r, c) for r in range(4) for c in range(4) if (r, c) not in {(1, 1), (1, 2), (2, 1), (2, 2)}], "group_sizes": [3, 4]},
        {"cells": [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (2, 4), (3, 1), (3, 3)], "group_sizes": [3, 4]},
        {"cells": [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (3, 2)], "group_sizes": [2, 5]},
        {"cells": [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2), (3, 0), (3, 1), (3, 2), (2, 3)], "group_sizes": [3, 4]},
    ],
}

GROUP_PALETTE = [
    ("1번 (빨강)", "#FF595E"),
    ("2번 (파랑)", "#1982C4"),
    ("3번 (노랑)", "#FFCA3A"),
    ("4번 (초록)", "#8AC926"),
    ("5번 (보라)", "#9B5DE5"),
    ("6번 (주황)", "#FF924C"),
]


def gen_congruent_puzzle(level_key):
    if level_key == "하":
        k = random.choice([2, 2, 3])
    elif level_key == "중":
        k = random.choice([2, 3, 3, 4])
    else:
        k = random.choice([3, 4, 4])

    allow_flip = True

    for _ in range(300):
        base = norm(random.choice(BASE_SHAPES[level_key]))
        variants = all_orientations(base, allow_flip=allow_flip)
        first = norm(random.choice(variants))
        sol_parts = [first]
        occupied = set(first)

        ok = True
        for _ in range(k - 1):
            placed_one = False
            adj_anchors = []
            for r, c in list(occupied):
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nxt = (r + dr, c + dc)
                    if nxt not in occupied and nxt not in adj_anchors:
                        adj_anchors.append(nxt)
            random.shuffle(adj_anchors)
            random.shuffle(variants)

            for ar, ac in adj_anchors:
                for v in variants:
                    br, bc = v[0]
                    cand = [(ar + dr - br, ac + dc - bc) for dr, dc in v]
                    if all(pt not in occupied for pt in cand):
                        sol_parts.append(sorted(cand))
                        occupied.update(cand)
                        placed_one = True
                        break
                if placed_one:
                    break

            if not placed_one:
                ok = False
                break

        if not ok or len(sol_parts) != k:
            continue

        all_pts = [pt for part in sol_parts for pt in part]
        if not is_connected(all_pts):
            continue

        mr = min(r for r, c in all_pts)
        mc = min(c for r, c in all_pts)
        sol_parts = [sorted([(r - mr, c - mc) for r, c in part]) for part in sol_parts]
        mask = sorted([pt for part in sol_parts for pt in part])

        rows = max(r for r, c in mask) + 1
        cols = max(c for r, c in mask) + 1
        target_canon = canonical_shape(sol_parts[0], allow_flip=allow_flip)
        per_piece = len(sol_parts[0])

        if not all(canonical_shape(p, allow_flip=allow_flip) == target_canon for p in sol_parts):
            continue

        groups = []
        for i in range(k):
            gname, ghex = GROUP_PALETTE[i % len(GROUP_PALETTE)]
            groups.append({
                "id": f"g_{i}",
                "name": gname,
                "color": ghex,
                "target": per_piece,
                "sol": sol_parts[i],
            })

        return {
            "mode": "congruent",
            "title": f"똑같은 모양 {k}조각으로 나누기 (조각당 {per_piece}칸)",
            "rows": rows,
            "cols": cols,
            "total": len(mask),
            "k": k,
            "per_piece": per_piece,
            "allow_flip": allow_flip,
            "target_canon": [list(pt) for pt in target_canon],
            "mask": [list(pt) for pt in mask],
            "groups": groups,
        }

    fallback_sol = [[(0, 0), (1, 0), (1, 1)], [(0, 1), (0, 2), (1, 2)]]
    mask = sorted([pt for part in fallback_sol for pt in part])
    target_canon = canonical_shape(fallback_sol[0], allow_flip=True)
    return {
        "mode": "congruent",
        "title": "똑같은 모양 2조각으로 나누기 (조각당 3칸)",
        "rows": 2,
        "cols": 3,
        "total": len(mask),
        "k": 2,
        "per_piece": 3,
        "allow_flip": True,
        "target_canon": [list(pt) for pt in target_canon],
        "mask": [list(pt) for pt in mask],
        "groups": [
            {"id": "g_0", "name": GROUP_PALETTE[0][0], "color": GROUP_PALETTE[0][1], "target": 3, "sol": fallback_sol[0]},
            {"id": "g_1", "name": GROUP_PALETTE[1][0], "color": GROUP_PALETTE[1][1], "target": 3, "sol": fallback_sol[1]},
        ],
    }


def gen_dot_puzzle(level_key):
    candidates = DIVERSE_DOT_BOARDS[level_key][:]
    random.shuffle(candidates)

    for chosen in candidates:
        valid_sizes = [s for s in chosen["group_sizes"] if len(chosen["cells"]) % s == 0]
        if not valid_sizes:
            continue
        gsize = random.choice(valid_sizes)

        for _ in range(80):
            cells = norm(chosen["cells"])
            for _ in range(random.randint(0, 3)):
                cells = rot90(cells)
            if random.choice([True, False]):
                cells = flip(cells)
            cells = norm(cells)

            total = len(cells)
            k = total // gsize

            rem = set(cells)
            sol_parts = []
            ok = True
            for _ in range(k):
                if not rem:
                    ok = False
                    break
                cur = [random.choice(list(rem))]
                rem.remove(cur[0])
                while len(cur) < gsize:
                    nbrs = [
                        (cr + dr, cc + dc)
                        for cr, cc in cur
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                        if (cr + dr, cc + dc) in rem
                    ]
                    nbrs = list(dict.fromkeys(nbrs))
                    if not nbrs:
                        break
                    nxt = random.choice(nbrs)
                    cur.append(nxt)
                    rem.remove(nxt)
                if len(cur) != gsize or not is_connected(cur):
                    ok = False
                    break
                sol_parts.append(sorted(cur))

            if ok and len(sol_parts) == k and len(rem) == 0:
                rows = max(r for r, c in cells) + 1
                cols = max(c for r, c in cells) + 1
                groups = []
                for i in range(k):
                    gname, ghex = GROUP_PALETTE[i % len(GROUP_PALETTE)]
                    groups.append({
                        "id": f"g_{i}",
                        "name": gname,
                        "color": ghex,
                        "target": gsize,
                        "sol": sol_parts[i],
                    })
                return {
                    "mode": "dots",
                    "title": f"구슬 {total}개를 {gsize}개씩 나머지 없이 {k}묶음으로 나누기",
                    "rows": rows,
                    "cols": cols,
                    "total": total,
                    "k": k,
                    "per_piece": gsize,
                    "allow_flip": True,
                    "target_canon": [],
                    "mask": [list(pt) for pt in cells],
                    "groups": groups,
                }

    fb_cells = [(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 2)]
    fb_sol = [[(0, 0), (1, 0)], [(0, 1), (1, 1)], [(1, 2), (2, 2)]]
    return {
        "mode": "dots",
        "title": "구슬 6개를 2개씩 나머지 없이 3묶음으로 나누기",
        "rows": 3,
        "cols": 3,
        "total": 6,
        "k": 3,
        "per_piece": 2,
        "allow_flip": True,
        "target_canon": [],
        "mask": [list(pt) for pt in fb_cells],
        "groups": [
            {"id": f"g_{i}", "name": GROUP_PALETTE[i][0], "color": GROUP_PALETTE[i][1], "target": 2, "sol": fb_sol[i]}
            for i in range(3)
        ],
    }


def render_divide_activity():
    st.subheader("✂️ 모양 나누기 (같은 모양 & n개씩 묶기)")

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        ptype = st.selectbox("나누기 유형", ["똑같은 모양으로 나누기", "구슬·점 n개씩 묶기"], key="div_ptype")
    with c2:
        level_label = st.selectbox("난이도", LEVEL_OPTIONS_SIMPLE, key="div_lv_select")
    with c3:
        st.write("")
        new_q = st.button("🎲 새 문제", use_container_width=True, key="div_new_q")

    mode_key = "congruent" if ptype.startswith("똑같은") else "dots"
    level_key = level_key_from_label(level_label)

    if (
        "div_mode" not in st.session_state
        or st.session_state.div_mode != mode_key
        or st.session_state.div_lv != level_key
        or new_q
    ):
        st.session_state.div_mode = mode_key
        st.session_state.div_lv = level_key
        st.session_state.div_data = (
            gen_congruent_puzzle(level_key)
            if mode_key == "congruent"
            else gen_dot_puzzle(level_key)
        )
        st.session_state.div_seed = random.randint(1, 999999)

    puzzle = dict(st.session_state.div_data)
    puzzle["seed"] = st.session_state.div_seed
    payload = json.dumps(puzzle)

    html_code = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
  * {{ box-sizing: border-box; user-select: none; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  body {{ margin: 0; padding: 8px; background: transparent; }}
  .wrap {{ display: flex; gap: 28px; align-items: flex-start; flex-wrap: wrap; }}
  .panel {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 18px; box-shadow: 0 4px 14px rgba(15,23,42,0.06); }}
  .panel-title {{ font-size: 17px; font-weight: 800; color: #0f172a; margin-bottom: 8px; }}
  .sub-note {{ font-size: 13px; color: #64748b; margin-bottom: 12px; line-height: 1.45; }}

  .mission-box {{
    background: #f1f5f9; border-radius: 12px; padding: 12px 14px; margin-bottom: 14px;
    font-size: 14px; font-weight: 800; color: #0f172a;
  }}

  .group-list {{ display: flex; flex-direction: column; gap: 10px; min-width: 250px; }}
  .group-card {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 12px; border-radius: 12px; border: 2px solid #e2e8f0;
    background: #f8fafc; cursor: pointer; transition: all 0.12s ease;
  }}
  .group-card.active {{ border-color: #0f172a; background: #ffffff; box-shadow: 0 4px 10px rgba(15,23,42,0.08); }}
  .swatch {{ width: 18px; height: 18px; border-radius: 5px; border: 2px solid #0f172a; flex-shrink: 0; }}
  .g-name {{ font-size: 14px; font-weight: 800; color: #0f172a; }}
  .g-stat {{ font-size: 12px; font-weight: 800; color: #334155; text-align: right; }}
  .g-stat.ok {{ color: #15803d; }}
  .g-stat.over {{ color: #dc2626; }}

  .board-box {{ display: flex; flex-direction: column; align-items: center; }}
  .action-row {{ margin-top: 12px; display: flex; gap: 8px; width: 100%; }}
  .action-row button {{
    flex: 1; padding: 9px 12px; border-radius: 10px; border: 1px solid #cbd5e1;
    background: #f8fafc; color: #0f172a; font-weight: 800; font-size: 13px; cursor: pointer;
  }}
  .action-row button:hover {{ background: #e2e8f0; }}
  .check-banner {{
    margin-top: 12px; width: 100%; padding: 11px 14px; border-radius: 10px;
    font-weight: 800; font-size: 14px; display: none;
  }}
  .check-banner.ok {{ background: #dcfce7; color: #166534; display: block; }}
  .check-banner.no {{ background: #fee2e2; color: #991b1b; display: block; }}
  .msg-hint {{
    margin-top: 8px; font-size: 13px; font-weight: 700; color: #475569; min-height: 18px;
  }}
</style>
</head>
<body>
<div class="wrap">
  <div class="panel">
    <div class="panel-title">1. 문제 조건 &amp; 조각/묶음 선택</div>
    <div class="mission-box" id="divMissionText"></div>
    <div class="sub-note" id="divGuideText"></div>
    <div class="group-list" id="divGroupList"></div>
  </div>

  <div class="panel board-box">
    <div class="panel-title">2. 나누기 판</div>
    <div class="sub-note" id="divSubBoardText"></div>
    <svg id="divBoardSvg"></svg>
    <div class="msg-hint" id="divHintText"></div>
    <div class="action-row">
      <button onclick="divClearAll()">🧹 모두 지우기</button>
      <button onclick="divCheckAnswer()">✅ 정답 확인</button>
    </div>
    <div class="check-banner" id="divCheckBanner"></div>
  </div>
</div>

<script>
const DIV_DATA = {payload};
const DIV_CELL = 54;
const DIV_PAD = 16;

let divGroups = JSON.parse(JSON.stringify(DIV_DATA.groups));
let divActiveGroupId = divGroups[0].id;
let divCellOwner = {{}};
let divIsPainting = false;
let divPaintMode = "set";

window.addEventListener("mouseup", () => {{ divIsPainting = false; }});

function divClearCheckBanner() {{
  const el = document.getElementById("divCheckBanner");
  el.className = "check-banner";
  el.style.display = "none";
  el.innerText = "";
}}

function divNorm(coords) {{
  if (!coords.length) return [];
  const minR = Math.min(...coords.map(p => p[0]));
  const minC = Math.min(...coords.map(p => p[1]));
  return coords.map(p => [p[0] - minR, p[1] - minC]).sort((a,b) => a[0]-b[0] || a[1]-b[1]);
}}

function divRot90(coords) {{
  return divNorm(coords.map(([r, c]) => [c, -r]));
}}

function divFlipCoords(coords) {{
  return divNorm(coords.map(([r, c]) => [r, -c]));
}}

function divCanonicalShape(coords, allowFlip) {{
  if (!coords.length) return "";
  const base = divNorm(coords);
  const variants = [];
  let cur = base;
  for (let i = 0; i < 4; i++) {{
    variants.push(JSON.stringify(cur));
    cur = divRot90(cur);
  }}
  if (allowFlip) {{
    cur = divFlipCoords(base);
    for (let i = 0; i < 4; i++) {{
      variants.push(JSON.stringify(cur));
      cur = divRot90(cur);
    }}
  }}
  variants.sort();
  return variants[0];
}}

function divGetGroupCells(gid) {{
  const res = [];
  for (const [k, v] of Object.entries(divCellOwner)) {{
    if (v === gid) {{
      const [r, c] = k.split(",").map(Number);
      res.push([r, c]);
    }}
  }}
  return res;
}}

function divIsConnected(cells) {{
  if (cells.length <= 1) return true;
  const set = new Set(cells.map(([r,c]) => `${{r}},${{c}}`));
  const start = cells[0];
  const visited = new Set([`${{start[0]}},${{start[1]}}`]);
  const stack = [start];
  while (stack.length > 0) {{
    const [r, c] = stack.pop();
    for (const [dr, dc] of [[-1,0],[1,0],[0,-1],[0,1]]) {{
      const nr = r + dr, nc = c + dc;
      const key = `${{nr}},${{nc}}`;
      if (set.has(key) && !visited.has(key)) {{
        visited.add(key);
        stack.push([nr, nc]);
      }}
    }}
  }}
  return visited.size === cells.length;
}}

function divBuildUnifiedShapeSVG(coords, fillColor, strokeColor, cellSize, pad, totalRows, totalCols) {{
  const set = new Set(coords.map(([r,c]) => `${{r}},${{c}}`));
  const w = totalCols * cellSize + pad * 2;
  const h = totalRows * cellSize + pad * 2;
  let parts = [];

  for (const [r, c] of coords) {{
    const x = pad + c * cellSize;
    const y = pad + r * cellSize;
    parts.push(`<rect x="${{x}}" y="${{y}}" width="${{cellSize}}" height="${{cellSize}}" rx="5" fill="${{fillColor}}" />`);
    if (set.has(`${{r-1}},${{c}}`)) parts.push(`<rect x="${{x+1}}" y="${{y-3}}" width="${{cellSize-2}}" height="6" fill="${{fillColor}}" />`);
    if (set.has(`${{r+1}},${{c}}`)) parts.push(`<rect x="${{x+1}}" y="${{y+cellSize-3}}" width="${{cellSize-2}}" height="6" fill="${{fillColor}}" />`);
    if (set.has(`${{r}},${{c-1}}`)) parts.push(`<rect x="${{x-3}}" y="${{y+1}}" width="6" height="${{cellSize-2}}" fill="${{fillColor}}" />`);
    if (set.has(`${{r}},${{c+1}}`)) parts.push(`<rect x="${{x+cellSize-3}}" y="${{y+1}}" width="6" height="${{cellSize-2}}" fill="${{fillColor}}" />`);
  }}

  for (const [r, c] of coords) {{
    const x = pad + c * cellSize;
    const y = pad + r * cellSize;
    if (!set.has(`${{r-1}},${{c}}`)) parts.push(`<line x1="${{x+1}}" y1="${{y}}" x2="${{x+cellSize-1}}" y2="${{y}}" stroke="${{strokeColor}}" stroke-width="2.5" stroke-linecap="round" />`);
    if (!set.has(`${{r+1}},${{c}}`)) parts.push(`<line x1="${{x+1}}" y1="${{y+cellSize}}" x2="${{x+cellSize-1}}" y2="${{y+cellSize}}" stroke="${{strokeColor}}" stroke-width="2.5" stroke-linecap="round" />`);
    if (!set.has(`${{r}},${{c-1}}`)) parts.push(`<line x1="${{x}}" y1="${{y+1}}" x2="${{x}}" y2="${{y+cellSize-1}}" stroke="${{strokeColor}}" stroke-width="2.5" stroke-linecap="round" />`);
    if (!set.has(`${{r}},${{c+1}}`)) parts.push(`<line x1="${{x+cellSize}}" y1="${{y+1}}" x2="${{x+cellSize}}" y2="${{y+cellSize-1}}" stroke="${{strokeColor}}" stroke-width="2.5" stroke-linecap="round" />`);
  }}

  return {{ svgInner: parts.join(""), w, h }};
}}

function divApplyCellAction(r, c, forceMode=null) {{
  const key = `${{r}},${{c}}`;
  const curOwner = divCellOwner[key];
  const mode = forceMode || ((curOwner === divActiveGroupId) ? "clear" : "set");
  if (mode === "clear") {{
    if (curOwner === divActiveGroupId) delete divCellOwner[key];
  }} else {{
    divCellOwner[key] = divActiveGroupId;
  }}
  divClearCheckBanner();
  divRenderAll();
}}

function divCheckGroupStatus(cells) {{
  const exact = cells.length === DIV_DATA.per_piece;
  const conn = divIsConnected(cells);
  if (DIV_DATA.mode === "congruent") {{
    const firstCells = divGetGroupCells(divGroups[0].id);
    const refCanon = firstCells.length === DIV_DATA.per_piece && divIsConnected(firstCells)
      ? divCanonicalShape(firstCells, DIV_DATA.allow_flip)
      : JSON.stringify(DIV_DATA.target_canon);
    const sameShape = exact && conn && (divCanonicalShape(cells, DIV_DATA.allow_flip) === refCanon);
    return {{ ok: sameShape, exact, conn, sameShape }};
  }} else {{
    return {{ ok: exact && conn, exact, conn, sameShape: true }};
  }}
}}

function divRenderGroups() {{
  const list = document.getElementById("divGroupList");
  list.innerHTML = "";

  for (const g of divGroups) {{
    const cells = divGetGroupCells(g.id);
    const stInfo = divCheckGroupStatus(cells);

    const card = document.createElement("div");
    card.className = `group-card ${{g.id === divActiveGroupId ? "active" : ""}}`;
    card.onclick = () => {{
      divActiveGroupId = g.id;
      divRenderAll();
    }};

    let statClass = "g-stat";
    let statusText = `${{cells.length}} / ${{DIV_DATA.per_piece}}개`;
    if (cells.length > DIV_DATA.per_piece) {{
      statClass += " over";
      statusText += " (초과)";
    }} else if (stInfo.ok) {{
      statClass += " ok";
      statusText += " ✓";
    }} else if (DIV_DATA.mode === "congruent" && stInfo.exact && stInfo.conn && !stInfo.sameShape) {{
      statusText += " (모양 다름)";
    }} else if (!stInfo.conn) {{
      statusText += " (이어야 함)";
    }}

    card.innerHTML = `
      <div style="display:flex; align-items:center; gap:10px;">
        <div class="swatch" style="background:${{g.color}};"></div>
        <div class="g-name">${{g.name}}</div>
      </div>
      <div class="${{statClass}}">${{statusText}}</div>
    `;
    list.appendChild(card);
  }}
}}

function divCheckAnswer() {{
  const banner = document.getElementById("divCheckBanner");
  let totalColored = 0;
  const reasons = [];

  const nonEmptyCanons = [];
  for (const g of divGroups) {{
    const cells = divGetGroupCells(g.id);
    totalColored += cells.length;
    if (cells.length !== DIV_DATA.per_piece) {{
      reasons.push(`${{g.name}}이(가) ${{cells.length}}개(목표 ${{DIV_DATA.per_piece}}개)`);
    }}
    if (!divIsConnected(cells)) {{
      reasons.push(`${{g.name}}이(가) 떨어져 있음`);
    }}
    if (DIV_DATA.mode === "congruent" && cells.length > 0 && divIsConnected(cells)) {{
      nonEmptyCanons.push(divCanonicalShape(cells, DIV_DATA.allow_flip));
    }}
  }}

  if (totalColored < DIV_DATA.total) {{
    reasons.unshift(`아직 안 나눈 칸/구슬 ${{DIV_DATA.total - totalColored}}개 남음`);
  }}

  if (DIV_DATA.mode === "congruent" && nonEmptyCanons.length >= 2) {{
    const distinct = new Set(nonEmptyCanons);
    if (distinct.size > 1) {{
      reasons.push("조각 모양이 서로 다름");
    }}
  }}

  if (totalColored === DIV_DATA.total && reasons.length === 0) {{
    banner.className = "check-banner ok";
    banner.style.display = "block";
    banner.innerText = DIV_DATA.mode === "congruent"
      ? "⭕ 맞아요! 똑같은 모양 조각들로 정확히 나눴습니다."
      : `⭕ 맞아요! ${{DIV_DATA.per_piece}}개씩 나머지 없이 ${{DIV_DATA.k}}묶음으로 정확히 나눴습니다.`;
  }} else {{
    banner.className = "check-banner no";
    banner.style.display = "block";
    banner.innerText = `❌ 틀렸어요! (${{reasons.join(", ")}})`;
  }}
}}

function divRenderBoard() {{
  const svg = document.getElementById("divBoardSvg");
  const w = DIV_DATA.cols * DIV_CELL + DIV_PAD * 2;
  const h = DIV_DATA.rows * DIV_CELL + DIV_PAD * 2;
  svg.setAttribute("width", w);
  svg.setAttribute("height", h);
  svg.setAttribute("viewBox", `0 0 ${{w}} ${{h}}`);

  let html = `<rect x="0" y="0" width="${{w}}" height="${{h}}" rx="16" fill="#0f172a" />`;

  const baseBuilt = divBuildUnifiedShapeSVG(DIV_DATA.mask, "#1e293b", "#64748b", DIV_CELL, DIV_PAD, DIV_DATA.rows, DIV_DATA.cols);
  html += baseBuilt.svgInner;

  for (const g of divGroups) {{
    const gCells = divGetGroupCells(g.id);
    if (gCells.length > 0) {{
      const gBuilt = divBuildUnifiedShapeSVG(gCells, g.color, "#0f172a", DIV_CELL, DIV_PAD, DIV_DATA.rows, DIV_DATA.cols);
      html += gBuilt.svgInner;
    }}
  }}

  if (DIV_DATA.mode === "dots") {{
    for (const [r, c] of DIV_DATA.mask) {{
      const cx = DIV_PAD + c * DIV_CELL + DIV_CELL / 2;
      const cy = DIV_PAD + r * DIV_CELL + DIV_CELL / 2;
      const owned = Boolean(divCellOwner[`${{r}},${{c}}`]);
      html += `<circle cx="${{cx}}" cy="${{cy}}" r="11" fill="${{owned ? "#ffffff" : "#f8fafc"}}" stroke="#0f172a" stroke-width="2.5" />`;
    }}
  }}

  for (const [r, c] of DIV_DATA.mask) {{
    const x = DIV_PAD + c * DIV_CELL;
    const y = DIV_PAD + r * DIV_CELL;
    html += `<rect data-r="${{r}}" data-c="${{c}}" x="${{x}}" y="${{y}}" width="${{DIV_CELL}}" height="${{DIV_CELL}}" fill="transparent" style="cursor:pointer;" />`;
  }}

  svg.innerHTML = html;

  svg.querySelectorAll("rect[data-r]").forEach(rect => {{
    const r = Number(rect.getAttribute("data-r"));
    const c = Number(rect.getAttribute("data-c"));

    rect.addEventListener("mousedown", (e) => {{
      e.preventDefault();
      divIsPainting = true;
      const curOwner = divCellOwner[`${{r}},${{c}}`];
      divPaintMode = (curOwner === divActiveGroupId) ? "clear" : "set";
      divApplyCellAction(r, c, divPaintMode);
    }});

    rect.addEventListener("mouseenter", () => {{
      if (divIsPainting) {{
        divApplyCellAction(r, c, divPaintMode);
      }}
    }});
  }});

  const disconnectedNames = divGroups
    .filter(g => !divIsConnected(divGetGroupCells(g.id)))
    .map(g => g.name);
  document.getElementById("divHintText").innerText =
    disconnectedNames.length > 0
      ? `⚠️ ${{disconnectedNames.join(", ")}} 조각/묶음의 칸이 떨어져 있어요. 이어지게 색칠해 보세요!`
      : "";
}}

function divClearAll() {{
  divCellOwner = {{}};
  divClearCheckBanner();
  divRenderAll();
}}

function divRenderAll() {{
  document.getElementById("divMissionText").innerText = DIV_DATA.title;
  if (DIV_DATA.mode === "congruent") {{
    document.getElementById("divGuideText").innerText =
      "각 조각의 모양이 서로 똑같도록(돌리거나 뒤집어도 가능) 칸을 클릭하거나 드래그해서 색칠하세요.";
    document.getElementById("divSubBoardText").innerText =
      `전체 ${{DIV_DATA.total}}칸을 똑같은 모양 조각 ${{DIV_DATA.k}}개로 나누세요 (한 조각당 ${{DIV_DATA.per_piece}}칸).`;
  }} else {{
    document.getElementById("divGuideText").innerText =
      `이어진 칸을 드래그해서 구슬을 ${{DIV_DATA.per_piece}}개씩 묶어 보세요.`;
    document.getElementById("divSubBoardText").innerText =
      `구슬 ${{DIV_DATA.total}}개를 ${{DIV_DATA.per_piece}}개씩 남김없이 ${{DIV_DATA.k}}묶음으로 나누세요.`;
  }}
  divRenderGroups();
  divRenderBoard();
}}

divRenderAll();
</script>
</body>
</html>
"""

    components.html(html_code, height=620, scrolling=True)


# =========================================================
# 3. 모양 겹치기 데이터 및 생성기
# =========================================================
SCENE_PUZZLES = {
    "하": [
        {
            "id": "low_1",
            "title": "두 그림을 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "해 그림", "kind": "clear_sun"},
            "card2": {"label": "구름 그림", "kind": "clear_cloud"},
            "correct": "clear_sun_cloud",
            "options": [
                {"id": "clear_sun_cloud", "kind": "clear_sun_cloud"},
                {"id": "clear_mountain_sea", "kind": "clear_mountain_sea"},
                {"id": "clear_tree_star", "kind": "clear_tree_star"},
                {"id": "clear_sea_island", "kind": "clear_sea_island"},
            ],
        },
        {
            "id": "low_2",
            "title": "두 그림을 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "산 그림", "kind": "clear_mountain"},
            "card2": {"label": "해 그림", "kind": "clear_sun"},
            "correct": "clear_mountain_sun",
            "options": [
                {"id": "clear_mountain_sun", "kind": "clear_mountain_sun"},
                {"id": "clear_cloud_rain", "kind": "clear_cloud_rain"},
                {"id": "clear_tree_star", "kind": "clear_tree_star"},
                {"id": "clear_sea_island", "kind": "clear_sea_island"},
            ],
        },
        {
            "id": "low_3",
            "title": "두 그림을 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "나무 그림", "kind": "clear_tree"},
            "card2": {"label": "별 그림", "kind": "clear_star"},
            "correct": "clear_tree_star",
            "options": [
                {"id": "clear_tree_star", "kind": "clear_tree_star"},
                {"id": "clear_sun_cloud", "kind": "clear_sun_cloud"},
                {"id": "clear_mountain_sea", "kind": "clear_mountain_sea"},
                {"id": "clear_cloud_rain", "kind": "clear_cloud_rain"},
            ],
        },
        {
            "id": "low_4",
            "title": "두 그림을 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "구름 그림", "kind": "clear_cloud"},
            "card2": {"label": "빗방울 그림", "kind": "clear_rain"},
            "correct": "clear_cloud_rain",
            "options": [
                {"id": "clear_cloud_rain", "kind": "clear_cloud_rain"},
                {"id": "clear_mountain_sun", "kind": "clear_mountain_sun"},
                {"id": "clear_tree_star", "kind": "clear_tree_star"},
                {"id": "clear_sea_island", "kind": "clear_sea_island"},
            ],
        },
        {
            "id": "low_5",
            "title": "두 그림을 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "산 그림", "kind": "clear_mountain"},
            "card2": {"label": "바다 그림", "kind": "clear_sea"},
            "correct": "clear_mountain_sea",
            "options": [
                {"id": "clear_mountain_sea", "kind": "clear_mountain_sea"},
                {"id": "clear_sun_cloud", "kind": "clear_sun_cloud"},
                {"id": "clear_tree_star", "kind": "clear_tree_star"},
                {"id": "clear_cloud_rain", "kind": "clear_cloud_rain"},
            ],
        },
        {
            "id": "low_6",
            "title": "두 그림을 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "바다 그림", "kind": "clear_sea"},
            "card2": {"label": "섬 그림", "kind": "clear_island"},
            "correct": "clear_sea_island",
            "options": [
                {"id": "clear_sea_island", "kind": "clear_sea_island"},
                {"id": "clear_mountain_sun", "kind": "clear_mountain_sun"},
                {"id": "clear_tree_star", "kind": "clear_tree_star"},
                {"id": "clear_cloud_rain", "kind": "clear_cloud_rain"},
            ],
        },
        {
            "id": "low_7",
            "title": "두 그림을 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "나무 그림", "kind": "clear_tree"},
            "card2": {"label": "해 그림", "kind": "clear_sun"},
            "correct": "clear_tree_sun",
            "options": [
                {"id": "clear_tree_sun", "kind": "clear_tree_sun"},
                {"id": "clear_mountain_sea", "kind": "clear_mountain_sea"},
                {"id": "clear_cloud_rain", "kind": "clear_cloud_rain"},
                {"id": "clear_sea_island", "kind": "clear_sea_island"},
            ],
        },
        {
            "id": "low_8",
            "title": "두 그림을 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "해 그림", "kind": "clear_sun"},
            "card2": {"label": "별 그림", "kind": "clear_star"},
            "correct": "clear_sun_star",
            "options": [
                {"id": "clear_sun_star", "kind": "clear_sun_star"},
                {"id": "clear_mountain_sea", "kind": "clear_mountain_sea"},
                {"id": "clear_tree_star", "kind": "clear_tree_star"},
                {"id": "clear_cloud_rain", "kind": "clear_cloud_rain"},
            ],
        },
    ],
    "중": [
        {
            "id": "mid_1",
            "title": "두 그림을 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "산 그림", "kind": "clear_mountain"},
            "card2": {"label": "바다 그림", "kind": "clear_sea"},
            "correct": "clear_mountain_sea",
            "options": [
                {"id": "clear_mountain_sea", "kind": "clear_mountain_sea"},
                {"id": "clear_mountain_sea_sun", "kind": "clear_mountain_sea_sun"},
                {"id": "clear_mountain_sun", "kind": "clear_mountain_sun"},
                {"id": "clear_sea_island", "kind": "clear_sea_island"},
            ],
        },
        {
            "id": "mid_2",
            "title": "두 그림을 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "바다 그림", "kind": "clear_sea"},
            "card2": {"label": "섬 그림", "kind": "clear_island"},
            "correct": "clear_sea_island",
            "options": [
                {"id": "clear_sea_island", "kind": "clear_sea_island"},
                {"id": "clear_sea_island_sun", "kind": "clear_sea_island_sun"},
                {"id": "clear_mountain_sea", "kind": "clear_mountain_sea"},
                {"id": "clear_sea_only", "kind": "clear_sea"},
            ],
        },
        {
            "id": "mid_3",
            "title": "두 그림을 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "나무 그림", "kind": "clear_tree"},
            "card2": {"label": "구름 그림", "kind": "clear_cloud"},
            "correct": "clear_tree_cloud",
            "options": [
                {"id": "clear_tree_cloud", "kind": "clear_tree_cloud"},
                {"id": "clear_tree_sun", "kind": "clear_tree_sun"},
                {"id": "clear_tree_star", "kind": "clear_tree_star"},
                {"id": "clear_tree_cloud_sun", "kind": "clear_tree_cloud_sun"},
            ],
        },
        {
            "id": "mid_4",
            "title": "두 그림을 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "해 그림", "kind": "clear_sun"},
            "card2": {"label": "구름 그림", "kind": "clear_cloud"},
            "correct": "clear_sun_cloud",
            "options": [
                {"id": "clear_sun_cloud", "kind": "clear_sun_cloud"},
                {"id": "clear_sun_cloud_rain", "kind": "clear_sun_cloud_rain"},
                {"id": "clear_cloud_rain", "kind": "clear_cloud_rain"},
                {"id": "clear_sun_star", "kind": "clear_sun_star"},
            ],
        },
        {
            "id": "mid_5",
            "title": "두 그림을 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "산 그림", "kind": "clear_mountain"},
            "card2": {"label": "해 그림", "kind": "clear_sun"},
            "correct": "clear_mountain_sun",
            "options": [
                {"id": "clear_mountain_sun", "kind": "clear_mountain_sun"},
                {"id": "clear_mountain_sea_sun", "kind": "clear_mountain_sea_sun"},
                {"id": "clear_mountain_sea", "kind": "clear_mountain_sea"},
                {"id": "clear_mountain_only", "kind": "clear_mountain"},
            ],
        },
        {
            "id": "mid_6",
            "title": "두 그림을 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "나무 그림", "kind": "clear_tree"},
            "card2": {"label": "별 그림", "kind": "clear_star"},
            "correct": "clear_tree_star",
            "options": [
                {"id": "clear_tree_star", "kind": "clear_tree_star"},
                {"id": "clear_tree_sun", "kind": "clear_tree_sun"},
                {"id": "clear_tree_cloud", "kind": "clear_tree_cloud"},
                {"id": "clear_sun_star", "kind": "clear_sun_star"},
            ],
        },
        {
            "id": "mid_7",
            "title": "두 그림을 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "구름 그림", "kind": "clear_cloud"},
            "card2": {"label": "빗방울 그림", "kind": "clear_rain"},
            "correct": "clear_cloud_rain",
            "options": [
                {"id": "clear_cloud_rain", "kind": "clear_cloud_rain"},
                {"id": "clear_sun_cloud_rain", "kind": "clear_sun_cloud_rain"},
                {"id": "clear_sun_cloud", "kind": "clear_sun_cloud"},
                {"id": "clear_cloud_only", "kind": "clear_cloud"},
            ],
        },
        {
            "id": "mid_8",
            "title": "두 그림을 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "나무 그림", "kind": "clear_tree"},
            "card2": {"label": "해 그림", "kind": "clear_sun"},
            "correct": "clear_tree_sun",
            "options": [
                {"id": "clear_tree_sun", "kind": "clear_tree_sun"},
                {"id": "clear_tree_cloud_sun", "kind": "clear_tree_cloud_sun"},
                {"id": "clear_tree_cloud", "kind": "clear_tree_cloud"},
                {"id": "clear_tree_star", "kind": "clear_tree_star"},
            ],
        },
    ],
    "상": [
        {
            "id": "high_1",
            "title": "왼쪽 카드 위에 오른쪽 카드를 그대로 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "뒤 카드 (해)", "kind": "occ_sun_base"},
            "card2": {"label": "앞 카드 (구름)", "kind": "occ_cloud_front"},
            "correct": "occ_cloud_over_sun",
            "options": [
                {"id": "occ_cloud_over_sun", "kind": "occ_cloud_over_sun"},
                {"id": "occ_sun_over_cloud", "kind": "occ_sun_over_cloud"},
                {"id": "occ_sun_cloud_apart", "kind": "occ_sun_cloud_apart"},
                {"id": "occ_cloud_only", "kind": "occ_cloud_front"},
            ],
        },
        {
            "id": "high_2",
            "title": "왼쪽 카드 위에 오른쪽 카드를 그대로 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "뒤 카드 (산)", "kind": "occ_mountain_base"},
            "card2": {"label": "앞 카드 (바다)", "kind": "occ_sea_front"},
            "correct": "occ_sea_over_mountain",
            "options": [
                {"id": "occ_sea_over_mountain", "kind": "occ_sea_over_mountain"},
                {"id": "occ_mountain_over_sea", "kind": "occ_mountain_over_sea"},
                {"id": "occ_sea_over_mountain_sun", "kind": "occ_sea_over_mountain_sun"},
                {"id": "occ_sea_only", "kind": "occ_sea_front"},
            ],
        },
        {
            "id": "high_3",
            "title": "왼쪽 카드 위에 오른쪽 카드를 그대로 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "뒤 카드 (해와 산)", "kind": "occ_mountain_sun_base"},
            "card2": {"label": "앞 카드 (구름)", "kind": "occ_cloud_front"},
            "correct": "occ_cloud_over_mountain_sun",
            "options": [
                {"id": "occ_cloud_over_mountain_sun", "kind": "occ_cloud_over_mountain_sun"},
                {"id": "occ_sun_over_cloud_mountain", "kind": "occ_sun_over_cloud_mountain"},
                {"id": "occ_mountain_sun_only", "kind": "occ_mountain_sun_base"},
                {"id": "occ_sea_over_mountain_sun", "kind": "occ_sea_over_mountain_sun"},
            ],
        },
        {
            "id": "high_4",
            "title": "두 투명 그림을 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "산과 바다 그림", "kind": "clear_mountain_sea"},
            "card2": {"label": "해와 구름 그림", "kind": "clear_sun_cloud_top"},
            "correct": "clear_full_scenery",
            "options": [
                {"id": "clear_full_scenery", "kind": "clear_full_scenery"},
                {"id": "clear_mountain_sea_sun", "kind": "clear_mountain_sea_sun"},
                {"id": "clear_mountain_sea_cloud", "kind": "clear_mountain_sea_cloud"},
                {"id": "clear_sea_island_sun", "kind": "clear_sea_island_sun"},
            ],
        },
        {
            "id": "high_5",
            "title": "왼쪽 카드 위에 오른쪽 카드를 그대로 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "뒤 카드 (구름)", "kind": "occ_cloud_front"},
            "card2": {"label": "앞 카드 (해)", "kind": "occ_sun_base"},
            "correct": "occ_sun_over_cloud",
            "options": [
                {"id": "occ_sun_over_cloud", "kind": "occ_sun_over_cloud"},
                {"id": "occ_cloud_over_sun", "kind": "occ_cloud_over_sun"},
                {"id": "occ_sun_cloud_apart", "kind": "occ_sun_cloud_apart"},
                {"id": "clear_sun_cloud", "kind": "clear_sun_cloud"},
            ],
        },
        {
            "id": "high_6",
            "title": "왼쪽 카드 위에 오른쪽 카드를 그대로 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "뒤 카드 (바다)", "kind": "occ_sea_front"},
            "card2": {"label": "앞 카드 (산)", "kind": "occ_mountain_base"},
            "correct": "occ_mountain_over_sea",
            "options": [
                {"id": "occ_mountain_over_sea", "kind": "occ_mountain_over_sea"},
                {"id": "occ_sea_over_mountain", "kind": "occ_sea_over_mountain"},
                {"id": "clear_mountain_sea", "kind": "clear_mountain_sea"},
                {"id": "occ_sea_over_mountain_sun", "kind": "occ_sea_over_mountain_sun"},
            ],
        },
        {
            "id": "high_7",
            "title": "두 투명 그림을 겹치면 어떤 모양이 될까요?",
            "card1": {"label": "바다와 섬 그림", "kind": "clear_sea_island"},
            "card2": {"label": "해 그림", "kind": "clear_sun_left"},
            "correct": "clear_sea_island_sun",
            "options": [
                {"id": "clear_sea_island_sun", "kind": "clear_sea_island_sun"},
                {"id": "clear_sea_island", "kind": "clear_sea_island"},
                {"id": "clear_mountain_sea_sun", "kind": "clear_mountain_sea_sun"},
                {"id": "clear_full_scenery", "kind": "clear_full_scenery"},
            ],
        },
    ],
}


def make_shuffled_queue(level_key: str):
    puzzles = SCENE_PUZZLES[level_key][:]
    random.shuffle(puzzles)
    return puzzles


def pop_next_puzzle(level_key: str):
    if "ov_queues" not in st.session_state:
        st.session_state.ov_queues = {}

    queue = st.session_state.ov_queues.get(level_key, [])
    if not queue:
        queue = make_shuffled_queue(level_key)

    raw = queue.pop(0)
    st.session_state.ov_queues[level_key] = queue

    draw_on_paper = random.random() < 0.15
    opts = raw["options"][:]
    random.shuffle(opts)
    correct_obj = next(o for o in raw["options"] if o["id"] == raw["correct"])
    return {
        "id": raw["id"],
        "title": raw["title"],
        "card1": raw["card1"],
        "card2": raw["card2"],
        "correct_id": raw["correct"],
        "correct_obj": correct_obj,
        "draw_on_paper": draw_on_paper,
        "options": opts,
    }


def render_overlap_activity():
    st.subheader("🏔️ 모양 겹치기")

    c1, c2 = st.columns([3, 1])
    with c1:
        level_label = st.selectbox("난이도", LEVEL_OPTIONS_OVERLAP, index=0, key="ov_lv_select")
    with c2:
        st.write("")
        new_q = st.button("🎲 새 문제", use_container_width=True, key="ov_new_q")

    level_key = level_key_from_label(level_label)

    if (
        "ov_lv" not in st.session_state
        or st.session_state.ov_lv != level_key
        or new_q
    ):
        st.session_state.ov_lv = level_key
        st.session_state.ov_data = pop_next_puzzle(level_key)
        st.session_state.ov_seed = random.randint(1, 999999)

    puzzle = dict(st.session_state.ov_data)
    puzzle["seed"] = st.session_state.ov_seed
    payload = json.dumps(puzzle)

    html_template = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
  * { box-sizing: border-box; user-select: none; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  body { margin: 0; padding: 8px; background: transparent; }
  .wrap { display: flex; flex-direction: column; gap: 16px; }
  .panel { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 18px; box-shadow: 0 4px 14px rgba(15,23,42,0.06); }
  .mission { font-size: 16px; font-weight: 800; color: #0f172a; margin-bottom: 14px; }

  .cards-row { display: flex; gap: 18px; align-items: center; flex-wrap: wrap; justify-content: center; }
  .card-box {
    display: flex; flex-direction: column; align-items: center;
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 12px;
  }
  .card-title { font-size: 13px; font-weight: 800; color: #334155; margin-bottom: 8px; }
  .plus-sign { font-size: 26px; font-weight: 900; color: #0f172a; }

  .paper-box {
    background: #fffbeb; border: 2px dashed #f59e0b; border-radius: 14px;
    padding: 18px; text-align: center; color: #92400e; font-weight: 900; font-size: 16px;
  }

  .options-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-top: 8px;
  }
  .opt-card {
    display: flex; flex-direction: column; align-items: center; gap: 8px;
    padding: 12px; border-radius: 14px; border: 2px solid #cbd5e1;
    background: #f8fafc; cursor: pointer; transition: all 0.12s ease;
  }
  .opt-card:hover { background: #f1f5f9; }
  .opt-card.selected { border-color: #0f172a; background: #e0f2fe; }
  .opt-num { font-size: 13px; font-weight: 800; color: #334155; }

  .btn-row { display: flex; gap: 10px; margin-top: 14px; }
  .btn-row button {
    padding: 11px 16px; border-radius: 10px; border: 1px solid #cbd5e1;
    background: #0f172a; color: #ffffff; font-weight: 800; font-size: 14px; cursor: pointer;
  }
  .btn-row button:hover { background: #1e293b; }

  .banner {
    margin-top: 14px; padding: 12px 16px; border-radius: 12px;
    font-weight: 800; font-size: 14px; display: none;
  }
  .banner.ok { background: #dcfce7; color: #166534; display: block; }
  .banner.no { background: #fee2e2; color: #991b1b; display: block; }

  .reveal-box {
    margin-top: 14px; padding: 16px; border-radius: 14px;
    border: 2px solid #16a34a; background: #f0fdf4;
    display: none; flex-direction: column; align-items: center; gap: 8px;
  }
  .reveal-title { font-size: 14px; font-weight: 900; color: #166534; }
</style>
</head>
<body>
<div class="wrap">
  <div class="panel">
    <div class="mission" id="ovMissionText"></div>
    <div class="cards-row">
      <div class="card-box">
        <div class="card-title" id="ovC1Title"></div>
        <div id="ovC1Art"></div>
      </div>
      <div class="plus-sign">＋</div>
      <div class="card-box">
        <div class="card-title" id="ovC2Title"></div>
        <div id="ovC2Art"></div>
      </div>
    </div>
  </div>

  <div class="panel">
    <div id="ovPaperPrompt" class="paper-box" style="display:none;">
      직접 종이에 그려보세요!
    </div>
    <div id="ovOptionsGrid" class="options-grid"></div>

    <div class="btn-row">
      <button onclick="ovCheckSceneAnswer()">✅ 정답 확인</button>
    </div>
    <div class="banner" id="ovResultBanner"></div>
    <div class="reveal-box" id="ovRevealBox">
      <div class="reveal-title">정답</div>
      <div id="ovRevealArt"></div>
    </div>
  </div>
</div>

<script>
const OV_DATA = __PAYLOAD_JSON__;
let ovSelectedOptId = null;

function ovDrawSceneSVG(kind, w = 160, h = 115) {
  const clearFrame = `<rect x="0" y="0" width="${w}" height="${h}" rx="12" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.5" />`;

  const sun = (cx = w * 0.78, cy = h * 0.25, r = 15) =>
    `<circle cx="${cx}" cy="${cy}" r="${r}" fill="#facc15" stroke="#eab308" stroke-width="2" />`;

  const cloud = (cx = w * 0.45, cy = h * 0.36, s = 1.05) => `
    <g transform="translate(${cx},${cy}) scale(${s})">
      <circle cx="-14" cy="4" r="11" fill="#ffffff" stroke="#94a3b8" stroke-width="1.6" />
      <circle cx="0" cy="-2" r="14" fill="#ffffff" stroke="#94a3b8" stroke-width="1.6" />
      <circle cx="15" cy="4" r="11" fill="#ffffff" stroke="#94a3b8" stroke-width="1.6" />
      <rect x="-14" y="2" width="29" height="12" rx="5" fill="#ffffff" />
      <line x1="-14" y1="15" x2="15" y2="15" stroke="#94a3b8" stroke-width="1.6" />
    </g>
  `;

  const greenMountain = (x1 = w * 0.12, y1 = h * 0.78, x2 = w * 0.36, y2 = h * 0.30, x3 = w * 0.60, y3 = h * 0.78) =>
    `<polygon points="${x1},${y1} ${x2},${y2} ${x3},${y3}" fill="#22c55e" stroke="#15803d" stroke-width="1.5" stroke-linejoin="round" />`;

  const doubleGreenMountain = `
    <polygon points="${w * 0.10},${h * 0.84} ${w * 0.34},${h * 0.34} ${w * 0.58},${h * 0.84}" fill="#22c55e" stroke="#15803d" stroke-width="1.4" />
    <polygon points="${w * 0.36},${h * 0.84} ${w * 0.58},${h * 0.44} ${w * 0.82},${h * 0.84}" fill="#16a34a" stroke="#15803d" stroke-width="1.4" />
  `;

  const seaBand = `
    <rect x="8" y="${h * 0.64}" width="${w - 16}" height="${h * 0.25}" rx="8" fill="#38bdf8" stroke="#0284c7" stroke-width="1.2" />
    <path d="M 18 ${h * 0.76} Q 38 ${h * 0.70} 58 ${h * 0.76} T 98 ${h * 0.76} T 138 ${h * 0.76}" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" />
  `;

  const island = (cx = w * 0.66, cy = h * 0.72) => `
    <ellipse cx="${cx}" cy="${cy}" rx="25" ry="9" fill="#fcd34d" stroke="#d97706" stroke-width="1.2" />
    <path d="M ${cx} ${cy - 2} L ${cx} ${cy - 22}" stroke="#78350f" stroke-width="3.5" />
    <path d="M ${cx} ${cy - 22} Q ${cx - 12} ${cy - 27} ${cx - 18} ${cy - 17}" fill="none" stroke="#16a34a" stroke-width="3.5" stroke-linecap="round" />
    <path d="M ${cx} ${cy - 22} Q ${cx + 12} ${cy - 27} ${cx + 18} ${cy - 17}" fill="none" stroke="#16a34a" stroke-width="3.5" stroke-linecap="round" />
  `;

  const tree = (cx = w * 0.38, cy = h * 0.64) => `
    <rect x="${cx - 5}" y="${cy}" width="10" height="22" rx="2" fill="#78350f" />
    <circle cx="${cx}" cy="${cy - 10}" r="20" fill="#16a34a" />
    <circle cx="${cx - 12}" cy="${cy - 4}" r="14" fill="#22c55e" />
    <circle cx="${cx + 12}" cy="${cy - 4}" r="14" fill="#22c55e" />
  `;

  const star = (cx, cy, r = 13) =>
    `<polygon points="${cx},${cy - r} ${cx + r * 0.35},${cy - r * 0.3} ${cx + r},${cy - r * 0.25} ${cx + r * 0.45},${cy + r * 0.25} ${cx + r * 0.6},${cy + r} ${cx},${cy + r * 0.6} ${cx - r * 0.6},${cy + r} ${cx - r * 0.45},${cy + r * 0.25} ${cx - r},${cy - r * 0.25} ${cx - r * 0.35},${cy - r * 0.3}" fill="#fde047" stroke="#eab308" stroke-width="1.5" />`;

  const rain = `
    <line x1="${w * 0.38}" y1="${h * 0.56}" x2="${w * 0.33}" y2="${h * 0.78}" stroke="#2563eb" stroke-width="3" stroke-linecap="round" />
    <line x1="${w * 0.50}" y1="${h * 0.56}" x2="${w * 0.45}" y2="${h * 0.78}" stroke="#2563eb" stroke-width="3" stroke-linecap="round" />
    <line x1="${w * 0.62}" y1="${h * 0.56}" x2="${w * 0.57}" y2="${h * 0.78}" stroke="#2563eb" stroke-width="3" stroke-linecap="round" />
  `;

  const standaloneRain = `
    <path d="M ${w * 0.34} ${h * 0.34} C ${w * 0.30} ${h * 0.44}, ${w * 0.26} ${h * 0.48}, ${w * 0.26} ${h * 0.54} A 8 8 0 0 0 ${w * 0.42} ${h * 0.54} C ${w * 0.42} ${h * 0.48}, ${w * 0.38} ${h * 0.44}, ${w * 0.34} ${h * 0.34} Z" fill="#38bdf8" stroke="#0284c7" stroke-width="1.5" />
    <path d="M ${w * 0.54} ${h * 0.38} C ${w * 0.50} ${h * 0.48}, ${w * 0.46} ${h * 0.52}, ${w * 0.46} ${h * 0.58} A 8 8 0 0 0 ${w * 0.62} ${h * 0.58} C ${w * 0.62} ${h * 0.52}, ${w * 0.58} ${h * 0.48}, ${w * 0.54} ${h * 0.38} Z" fill="#38bdf8" stroke="#0284c7" stroke-width="1.5" />
    <path d="M ${w * 0.72} ${h * 0.34} C ${w * 0.68} ${h * 0.44}, ${w * 0.64} ${h * 0.48}, ${w * 0.64} ${h * 0.54} A 8 8 0 0 0 ${w * 0.80} ${h * 0.54} C ${w * 0.80} ${h * 0.48}, ${w * 0.76} ${h * 0.44}, ${w * 0.72} ${h * 0.34} Z" fill="#38bdf8" stroke="#0284c7" stroke-width="1.5" />
  `;

  let body = clearFrame;

  if (kind === "clear_sun") body += sun(w * 0.32, h * 0.46, 17);
  else if (kind === "clear_sun_left") body += sun(w * 0.26, h * 0.30, 15);
  else if (kind === "clear_cloud") body += cloud(w * 0.66, h * 0.48, 1.05);
  else if (kind === "clear_rain") body += standaloneRain;
  else if (kind === "clear_sun_cloud") body += sun(w * 0.32, h * 0.46, 17) + cloud(w * 0.66, h * 0.48, 1.05);
  else if (kind === "clear_sun_cloud_rain") body += sun(w * 0.30, h * 0.42, 16) + cloud(w * 0.64, h * 0.42, 1.0) + rain;
  else if (kind === "clear_sun_star") body += sun(w * 0.32, h * 0.48, 17) + star(w * 0.68, h * 0.48, 14);
  else if (kind === "clear_cloud_rain") body += cloud(w * 0.50, h * 0.36, 1.05) + rain;

  else if (kind === "clear_mountain") body += greenMountain(w * 0.12, h * 0.78, w * 0.36, h * 0.30, w * 0.60, h * 0.78);
  else if (kind === "clear_mountain_only") body += greenMountain(w * 0.12, h * 0.78, w * 0.36, h * 0.30, w * 0.60, h * 0.78);
  else if (kind === "clear_mountain_sun") body += greenMountain(w * 0.12, h * 0.78, w * 0.36, h * 0.30, w * 0.60, h * 0.78) + sun(w * 0.76, h * 0.32, 15);
  else if (kind === "clear_sea") body += seaBand;
  else if (kind === "clear_sea_only") body += seaBand;
  else if (kind === "clear_mountain_sea") body += greenMountain(w * 0.12, h * 0.64, w * 0.36, h * 0.24, w * 0.60, h * 0.64) + seaBand;
  else if (kind === "clear_mountain_sea_sun") body += greenMountain(w * 0.12, h * 0.64, w * 0.36, h * 0.24, w * 0.60, h * 0.64) + seaBand + sun(w * 0.78, h * 0.28, 14);
  else if (kind === "clear_mountain_sea_cloud") body += greenMountain(w * 0.12, h * 0.64, w * 0.36, h * 0.24, w * 0.60, h * 0.64) + seaBand + cloud(w * 0.72, h * 0.28, 0.95);

  else if (kind === "clear_island") body += island(w * 0.66, h * 0.64);
  else if (kind === "clear_sea_island") body += seaBand + island(w * 0.66, h * 0.64);
  else if (kind === "clear_sea_island_sun") body += seaBand + island(w * 0.66, h * 0.64) + sun(w * 0.26, h * 0.30, 15);

  else if (kind === "clear_tree") body += tree(w * 0.36, h * 0.64);
  else if (kind === "clear_star") body += star(w * 0.72, h * 0.34, 14);
  else if (kind === "clear_tree_star") body += tree(w * 0.36, h * 0.64) + star(w * 0.72, h * 0.34, 14);
  else if (kind === "clear_tree_sun") body += tree(w * 0.36, h * 0.64) + sun(w * 0.74, h * 0.32, 15);
  else if (kind === "clear_tree_cloud") body += tree(w * 0.36, h * 0.64) + cloud(w * 0.70, h * 0.36, 1.0);
  else if (kind === "clear_tree_cloud_sun") body += tree(w * 0.34, h * 0.64) + sun(w * 0.78, h * 0.26, 13) + cloud(w * 0.64, h * 0.40, 0.95);

  else if (kind === "occ_sun_base") body += sun(w * 0.56, h * 0.45, 20);
  else if (kind === "occ_cloud_front") body += cloud(w * 0.46, h * 0.48, 1.25);
  else if (kind === "occ_cloud_over_sun") body += sun(w * 0.56, h * 0.45, 20) + cloud(w * 0.46, h * 0.48, 1.25);
  else if (kind === "occ_sun_over_cloud") body += cloud(w * 0.46, h * 0.48, 1.25) + sun(w * 0.56, h * 0.45, 20);
  else if (kind === "occ_sun_cloud_apart") body += sun(w * 0.78, h * 0.30, 15) + cloud(w * 0.34, h * 0.52, 1.15);

  else if (kind === "occ_mountain_base") body += doubleGreenMountain;
  else if (kind === "occ_sea_front") body += seaBand;
  else if (kind === "occ_sea_over_mountain") body += doubleGreenMountain + seaBand;
  else if (kind === "occ_mountain_over_sea") body += seaBand + doubleGreenMountain;
  else if (kind === "occ_sea_over_mountain_sun") body += doubleGreenMountain + seaBand + sun(w * 0.80, h * 0.25, 14);

  else if (kind === "occ_mountain_sun_base") body += sun(w * 0.56, h * 0.45, 20) + greenMountain(w * 0.10, h * 0.84, w * 0.30, h * 0.42, w * 0.50, h * 0.84);
  else if (kind === "occ_cloud_over_mountain_sun") body += sun(w * 0.56, h * 0.45, 20) + greenMountain(w * 0.10, h * 0.84, w * 0.30, h * 0.42, w * 0.50, h * 0.84) + cloud(w * 0.46, h * 0.48, 1.25);
  else if (kind === "occ_sun_over_cloud_mountain") body += cloud(w * 0.46, h * 0.48, 1.25) + sun(w * 0.56, h * 0.45, 20) + greenMountain(w * 0.10, h * 0.84, w * 0.30, h * 0.42, w * 0.50, h * 0.84);

  else if (kind === "clear_sun_cloud_top") body += sun(w * 0.78, h * 0.26, 14) + cloud(w * 0.56, h * 0.28, 0.95);
  else if (kind === "clear_full_scenery") body += greenMountain(w * 0.12, h * 0.64, w * 0.36, h * 0.24, w * 0.60, h * 0.64) + seaBand + sun(w * 0.78, h * 0.26, 14) + cloud(w * 0.56, h * 0.28, 0.95);

  return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${body}</svg>`;
}

function ovRenderOptions() {
  const grid = document.getElementById("ovOptionsGrid");
  const paperBox = document.getElementById("ovPaperPrompt");
  if (OV_DATA.draw_on_paper) {
    paperBox.style.display = "block";
    grid.style.display = "none";
    return;
  }

  paperBox.style.display = "none";
  grid.style.display = "grid";
  grid.innerHTML = "";

  OV_DATA.options.forEach((opt, idx) => {
    const card = document.createElement("div");
    card.className = `opt-card ${ovSelectedOptId === opt.id ? "selected" : ""}`;
    card.onclick = () => {
      ovSelectedOptId = opt.id;
      ovRenderOptions();
    };
    card.innerHTML = `
      <div class="opt-num">${idx + 1}번</div>
      ${ovDrawSceneSVG(opt.kind, 150, 105)}
    `;
    grid.appendChild(card);
  });
}

function ovCheckSceneAnswer() {
  const banner = document.getElementById("ovResultBanner");
  const reveal = document.getElementById("ovRevealBox");
  const revealArt = document.getElementById("ovRevealArt");

  reveal.style.display = "flex";
  revealArt.innerHTML = ovDrawSceneSVG(OV_DATA.correct_obj.kind, 210, 145);

  if (OV_DATA.draw_on_paper) {
    banner.className = "banner ok";
    banner.innerText = "정답 확인";
    return;
  }

  if (ovSelectedOptId === OV_DATA.correct_id) {
    banner.className = "banner ok";
    banner.innerText = "⭕ 맞아요!";
  } else {
    banner.className = "banner no";
    banner.innerText = "❌ 틀렸어요!";
  }
}

document.getElementById("ovMissionText").innerText = OV_DATA.title;
document.getElementById("ovC1Title").innerText = OV_DATA.card1.label;
document.getElementById("ovC2Title").innerText = OV_DATA.card2.label;
document.getElementById("ovC1Art").innerHTML = ovDrawSceneSVG(OV_DATA.card1.kind, 165, 115);
document.getElementById("ovC2Art").innerHTML = ovDrawSceneSVG(OV_DATA.card2.kind, 165, 115);
ovRenderOptions();
</script>
</body>
</html>
"""

    html_code = html_template.replace("__PAYLOAD_JSON__", payload)
    components.html(html_code, height=600, scrolling=True)


# =========================================================
# 메인 내비게이션
# =========================================================
if "facto_activity" not in st.session_state:
    st.session_state.facto_activity = "모양 맞춰넣기"

st.title("📐 팩토 창의사고력 수학")

nav_cols = st.columns(3)
for idx, act_name in enumerate(ACTIVITY_OPTIONS):
    is_active = st.session_state.facto_activity == act_name
    with nav_cols[idx]:
        if st.button(
            act_name,
            use_container_width=True,
            type="primary" if is_active else "secondary",
            key=f"nav_btn_{idx}",
        ):
            st.session_state.facto_activity = act_name
            st.rerun()

st.divider()

current_activity = st.session_state.facto_activity
if current_activity == "모양 맞춰넣기":
    render_make_activity()
elif current_activity == "모양 나누기":
    render_divide_activity()
else:
    render_overlap_activity()