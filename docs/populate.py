#!/usr/bin/env python3
"""Populate the saved Christie’s mirror with the supplied, closed auction archive."""
from pathlib import Path
from bs4 import BeautifulSoup
from collections import Counter
from html import escape
from urllib.parse import urlencode, urlparse
import copy, hashlib, json, re, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'
approved=json.loads((ROOT/'docs/site-copy.json').read_text())
catalogue_css='assets/catalogue.css?v='+hashlib.sha256((ROOT/'assets/catalogue.css').read_bytes()).hexdigest()[:12]
DATA.mkdir(exist_ok=True)
if len(sys.argv)>1:
    source=Path(sys.argv[1]).expanduser().resolve()
    for name in ['lots.json','sources.json','REPORT.md']:
        shutil.copy2(source/name,DATA/name)
    shutil.copytree(source/'img',ROOT/'img',dirs_exist_ok=True)
assert (DATA/'lots.json').exists(), 'First run: python3 docs/populate.py ../auction-data'
subprocess.run([sys.executable,str(ROOT/'docs/rebrand.py')],check=True,cwd=ROOT)
lots=json.loads((DATA/'lots.json').read_text());sources=json.loads((DATA/'sources.json').read_text())
assert len(lots)==250 and len({x['id'] for x in lots})==250
assert all(x['status']=='closed' for x in lots)
assert sum(len(x['images']) for x in lots)==947
for x in lots:
    for name in x['images']:assert (ROOT/name).is_file(), name
byid={x['id']:x for x in lots}
CATS={'watches':'Watches','cards':'Trading cards','memorabilia':'Memorabilia'}
def soup(text):return BeautifulSoup(text,'html.parser')
def E(text):return escape(str(text),quote=True)
def money(n,currency='GBP'):return ('£' if currency=='GBP' else currency+' ')+f'{n:,.0f}'
def url(x):return 'lots/'+x['id']+'.html'
def caturl(cat):return 'catalogue.html?'+urlencode({'category':cat})
def fragment(text):return soup(text).find()
def appendhtml(el,text):
    for item in list(soup(text).contents):el.append(item)
def settext(el,text):el.clear();el.append(str(text))
def content(el):return ' '.join(str(t).strip() for t in el.find_all(string=True)).strip()
def image(el,x,n=0,eager=False):
    img=el if el.name=='img' else el.find('img')
    img.attrs={'src':x['images'][n],'alt':x['title'],'class':'chr-img lazyloaded','decoding':'async','loading':'eager' if eager else 'lazy'}
    for e in el.select('source'):e.decompose()
def price(x):
    basis=sources[x['id']]['estimateBasis']
    label='Derived range' if basis=='derived_from_verified_sale' else 'Source estimate'
    return label,money(x['estimateLow'])+' – '+money(x['estimateHigh'])
s=soup((ROOT/'index.html').read_text());company=soup((ROOT/'company.html').read_text())
lot_template=copy.deepcopy(s.find('chr-lot-tile'))
def lot_tile(x):
    tile=copy.deepcopy(lot_template);tile['data-lot-id']=x['id']
    image(tile,x)
    for e in tile.select('[id]'):del e['id']
    anchor=tile.select_one('.chr-lot-tile__link');anchor['href']=url(x);settext(anchor,x['title'])
    settext(tile.select_one('.chr-lot-tile__secondary-title'),CATS[x['category']]+' · Auction closed')
    label,value=price(x);p=tile.select_one('.chr-lot-tile__price-container');p['aria-label']=label+' '+value
    settext(p.select_one('.chr-lot-tile__price-label'),label);settext(p.select_one('.chr-lot-tile__price-value'),value)
    settext(tile.select_one('.chr-lot-tile__dynamic-price'),'Hammer '+money(x['result']) if x['result'] is not None else 'Hammer not verified')
    button=tile.select_one('chr-button-save-lot button');button['data-save-lot']=x['id'];button['data-lot-title']=x['title'];button['aria-label']='Save '+x['title'];settext(button.select_one('.chr-button__text'),'Save lot')
    return tile

