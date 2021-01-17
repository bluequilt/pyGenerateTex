import re
from itertools import *


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


def add_style(content, styles):
    if styles["bf"]:
        return "\\textbf{%s}" % (content,)
    return content


def add_table_style(content, styles, single_row):
    content = add_style(content, styles)
    content = valign_words(content, styles["v"])
    return halign_words(content, styles["h"], single_row)


class TableEnv(object):
    @staticmethod
    def _cal_head_lines(raw_table):
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
        return blines_latex

    def __init__(self, initial):
        for attr, value in initial["env"].items():
            setattr(self, attr, value)
        self.speical_cells = {"vb": None, "v": None, "mrb": ""}
        self._set_col_lens(initial["col_lens"], self.tablewidth)
        self._set_col_styles(initial["col_styles"])
        self._set_head(initial["head"])

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

    def _set_col_lens(self, raw_list, tablewidth):
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
                paras.pop("type")
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
                if t in self.speical_cells:
                    cell_words = self.speical_cells[t]
                elif t == "mcrb":
                    cell_words = self.mcrb(paras["cols"])
                else:
                    cell_words = getattr(self, t)(**paras)
                row_list.append(cell_words)
            result.append(row_list)
        return result

    def _set_head(self, raw_table):

        # 多列单元格实际上少一列
        table_contents = tuple(
            tuple(cell for cell in row if cell is not None)
            for row in self._cal_head_array(raw_table)
        )
        head_latex = "\n".join(
            "%s\\\\%s" % ("&\n".join(row), bline)
            for row, bline in zip(table_contents, self._cal_head_lines(raw_table))
        )
        self.head = "\\firsthline\n%s\n" % (head_latex,)

    def _set_col_styles(self, col_styles):
        cur_styles_bycol = []
        for styles in col_styles:
            curstyles = self.default_style.copy()
            curstyles.update(styles)
            cur_styles_bycol.append(curstyles)
        self.col_styles = cur_styles_bycol

    def get_table_content(self, array2d):
        if len(array2d) == 0:
            return "\\lasthline\n"
        result = "\\\\\n\\hline\n".join(
            "&\n".join(
                self.cell(cell, col_i, **self.col_styles[col_i])
                for (col_i, cell) in enumerate(row)
            )
            for row in array2d
        )
        return "\\hline\n%s\\\\\n\\lasthline\n" % (result,)

    def get_table(self, array2d):
        begin_env = "\\begin{tabular}{|%s|}\n" % ("|".join(["c"] * len(self.col_lens)),)
        return "".join(
            (begin_env, self.head, self.get_table_content(array2d), "\\end{tabular}\n",)
        )

