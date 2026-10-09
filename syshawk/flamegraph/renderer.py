"""Render sampled stacks as a self-contained HTML flame graph."""

from __future__ import annotations
import json


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>🦅 SysHawk — CPU Flame Graph</title>
<style>
  body { margin: 0; background: #1e1e2e; color: #cdd6f4; font-family: -apple-system, "Segoe UI", sans-serif; }
  h1   { text-align: center; padding: 18px 0 4px; font-size: 18px; font-weight: 500; color: #89b4fa; }
  p.sub { text-align: center; color: #6c7086; font-size: 12px; margin: 0 0 16px; }
  #chart { width: 100%; overflow-x: auto; }
  canvas { display: block; margin: 0 auto; cursor: crosshair; }
  #tooltip {
    position: fixed; background: #313244; border: 1px solid #45475a;
    padding: 6px 10px; border-radius: 6px; font-size: 12px; pointer-events: none;
    display: none; color: #cdd6f4; max-width: 320px; word-break: break-all;
  }
</style>
</head>
<body>
<h1>🦅 SysHawk — CPU Flame Graph</h1>
<p class="sub">Hover over a frame to inspect. Width ∝ CPU samples.</p>
<div id="chart"><canvas id="fg"></canvas></div>
<div id="tooltip"></div>
<script>
const RAW = __STACKS_JSON__;

// Parse folded stacks into a tree
function buildTree(stacks) {
  const root = { name: "root", value: 0, children: {} };
  for (const [stack, count] of Object.entries(stacks)) {
    const parts = stack.split(";");
    let node = root;
    node.value += count;
    for (const part of parts.slice(1)) {
      if (!node.children[part]) node.children[part] = { name: part, value: 0, children: {} };
      node = node.children[part];
      node.value += count;
    }
  }
  return root;
}

// Flatten tree into renderable frames
function flatten(node, x, width, depth, frames) {
  frames.push({ name: node.name, x, width, depth, value: node.value });
  const total = node.value;
  let cx = x;
  for (const child of Object.values(node.children)) {
    const w = width * (child.value / total);
    flatten(child, cx, w, depth + 1, frames);
    cx += w;
  }
  return frames;
}

const COLORS = [
  "#f38ba8","#fab387","#f9e2af","#a6e3a1","#89dceb","#89b4fa","#cba6f7","#eba0ac"
];
function color(name, depth) {
  let h = 0; for (const c of name) h = (h * 31 + c.charCodeAt(0)) & 0xffff;
  return COLORS[h % COLORS.length];
}

const tree = buildTree(RAW);
const canvas = document.getElementById("fg");
const tooltip = document.getElementById("tooltip");
const ctx = canvas.getContext("2d");

const W = Math.min(window.innerWidth - 32, 1200);
const ROW = 22;
const frames = flatten(tree, 0, W, 0, []);
const maxDepth = Math.max(...frames.map(f => f.depth));
const H = (maxDepth + 2) * ROW;
canvas.width = W; canvas.height = H;

function draw() {
  ctx.clearRect(0, 0, W, H);
  for (const f of frames) {
    if (f.width < 1) continue;
    const y = f.depth * ROW;
    ctx.fillStyle = color(f.name, f.depth);
    ctx.fillRect(f.x + 0.5, y + 0.5, f.width - 1, ROW - 1);
    if (f.width > 40) {
      ctx.fillStyle = "#1e1e2e";
      ctx.font = "11px monospace";
      ctx.fillText(
        f.name.length > (f.width / 7) ? f.name.slice(0, Math.floor(f.width / 7) - 1) + "…" : f.name,
        f.x + 4, y + 15
      );
    }
  }
}
draw();

canvas.addEventListener("mousemove", e => {
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  const hit = frames.find(f => mx >= f.x && mx <= f.x + f.width && my >= f.depth * ROW && my < (f.depth + 1) * ROW);
  if (hit) {
    tooltip.style.display = "block";
    tooltip.style.left = (e.clientX + 12) + "px";
    tooltip.style.top  = (e.clientY + 12) + "px";
    const pct = ((hit.value / tree.value) * 100).toFixed(1);
    tooltip.innerHTML = `<b>${hit.name}</b><br>samples: ${hit.value} (${pct}%)`;
  } else {
    tooltip.style.display = "none";
  }
});
canvas.addEventListener("mouseleave", () => tooltip.style.display = "none");
</script>
</body>
</html>
"""


def render_html(stacks: dict[str, int], output_path: str) -> None:
    """Write a self-contained HTML flame graph to *output_path*."""
    html = _HTML_TEMPLATE.replace("__STACKS_JSON__", json.dumps(stacks))
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(html)