def shared(page):
    page.head.append(page.new_tag('link',rel='stylesheet',href=catalogue_css))
    script=page.new_tag('script',src='assets/catalogue.js',defer='');page.select_one('script[src="fingerprint.js"]').insert_before(script)
    header=page.select_one('#headerHost template')
    items=header.select('nav[aria-label="Primary"]>div>ul>li')
    groups=[('Archive','catalogue.html',[('All 250 lots','catalogue.html'),('Watches',caturl('watches')),('Trading cards',caturl('cards')),('Memorabilia',caturl('memorabilia')),('Saved lots','catalogue.html?saved=1')]),('Watches',caturl('watches'),[('All watches',caturl('watches'))]+[(m,'catalogue.html?'+urlencode({'category':'watches','maker':m})) for m in ['Rolex','Patek Philippe','Cartier','Berneron']]),('Cards',caturl('cards'),[('All trading cards',caturl('cards')),('Pokémon','catalogue.html?category=cards&q=Pokemon'),('Michael Jordan','catalogue.html?category=cards&q=Jordan'),('Shohei Ohtani','catalogue.html?category=cards&q=Ohtani')]),('Memorabilia',caturl('memorabilia'),[('All memorabilia',caturl('memorabilia')),('Film','catalogue.html?category=memorabilia&subtype=film'),('Sports','catalogue.html?category=memorabilia&subtype=sports')]),('The house','company.html#about',[('About FlintVellum','company.html#about'),('How it works','company.html#how-it-works'),('Our specialisms','company.html#collectibles'),('Careers','company.html#roles'),('About the archive','archive.html')])]
    panel_template=copy.deepcopy(header.select_one('#chrPrimaryMenuItem_0').select_one('ul'))
    li_template=copy.deepcopy(panel_template.find('li'))
    for idx,item in enumerate(items):
        if idx>=len(groups):item.decompose();continue
        title,href,links=groups[idx];a=item.find('a');settext(a,title);a['href']=href
        panel=header.find(id=a['aria-controls']);panel.clear()
        ul=copy.deepcopy(panel_template);ul.clear()
        for label,target in links:
            li=copy.deepcopy(li_template);link=li.find('a');link['href']=target;link['aria-label']=label;settext(link,label);ul.append(li)
        panel.append(ul);panel.parent['inert']=''
    # Retain the original utility bar, with local saved lots and a static currency label.
    for button in header.select('button'):
        if content(button)=='Sign in' or button.get('aria-label')=='User navigation':
            button.name='a';button['href']='catalogue.html?saved=1';button['aria-label']='Saved lots'
            for text in list(button.find_all(string=True)):
                if 'Sign in' in text:text.replace_with(str(text).replace('Sign in','Saved lots'))
        if button.get('aria-controls')=='language-menu':
            button.find_parent('li').clear()
    for field in header.select('input[type="search"]'):
        field['placeholder']='Search the archive';field['aria-label']='Search the archive';field['name']='q';field.find_parent('form')['action']='catalogue.html'
    for e in header.select('a[href]'):
        if e['href'].startswith('https://'):e['href']='catalogue.html'
    footer=page.select_one('#footerHost template');nav=footer.select_one('nav[aria-label="Footer"]')
    footgroups=[('Explore',[('All lots','catalogue.html'),('Watches',caturl('watches')),('Trading cards',caturl('cards')),('Memorabilia',caturl('memorabilia')),('Saved lots','catalogue.html?saved=1')]),('The house',[('About FlintVellum','company.html#about'),('How it works','company.html#how-it-works'),('Our specialisms','company.html#collectibles'),('Careers','company.html#roles')]),('The archive',[('About this collection','archive.html'),('Sources and price notes','archive.html#prices'),('Collection report','data/REPORT.md'),('Download catalogue data','data/lots.json')])]
    for idx,group in enumerate(nav.find_all('div',recursive=False)):
        if idx>=3:group.decompose();continue
        title,links=footgroups[idx];settext(group.find('h3'),title)
        ul=group.find('ul');li_template2=copy.deepcopy(ul.find('li'));ul.clear()
        for label,target in links:
            li=copy.deepcopy(li_template2);a=li.find('a');settext(a,label);a['href']=target;ul.append(li)
    # The legal/social row must not send visitors to another house's accounts or policies.
    for a in list(footer.select('a[href]')):
        if a['href'].startswith('http'):
            parent=a.find_parent('li')
            (parent or a).decompose()
    for button in list(footer.select('button')):
        if 'Cookie' in content(button):settext(button,'Privacy')
        else:(button.find_parent('li') or button).decompose()
    for e in page.select('chr-error'):e.decompose()
    for a in page.select('a[tabindex="-1"]'):del a['tabindex']
    # Browser shadow roots inherit these semantic tokens; source component CSS is unchanged.
    style=page.new_tag('style');style.string='nav[aria-label="Primary"]>div>ul>li>a{padding-left:14px;padding-right:14px}';header.append(style)

