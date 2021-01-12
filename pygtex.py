import jinja2
from pathlib import Path
import subprocess
from os import system

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
template = latex_jinja_env.get_template("template.tex")


def generate():
    with open("pygtex.tex", "w", encoding="utf-8") as f:
        f.write(template.render({"section1": "Long Form", "section2": "Short Form"}))


def main(topdf=False, clear_tmp=False):
    generate()
    if topdf:
        compile_command = "latexmk -pdf pygtex.tex"
        compile_process = subprocess.Popen(
            compile_command, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        # 编译期间可以干点别的事
        print("证明异步运行！！！")
        compile_process.wait()
        if clear_tmp:
            system("latexmk -c")


main()
