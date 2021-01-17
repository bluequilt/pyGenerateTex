import subprocess
from os import system
from json import load as load_json

#
from myenv import *
from tableenv import *

template = latex_jinja_env.get_template("template.tex")


def generate():
    with open("geometry.json", "r", encoding="utf-8") as geometry_f:
        geometry_settings = load_json(geometry_f)
    geo = Geometry(geometry_settings)
    # ========读取表格设置========
    with open("tables.json", "r", encoding="utf-8") as htable_f:
        table_settings = load_json(htable_f)
    table_settings["check_table"]["env"]["tablewidth"] = geo.textwidth - 4
    # ========读取数据库========
    with open("db.json", "r", encoding="utf-8") as db_f:
        db_dict = load_json(db_f)
    # ========建立总渲染参数，注入简单变量========
    render_dict = {}
    render_dict["geometry"] = geo
    render_dict["intro_width"] = geo.textwidth * (9 / 16) - 4
    render_dict["picbox_width"] = geo.textwidth * (7 / 16) - 4
    render_dict["picbox_half_width"] = render_dict["picbox_width"] / 2 - 2
    render_dict.update(db_dict)
    # ========注入计算内容========
    tableenv = TableEnv(table_settings["check_table"])
    render_dict["check_table"] = {
        "content": tableenv.get_table(db_dict["检查项目"]),
        "tabcolsep": tableenv.tabcolsep,
    }
    with open("pygtex.tex", "w", encoding="utf-8") as f:
        f.write(template.render(render_dict))


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