shared(s);shared(company)
sections=s.main.find_all('section',recursive=False)
# Reuse the captured image-slide markup for all four hero moments.
hero=s.select_one('chr-header-carousel');slides=hero.select_one('.glide__slides');hero_template=copy.deepcopy(slides.select('chr-header-carousel-slide')[1]);slides.clear()
hero_entries=[('THE FLINTVELLUM ARCHIVE','Objects worth knowing',approved['homeHeroSubtitle'],'w-0001','catalogue.html'),('100 WATCHES','Independent minds. Enduring design.','From Berneron and Cartier to Patek Philippe, explore the watch archive.','w-0003',caturl('watches')),('100 TRADING CARD LOTS','The collector’s eye','Discover graded cards, rare parallels and the names that define a collection.','c-0002',caturl('cards')),('50 PIECES OF MEMORABILIA','Beyond the screen. Beyond the game.','Explore objects catalogued from the worlds of film and sport.','m-0004',caturl('memorabilia'))]
for idx,(eyebrow,title,desc,id,target) in enumerate(hero_entries):
    slide=copy.deepcopy(hero_template);x=byid[id]
    slide.select_one('[aria-roledescription="Slide"]')['aria-label']=title
    settext(slide.select_one('.chr-label'),eyebrow);settext(slide.find('h2'),title);settext(slide.select_one('.chr-heading-s-serif'),desc)
    slide.select_one('.chr-hero-banner__details-list').clear()
    appendhtml(slide.select_one('.chr-hero-banner__details-list'),'<li class="chr-hero-banner__details-item"><span class="chr-label">CLOSED AUCTIONS · SOURCE CATALOGUES</span></li>')
    a=slide.select_one('.chr-hero-banner__button a');a['href']=target;a['aria-label']='Explore '+('the archive' if idx==0 else CATS[x['category']]);settext(a.select_one('.chr-button__text'),'Explore the archive' if idx==0 else 'Explore '+CATS[x['category']].lower())
    image(slide,x,eager=idx==0)
    banner=slide.select_one('.chr-hero-banner');banner['style']='--c-hero-banner-background:var(--fv-soft)'
    if idx==0:
        banner['class']=['chr-hero-banner','chr-hero-banner--carousel','chr-hero-banner--dark','chr-section--black'];banner['style']='--c-hero-banner-background:var(--fv-ink)'
        a['class']=[c.replace('--light','--dark') for c in a['class']]
    slide['data-theme-arrows']='light' if idx==0 else 'dark';slide['data-theme-pagination']=slide['data-theme-arrows'];slides.append(slide)
