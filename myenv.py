import jinja2
from pathlib import Path
import re
from itertools import *

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


def list_or(*lists):
    return tuple(any(item) for item in zip(*lists))


def list_and(*lists):
    return tuple(all(item) for item in zip(*lists))


def add_table_style(content, styles, single_row):
    content = add_style(content, styles)
    content = valign_words(content, styles["v"])
    return halign_words(content, styles["h"], single_row)


class TableEnv(object):
    def __init__(self, initial):
        for attr, value in initial["env"].items():
            setattr(self, attr, value)
        self.speical_cells = {"vb": None, "v": None, "mrb": ""}
        self._cal_col_lens(initial["col_lens"], self.tablewidth)
        self._cal_head(initial["head"])

    def fullwidth(self, index):
        return self.col_lens[index]

    def innerwidth(self, index):
        return self.col_lens[index] - 2 * self.tabcolsep

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

    def mcrb(self, cols, **styles):
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

    def _cal_col_lens(self, raw_list, tablewidth):
        # ========计算单元格宽度========
        total_len = tablewidth
        # self.col_lens存的都是绝对长度，raw_list是混杂的原始输入
        self.col_lens = [0] * len(raw_list)
        # 首先把raw_list中的固定长度存储到self.col_lens中
        for index, item in enumerate(
            filter(lambda abc: isinstance(abc, str), raw_list)
        ):
            fixed_len = float(re.search(r"(\d+(\.\d+)?)mm", item).group(1))
            total_len -= fixed_len
            self.col_lens[index] = fixed_len
        # 得到所有浮动单元格的相对长度的总和
        flex_unit = sum(filter(lambda item: not isinstance(item, str), raw_list))
        # 计算所有浮动单元格的绝对长度
        self.col_lens = tuple(
            (item if item > 0 else (raw_list[index] / flex_unit) * total_len)
            for (index, item) in enumerate(self.col_lens)
        )
        # 如果一开始每个单元格的宽度都是固定的，则校准总宽度
        self.tablewidth = sum(self.col_lens) if flex_unit == 0 else tablewidth

    def _cal_head_array(self, raw_table):
        result = []
        for row in raw_table:
            row_list = []
            for col_i, cell in enumerate(row):
                t = cell["type"]
                paras = self.head_style.copy()
                paras.update(cell)
                if t in ("cell", "mr"):
                    paras["col"] = col_i
                elif t in ("mc", "mcr"):
                    paras["cols"] = (
                        col_i,
                        col_i
                        + sum(
                            1
                            for j in takewhile(
                                lambda i: i["type"] == "v", row[col_i + 1 :]
                            )
                        ),
                    )
                elif t == "mcrb":
                    paras["cols"] = (
                        col_i,
                        col_i
                        + sum(
                            1
                            for j in takewhile(
                                lambda i: i["type"] == "vb", row[col_i + 1 :]
                            )
                        ),
                    )
                row_list.append(
                    self.speical_cells[t]
                    if t in self.speical_cells
                    else getattr(self, t)(**paras)
                )
            result.append(row_list)
        return result

    def _cal_head(self, raw_table):
        # 计算划线
        blines_latex = []
        for row_i, row in enumerate(raw_table):
            # 本行是多行单元格的首行
            bline1 = (cell["type"] in ("mcr", "mr", "v") for cell in row)
            # 本行和下一行都是多行单元格的非首行
            bline2 = (cell["type"] in ("mcrb", "mrb", "vb") for cell in row)
            bline3 = (
                [False] * len(row)
                if row_i == len(raw_table) - 1
                else [
                    cell["type"] in ("mcrb", "mrb", "vb")
                    for cell in raw_table[row_i + 1]
                ]
            )
            # 这个列表里的True是不要划线的地方，False是要划线的地方
            bline = list_or(bline1, list_and(bline2, bline3))
            groups = groupby(range(len(bline)), key=lambda i: bline[i])
            groups = tuple((k, tuple(v)) for k, v in groups)
            # bline_latex只是一行的所有间断线
            # "datalist[0]+1"是因为latex认为的列号从1开始
            bline_latex = "".join(
                (
                    "\\hline"
                    if len(datalist) == len(bline)
                    else "\\cline{%s-%s}" % (datalist[0] + 1, datalist[-1] + 1)
                )
                for key, datalist in filter(lambda item: not item[0], groups)
            )
            blines_latex.append(f"\n{bline_latex}")
        # 表头的最后一行没有线，因为表格有可能没有数据，数据区看情况决定是否是lasthline
        blines_latex[-1] = ""
        # 多列单元格实际上少一列
        table_contents = tuple(
            tuple(cell for cell in row if cell is not None)
            for row in self._cal_head_array(raw_table)
        )
        head_latex = "\n".join(
            "%s\\\\%s" % ("&\n".join(row), bline)
            for row, bline in zip(table_contents, blines_latex)
        )
        self.head = "\\firsthline\n%s\n" % (head_latex,)

    def get_table_content(self, array2d, styles_bycol):
        if len(array2d) == 0:
            return "\\lasthline\n"
        # 省略的样式采用默认设置，字典合并的写法只能在3.9以上的版本优化
        cur_styles_bycol = []
        for styles in styles_bycol:
            curstyles = self.default_style.copy()
            curstyles.update(styles)
            cur_styles_bycol.append(curstyles)
        #
        result = "\\\\\n\\hline\n".join(
            "&\n".join(
                self.cell(cell, col_i, **cur_styles_bycol[col_i])
                for (col_i, cell) in enumerate(row)
            )
            for row in array2d
        )
        return "\\hline\n%s\\\\\n\\lasthline\n" % (result,)

    def get_table(self, array2d, styles_bycol):
        begin_env = "\\begin{tabular}{|%s|}\n" % ("|".join(["c"] * len(self.col_lens)),)
        return "".join(
            (
                begin_env,
                self.head,
                self.get_table_content(array2d, styles_bycol),
                "\\end{tabular}\n",
            )
        )

