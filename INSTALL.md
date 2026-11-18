# 安装指南

本 skill 遵循 **Agent Skills 开放标准**：核心是一个带 YAML frontmatter 的 `SKILL.md`，加上可选的 `scripts/`、`references/`。文件内容在所有支持该标准的 AI 工具间通用，**无需修改**，只需放进所用工具能发现的 skill 目录。

## 一句话安装（推荐，发给你的 AI 即可）

> 帮我从 `https://github.com/fszhang134888-lab/aligned-roster-docx` 安装这个 skill，按你自己的 skill 安装规范放到对应目录。装完请按本仓库 `INSTALL.md` 的「安装后自检」逐项核对，三项全过再报告安装成功。

这段话不含任何具体路径或工具名——每家 AI 都知道自己的 skill 该放哪，让它自己判断最不容易出错。

## 各工具的 skill 目录（供参考）

装的时候不必死记，上面那句话让 AI 自己查即可。下表仅供参考：

| 工具 | 个人级（全局可用） | 项目级 |
|---|---|---|
| WorkBuddy | `~/.workbuddy/skills/` | `<项目>/.workbuddy/skills/` |
| Claude Code | `~/.claude/skills/` | `<项目>/.claude/skills/` |
| Codex | `~/.agents/skills/` | `<项目>/.agents/skills/` |
| Cursor | `~/.cursor/skills/` | `<项目>/.cursor/skills/` |

补充：
- Cursor 同时兼容 `~/.claude/skills/`、`~/.agents/skills/`、`~/.codex/skills/`，放到这些目录也能被发现。
- 目录里要放的是**整个 skill 文件夹**（文件夹名即 skill 名 `aligned-roster-docx`），里面有 `SKILL.md` 和 `scripts/` 等，不要只把 `SKILL.md` 一个文件丢进去。
- 新装的 skill 若没立刻出现，重启一下对应工具（部分工具会自动检测）。

## 手动安装（git clone）

```bash
git clone https://github.com/fszhang134888-lab/aligned-roster-docx.git
```

把 clone 下来的 `aligned-roster-docx` 文件夹整个移到你所用工具的 skill 目录（见上表），确保最终结构是：

```
<skill 目录>/aligned-roster-docx/
├── SKILL.md
├── INSTALL.md
├── LICENSE
├── README.md
├── references/
│   ├── alignment-playbook.md
│   └── edsdk-pitfalls.md
└── scripts/
    ├── docx2pdf.ps1
    ├── name_format.py
    └── verify_layout.py
```

## 安装后自检（三项全过才算成功）

1. **身份核对**：`SKILL.md` 的 frontmatter 里 `name: aligned-roster-docx`，描述含"严格列对齐"字样。
2. **文件完整**：`scripts/` 下有 `name_format.py`、`verify_layout.py`、`docx2pdf.ps1`，`references/` 下有两个 `.md`。
3. **功能自测**：在 `scripts/` 目录运行 `python name_format.py`，输出应包含：
   - `'李明' -> '李\u3000明'`（两字名中间是全角空格）
   - `'阿依古丽*买买提' -> '阿依古丽\u2022买买提'`（星号归一化成实心圆点 U+2022）

三项任一不符，说明装错或文件不全，重新安装。

## 依赖

运行脚本需要：`python-docx`、`openpyxl`、`pypinyin`、`pypdfium2`、`numpy`、`Pillow`；`verify_layout.py` 另需 `pdfplumber`。`docx2pdf.ps1` 需 Windows + Microsoft Word。

## 固定版本（可选）

想锁定版本、避免"装到最新版"碰运气，用 release tag 或 commit：

```bash
git clone https://github.com/fszhang134888-lab/aligned-roster-docx.git
cd aligned-roster-docx
git checkout v1.0.0        # 或某个具体 commit
```
