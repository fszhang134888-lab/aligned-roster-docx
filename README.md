# aligned-roster-docx

制作与修订「姓名/班级需严格列对齐」的中文公文类 docx（公假条、活动证明、参赛名单、值班表、公示名单等），并转换为 PDF 交付。

这是一个 [WorkBuddy / Claude Code 风格的 Agent Skill](https://www.workbuddy.cn/)，把"照着扫描件复刻一份排版严格的中文名单公文"这套流程固化下来：参照件识别 → 名单解析 → 制表位严格对齐 → 字体鉴定 → Word 转 PDF → 像素级验证。

## 为什么需要它

用空格给中文名单"补对齐"永远对不齐——空格宽度随字体和渲染器变化，实测有 3~6pt 漂移，肉眼可见。本 skill 的核心是用 OOXML 原生制表位（`w:tabs`）做列对齐，跨 Word/WPS 渲染一致，并提供一整套验证与避坑方案。

## 目录结构

```
.
├── SKILL.md                          # 主文件：适用场景、铁律、标准流程、命名规范
├── references/
│   ├── alignment-playbook.md         # 制表位布局计算、中文字体度量、扫描件字体鉴定
│   └── edsdk-pitfalls.md             # editor_sdk 的静默失败坑位与解法
└── scripts/
    ├── docx2pdf.ps1                  # Word COM 高保真转 PDF（先删旧文件防静默不写）
    ├── name_format.py                # 姓名显示格式化：两字名插全角空格、民族名连接符归一化
    └── verify_layout.py              # PDF 列对齐 / 分页验证（列签名聚类 + 停靠点驱动两种模式）
```

## 三条铁律

1. **严格对齐只用制表位**，永远不用空格或全角空格补列距。
2. **图片型 PDF**（无文字层）用渲染成图 + 视觉读版式，别死磕 `extract_text`。
3. **交付前走"改 → 转 PDF → 像素测量"闭环**，编辑器里看着齐不算齐。

## 姓名显示规范

- 两字中文名展示时中间插一个全角空格 U+3000（`李明` → `李 明`）。
- 少数民族姓名的连接符统一为实心圆点 U+2022（`阿依古丽•买买提`），禁止用星号 `*`。
- 两者都只改**显示**，排序/去重键仍用原始姓名。

## 用法

作为一个 Agent Skill，放到 `~/.workbuddy/skills/aligned-roster-docx/` 即可被自动发现调用。独立脚本也可直接用：

```bash
# 姓名格式化（可作为模块 import）
python scripts/name_format.py

# docx 转 PDF（Windows + Word，须经 PowerShell）
powershell -ExecutionPolicy Bypass -File scripts/docx2pdf.ps1 -Src input.docx -Dst output.pdf

# 验证列对齐（默认列签名聚类）
python scripts/verify_layout.py output.pdf
# 姓名含内部空格时用停靠点驱动模式（坐标为页面 x = 左边距 + 制表位）
python scripts/verify_layout.py output.pdf --stops 216.4,278.4,340.4,402.4,464.4
```

依赖：`python-docx`、`openpyxl`、`pypinyin`、`pypdfium2`、`numpy`、`Pillow`（验证模式另需 `pdfplumber`）；转 PDF 需本机安装 Microsoft Word。

## 许可

MIT — 见 [LICENSE](LICENSE)。
