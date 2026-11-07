"""계약 문서 docx 의 '대표: 정준수 (인)' 자리에 인감(투명 PNG)을 찍고 PDF 로 변환한다.

사용: python3 contract/stamp_seal.py <인감.png> <출력 폴더> [docx ...]
- 저장소(contract/)의 docx·pdf 는 건드리지 않는다. 인감이 찍힌 파일은 출력 폴더(납품 패키지)에만 둔다.
  (저장소는 공개라 인감 이미지가 올라가면 안 된다.)
"""
import sys, pathlib, glob, subprocess, shutil
import docx
from docx.shared import Mm, Pt
from docx.oxml.ns import qn
from docx.oxml import parse_xml

SEAL = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
FILES = sys.argv[3:] or sorted(glob.glob(str(pathlib.Path(__file__).parent / "*.docx")))
SIZE = Mm(12)                       # 인감 지름 12mm (본문 10.5pt 기준)
DX, DY = Mm(10.6), Pt(5)            # '      (인)' run 시작점 기준 (인) 글자 중심까지의 거리, 세로 보정

def to_anchor(inline, dx_emu, dy_emu):
    extent = inline.find(qn('wp:extent')); cx, cy = extent.get('cx'), extent.get('cy')
    docPr = inline.find(qn('wp:docPr')); graphic = inline.find(qn('a:graphic'))
    a = parse_xml(
        '<wp:anchor xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'distT="0" distB="0" distL="0" distR="0" simplePos="0" relativeHeight="251659264" behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1">'
        '<wp:simplePos x="0" y="0"/>'
        f'<wp:positionH relativeFrom="character"><wp:posOffset>{dx_emu}</wp:posOffset></wp:positionH>'
        f'<wp:positionV relativeFrom="line"><wp:posOffset>{dy_emu}</wp:posOffset></wp:positionV>'
        f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/><wp:wrapNone/></wp:anchor>')
    a.append(docPr); a.append(graphic); return a

for f in FILES:
    d = docx.Document(f); hit = 0
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    if '(인)' in p.text and '정준수' in p.text:
                        run = p.runs[-1]
                        pic = p.add_run(); pic.add_picture(str(SEAL), width=SIZE, height=SIZE)
                        run._r.addprevious(pic._r)
                        inline = pic._r.find('.//' + qn('wp:inline'))
                        inline.getparent().replace(inline, to_anchor(inline, int(DX - SIZE / 2), int(-SIZE / 2 + DY))); hit += 1
    out = OUT / pathlib.Path(f).name; d.save(out); print('stamped', hit, '->', out)
subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', str(OUT)] + [str(OUT / pathlib.Path(f).name) for f in FILES], check=True, capture_output=True)
print('pdf written to', OUT)
