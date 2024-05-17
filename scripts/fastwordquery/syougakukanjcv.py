# -*- coding:utf-8 -*-
import os
import re
import random
import json
from ..base import *
import traceback, pdb, sys

from aqt.qt import debug

# from BeautifulSoup import BeautifulSoup
# from bs4 import BeautifulSoup

DICT_PATH = "C:/Users/Administrator/Downloads/jc/小学馆v3/Shogakukanjcv3.mdx"
JEV_PATH = "C:/Users/Administrator/AppData/Roaming/Anki2/addons21/fastwq1/service/dict/jev_list.txt"


def add_key(obj, key, value):
    if value:
        obj[key] = value


@register(["本地词典-小学馆日汉v3", "小学馆日汉v3"])
class syogakukanjcv(MdxService):
    def __init__(self):
        dict_path = DICT_PATH
        # if DICT_PATH is a path, stop auto detect
        if not dict_path:
            from ...service import service_manager, service_pool

            for clazz in service_manager.mdx_services:
                service = service_pool.get(clazz.__unique__)
                title = service.builder._title if service and service.support else ""
                service_pool.put(service)
                if title.startswith("小学馆日汉v3"):
                    dict_path = service.dict_path
                    break

        self.jev_entries = set(
            line.strip() for line in open(JEV_PATH, encoding="utf-8")
        )
        super(syogakukanjcv, self).__init__(dict_path)

    @property
    def title(self):
        return getattr(self, "__register_label__", self.unique)

    def _get_html(self):
        html = self.get_html()
        if html.startswith("@@@LINK="):
            available_entries = [t[8:] for t in html.split()]
            for word in available_entries:
                if word not in self.jev_entries:
                    self.word = word
                    html = self.get_html()
        return html

    @export("full")
    def full(self):
        return self._get_html()

    def _find_meaning_tag(self, tag):
        return (
            tag.name == "p"
            and tag.attrs.get("data-orgtag") == "meaning"
            and not tag.attrs.get("type") == "補足"
        )

    def _get_meanings(self, target, result):
        defs = []
        meanings = target.find_all(self._find_meaning_tag, recursive=False)
        for i, meaning in enumerate(meanings):
            if meaning.attrs.get("level") == "1":
                continue
            # remove reference definition
            if meaning.find("ref", recursive=False):
                continue

            def_obj = {}

            """
            #fix "置く" def-12.
            <meaning>
            <meaning type="補足">
            <example>
            """
            hosoku_tag = None
            next_sib = meaning.next_sibling
            if next_sib and next_sib.attrs.get("type") == "補足":
                hosoku_tag = next_sib
                hosoku_tag.extract()
                def_obj["label"] = "[補足]"

            first_text_node = meaning.find(string=True, recursive=False)
            if first_text_node:
                first_text_node_text = first_text_node.get_text()
                text_content = meaning.get_text()
                if first_text_node_text.startswith(("⇒", "→")):
                    continue
                if first_text_node_text.startswith(("[", "<", "〈")):
                    if first_text_node_text == text_content:
                        result["label"] = result.get("label", "") + text_content
                        continue
                    else:
                        first_text_node.extract()
                        def_obj["label"] = (
                            def_obj.get("label", "") + first_text_node_text
                        )

            defs.append(def_obj)

            white_squares = meaning.find_all("span", class_="white-square")
            for tag in white_squares:
                tag.extract()

            index_el = meaning.find("b")
            if index_el and index_el.get_text().isnumeric():
                index_el.extract()

            definition = meaning.find("span", attrs={"type": "語義区分2"})
            if definition:
                definition.extract()
                def_obj["definition"] = definition.get_text()
                if hosoku_tag:
                    def_obj["definition"] += hosoku_tag.get_text().replace("[補足]", "")
            def_obj["def_cn"] = meaning.get_text()

            for tag in meaning.next_siblings:
                if tag.get("data-orgtag") == "example":
                    example = {}
                    ja = tag.find("jae")
                    cn = tag.find("ja_cn")
                    if ja:
                        example["ja"] = ja.get_text()
                    if cn:
                        example["cn"] = cn.get_text()
                    if ja or cn:
                        def_obj.setdefault("examples", []).append(example)
                else:
                    break

        return defs

    def _get_subheads(self, name, target):
        result = []
        sections = target.find_all("div", attrs={"type": name}, recursive=False)

        for item in sections:
            obj = {
                "usage": item.find(
                    "div", attrs={"data-orgtag": "subheadword"}, recursive=False
                ).get_text()
            }
            defs = self._get_meanings(item, obj)
            if defs:
                obj["defs"] = defs
                result.append(obj)

        return result

    @export("json")
    def injson(self):
        try:
            html = self._get_html()
            soup = parse_html(html)
            entries = soup.find_all("h2", recursive=False) + soup.find_all(
                "h3", recursive=False
            )
            result = []

            if entries:
                for entry in entries:
                    obj = {"label": ""}
                    yomi = entry.find("span", class_="pinyin_h")
                    if yomi:
                        yomi.extract()
                        obj["yomi"] = yomi.get_text()
                    obj["word"] = entry.get_text()
                    body = entry.find_next_sibling("section", class_="description")

                    add_key(obj, "defs", self._get_meanings(body, obj))

                    if not obj["label"]:
                        del obj["label"]

                    add_key(obj, "idioms", self._get_subheads("慣用句", body))
                    add_key(obj, "compounds", self._get_subheads("複合語", body))

                    if any(key in obj for key in ("defs", "idioms", "compounds")):
                        result.append(obj)
            else:
                compounds = self._get_subheads("複合語", soup)
                if compounds:
                    result.append({"word": self.word, "compounds": compounds})

            if not result:
                return ""

            return json.dumps(result, ensure_ascii=False)
        except:
            extype, value, tb = sys.exc_info()
            print(traceback.format_exc())
            traceback.print_exc()
            pdb.post_mortem(tb)
