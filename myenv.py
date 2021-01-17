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

