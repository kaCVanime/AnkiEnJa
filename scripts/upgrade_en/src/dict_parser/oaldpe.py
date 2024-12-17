import re
from copy import copy
from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm

from .base import Base
from ..utils import (
    import_from,
    get_soup_text,
    normalize_redirect_word,
    remove_last_word,
)

def normalize_chn(chn):
    return re.sub('[(（）)]', '', chn).strip()

def abbrev(s):
    s = s.replace('somebody', 'sb')
    s = s.replace('something', 'sth')
    return s


class OaldpeParser(Base):

    def __init__(self, soup, entry, word_overwrite):
        super().__init__(soup)
        self.entry = entry
        self.word_overwrite = word_overwrite

    def specify_def(self, def_id):
        self.x_def_id = def_id

    @staticmethod
    def is_redirect_entry(html):
        # raise NotImplementedError
        soup = BeautifulSoup(html, 'html.parser')
        entries = OaldpeParser.get_entries(soup)
        if len(entries) > 1:
            return False
        entry = entries[0]
        single = entry.find('ol', class_='sense_single', recursive=False)
        phrv = entry.find('aside', class_='phrasal_verb_links')
        idiom = entry.find('span', class_='idm-g')
        if single:
            definition = single.find('span', class_='def')
            use = single.find('span', class_='use')
        return not phrv and not idiom and single and not definition and not use

    @staticmethod
    def get_best_redirect_word(html):
        entry = BeautifulSoup(html, 'html.parser')

        def get_href_keyword(h):
            keyword = 'entry://'
            return h[len(keyword):] if h else None

        href = None
        if single := entry.find('ol', class_='sense_single'):
            href = single.find('a', class_='Ref').get('href', None)
        elif seealso := entry.body.find('body-content').find('div', class_='seealso'):
            href = seealso.find('a').get('href', None)
        return get_href_keyword(href)

    @staticmethod
    def get_entries(soup):
        entries = soup.find_all('div', class_='entry')

        return entries or soup.find_all('span', class_='idm-g')

    def get_word(self):
        if headword := self.entry.find('h1', class_='headword'):
            hms = headword.find_all('span', class_='hm')
            for hm in hms:
                hm.extract()
            return headword.get_text().replace('™', '')
        elif "idm-g" in self.entry.get("class", ""):
            return self.entry.find('span', class_='idm').get_text()

    def get_word_variants(self):
        return [v.get_text() for v in
                self.entry.find('div', class_='webtop').find_all('div', class_='variants', recursive=False)]

    def get_phonetics(self):
        return (
            get_soup_text(self.entry.find('div', class_='phons_br')),
            get_soup_text(self.entry.find('div', class_='phons_n_am'))
        )

    def _parse_example(self, li, prefix):
        cf = li.find('span', class_='cf')
        x = li.find('span', {'class': ['x', 'unx']})
        if not x:
            return None
        p = x
        xt = x.find(['xt', 'unxt'])
        if xt:
            xt.extract()
            p = xt
        s_chn = p.find('chn', class_='simple')
        t_chn = p.find('chn', class_='traditional')
        if s_chn:
            s_chn.extract()
        if t_chn:
            t_chn.extract()
        return {
            "usage": abbrev(cf.get_text()) if cf else "",
            "labels": self._parse_labels(li.find('div', class_='exText')),
            "en": x.get_text(),
            "cn": s_chn.get_text() if s_chn else "",
            "ai": bool(s_chn.find('ai')) if s_chn else False,
            "name": prefix
        }

    def _parse_labels(self, box):
        if not box:
            return None
        labels = box.find_all('span', class_='labels', recursive=False)
        for label in labels:
            labelx = label.find('labelx')
            if labelx:
                labelx.extract()
        s = "".join([a.get_text() for a in labels]) if labels else ""
        return s

    def _get_def_inline_topics(self, box):
        if not box:
            return ''
        topics = box.find_all('span', class_='dis-g', recursive=False)
        contents = []
        for t in topics:
            dtxts = t.find_all('span', class_='dtxt', recursive=False)
            for dtxt in dtxts:
                dtxtx = dtxt.dtxtx
                if dtxtx:
                    dtxtx.extract()
            contents.extend(dtxts)
        return [get_soup_text(c) for c in contents]

    def _parse_usage(self, li, sensetop):
        cf0 = sensetop.find_all('span', class_='cf', recursive=False) if sensetop else []
        cf1 = li.find_all('span', class_='cf', recursive=False)

        return ' | '.join([abbrev(cf.get_text()) for cf in [*cf0, *cf1]])

    def _parse_def(self, li):
        definition = get_soup_text(li.find('span', class_='def'))
        if not definition:
            return None
        sense_top = li.find('span', class_='sensetop', recursive=False)
        variants = li.find('div', {"class": "variants"})

        cefr = li.get('cefr', '')

        id = li.get('id')
        topic = li.find('span', class_='topic-g', recursive=False)
        if topic and not cefr:
            topic_cefr = topic.find('span', class_='topic_cefr')
            cefr = get_soup_text(topic_cefr)

        eg_box = li.find('ul', class_='examples')
        examples = list(
            filter(
                None,
                [self._parse_example(li, f'{id}_{idx}') for idx, li in
                 enumerate(eg_box.find_all('li', recursive=False))] if eg_box else []
            )
        )
        if len(examples) < 10:
            extra = li.find('span', class_='unbox', unbox='extra_examples')
            if extra:
                extra_eg_box = extra.find('ul', class_='examples')
                start = len(examples)
                examples.extend(
                    [self._parse_example(li, f'{id}_{idx + start}') for idx, li in
                     enumerate(extra_eg_box.find_all('li', recursive=False))]
                )
        def_t = li.find('deft')

        return {
            "id": id,
            "cefr": cefr.upper(),
            "usage": self._parse_usage(li, sense_top),
            "labels": self._parse_labels(sense_top) + self._parse_labels(li),
            "definition": definition,
            "def_cn": normalize_chn(def_t.find('chn', class_='simple').get_text()) if def_t else '',
            "examples": examples or None,
            "variants": get_soup_text(variants),
            "topic": "=_=".join(
                [*([t.get_text() for t in topic.find_all('span', class_='topic_name')] if topic else []),
                 *self._get_def_inline_topics(li), *self._get_def_inline_topics(sense_top)]
            )
        }

    def _parse_def_box(self, root):
        defs = root.find('ol', class_='senses_multiple', recursive=False)
        if not defs:
            defs = root.find('ol', class_='sense_single', recursive=False)

        return defs

    def get_defs_and_egs(self, root=None):
        root = root or self.entry

        def parse_sense_boxes(boxes):
            return [self._parse_def(box.find('li')) for box in boxes.find_all('div', class_='li_sense')]

        if def_box := self._parse_def_box(root):
            return list(
                filter(None, parse_sense_boxes(def_box))
            )

        elif pvgs := root.find_all('span', class_='pv-g', recursive=False):
            results = []
            for pv in pvgs:
                if def_box := self._parse_def_box(pv):
                    results.extend(
                        list(
                            filter(None, parse_sense_boxes(def_box))
                        )
                    )
            return results

        return None

    def get_idioms(self):
        return [
            {
                "usage": abbrev(g.find('span', class_='idm').get_text()),
                "defs": self.get_defs_and_egs(root=g)
            }
            for g in self.entry.find_all('span', class_='idm-g')
        ]

    def get_usage(self):
        pass

    def _parse_phrase(self, li):
        a = li.find('a', class_='Ref')
        href = a.get('href', None)
        keyword = 'entry://'
        idx = href.index('#') if '#' in href else None
        redirect = href[len(keyword):idx]

        if '_' in redirect:
            redirect = redirect.split('_')[0]
        # tear-up1
        redirect = re.sub('\d+$', '', redirect)

        DictHelper = import_from('..utils', 'DictHelper', package='src.dict_parser')
        ParserManager = import_from('..dict_parser', 'ParserManager', package='src.dict_parser')

        dict_helper = DictHelper()
        parser = ParserManager()

        html = dict_helper.query_oaldpe(redirect)
        h = html[0]
        redirect_keyword = '@@@LINK='
        if h.startswith(redirect_keyword):
            h.strip()
            h = h[len(redirect_keyword):].strip()
            # loop
            if h == 'bale-out' or h == 'bale out':
                return None
            html = dict_helper.query_oaldpe(h)
            h = html[0]
        return parser.parse(h, redirect, mode='phrv')

    def get_phrases(self, parent=None):
        box = self.entry.find('aside', class_='phrasal_verb_links')

        return list(
            filter(None, [self._parse_phrase(p) for p in box.ul.find_all('li', recursive=False)])
        ) if box else None

    def get_entry_prefix(self, word=None):
        pass

    def get_pos(self):
        pos = self.entry.find('span', class_='pos')
        return get_soup_text(pos)

    def get_labels(self):
        return self._parse_labels(self.entry.find('div', class_='webtop'))

    def _parse_syn_overview(self, body):
        p = body.find('span', class_='p', recursive=False)
        if not p:
            return '', ''
        undt = p.undt
        def_cn = ''
        if undt:
            undt.extract()
            def_cn = undt.find('chn', class_='simple').get_text()
        return p.get_text(), def_cn

    def _parse_syn_id(self, box):
        title = box.find('span', class_='box_title')
        short_id = title.unboxx.next_sibling.get_text()

        return f'Synonyms_{short_id}'

    def _parse_syn_def(self, defpara, prefix):
        box = copy(defpara)

        word = box.find('span', class_='eb')
        word.extract()
        word = word.get_text()

        id = f'{prefix}_{word}'

        trans = box.undt
        if trans:
            trans.decompose()

        eg_box = box.find(True, class_='examples')
        if eg_box:
            eg_box.extract()
        examples = list(
            filter(
                None,
                [self._parse_x_example(li, f'{id}_{idx}') for idx, li in
                 enumerate(eg_box.find_all('li', recursive=False))] if eg_box else []
            )
        )

        note = box.find('span', class_='un', un='note')
        if note:
            note.extract()
            undts = note.find_all('undt')
            for u in undts:
                u.decompose()
            note = note.get_text()

        definition = re.sub('(\s?Compare)?:$', '', box.get_text().strip())

        return {
            "id": id,
            "word": word,
            "definition": definition,
            "examples": examples,
            "note": note or ''
        }

    def _parse_syn_defs(self, body, prefix):
        defs = body.find_all('span', class_='defpara')
        return [self._parse_syn_def(d, prefix) for d in defs]

    def _par_syn_group(self, body):
        bs = body.find_all('span', class_='unbox', recursive=False)
        assert len(bs) >= 2
        return f'{bs[0].next_element} ▪ {bs[1].get_text()}'

    def get_synonyms(self):
        boxes = self.entry.find_all('span', class_='unbox', unbox='synonyms')

        return [
            {
                "id": (syn_id := self._parse_syn_id(box)),
                "overview": (body := box.find('span', class_='body')) and (overviews := self._parse_syn_overview(body))[
                    0],
                "group": self._par_syn_group(body),
                "overview_cn": re.sub('以上(?:各|两)词均?(?:含|指|为|用以|可指)?(.+?)(?:之义)?。', r'\1', overviews[1]),
                "defs": self._parse_syn_defs(body, syn_id)
            }
            for box in boxes
        ] or None

    def _parse_wiw_id(self, box):
        title = box.find('span', class_='box_title')
        short_id = title.unboxx.next_sibling.get_text().replace('/', '-')

        return f'Which_word_{short_id}'

    def _parse_wiw_overview(self, body):
        return self._parse_syn_overview(body)

    def _parse_x_example(self, li, prefix):
        x = li.find('div', class_='exText')
        if not x:
            return None
        p = x
        xt = x.find(['xt', 'unxt', 'undt'])
        if xt:
            xt.extract()
            p = xt
        s_chn = p.find('chn', class_='simple')
        t_chn = p.find('chn', class_='traditional')
        if s_chn:
            s_chn.extract()
        if t_chn:
            t_chn.extract()
        return {
            "usage": "",
            "labels": "",
            "en": x.get_text(),
            "cn": s_chn.get_text() if s_chn else "",
            "ai": bool(s_chn.find('ai')) if s_chn else False,
            "name": prefix
        }

    def _parse_wiw_item(self, item, id):
        item = copy(item)

        eg_box = item.find('ul', class_='examples')
        if eg_box:
            eg_box.extract()
        examples = list(
            filter(
                None,
                [self._parse_x_example(li, f'{id}_{idx}') for idx, li in
                 enumerate(eg_box.find_all('li', recursive=False))] if eg_box else []
            )
        )

        cn = ''
        undt = item.undt
        if undt:
            undt.extract()
            cn = undt.find('chn', class_='simple').get_text()

        if labelxs := item.find_all('labelx'):
            for l in labelxs:
                l.extract()

        definition = re.sub('(\s?Compare)?:$', '', item.get_text().strip())
        if len(definition) < 5:
            return None
        return {
            "id": id,
            "definition": definition,
            "def_cn": cn,
            "examples": examples
        }

    def _parse_wiw_items(self, li, prefix):
        items = li.find_all('div', class_='item', recursive=False)

        return list(filter(None, [self._parse_wiw_item(item, f'{prefix}_{idx}') for idx, item in enumerate(items)]))

    def _parse_wiw_bullets(self, body, prefix):
        lis = body.ul.find_all('li', recursive=False)
        return [self._parse_wiw_items(li, f'{prefix}_{idx}') for idx, li in enumerate(lis)]

    def get_which_words(self):
        boxes = self.entry.find_all('span', class_='unbox', unbox='which_word')

        return [
            {
                "id": (wiw_id := self._parse_wiw_id(box)),
                "group": box.find('span', class_='box_title').find('span', class_='closed').get_text().replace(
                    '/',
                    '▪'
                ),
                "overview": (body := box.find('span', class_='body')) and (overviews := self._parse_wiw_overview(body))[
                    0],
                # "overview_cn": re.sub('.+?均(.+)|.+?(常.+)', r'\1', overviews[1]),
                "overview_cn": overviews[1],
                "defs": self._parse_wiw_bullets(body, wiw_id)
            }
            for box in boxes
        ] or None
