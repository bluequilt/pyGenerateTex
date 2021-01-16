import jinja2
from pathlib import Path
import re

latex_jinja_env = jinja2.Environment(
    block_start_string="\BLOCK{",
    block_end_string="}",
    variable_start_string="\VAR{",
    variable_end_string="}",
    comment_start_string="\#{",
    comment_end_string="}",
    line_statement_prefix="%%",
    line_comment_prefix="%#",
    trim_blocks=True,
    autoescape=False,
    loader=jinja2.FileSystemLoader(Path(".").absolute()),
)


def add_style(content, styles):
    if styles["bf"]:
        return "\\textbf{%s}" % (content,)
    return content


class Geometry(object):
    """默认单位为毫米
变量名参考：书P143-144"""

    def __init__(self, initial):
        for attr, value in initial.items():
            setattr(self, attr, value)

    @property
    def textwidth(self):
        return self.paperwidth - self.left - self.right

    @property
    def textheight(self):
        return self.paperheight - self.top - self.bottom

    @property
    def header(self):
        return ",".join(
            f"{k}={round(getattr(self, k), 2)}mm"
            for k in ("paperwidth", "paperheight", "top", "bottom", "left", "right")
        )

    # ========本项目特有的========
    @property
    def intro_width(self):
        return self.textwidth * (9 / 16) - 2

    @property
    def picbox_width(self):
        return self.textwidth * (7 / 16) - 2

    @property
    def picbox_half_width(self):
        return self.picbox_width / 2 - 2


def valign_words(content, align):
    return {
        "b": "\\rule{0mm}{\\fill}\\\\" + content,
        "t": content + "\\\\\\rule{0mm}{\\fill}",
        "c": content,
    }[align]


def halign_words(content, align, single_row):
    content = (
        "".join(("\\smallskip ", content, "\\smallskip")) if single_row else content
    )
    return {
        "r": "\\raggedleft " + content,
        "c": "\\centering " + content,
        "l": "\\raggedright " + content,
        "j": content,
    }[align]


def add_table_style(content, styles, single_row):
    content = add_style(content, styles)
    content = valign_words(content, styles["v"])
    return halign_words(content, styles["h"], single_row)


class TableEnv(object):
    def __init__(self, initial):
        col_lens = initial["col_lens"]
        initial.pop("col_lens")
        for attr, value in initial.items():
            setattr(self, attr, value)
        # ========计算单元格宽度========
        total_len = self.tablewidth
        # self.col_lens存的都是绝对长度，col_lens是混杂的原始输入
        self.col_lens = [0] * len(col_lens)
        # 首先把col_lens中的固定长度存储到self.col_lens中
        for index, item in enumerate(
            filter(lambda abc: isinstance(abc, str), col_lens)
        ):
            fixed_len = float(re.search(r"(\d+(\.\d+)?)mm", item).group(1))
            total_len -= fixed_len
            self.col_lens[index] = fixed_len
        # 得到所有浮动单元格的相对长度的总和
        flex_unit = sum(filter(lambda item: not isinstance(item, str), col_lens))
        # 计算所有浮动单元格的绝对长度
        self.col_lens = tuple(
            (item if item > 0 else (col_lens[index] / flex_unit) * total_len)
            for (index, item) in enumerate(self.col_lens)
        )
        # 如果一开始每个单元格的宽度都是固定的，则校准总宽度
        self.tablewidth = sum(self.col_lens) if flex_unit == 0 else self.tablewidth

    def fullwidth(self, index):
        # 模板内手写列号从1开始
        return self.col_lens[index - 1]

    def innerwidth(self, index):
        # 模板内手写列号从1开始
        return self.col_lens[index - 1] - 2 * self.tabcolsep

    def _multicol_width(self, cols):
        "cols是有两个值的元组"
        return sum(self.innerwidth(i) for i in range(cols[0], cols[1] + 1))

    def cell(self, content, col, **styles):
        curstyles = self.default_style.copy()
        curstyles.update(styles)
        return "\\parbox[c][][s]{%smm}{%s}" % (
            round(self.innerwidth(col), 2),
            add_table_style(content, curstyles, True),
        )

    def mc(self, content, cols, **styles):
        "cols是有两个值的元组，开始列号和结束列号"
        curstyles = self.default_style.copy()
        curstyles.update(styles)
        return "\multicolumn{%d}{|c|}{\parbox[c][][c]{%smm}{%s}}" % (
            cols[1] - cols[0] + 1,
            round(self._multicol_width(cols), 2),
            add_table_style(content, curstyles, True),
        )

    def mcrb(self, cols):
        "multi_column_row_blank，用于多行多列合并的非首行"
        return "\multicolumn{%d}{|c|}{}" % (cols[1] - cols[0] + 1,)

    def mcr(self, content, cols, row_count, **styles):
        """cols是有两个值的元组，开始列号和结束列号
halign: t, c, b
valign: l, c, r, j"""
        curstyles = self.default_style.copy()
        curstyles.update(styles)
        return "\multicolumn{%d}{|c|}{\multirow{%d}*{\parbox[c][][c]{%smm}{%s}}}" % (
            cols[1] - cols[0] + 1,
            row_count,
            round(self._multicol_width(cols), 2),
            add_table_style(content, curstyles, False),
        )

    def mr(self, content, col, row_count, **styles):
        curstyles = self.default_style.copy()
        curstyles.update(styles)
        return "\multirow{%d}*{\parbox[c][][c]{%smm}{%s}}" % (
            row_count,
            round(self.innerwidth(col), 2),
            add_table_style(content, curstyles, False),
        )