# The editorial highlight carousel uses real lot records.
promo=sections[0];settext(promo.find('h2'),'Selected from the archive')
for tile,id in zip(promo.select('.glide__slide'),['w-0001','c-0002','m-0004','w-0003','c-0014','m-0016']):
    x=byid[id];image(tile,x);settext(tile.select_one('.chr-auction-tile-next__detail span'),CATS[x['category']]+' · Auction closed');settext(tile.find('h3'),x['title']);tile.find('a')['href']=url(x)
# Keep both responsive forms of the original upcoming-auctions block, now closed sales.
auction_groups=[]
for cat in CATS:
    counts=Counter(x['auction'] for x in lots if x['category']==cat)
    for name,count in counts.most_common(2):
        members=[x for x in lots if x['auction']==name and x['category']==cat];auction_groups.append((name,count,cat,members[0]))
for block in sections[1].select('chr-upcoming-auctions'):
    settext(block.find('h2'),'From the auction archive')
    filters=block.select('chr-quick-filters button')
    for b,(key,label) in zip(filters,[('all','All'),*CATS.items()]):settext(b.select_one('.chr-button__text'),label);b['data-category-filter']=key
    for a in block.select('a[href]'):a['href']='catalogue.html'
    old_tiles=block.select('chr-auction-tile-next');mobile='fv-upcoming-mobile' in block.get('class',[])
    template=copy.deepcopy(old_tiles[0] if mobile else old_tiles[0].parent);container=old_tiles[0].parent if mobile else old_tiles[0].parent.parent;container.clear()
    for name,count,cat,x in auction_groups:
        item=copy.deepcopy(template);item['data-auction-category']=cat;tile=item if mobile else item.find('chr-auction-tile-next');image(tile,x)
        detail=tile.select_one('.chr-auction-tile-next__details');detail.clear();appendhtml(detail,f'<span class="chr-label">{count} LOTS · AUCTION CLOSED</span>')
        settext(tile.find('h3'),name);tile.find('a')['href']='catalogue.html?'+urlencode({'auction':name,'category':cat})
        settext(tile.select_one('.chr-auction-tile-next__icons'),CATS[cat]);container.append(item)
    status=block.select_one('[role="status"]')
    if status:status['aria-label']='Found 6 sales'
# The lot carousel retains source lot tiles, populated across all three categories.
trending=sections[2];settext(trending.find('h2'),'Selected lots')
for a in trending.select('a[href]'):a['href']='catalogue.html'
track=trending.select_one('.glide__slides');tile_wrapper=copy.deepcopy(track.find(recursive=False));track.clear()
featured=['w-0001','c-0001','m-0004','w-0003','c-0002','m-0016','w-0009','c-0013','m-0020','w-0014','c-0022','m-0036']
for id in featured:
    wrapper=copy.deepcopy(tile_wrapper);wrapper.clear();wrapper.append(lot_tile(byid[id]));track.append(wrapper)
# Replace the newsletter promise with a functioning catalogue action.
banner=sections[3];settext(banner.find('h3'),'A collection to return to');settext(banner.select_one('.chr-body'),'Save the objects that catch your eye. Your selection stays in this browser, ready for your next visit.')
b= banner.find('button');b.name='a';b.attrs={'class':b['class'],'href':'catalogue.html?saved=1'};settext(b.select_one('.chr-button__text'),'VIEW SAVED LOTS');image(banner,byid['w-0014'],1)
stories=sections[4];settext(stories.find('h2'),'Objects in focus')
for tile,id in zip(stories.select('.chr-feature-card-next'),['m-0004','c-0022','w-0001']):
    x=byid[id];image(tile,x);settext(tile.find('time'),'Auction closed');settext(tile.select_one('.chr-feature-card-next__category'),CATS[x['category']]);a=tile.select_one('.chr-feature-card-next__link');settext(a,x['title']);a['href']=url(x)
