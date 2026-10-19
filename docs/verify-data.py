#!/usr/bin/env python3
"""Validate the complete static collection, source records and protected copy."""
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlsplit, unquote
import hashlib, json, re, subprocess
from archive_display import title
ROOT=Path(__file__).resolve().parent.parent
lots=json.loads((ROOT/'_catalogue/lots.json').read_text());sources=json.loads((ROOT/'_catalogue/sources.json').read_text())
assert len(lots)==250 and len({x['id'] for x in lots})==250
assert sum(len(x['images']) for x in lots)==947
assert sum(x['result'] is not None for x in lots)==127
pages=[ROOT/name for name in ['index.html','catalogue.html','archive.html','company.html','careers/index.html']]+list((ROOT/'lots').glob('*.html'))
assert len(pages)==255
for path in pages:
    text=path.read_text();page=BeautifulSoup(text,'html.parser')
    assert text.count('fingerprint.js')==1 and re.search(r'<script src="fingerprint.js" defer></script>\s*</body>',text),path
    assert not page.select('a[href^="data/"]'),path
    assert 'Collection report' not in text and 'Download catalogue data' not in text,path
    if path.name not in ['index.html','company.html'] or path.parent.name=='lots':
        assert not re.search(r'\d',page.main.get_text()),path
    footer=page.select_one('#footerHost template nav[aria-label="Footer"]')
    assert len(footer.select('a[href]'))==10,path
    assert page.select_one('#footerHost .fv-footer-contact-copy a')['href']=='mailto:stevelikejobs@proton.me?subject=FlintVellum%20role%20enquiry',path
    for node in page.select('[src],a[href],link[href]'):
        value=node.get('src',node.get('href'));u=urlsplit(value)
        if u.scheme or u.netloc or not u.path:continue
        assert (ROOT/unquote(u.path)).exists(),(path,value)
    for host in page.select('#headerHost template,#footerHost template'):
        assert not any(urlsplit(a['href']).netloc for a in host.select('a[href]')),path
for lot in lots:
    page=BeautifulSoup((ROOT/'lots'/f'{lot["id"]}.html').read_text(),'html.parser')
    assert lot['status']=='closed' and page.h1.get_text()==title(lot)
    assert [a['href'] for a in page.select('[data-gallery-index]')]==lot['images']
    assert page.select_one('#lot-image')['src']==lot['images'][0]
    assert page.select_one('.fv-lot-summary .fv-source-link')['href']==sources[lot['id']]['url']
    assert 'Auction closed' in page.main.get_text()
    assert 'FlintVellum has not independently inspected' in page.select_one('.fv-source-notes').get_text()
    for image in sources[lot['id']]['images']:
        assert hashlib.sha256((ROOT/image['path']).read_bytes()).hexdigest()==image['sha256'],image['path']
original=BeautifulSoup(subprocess.check_output(['git','show','christies-pristine^:index.html'],cwd=ROOT,text=True),'html.parser')
approved=json.loads((ROOT/'docs/site-copy.json').read_text())
for location in original.select('.role-location'):location.string=approved['roleLocation']
company=BeautifulSoup((ROOT/'company.html').read_text(),'html.parser')
careers=BeautifulSoup((ROOT/'careers/index.html').read_text(),'html.parser')
for page in [company,careers]:
    for role,original_role in zip(page.select('.role'),original.select('.role')):
        assert role.find('h3').get_text()==original_role.find('h3').get_text()
        assert [x.get_text() for x in role.find_all('p',recursive=False)]==[x.get_text() for x in original_role.find_all('p',recursive=False)]
details=json.loads((ROOT/'docs/role-details.json').read_text())
assert details['status'] in careers.main.get_text() and details['status'] in company.main.get_text()
for key in ['backend','sales']:
    role=careers.find(id=details[key]['id'])
    for line in details[key]['responsibilities']+details[key]['requirements']:assert line in role.get_text()
assert company.select_one('.recruiter').get_text()==original.select_one('.recruiter').get_text()
assert company.select_one('.recruiter a')['href']==original.select_one('.recruiter a')['href']
assert (ROOT/'fingerprint.js').read_bytes()==subprocess.check_output(['git','show','HEAD:fingerprint.js'],cwd=ROOT)
home=BeautifulSoup((ROOT/'index.html').read_text(),'html.parser')
for page in [home,company]:
    assert page.select('#how-it-works .steps li')[2].find('p').get_text()==approved['settlementStep']
assert home.select_one('chr-header-carousel-slide .chr-heading-s-serif').get_text()==approved['homeHeroSubtitle']
assert company.select_one('.hero-copy .intro').get_text()==approved['companyHeroSubtitle']
assert len(home.select('.fv-specialism img'))==3
homepage_photos=[image['src'] for image in home.main.select('img[src]')]
assert len(homepage_photos)==len(set(homepage_photos)), 'Repeated homepage photograph'
assert not (ROOT/'assets/editorial/watches.jpg').exists()
assert home.select_one('chr-header-carousel-slide img')['src']=='img/w-0001/01.jpg'
assert not (ROOT/'data').exists()
assert '_catalogue' in (ROOT/'_config.yml').read_text()
assert not list(ROOT.rglob('REPORT.md'))
for a in home.main.select('a[href]'):assert not urlsplit(a['href']).netloc
print('PASS: every route, original image hash, catalogue source, number-free archive, compact footer, approved settlement/careers copy and analytics hook.')
