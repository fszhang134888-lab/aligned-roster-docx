#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""verify_layout.py — 验证名单类 PDF 的列对齐与分页。

用法: python verify_layout.py <pdf路径> [--stops <页面绝对停靠点,逗号分隔>]
      python verify_layout.py <pdf路径> --rows N

做三件事:
  1. 逐文本行测量"墨块列"起始 x 坐标 (pt)，跨行比对 -> 报告每列的位置离散度
     (对齐合格: 离散度 < 2pt; 用空格补齐的方案通常有 3~6pt 漂移)
  2. 报告每页内容底部位置 vs 可用区底部 (页高-下边距)，判断"写满没有"
  3. 输出每页文本行数，辅助确认分页点

两种列校验模式:
  * 默认: "列签名聚类" —— 自动识别名单行，适合普通名单。
  * --stops: "停靠点驱动" —— 给定页面绝对停靠点(左边距+制表位)，逐行把每个
    停靠点匹配到最近的墨块起点。适合姓名含"两字名中间全角空格"的文档:
    像素检测会把 `李 明` 拆成两个墨块，污染列签名聚类；停靠点驱动模式下
    姓名首字仍精确落在停靠点上，第二个墨块离下一停靠点足够远，不受影响。

停靠点换算: 页面 x = 左边距 + 段落制表位。例: 左边距 62.4pt + 制表位
154/216/278/340/402 -> --stops 216.4,278.4,340.4,402.4,464.4

