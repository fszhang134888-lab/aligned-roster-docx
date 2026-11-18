# -*- coding: utf-8 -*-
"""姓名显示格式化 — 两字中文姓名中间插入全角空格 U+3000。

项目硬性约定：`李明` 在名单中显示为 `李 明`；三字及以上保持不变。

关键原则：**只改显示，不改数据键**。排序 / 去重 / 正文取名一律用原始
无空格姓名，只在写入名单行拼制表符那一步调用 display_name()，否则
同一个人的 `李明` 与 `李 明` 会被当成两条记录。

用法:
    from name_format import display_name
    line = "\t".join(display_name(n) for n in group)
"""
import re

IDEOSPACE = "\u3000"  # 全角空格 U+3000，即"中文的空格"
BULLET = "\u2022"     # 实心圆点，少数民族姓名连接符（用户要的"加粗的一点"）

# 仅当姓名恰好是两个汉字时插空格；含字母/符号/空格的（如民族名音译）不处理
_TWO_HANZI = re.compile(r"^[\u4e00-\u9fff]{2}$")
# 非标准连接符 -> 统一成 U+2022：星号/间隔号/中点/日文中点等
_BAD_SEP = re.compile(r"[*·・‧∙・﹒．▪]")


def normalize_sep(name):
    """少数民族姓名连接符归一化：把 * · 等替换成实心圆点 U+2022。"""
    return _BAD_SEP.sub(BULLET, str(name))


def display_name(name):
    """姓名显示格式化：先归一化民族名连接符，再给两字名插全角空格。

    注意：排序/去重键用原始姓名，仅在写入名单行/正文展示时调用本函数。
    """
    s = normalize_sep(name)
    if _TWO_HANZI.match(s):
        return s[0] + IDEOSPACE + s[1]
    return s


if __name__ == "__main__":
    # 自测
    cases = ["李明", "王芳华", "张国强", "阿依古丽*买买提",
             "木尔扎别克·阿力", "阿依古丽•买买提", "O'Neil", "欧阳娜娜"]
    for c in cases:
        print(repr(c), "->", repr(display_name(c)))
