import subprocess


def rewa():
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
            word_node = "".join(
                (r"\structWord{", item["word1"], "}{", item["word2"], "}")
            )
            pic_node = "".join((r"\structPic{", item["pic1"], "}{", item["pic2"], "}"))
            f.write(
                "".join((
                    r"\structTable{",
                    item["title"],
                    "}{",
                    word_node,
                    "}{",
                    pic_node,
                    "}",
                ))
            )


rewa()
aa = subprocess.Popen(
    "latexmk -pdf -file-line-error -halt-on-error -interaction=nonstopmode test1.tex", shell=True
)
# 编译期间可以干点别的事
print("证明异步运行！！！")
aa.wait()
