#!/usr/bin/env python3
"""Validate the complete static collection, source records and protected copy."""
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlsplit, unquote
import hashlib, json, re, subprocess
ROOT=Path(__file__).resolve().parent.parent
lots=json.loads((ROOT/'data/lots.json').read_text());sources=json.loads((ROOT/'data/sources.json').read_text())
assert len(lots)==250 and len({x['id'] for x in lots})==250
assert sum(len(x['images']) for x in lots)==947
assert sum(x['result'] is not None for x in lots)==127
pages=[ROOT/name for name in ['index.html','catalogue.html','archive.html','company.html','careers/index.html']]+list((ROOT/'lots').glob('*.html'))
assert len(pages)==255
for path in pages:
    text=path.read_text();page=BeautifulSoup(text,'html.parser')
    assert text.count('fingerprint.js')==1 and re.search(r'<script src="fingerprint.js" defer></script>\s*</body>',text),path
    for node in page.select('[src],a[href],link[href]'):
        value=node.get('src',node.get('href'));u=urlsplit(value)
        if u.scheme or u.netloc or not u.path:continue
        assert (ROOT/unquote(u.path)).exists(),(path,value)
    for host in page.select('#headerHost template,#footerHost template'):
        assert not any(urlsplit(a['href']).netloc for a in host.select('a[href]')),path
for lot in lots:
    page=BeautifulSoup((ROOT/'lots'/f'{lot["id"]}.html').read_text(),'html.parser')
    assert lot['status']=='closed' and page.h1.get_text()==lot['title']
    assert [a['href'] for a in page.select('[data-gallery-index]')]==lot['images']
    assert page.select_one('#lot-image')['src']==lot['images'][0]
    assert page.select_one('.fv-lot-summary .fv-source-link')['href']==sources[lot['id']]['url']
    assert lot['condition'] in page.select_one('.fv-object-notes').get_text()
    for note in sources[lot['id']]['notes']:assert note in page.select_one('.fv-source-notes').get_text(),lot['id']
    for image in sources[lot['id']]['images']:
        assert hashlib.sha256((ROOT/image['path']).read_bytes()).hexdigest()==image['sha256'],image['path']
original=BeautifulSoup(subprocess.check_output(['git','show','christies-pristine^:index.html'],cwd=ROOT,text=True),'html.parser')
approved=json.loads((ROOT/'docs/site-copy.json').read_text())
for location in original.select('.role-location'):location.string=approved['roleLocation']
company=BeautifulSoup((ROOT/'company.html').read_text(),'html.parser')
careers=BeautifulSoup((ROOT/'careers/index.html').read_text(),'html.parser')
for page in [company,careers]:
    assert [x.get_text() for x in page.select('.role')]==[x.get_text() for x in original.select('.role')]
assert company.select_one('.recruiter').get_text()==original.select_one('.recruiter').get_text()
assert company.select_one('.recruiter a')['href']==original.select_one('.recruiter a')['href']
assert (ROOT/'fingerprint.js').read_bytes()==subprocess.check_output(['git','show','HEAD:fingerprint.js'],cwd=ROOT)
home=BeautifulSoup((ROOT/'index.html').read_text(),'html.parser')
for page in [home,company]:
    assert page.select('#how-it-works .steps li')[2].find('p').get_text()==approved['settlementStep']
assert home.select_one('chr-header-carousel-slide .chr-heading-s-serif').get_text()==approved['homeHeroSubtitle']
assert company.select_one('.hero-copy .intro').get_text()==approved['companyHeroSubtitle']
for block in home.select('chr-upcoming-auctions'):assert len(block.select('chr-auction-tile-next'))==6
for a in home.main.select('a[href]'):assert not urlsplit(a['href']).netloc
print('PASS: 255 routes; 250 records; 947 original image hashes; source notes; approved settlement/careers copy; unchanged analytics and one correctly placed hook per page.')
