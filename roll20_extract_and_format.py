import re
import os
import sys
from typing import Tuple, Optional
from urllib import parse

import jinja2
from bs4 import BeautifulSoup, Tag


def escape_latex(unescape: str) -> str:
    escape_map = {
        ord("&"): "\\&",
        ord("%"): "\\%",
        ord("$"): "\\$",
        ord("#"): "\\#",
        ord("_"): "\\_",
        ord("{"): "\\{",
        ord("}"): "\\}",
        ord("~"): "\\textasciitilde{}",
        ord("^"): "\\textasciicircum{}",
        ord("\\"): "\\textbackslash{}",
    }
    return unescape.translate(escape_map)


def general_extract(tag: Tag) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    chat_id_tag = tag.select_one(".by")
    if chat_id_tag:
        chat_id = chat_id_tag.string
        chat_id = re.sub(r"\s+", " ", chat_id)
        chat_id = re.sub(r"^(.*):$", r"\1", chat_id)
        chat_id = escape_latex(chat_id)
        chat_id_tag.clear()
    else:
        chat_id = None

    chat_img_tag = tag.select_one(".avatar")
    if chat_img_tag:
        chat_img = parse.unquote(chat_img_tag.img["src"])
    else:
        chat_img = None

    chat_ts_tag = tag.select_one(".tstamp")
    if chat_ts_tag:
        chat_ts_tag.clear()

    chat_text = re.sub(r"\s+", " ", tag.text).strip()
    chat_text = escape_latex(chat_text)

    return (chat_id, chat_text, chat_img)


def main():
    target_path = sys.argv[1]
    if not os.path.isfile(target_path):
        print(f"insert regular file ex. python {__file__} sample\\target.html")
    with open(target_path, "r", encoding="utf-8") as fp:
        html = fp.read()

    bs = BeautifulSoup(html, "lxml")

    extract_chat = list()

    chat_title = bs.title.string
    for idx, li in enumerate(bs.select(".textchatcontainer .content .message")):
        if "general" in li["class"]:
            chat_type = "general"
            chat_id, chat_text, chat_img = general_extract(li)
        elif "emote" in li["class"]:
            chat_type = "emote"
            chat_id, chat_text, chat_img = general_extract(li)
        elif "rollresult" in li["class"]:
            chat_type = "rollresult"
            chat_id, chat_text, chat_img = general_extract(li)
        elif "desc" in li["class"]:
            chat_type = "desc"
            chat_id, chat_text, chat_img = general_extract(li)
        else:  # fallback
            chat_type = "fallback"
            chat_id, chat_text, chat_img = None, None, None
        if chat_id or chat_type == "emote" or chat_type == "desc":
            extract_chat.append((chat_id, chat_img, list()))
        extract_chat[-1][2].append((chat_type, chat_text))

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
        loader=jinja2.FileSystemLoader(os.path.abspath(".")),
    )
    template = latex_jinja_env.get_template("jinja-latex.tex")
    formatted = template.render(section1=chat_title, chat=extract_chat)

    with open("./formatted.tex", "w", encoding="utf-8") as fp:
        fp.write(formatted)

    print("done!")


if __name__ == "__main__":
    main()