for a in stories.select('header a,footer a'):a['href']='catalogue.html'
more=sections[5];settext(more.find('h2'),'More from FlintVellum')
for tile,(title,desc,target,id) in zip(more.select('.chr-promo-banner-next'),[('The auction archive','250 lots across watches, trading cards and memorabilia.','catalogue.html','w-0003'),('How it works','Consignment, authentication, custody and settlement.','company.html#how-it-works','c-0013'),('About the house','A London auction house built for collectors and consignors.','company.html#about','m-0016')]):
    settext(tile.find('h3'),title);settext(tile.select_one('.chr-body'),desc);tile.find('a')['href']=target;tile.find('a').attrs.pop('target',None);image(tile,byid[id])
# Make all remaining homepage calls to action local and remove stale source labels.
for a in s.main.select('a[href]'):
    if a['href'].startswith('https://'):a['href']='catalogue.html'

# Keep the approved consignment policy visible on the homepage as well as the company page.
process=copy.deepcopy(company.select_one('#how-it-works'))
process['class']=['chr-section','fv-home-process']
container=s.new_tag('div',attrs={'class':'container-fluid'})
for node in list(process.contents):container.append(node.extract())
process.append(container)
more.insert_before(process)
careers_callout=fragment('<section id="careers" class="chr-section fv-home-careers"><div class="container-fluid"><div><p class="chr-label">JOIN FLINTVELLUM</p><h2 class="chr-heading-l-serif">Careers at FlintVellum</h2><p>Explore our open roles in auctions, settlement and consignments. International candidates are welcome.</p></div><a class="chr-button chr-button--secondary chr-button--lg chr-button--light" href="careers/"><span class="chr-button__text">View open roles</span></a></div></section>')
more.insert_before(careers_callout)

shell=copy.deepcopy(s);shell.main.clear()
def newpage(title,html):
    page=copy.deepcopy(shell);page.title.string=title+' | FlintVellum';appendhtml(page.main,html);return page

def write(page,path):
    for anchor in page.select('a[href]'):
        if anchor['href'] in ['company.html#roles','#roles'] and 'Careers' in content(anchor):
            anchor['href']='careers/'
        elif anchor['href']=='company.html#how-it-works':
            anchor['href']='index.html#how-it-works'
    for e in page.select('[id^="chr-img__"]'):del e['id']
    out=str(page).replace('viewbox=','viewBox=').replace('textlength=','textLength=').replace('lengthadjust=','lengthAdjust=')
    out=out.replace('<script defer="" src="fingerprint.js"></script>','<script src="fingerprint.js" defer></script>\n')
    assert out.count('fingerprint.js')==1 and re.search(r'<script src="fingerprint.js" defer></script>\s*</body>',out)
    (ROOT/path).parent.mkdir(parents=True,exist_ok=True);(ROOT/path).write_text(out)

careers=newpage('Careers', '<div class="container-fluid fv-careers"><header><p class="chr-label">JOIN FLINTVELLUM</p><h1 class="chr-heading-xl-serif">Careers at FlintVellum</h1><p>Help build our auction house across auctions, settlement and consignments.</p></header></div>')
careers.head.insert(0,careers.new_tag('base',href='../'))
careers.find('meta',attrs={'name':'description'})['content']='Open roles at FlintVellum. UK or EU preferred; international candidates welcome. Must overlap UK hours.'
roles=copy.deepcopy(company.select_one('#roles'))
settext(roles.select_one('#roles-heading'),'Open roles')
careers.select_one('.fv-careers').append(roles)
# The recruitment contact is already present beside the roles on this page.
careers.select_one('#footerHost .fv-contact').decompose()
write(careers,'careers/index.html')