依赖: pypdfium2, numpy, Pillow
"""
import sys
import numpy as np
import pypdfium2 as pdfium


def analyze(pdf_path, stops=None):
    pdf = pdfium.PdfDocument(pdf_path)
    print(f"pages: {len(pdf)}")
    all_cols = []          # 所有名单行的列起点（用于跨页离散度统计）
    for pi in range(len(pdf)):
        page = pdf[pi]
        pw, ph = page.get_size()
        img = page.render(scale=3).to_pil().convert("L")
        a = np.array(img)
        H, W = a.shape
        dark = a < 128

        # --- 文本行 band 检测 ---
        rowsum = dark.sum(axis=1)
        bands, in_b = [], False
        for y in range(H):
            if rowsum[y] > 3 and not in_b:
                s, in_b = y, True
            elif rowsum[y] <= 3 and in_b:
                bands.append((s, y - 1))
                in_b = False
        if in_b:
            bands.append((s, H - 1))

        usable_bottom = ph - 68.0  # 默认下边距 2.4cm=68pt；如不同按实际改
        print(f"--- page {pi+1}: {len(bands)} text bands, "
              f"content bottom = {bands[-1][1]/3:.0f}pt / usable {usable_bottom:.0f}pt "
              f"({100*(bands[-1][1]/3)/usable_bottom:.0f}% full)")

        for s, e in bands:
            if e - s < 8:
                continue
            sub = dark[s:e + 1, :]
            colhas = sub.any(axis=0)
            # 墨块 run
            runs, in_r = [], False
            for x in range(W):
                if colhas[x] and not in_r:
                    rs, in_r = x, True
                elif not colhas[x] and in_r:
                    if x - rs > 4:
                        runs.append((rs, x - 1))
                    in_r = False
            # 合并同一字符/姓名的相邻 run (间距 < ~6.7pt 视为同一字块)
            merged = []
            for r in runs:
                if merged and r[0] - merged[-1][1] < 20:
                    merged[-1] = (merged[-1][0], r[1])
                else:
                    merged.append(r)
            starts = [round(m[0] / 3, 1) for m in merged]
            if len(starts) >= 4:
                all_cols.append((starts, s / 3))
            print(f"  y={s/3:6.1f}  cols={starts}")

    # --- 列对齐统计 ---
    if stops:
        _report_by_stops(all_cols, stops)
    else:
        _report_by_signature(all_cols)


def _report_by_signature(all_cols):
    """默认模式: 按列位置签名聚类，取最大组作为名单行。"""
    if not all_cols:
        print("\nno candidate rows detected (need rows with >=4 ink columns)")
        return
    from collections import Counter
    def sig(cols):
        return tuple(round(v / 10) * 10 for v in cols)
    groups = Counter(sig(c) for c, _ in all_cols if len(c) >= 4)
    best_sig, best_n = groups.most_common(1)[0]
    roster = [(c, y) for c, y in all_cols if len(c) >= 4 and sig(c) == best_sig]
    cols_only = [c for c, _ in roster]
    ncol = len(best_sig)
    print(f"\n=== alignment report ({len(roster)} roster rows [largest column-signature group], {ncol} columns) ===")
    worst = 0.0
    for ci in range(ncol):
        vals = [c[ci] for c in cols_only]
        spread = max(vals) - min(vals)
        worst = max(worst, spread)
        print(f"  col{ci+1}: mean={np.mean(vals):7.1f}pt  spread={spread:5.1f}pt")
    print(f"  worst column spread: {worst:.1f}pt -> {'PASS (<2pt)' if worst < 2 else 'FAIL (>=2pt, 列有漂移，检查是否用了空格补齐)'}")
    print("  (注: <2pt 内为字形左侧 bearing 正常差异; 空格补齐方案的漂移通常 3~6pt)")
    print("  (若名单用了'两字名中间全角空格'导致误报，改用 --stops 模式)")


def _report_by_stops(all_cols, stops):
    """停靠点驱动: 每行把每个停靠点匹配到最近墨块起点，统计跨行偏差。"""
    if not all_cols:
        print("\nno candidate rows detected")
        return
    # 名单行判定: 停靠点间隔通常 >=60pt, 正文/落款行的墨块是连续排布, 不可能在
    # 多个相隔很远的停靠点上同时"严格命中"。要求至少 MIN_HIT 个停靠点的偏差 < 3pt。
    TOL = 3.0       # 严格命中阈值(pt)
    MIN_HIT = 3     # 至少这么多个停靠点严格命中才认作名单行
    roster = []
    for c, y in all_cols:
        hits = [min((abs(v - s) for v in c), default=1e9) < TOL for s in stops]
        if sum(hits) >= MIN_HIT:
            roster.append((c, y))
    print(f"\n=== alignment report (STOP-DRIVEN, {len(roster)} roster rows of "
          f"{len(all_cols)} candidates, {len(stops)} stops) ===")
    if not roster:
        print("  no roster rows recognized (check --stops coordinates: "
              "page x = left margin + tab stop)")
        return
    worst = 0.0
    for ci, stop in enumerate(stops):
        matched = []   # 仅统计该停靠点"严格命中"的行, 避免尾行/空列拉偏
        for cols, _ in roster:
            nearest = min(cols, key=lambda v: abs(v - stop))
            if abs(nearest - stop) < TOL:
                matched.append(nearest - stop)
        if not matched:
            print(f"  stop{ci+1}@{stop:g}pt: (no hits)")
            continue
        spread = max(matched) - min(matched)
        worst = max(worst, spread)
        print(f"  stop{ci+1}@{stop:g}pt: n={len(matched):3d}  mean|dev|={np.mean([abs(m) for m in matched]):4.1f}pt  "
              f"spread={spread:4.1f}pt")
    # 合格线 3pt: 墨块起始 x 含字形左侧 bearing 差异, 不同汉字天然浮动可达 2~3pt,
    # 但制表位停靠精度其实 <=1pt(见 mean|dev|)。>3pt 才说明真的用了空格补齐在漂移。
    print(f"  worst stop spread: {worst:.1f}pt -> {'PASS (<3pt)' if worst < 3 else 'FAIL (>=3pt)'}")
    print("  (停靠点 = 页面左边距 + 段落制表位; 只统计多个停靠点同时命中的名单行)")
    print("  (判定看 mean|dev|: <=1pt 为制表位真齐; spread 2~3pt 是字形 left bearing 正常浮动)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    pdf_path = sys.argv[1]
    stops = None
    if "--stops" in sys.argv:
        i = sys.argv.index("--stops")
        if i + 1 >= len(sys.argv):
            print("ERROR: --stops needs a comma-separated list of x coordinates (pt)")
            sys.exit(2)
        try:
            stops = [float(v) for v in sys.argv[i + 1].split(",")]
        except ValueError as ex:
            print("ERROR: bad --stops value:", ex)
            sys.exit(2)
    analyze(pdf_path, stops=stops)
