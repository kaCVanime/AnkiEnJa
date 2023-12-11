#-*- coding:utf-8 -*-
import json
from ..base import *

DICT_PATH = u"C:/Users/Administrator/Downloads/OxfordAdvanced/牛津高阶英汉双解词典(第9版)_V3.1.2版.mdx"

@register([u'本地词典-牛津高阶9JSON提取', u'牛津高阶9JSON提取'])
class oalecd9_mdx(MdxService):

    def __init__(self):
        dict_path = DICT_PATH
        # if DICT_PATH is a path, stop auto detect
        if not dict_path:
            from ...service import service_manager, service_pool
            for clazz in service_manager.mdx_services:
                service = service_pool.get(clazz.__unique__)
                title = service.builder._title if service and service.support else u''
                service_pool.put(service)
                if title.startswith(u'牛津高阶英汉双解词典'):
                    dict_path = service.dict_path
                    break
        super(oalecd9_mdx, self).__init__(dict_path)

    @property
    def title(self):
        return getattr(self, '__register_label__', self.unique)

    @export('simple_definitions')
    def meanings(self):
        soup = parse_html(self.get_html())
        definitions = soup.find_all('def')
        def_str = ''
        if definitions:
            for i, definition in enumerate(definitions):
                def_str = def_str + str(i+1) + '. ' + definition.get_text() + '<br><br>'
        return def_str

    @export('clear')
    def clear(self):
        return ''

    @export('label')
    def labels(self):
        soup = parse_html(self.get_html())
        container = soup.find('pron') or soup.find('top-g')
        labels = container.find_all('label-g-blk')
        label = labels[-1] if labels else ''
        return label.get_text()

    def _get_component_str(self, target, tag, recursive=False):
        box = target.find(tag, recursive=recursive)
        return box.get_text() if box else ''

    def _remove_empty_attr(self, target):
        for attr, value in list(target.items()):
            if not value:
                del target[attr]
        return target
    def _get_definition_and_examples(self, target):
        result = []
        def_containers = target.find_all('sn-gs')
        defs = []
        for container in def_containers:
            defs = defs + container.find_all('sn-g')
        for definition_box in defs:
            definition = definition_box.find('def', recursive=False)
            if not definition:
                continue
            label_str = self._get_component_str(definition_box, 'label-g-blk')
            usage_str = self._get_component_str(definition_box, 'cf-blk')
            cn_str = definition.chn.extract().get_text() if definition.chn else ''
            examples_list = []
            obj = {'label': label_str, 'usage': usage_str, 'definition': definition.get_text(), 'def_cn': cn_str}
            result.append(self._remove_empty_attr(obj))
            obj['examples'] = examples_list
            eg_container = definition_box.find('x-gs')
            if not eg_container:
                continue
            egs = eg_container.find_all('x-g-blk')
            for eg_box in egs:
                label_str = self._get_component_str(eg_box, 'label-g-blk')
                usage_str = self._get_component_str(eg_box, 'cf-blk')
                eg = eg_box.find('x')
                cn_str = eg.chn.extract().get_text() if eg.chn else ''
                if eg.get_text():
                    example_obj = {'label': label_str, 'usage': usage_str, 'en': eg.get_text(), 'cn': cn_str}
                    examples_list.append(self._remove_empty_attr(example_obj))
            if not examples_list:
                del obj['examples']
        return result

    @export('idioms')
    def idioms(self):
        soup = parse_html(self.get_html())
        result = []
        idioms = soup.find_all('idm-g')
        for idiom in idioms:
            entry = idiom.find('top-g')
            result.append({'usage': entry.get_text(), 'defs': self._get_definition_and_examples(idiom)})

        if not result:
            return ''
        return json.dumps(result, ensure_ascii=False)

    @export('phrase verbs')
    def phrase_verbs(self):
        soup = parse_html(self.get_html())
        result = []
        for phrv in soup.find_all('pv-g'):
            entry = phrv.find('top-g')
            usages = list(map((lambda x: x.get_text()), entry.find_all('pv')))
            result.append({'usage': " | ".join(usages), 'defs': self._get_definition_and_examples(phrv)})
        if not result:
            return ''
        return json.dumps(result, ensure_ascii=False)

    @export('examples')
    def examples(self):
        soup = parse_html(self.get_html())
        ex_containers = soup.find_all('idm-g') + soup.find_all('pv-gs-blk')
        for container in ex_containers:
            container.extract()
        result = self._get_definition_and_examples(soup)

        if not result:
            return ''
        return json.dumps(result, ensure_ascii=False)

