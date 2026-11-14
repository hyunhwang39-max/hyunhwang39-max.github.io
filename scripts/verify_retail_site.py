"""Validate local navigation, public aggregates and the portfolio integration."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,csv
ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.ids=set();self.images=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:
            assert a['id'] not in self.ids, 'duplicate id'
            self.ids.add(a['id'])
        if tag=='img':
            assert a.get('alt'), 'missing image description'
            self.images+=1
        for key in ['href','src']:
            if key in a:self.links.append(a[key])
count=0
for path in [ROOT/'index.html',ROOT/'projects/retail-analysis.html']:
    page=path.read_text(encoding='utf8');p=Links();p.feed(page)
    assert 'mailto:' not in page and 'tel:' not in page
    for link in p.links:
        u=urlsplit(link)
        if u.scheme:continue
        target=(path.parent/unquote(u.path)).resolve() if u.path else path
        assert target.is_relative_to(ROOT) and target.exists(),f'missing link: {link}'
        if u.fragment and target==path:assert u.fragment in p.ids,link
        count+=1
    if path.name=='retail-analysis.html':assert p.images==4
home=(ROOT/'index.html').read_text(encoding='utf8')
assert '가상 데이터' not in home and '4.42/4.5' in home and 'Summa Cum Laude' in home
assert home.index('id="projects"')<home.index('id="education"')
s=json.loads((ROOT/'projects/retail-data/summary.json').read_text(encoding='utf8'))
assert s['raw_rows']==1067371 and s['cross_sheet_copies_removed']==22523
assert abs(s['gross']-s['credit']-s['net'])<1e-7
assert abs(s['france_focus']['share_country_credit_pct']-67.834737)<.00001
for path in (ROOT/'projects/retail-data').glob('*.csv'):
    header=next(csv.reader(path.open(encoding='utf8')))
    assert 'Customer ID' not in header
print(f'PASS: {count} local links, 4 chart alt texts, verified key results, no customer IDs in CSV exports.')