intro='An archive of closed auctions from the original auction houses. These lots are not offered for bidding by FlintVellum.'
filter_options=lambda items:''.join(f'<option value="{E(v)}">{E(v)}</option>' for v in sorted(set(items)))
page=newpage('Auction archive',f'''<div class="container-fluid fv-catalogue">
<header class="fv-catalogue-heading"><p class="chr-label">THE FLINTVELLUM ARCHIVE</p><h1 class="chr-heading-xl-serif">Auction archive</h1><p>{intro} <a href="archive.html">About the archive</a></p></header>
<nav class="fv-category-tabs" aria-label="Collection categories"><a href="catalogue.html" data-category="all">All lots <span>250</span></a>{''.join(f'<a href="{caturl(k)}" data-category="{k}">{v} <span>{sum(x["category"]==k for x in lots)}</span></a>' for k,v in CATS.items())}</nav>
<form class="fv-filters" id="catalogue-filters" role="search"><label class="fv-search-label">Search the archive<input name="q" type="search" placeholder="Maker, object, player or reference"></label><label>Maker<select name="maker"><option value="">All makers</option>{filter_options(x['maker'] for x in lots)}</select></label><label>Auction<select name="auction"><option value="">All auctions</option>{filter_options(x['auction'] for x in lots)}</select></label><label>Sort by<select name="sort"><option value="curated">Archive order</option><option value="result-desc">Hammer: high to low</option><option value="result-asc">Hammer: low to high</option><option value="estimate-desc">Estimate: high to low</option><option value="estimate-asc">Estimate: low to high</option><option value="year-desc">Year: newest first</option></select></label><label class="fv-check"><input type="checkbox" name="result" value="1"> With a verified hammer</label><label class="fv-check"><input type="checkbox" name="saved" value="1"> Saved lots</label><button class="fv-text-button" type="reset">Clear filters</button><button class="fv-text-button" type="submit">Search</button></form>
<div class="fv-results-line"><p id="result-count" role="status" aria-live="polite">250 lots · All auctions closed</p><p>Prices shown in GBP</p></div><div class="fv-lot-grid" id="lot-grid"></div>
<p class="fv-empty" hidden>No lots match your selection. <button type="button" data-clear-filters>Clear filters</button></p><nav class="fv-pagination" aria-label="Catalogue pages"></nav>
<noscript><p>All 250 lots are listed below. Enable JavaScript to search, filter and save lots.</p><style>.fv-result[hidden]{{display:block!important}}.fv-filters,.fv-pagination{{display:none}}</style></noscript>
<p class="fv-price-note">Card ranges are derived from verified hammer prices, not auction-house estimates. Converted figures use the supplied 16 October 2026 exchange rates. <a href="archive.html#prices">Read the price notes</a>.</p></div>''')
grid=page.find(id='lot-grid')
for i,x in enumerate(lots):
    record=page.new_tag('article',attrs={'class':'fv-result','data-id':x['id'],'data-category':x['category'],'data-maker':x['maker'],'data-auction':x['auction'],'data-result':'' if x['result'] is None else str(x['result']),'data-estimate':str(x['estimateLow']),'data-year':str(x['year'] or ''),'data-search':' '.join(str(x[k]) for k in ['id','title','maker','reference','year','specs','provenance']).casefold(),'data-subtype':next((n.split(': ',1)[1] for n in sources[x['id']]['notes'] if n.startswith('Memorabilia subtype:')),'')})
    if i>=24:record['hidden']=''
    record.append(lot_tile(x));grid.append(record)
