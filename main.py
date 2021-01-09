import subprocess
from os import system


def node_join(command, *para_arr):
    result = [command]
    result.extend("".join(("{", para, "}")) for para in para_arr)
    return "".join(result)


def generate():
    with open("textfill.tex", "w", encoding="utf-8") as f:
        for item in (
            {
                "title": "OP10",
                "word1": "word11",
                "word2": "word12",
                "pic1": "pic11",
                "pic2": "pic12",
            },
            {
                "title": "OP210",
                "word1": "word21",
                "word2": "word22",
                "pic1": "pic21",
                "pic2": "pic22",
            },
        ):
            word_node = node_join(r"\structWord", item["word1"], item["word2"],)

            pic_node = node_join(r"\structPic", item["pic1"], item["pic2"],)
            f.write(node_join(r"\structTable", item["title"], word_node, pic_node,))


def main(clear_tmp=False):
    generate()
    compile_command = "latexmk -pdf -file-line-error -halt-on-error -interaction=nonstopmode test1.tex"
    compile_process = subprocess.Popen(
        compile_command, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    # 编译期间可以干点别的事
    print("证明异步运行！！！")
    compile_process.wait()
    if clear_tmp:
        system("latexmk -c")


main()
