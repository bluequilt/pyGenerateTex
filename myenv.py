import jinja2
from pathlib import Path


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
# def latex_kv(obj, attr, precision=2):
#     return f"{attr}={round(getattr(obj, attr), precision)}"
# latex_jinja_env.filters["keyvalue"] = latex_kv


class LTCEnv(object):
    def __init__(self, initial=None, manual=None):
        tempvar = {}
        tempvar.update(initial or {})
        tempvar.update(manual or {})
        for attr, value in tempvar.items():
            setattr(self, attr, value)


class Geometry(LTCEnv):
    """默认单位为毫米
变量名参考：书P143-144"""

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