write(page,'catalogue.html')
# Static detail pages, so every lot and its source notes also work without JavaScript.
for x in lots:
    src=sources[x['id']];label,estimate=price(x)
    source_name={'www.phillips.com':'Phillips','www.christies.com':'Christie’s','onlineonly.christies.com':'Christie’s','www.sothebys.com':'Sotheby’s','www.fanaticscollect.com':'Fanatics Collect'}.get(urlparse(src['url']).netloc,urlparse(src['url']).netloc)
    result=money(x['result']) if x['result'] is not None else 'Not publicly verified'
    notes=''.join(f'<li>{E(n)}</li>' for n in src['notes'])
    references=''.join(f'<li><a href="{E(u)}" target="_blank" rel="noopener">{E(urlparse(u).netloc)}: reference {i+1}</a></li>' for i,u in enumerate(src['referenceUrls']))
    original_price='' if src['originalPrice'] is None else f'<p>Original source price: {money(src["originalPrice"],src["originalCurrency"])} ({E(str(src["originalPriceType"]).replace("_"," "))}).</p>'
    fx=f'<p>GBP conversion: {E(src["originalCurrency"])} × {src["fxToGBP"]:.8f}, rate dated {E(src["fxDate"])}. Converted prices are rounded to whole pounds.</p>' if src['originalCurrency']!='GBP' else '<p>Source prices are in GBP.</p>'
    thumbs=''.join(f'<a class="fv-gallery-thumb" href="{E(path)}" data-gallery-index="{i}" aria-label="View image {i+1} of {len(x["images"])}"><img src="{E(path)}" loading="lazy" alt="{E(x["title"])} · view {i+1}"></a>' for i,path in enumerate(x['images']))
    page=newpage(x['title'],f'''<div class="container-fluid fv-detail"><nav class="fv-breadcrumb" aria-label="Breadcrumb"><a href="catalogue.html">Archive</a><span>/</span><a href="{caturl(x['category'])}">{CATS[x['category']]}</a><span>/</span><span>{E(x['id'])}</span></nav>
<div class="fv-detail-grid"><section class="fv-gallery" aria-label="Lot photographs"><a class="fv-gallery-main" href="{x['images'][0]}" aria-label="Enlarge lot photograph"><img id="lot-image" src="{x['images'][0]}" alt="{E(x['title'])}" fetchpriority="high"></a><p class="fv-gallery-count">1 / {len(x['images'])} · Select a view, or enlarge the photograph</p><div class="fv-gallery-thumbs">{thumbs}</div></section>
<section class="fv-lot-summary"><p class="chr-label">{CATS[x['category']]} · Archive {E(x['id'])}</p><h1 class="chr-heading-l-serif">{E(x['title'])}</h1><p class="fv-lot-reference">{E(x['reference'])}</p><p class="fv-closed">Auction closed</p><dl class="fv-lot-prices"><div><dt>{label}</dt><dd>{estimate}</dd></div><div><dt>Verified hammer</dt><dd>{result}</dd></div></dl>{'<p class="fv-price-note">Indicative range: 80%–120% of the verified hammer, not a published auction estimate.</p>' if x['category']=='cards' else ''}
<p>{E(x['auction'])}</p><p class="fv-source-credit">Source: {E(source_name)} · Original lot {E(src['originalLot'])}</p><p class="fv-price-note">A historical auction record. This item is not available to bid on here.</p><button class="chr-button chr-button--secondary chr-button--lg chr-button--light chr-button--full-width" data-save-lot="{x['id']}" data-lot-title="{E(x['title'])}" aria-pressed="false"><span class="chr-button__text">Save lot</span></button><a class="fv-source-link" href="{E(src['url'])}" target="_blank" rel="noopener">View the original catalogue ↗</a></section></div>
<div class="fv-object-notes"><section><h2 class="chr-heading-m-serif">Lot details</h2><dl class="fv-specs"><div><dt>Maker</dt><dd>{E(x['maker'])}</dd></div><div><dt>Year</dt><dd>{E(x['year']) if x['year'] else 'Not established'}</dd></div><div><dt>Reference</dt><dd>{E(x['reference'])}</dd></div></dl><ul>{''.join(f'<li>{E(v)}</li>' for v in x['specs'])}</ul></section><section><h2 class="chr-heading-m-serif">Condition</h2><p>{E(x['condition'])}</p><h2 class="chr-heading-m-serif">Provenance</h2><p>{E(x['provenance'])}</p></section></div>
<details class="fv-source-notes"><summary>Source, price notes and catalogue corrections</summary><p>Descriptions, signatures, grading and game or screen use remain source catalogue attributions. FlintVellum has not independently inspected these archived objects.</p>{fx}{original_price}<ul>{notes}</ul><h3>Supporting sources</h3><ul>{references}</ul><a href="archive.html#prices">About archive prices and attribution</a></details>
<section class="fv-related"><h2 class="chr-heading-l-serif">More from {CATS[x['category']].lower()}</h2><div class="fv-lot-grid"></div></section></div>''')
    page.head.insert(0,page.new_tag('base',href='../'))
    page.find('meta',attrs={'name':'description'})['content']=x['title']+' · Closed auction record with photographs, condition and source notes.'
    related=[v for v in lots if v['category']==x['category'] and v['id']!=x['id']]
    start=int(x['id'].split('-')[1])%len(related)
    for v in (related+related)[start:start+4]:page.select_one('.fv-related .fv-lot-grid').append(lot_tile(v))
    write(page,url(x))
