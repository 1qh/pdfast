import os
import re

from pypdf import PdfReader

TAB_SIZE = 4


def leading_spaces(s: str) -> int:
    return len(s) - len(s.lstrip())


def samestr(a: str, b: str) -> bool:
    return a.replace(' ', '') == b.replace(' ', '')


class PdfExtractor:
    def __init__(self, pdf: str, toc: str):
        rd = PdfReader(pdf)
        self.pages = [i.extract_text().strip().replace('  ', ' ') for i in rd.pages]
        bm = toc.splitlines()
        self.levels = [leading_spaces(i) // TAB_SIZE for i in bm]
        bm = [i.strip().split('\"') for i in bm]
        self.outline = [i[1] for i in bm]
        self.pagenum = [int(i[2]) - 1 for i in bm]
        assert len(self.outline) == len(self.levels) == len(self.pagenum)

    def __call__(self, at: str = None):
        pages = self.pages
        outline = self.outline
        levels = self.levels
        pagenum = self.pagenum

        idx = outline.index(at)
        level = levels[idx]

        end = next(
            (
                idx + distant
                for distant, l in enumerate(levels[idx + 1 :], 1)
                if l <= level
            ),
            None,
        )
        p_lo = int(pagenum[idx])
        p_hi = int(pagenum[end]) if end else len(pages)
        to = outline[end] if end else None
        print(f'Extract from: {at} p{p_lo} to: {to} p{p_hi}')

        txt = pages[p_lo] if p_hi == p_lo else '\n'.join(pages[p_lo:p_hi])
        txt = [i.strip() for i in txt.splitlines()]
        lo = next((i for i, t in enumerate(txt) if samestr(at, t)), -1)
        hi = next((i for i, t in enumerate(txt) if to and samestr(to, t)), len(txt))
        return '\n'.join([i for i in txt[lo:hi] if not i.isnumeric()])


class BookmarksExtractor:
    def __init__(
        self,
        pdf: str,
        temp_toc: str | None = 'temp.txt',
    ):
        if pdf:
            os.system(
                f'''
                pdfxmeta -a 1 {pdf} >> recipe.toml
                pdfxmeta -a 2 {pdf} >> recipe.toml
                pdftocgen {pdf} < recipe.toml > {temp_toc}
                '''
            )
        with open(temp_toc, 'r') as f:
            self.toc = [i.strip() for i in f.readlines()]

    def __call__(self, postprocess: bool = True):
        toc = self.toc
        if postprocess:
            # start from toc string
            target = '目次'
            start = next((i for i, l in enumerate(toc) if target in l), 0)
            toc = toc[start:]

            # remove lines with '...'
            toc = [i for i in toc if '...' not in i]

            # find lines with number pattern
            pattern = re.compile(r'(?<=^.{1})\d+\.(\d+)?(.\d+)?(.\d+)?\s.*')
            toc = list(filter(pattern.search, toc))

            toc = [i.replace('  ', ' ') for i in toc]
            # level indent based on number pattern
            num = [i.strip()[1] for i in toc]
            level = [
                (len(i) - 1) if i[1].isnumeric() else 0
                for i in [l.split()[0].split('.') for l in toc]
            ]
            for i, l in enumerate(toc):
                if '目次' in l:
                    continue
                cur_lv = level[i]
                pre_lv = level[i - 1] if i > 0 else None
                pre = num[i - 1] if i > 0 else None
                cur = num[i]
                nex = num[i + 1] if i < len(toc) - 1 else None

                if pre and cur and nex and pre_lv and cur_lv < pre_lv and cur < nex:
                    level[i] = pre_lv
                    if cur < pre:
                        level[i] += 1

                toc[i] = level[i] * TAB_SIZE * ' ' + l

        return '\n'.join(toc)
