import subprocess
from os import system
from myenv import *
from json import load as load_json

template = latex_jinja_env.get_template("template.tex")


def generate():
    with open("geometry.json", "r", encoding="utf-8") as geometry_f:
        geometry_settings = load_json(geometry_f)
    geo = Geometry(geometry_settings)
    # ========ddd========
    with open("htable.json", "r", encoding="utf-8") as htable_f:
        htable_settings = load_json(htable_f)
    htable_settings["tablewidth"] = geo.textwidth
    tableenv = TableEnv(htable_settings)
    # ========ddd========
    with open("db.json", "r", encoding="utf-8") as db_f:
        db_dict = load_json(db_f)
    # ========ddd========
    render_dict = {}
    render_dict["geometry"] = geo
    render_dict["htable"] = tableenv
    render_dict.update(db_dict)
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
