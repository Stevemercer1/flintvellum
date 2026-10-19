#!/usr/bin/env python3
"""Validate the complete static collection, source records and protected copy."""
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlsplit, unquote
import hashlib, json, re, subprocess
from archive_display import title
ROOT=Path(__file__).resolve().parent.parent
approved=json.loads((ROOT/'docs/site-copy.json').read_text())
lots=json.loads((ROOT/'_catalogue/lots.json').read_text());sources=json.loads((ROOT/'_catalogue/sources.json').read_text())
assert len(lots)==259 and len({x['id'] for x in lots})==259
assert sum(len(x['images']) for x in lots)==989
assert sum(x['result'] is not None for x in lots)==128
pages=[ROOT/name for name in ['index.html','catalogue.html','archive.html','company.html','careers/index.html']]+list((ROOT/'lots').glob('*.html'))
assert len(pages)==264
for path in pages:
    text=path.read_text();page=BeautifulSoup(text,'html.parser')
    assert text.count('fingerprint.js')==1 and re.search(r'<script src="fingerprint.js" defer></script>\s*</body>',text),path
    assert not page.select('a[href^="data/"]'),path
    assert not any(stale in text for stale in ['stevelikejobs@proton.me','Tel Aviv, Israel','£110,000']),path
    assert 'Collection report' not in text and 'Download catalogue data' not in text,path
    if path.name=='archive.html':
        assert not re.search(r'\d',page.main.get_text()),path
    footer=page.select_one('#footerHost template nav[aria-label="Footer"]')
    assert len(footer.select('a[href]'))==10,path
    assert page.select_one('#footerHost .fv-footer-contact-copy a')['href']==approved['contactMailto'],path
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
    assert page.select_one('.fv-closed').get_text() in ['Auction closed','Enquiry only']
    assert 'not available to bid on here' in page.main.get_text()
    assert bool(page.select_one('[data-enquiry-form]'))==(page.select_one('.fv-closed').get_text()=='Enquiry only')
    assert page.select_one('.fv-currency form [name=amount]')['value']==str(lot['estimateLow'])
    prices=page.select_one('.fv-lot-prices').get_text()
    assert f"£{lot['estimateLow']:,.0f}" in prices and f"£{lot['estimateHigh']:,.0f}" in prices
    assert ('Derived historical range' in prices)==(sources[lot['id']]['estimateBasis']=='derived_from_verified_sale')
    assert 'FlintVellum has not independently inspected' in page.select_one('.fv-source-notes').get_text()
    for image in sources[lot['id']]['images']:
        assert hashlib.sha256((ROOT/image['path']).read_bytes()).hexdigest()==image['sha256'],image['path']
original=BeautifulSoup(subprocess.check_output(['git','show','christies-pristine^:index.html'],cwd=ROOT,text=True),'html.parser')
approved=json.loads((ROOT/'docs/site-copy.json').read_text())
for location in original.select('.role-location'):location.string=approved['roleLocation']
original.select('.role')[0].find_all('p',recursive=False)[1].string=approved['backendSalary']
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
    for line in details[key]['responsibilities']+details[key]['requirements']+details[key].get('hiringProcess',[]):assert line in role.get_text()
assert company.select_one('.recruiter').get_text(' ',strip=True)==approved['contactLine']+' '+approved['contactEmail']
assert company.select_one('.recruiter a')['href']==approved['contactMailto']
assert (ROOT/'fingerprint.js').read_bytes()==subprocess.check_output(['git','show','HEAD:fingerprint.js'],cwd=ROOT)
home=BeautifulSoup((ROOT/'index.html').read_text(),'html.parser')
founder=json.loads((ROOT/'docs/founder-copy.json').read_text())
assert 200<=len(' '.join(founder['paragraphs']).split())<=280 and len(founder['linkedin'].split())==25
for page in [home,company]:
    assert [p.get_text() for p in page.select('#about .fv-founder-copy p')]==founder['paragraphs']
    assert page.select_one('#about .fv-founder-line').get_text()==founder['founderLine']
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
print('PASS: every route, original image hash, catalogue source, historical price labels, compact footer, approved settlement/careers copy and analytics hook.')