archive=newpage('About the archive',f'''<article class="container-fluid fv-archive-notes"><p class="chr-label">THE COLLECTION</p><h1 class="chr-heading-xl-serif">About the archive</h1><p class="fv-intro">250 lots. 947 photographs. Three collecting worlds.</p><p>{intro}</p><p>The supplied collection was assembled on 19 October 2026 from Phillips, Christie’s, Sotheby’s and Fanatics Collect. It contains 100 watches, 100 trading-card lots and 50 pieces of memorabilia, including 14 film and 36 sports lots.</p><h2 id="prices" class="chr-heading-l-serif">Reading the prices</h2><p>All 250 auctions are closed. A verified hammer price is available for 127 lots. Where a public hammer was not verified, we say so. A missing result does not mean an item was unsold.</p><p>Watch and memorabilia estimates are source catalogue estimates. Card ranges are derived as 80%–120% of verified final hammer bids, because the card source does not publish estimates. Derived ranges are labelled throughout the archive.</p><p>Non-GBP figures are converted using the supplied Frankfurter rates dated 16 October 2026 and rounded to whole pounds. These are reference conversions, not exchange rates at the date of sale. Each lot’s source notes retain the original currency and price type. Premium-inclusive totals are never substituted for hammer prices.</p><h2 class="chr-heading-l-serif">Condition and attribution</h2><p>Catalogue condition, ownership, signatures and game or screen use remain attributions by the original auction house. No physical inspection, independent authentication, regrading or timekeeping test was performed for this archive.</p><p>Ten exact years are unknown. For memorabilia, a year can identify a season, event or film release. Source conflicts and catalogue corrections are retained on the relevant lot pages. The two-card lot c-0022 remains one lot, with both certificates recorded in its notes.</p><h2 class="chr-heading-l-serif">Using the collection</h2><p>Search by object, maker, player or reference. Narrow the archive by category, maker or auction, then open a lot to see every supplied photograph and its original source. Saved lots stay in this browser and do not require an account.</p><p><a class="fv-source-link" href="catalogue.html">Explore all 250 lots →</a></p><h2 class="chr-heading-l-serif">Collection records</h2><p><a href="data/REPORT.md">Full collection report</a> · <a href="data/lots.json">Lot data</a> · <a href="data/sources.json">Source records</a></p></article>''')
write(archive,'archive.html');write(s,'index.html');write(company,'company.html')
manifest=json.loads((ROOT/'clone.json').read_text())
manifest['pages']=['/','catalogue.html','archive.html','company.html','careers/']+[url(x) for x in lots]
manifest['collection']={'lots':250,'images':947,'status':'closed','data':'data/lots.json','sources':'data/sources.json','report':'data/REPORT.md'}
(ROOT/'clone.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Populated 250 static lot pages, 947 images, homepage, catalogue, company and archive notes.')
