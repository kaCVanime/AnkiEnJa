#-*- coding:utf-8 -*-
from ..base import *

DICT_PATH = u"C:/Users/Administrator/Downloads/Compressed/大辞泉202304/大辞泉202304/DJS.mdx"

@register([u'本地词典-大辞泉', u'大辞泉'])
class daijisen_mdx(MdxService):

    def __init__(self):
        dict_path = DICT_PATH
        # if DICT_PATH is a path, stop auto detect
        if not dict_path:
            from ...service import service_manager, service_pool
            for clazz in service_manager.mdx_services:
                service = service_pool.get(clazz.__unique__)
                title = service.builder._title if service and service.support else u''
                service_pool.put(service)
                if title.startswith(u'DJS'):
                    dict_path = service.dict_path
                    break
        super(daijisen_mdx, self).__init__(dict_path)

    @property
    def title(self):
        return getattr(self, '__register_label__', self.unique)

    @export('accent')
    def meanings(self):
        soup = parse_html(self.get_default_html())
        accent = soup.find('maccentaudiog')
        if accent:
            img_tag = accent.a
            img_tag.decompose()
            return accent.get_text()
        return ''

    @export('表記')
    def hyouki(self):
        soup = parse_html(self.get_default_html())
        items = list(set(map(lambda t: t.get_text(), soup.find_all('headword', class_="表記"))))
        result = ''
        if items and len(items) <= 3:
            for item in items:
                result = result + item
        return result
