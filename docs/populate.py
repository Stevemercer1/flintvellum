#!/usr/bin/env python3
"""Populate the saved Christie’s mirror with the supplied, closed auction archive."""
from pathlib import Path
from bs4 import BeautifulSoup
from collections import Counter
from html import escape
from urllib.parse import urlencode, urlparse
import copy, hashlib, json, re, subprocess, sys
ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'_catalogue'
approved=json.loads((ROOT/'docs/site-copy.json').read_text())
catalogue_css='assets/catalogue.css?v='+hashlib.sha256((ROOT/'assets/catalogue.css').read_bytes()).hexdigest()[:12]
DATA.mkdir(exist_ok=True)
if len(sys.argv)>1:
    source=Path(sys.argv[1]).expanduser().resolve()
    from import_catalogue import merge
    merge(ROOT,source)
assert (DATA/'lots.json').exists(), 'First run: python3 docs/populate.py ../auction-data'
subprocess.run([sys.executable,str(ROOT/'docs/rebrand.py')],check=True,cwd=ROOT)
lots=json.loads((DATA/'lots.json').read_text());sources=json.loads((DATA/'sources.json').read_text())
assert len(lots)==len({x['id'] for x in lots})
assert all(x['status']=='closed' for x in lots)
for x in lots:
    for name in x['images']:assert (ROOT/name).is_file(), name
byid={x['id']:x for x in lots}
CATS={'watches':'Watches','cards':'Trading cards','memorabilia':'Memorabilia'}
from archive_display import title as display_title
EDITORIAL={'watches':('img/w-0014/02.jpg','The movement of a Lederer Central Impulse Chronometer'),'cards':('assets/editorial/cards.jpg','Japanese Pokémon cards on a dark table'),'memorabilia':('assets/editorial/cinema.jpg','A vintage projector casting a beam of light')}
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
    img.attrs={'src':x['images'][n],'alt':display_title(x),'class':'chr-img lazyloaded','decoding':'async','loading':'eager' if eager else 'lazy'}
    for e in el.select('source'):e.decompose()
def editorial(el,cat,eager=False):
    img=el if el.name=='img' else el.find('img')
    name,alt=EDITORIAL[cat]
    img.attrs={'src':name,'alt':alt,'class':'chr-img lazyloaded fv-editorial-photo','decoding':'async','loading':'eager' if eager else 'lazy'}
    if eager:img['fetchpriority']='high'
    for e in el.select('source'):e.decompose()
def price(x):
    basis=sources[x['id']]['estimateBasis']
    label='Derived historical range · GBP' if basis=='derived_from_verified_sale' else 'Historical estimate · GBP'
    return label,money(x['estimateLow'])+' – '+money(x['estimateHigh'])
def enquiry_only(x):
    # This is a sourcing route for a similar object, never a claim of available stock.
    return int(hashlib.sha256(('flintvellum-enquiry:'+x['id']).encode()).hexdigest()[:8],16)%3==0
def status_label(x):return 'Enquiry only' if enquiry_only(x) else 'Auction closed'
def currency_reference(x):
    return f'''<details class="fv-currency"><summary>Currency reference</summary><form hidden><div class="fv-form-row"><label>Amount in GBP<input name="amount" type="number" inputmode="decimal" min="0.01" max="1000000000000" step="0.01" value="{x['estimateLow']}" required></label><label>Convert to<select name="asset"><option value="BTC">Bitcoin</option><option value="ETH">Ethereum</option><option value="USDC">USDC</option><option value="USDT">USDT</option></select></label></div><p class="fv-conversion" data-conversion role="status" aria-live="polite"></p><p class="fv-price-note" data-rate-status></p><button type="submit" class="fv-text-button" data-refresh-rates>Refresh rates</button></form><noscript><p>Enable JavaScript to use the currency reference.</p></noscript><p class="fv-price-note">Indicative conversion using <a href="https://docs.cdp.coinbase.com/coinbase-app/track-apis/exchange-rates" target="_blank" rel="noopener">Coinbase reference rates</a>, excluding fees. This is not a settlement quote.</p></details>'''
def enquiry_form(x):
    if not enquiry_only(x):return ''
    return f'''<details class="fv-enquiry"><summary>Prepare a private enquiry</summary><p>Looking for a similar piece? Set out your budget and preferences below.</p><p class="fv-price-note">This prepares a draft for your email app. Nothing is sent from this page.</p><form data-enquiry-form data-title="{E(display_title(x))}" hidden><div class="fv-form-row"><label>Proposed budget in GBP<input name="budget" type="number" inputmode="decimal" min="0.01" max="1000000000000" step="0.01" required placeholder="Your proposed amount"></label><label>Preferred settlement<select name="preference"><option value="BTC">Bitcoin</option><option value="ETH">Ethereum</option><option value="USDC">USDC</option><option value="USDT">USDT</option><option value="other">Other major asset, on request</option></select></label></div><label>What matters to you?<textarea name="notes" rows="3" maxlength="2000" placeholder="Condition, provenance, or another detail you have in mind"></textarea></label><button class="chr-button chr-button--secondary chr-button--lg chr-button--light" type="submit"><span class="chr-button__text">Prepare enquiry</span></button></form><noscript><p>Enable JavaScript to prepare an enquiry.</p></noscript><div data-enquiry-result hidden><label>Your enquiry draft<textarea readonly rows="9" aria-label="Your enquiry draft"></textarea></label><div class="fv-enquiry-actions"><button type="button" class="fv-text-button" data-copy-draft>Copy enquiry</button><a data-email-draft>Open email draft ↗</a></div><p class="fv-price-note" data-copy-status role="status" aria-live="polite"></p></div></details>'''
def price_detail(x):
    label,value=price(x)
    src=sources[x['id']]
    if src['estimateBasis']=='derived_from_verified_sale':
        note='A derived range of 80–120% of the verified historical hammer price, converted to GBP. This is not a published auction estimate or an asking price.'
    else:
        note='The original auction estimate, shown as an approximate GBP equivalent. This is a historical reference, not an asking price.'
    result=f'<div><dt>Historical hammer · GBP</dt><dd>{money(x["result"])}</dd></div>' if x['result'] is not None else ''
    return f'<dl class="fv-lot-prices"><div><dt>{label}</dt><dd>{value}</dd></div>{result}</dl><p class="fv-price-note">{note}</p>'
s=soup((ROOT/'index.html').read_text());company=soup((ROOT/'company.html').read_text())
lot_template=copy.deepcopy(s.find('chr-lot-tile'))
def lot_tile(x):
    tile=copy.deepcopy(lot_template);tile['data-lot-id']=x['id']
    image(tile,x)
    for e in tile.select('[id]'):del e['id']
    anchor=tile.select_one('.chr-lot-tile__link');anchor['href']=url(x);settext(anchor,display_title(x))
    settext(tile.select_one('.chr-lot-tile__secondary-title'),CATS[x['category']]+' · '+status_label(x))
    for el in tile.select('.chr-lot-tile__price-container,.chr-lot-tile__dynamic-price'):el.decompose()
    label,value=price(x)
    appendhtml(tile.select_one('.chr-lot-tile__content'),f'<p class="fv-tile-price"><span>{label}</span><strong>{value}</strong></p>')
    button=tile.select_one('chr-button-save-lot button');button['data-save-lot']=x['id'];button['data-lot-title']=display_title(x);button['aria-label']='Save '+display_title(x);settext(button.select_one('.chr-button__text'),'Save lot')
    return tile

def shared(page):
    page.head.append(page.new_tag('link',rel='stylesheet',href=catalogue_css))
    script=page.new_tag('script',src='assets/catalogue.js',defer='');page.select_one('script[src="fingerprint.js"]').insert_before(script)
    header=page.select_one('#headerHost template')
    items=header.select('nav[aria-label="Primary"]>div>ul>li')
    groups=[('Archive','catalogue.html',[('Explore the archive','catalogue.html'),('Watches',caturl('watches')),('Trading cards',caturl('cards')),('Memorabilia',caturl('memorabilia')),('Saved lots','catalogue.html?saved=1')]),('Watches',caturl('watches'),[('All watches',caturl('watches'))]+[(m,'catalogue.html?'+urlencode({'category':'watches','maker':m})) for m in ['Rolex','Patek Philippe','Cartier','Berneron']]),('Cards',caturl('cards'),[('All trading cards',caturl('cards')),('Pokémon','catalogue.html?category=cards&q=Pokemon'),('Michael Jordan','catalogue.html?category=cards&q=Jordan'),('Shohei Ohtani','catalogue.html?category=cards&q=Ohtani')]),('Memorabilia',caturl('memorabilia'),[('All memorabilia',caturl('memorabilia')),('Film','catalogue.html?category=memorabilia&subtype=film'),('Sports','catalogue.html?category=memorabilia&subtype=sports')]),('The house','company.html#about',[('About FlintVellum','company.html#about'),('How it works','company.html#how-it-works'),('Our specialisms','company.html#collectibles'),('Careers','company.html#roles'),('About the archive','archive.html')])]
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
    footer=page.select_one('#footerHost template')
    logo=copy.deepcopy(header.select_one('.fv-full-logo'))
    contact=copy.deepcopy(page.select_one('.recruiter'));contact['class']=['fv-footer-contact-copy']
    footer.clear()
    markup=(ROOT/'docs/footer.html').read_text().replace('{{logo}}',str(logo)).replace('{{contact}}',str(contact)).replace('{{policy}}',E(approved['settlementPolicy']))
    appendhtml(footer,markup)
    for e in page.select('chr-error'):e.decompose()
    for a in page.select('a[tabindex="-1"]'):del a['tabindex']
    # Browser shadow roots inherit these semantic tokens; source component CSS is unchanged.
    style=page.new_tag('style');style.string='nav[aria-label="Primary"]>div>ul>li>a{padding-left:14px;padding-right:14px}';header.append(style)

shared(s);shared(company)
sections=s.main.find_all('section',recursive=False)
# Reuse the captured image-slide markup for all four hero moments.
hero=s.select_one('chr-header-carousel');slides=hero.select_one('.glide__slides');hero_template=copy.deepcopy(slides.select('chr-header-carousel-slide')[1]);slides.clear()
hero_entries=[('THE FLINTVELLUM ARCHIVE','Some objects stay with you.',approved['homeHeroSubtitle'],'w-0001','catalogue.html'),('WATCHES','Independent minds. Enduring design.','From Berneron and Cartier to Patek Philippe, explore the watch archive.','w-0003',caturl('watches')),('TRADING CARDS','The collector’s eye','Discover graded cards, rare parallels and the names that define a collection.','c-0002',caturl('cards')),('MEMORABILIA','Beyond the screen. Beyond the game.','Explore objects catalogued from the worlds of film and sport.','m-0014',caturl('memorabilia'))]
for idx,(eyebrow,title,desc,id,target) in enumerate(hero_entries):
    slide=copy.deepcopy(hero_template);x=byid[id]
    slide.select_one('[aria-roledescription="Slide"]')['aria-label']=title
    settext(slide.select_one('.chr-label'),eyebrow);settext(slide.find('h2'),title);settext(slide.select_one('.chr-heading-s-serif'),desc)
    slide.select_one('.chr-hero-banner__details-list').clear()
    appendhtml(slide.select_one('.chr-hero-banner__details-list'),'<li class="chr-hero-banner__details-item"><span class="chr-label">AN INVITATION TO LOOK CLOSER</span></li>')
    a=slide.select_one('.chr-hero-banner__button a');a['href']=target;a['aria-label']='Explore '+('the archive' if idx==0 else CATS[x['category']]);settext(a.select_one('.chr-button__text'),'Explore the archive' if idx==0 else 'Explore '+CATS[x['category']].lower())
    image(slide,x,eager=idx==0)
    slide.find('img')['class']='chr-img lazyloaded fv-hero-object'
    if idx==0:slide.find('img')['fetchpriority']='high'
    caption=fragment(f'<a class="fv-hero-object-caption" href="{url(x)}">{E(display_title(x))} <span>From the archive ↗</span></a>')
    slide.select_one('.chr-hero-banner__video-wrapper').append(caption)
    banner=slide.select_one('.chr-hero-banner');banner['style']='--c-hero-banner-background:var(--fv-soft)'
    if idx==0:
        banner['class']=['chr-hero-banner','chr-hero-banner--carousel','chr-hero-banner--dark','chr-section--black'];banner['style']='--c-hero-banner-background:var(--fv-ink)'
        a['class']=[c.replace('--light','--dark') for c in a['class']]
    slide['data-theme-arrows']='light' if idx==0 else 'dark';slide['data-theme-pagination']=slide['data-theme-arrows'];slides.append(slide)
# Named story controls and a direct, smooth-scroll invitation replace anonymous dots.
for bullet,label in zip(hero.select('.glide__bullet'),['Discover','Watches','Cards','Memorabilia']):
    bullet.name='button';bullet.clear();bullet['type']='button';bullet['aria-label']='Show '+label.lower();bullet.attrs.pop('role',None);settext(bullet,label)
hero.select_one('.glide__bullets').append(fragment('<a class="fv-scroll-cue" href="#discover">Scroll to discover <span aria-hidden="true">↓</span></a>'))
s.main['class']=['fv-home']
# The editorial highlight carousel uses real lot records.
promo=sections[0];promo['id']='discover';promo['class'].append('fv-discover');settext(promo.find('h2'),'Selected from the archive')
for tile,id in zip(promo.select('.glide__slide'),['w-0094','c-0014','m-0016','w-0051','c-0022','m-0011']):
    x=byid[id];image(tile,x);settext(tile.select_one('.chr-auction-tile-next__detail span'),CATS[x['category']]+' · '+status_label(x));settext(tile.find('h3'),display_title(x));tile.find('a')['href']=url(x)
# A photographic introduction to the house's collecting specialisms.
specialisms=sections[1];specialisms.clear();specialisms['id']='specialisms';specialisms['class']=['chr-section','fv-specialisms']
appendhtml(specialisms,'<div class="container-fluid"><header><p class="chr-label">OUR SPECIALISMS</p><h2 class="chr-heading-l-serif">Follow your fascination.</h2><p>Precision. Obsession. A moment that never quite leaves you.</p></header><div class="fv-specialism-grid"></div></div>')
for cat,desc in [('watches','Mechanical ingenuity. Unmistakable character.'),('cards','Small surfaces. Entire worlds.'),('memorabilia','Fragments of the screen. Echoes of the game.')]:
    name,alt=EDITORIAL[cat]
    appendhtml(specialisms.select_one('.fv-specialism-grid'),f'<a class="fv-specialism" href="{caturl(cat)}"><div class="fv-specialism-image"><img src="{name}" alt="{alt}" loading="lazy" decoding="async"></div><div class="fv-specialism-caption"><h3>{CATS[cat]}</h3><span aria-hidden="true">↗</span></div><p>{desc}</p></a>')
# The same photographs give the company specialisms a clear visual presence.
for category,cat in zip(company.select('#collectibles .category'),CATS):
    name,alt=EDITORIAL[cat]
    category.insert(0,fragment(f'<img class="fv-company-specialism" src="{name}" alt="{alt}" loading="lazy" decoding="async">'))
# The lot carousel retains source lot tiles, populated across all three categories.
trending=sections[2];settext(trending.find('h2'),'Selected lots')
for a in trending.select('a[href]'):a['href']='catalogue.html'
track=trending.select_one('.glide__slides');tile_wrapper=copy.deepcopy(track.find(recursive=False));track.clear()
featured=['w-0101','c-0101','m-0053','w-0022','c-0013','m-0039','w-0049','c-0057','m-0005','w-0065','c-0036','m-0006']
for id in featured:
    wrapper=copy.deepcopy(tile_wrapper);wrapper.clear();wrapper.append(lot_tile(byid[id]));track.append(wrapper)
# Replace the newsletter promise with a functioning catalogue action.
banner=sections[3];settext(banner.find('h3'),'A collection to return to');settext(banner.select_one('.chr-body'),'Save the objects that catch your eye. Your selection stays in this browser, ready for your next visit.')
b= banner.find('button');b.name='a';b.attrs={'class':b['class'],'href':'catalogue.html?saved=1'};settext(b.select_one('.chr-button__text'),'VIEW SAVED LOTS');image(banner,byid['w-0025']);banner['class'].append('fv-saved-banner')
stories=sections[4];settext(stories.find('h2'),'Objects in focus')
for tile,id in zip(stories.select('.chr-feature-card-next'),['m-0004','c-0026','w-0058']):
    x=byid[id];image(tile,x);settext(tile.find('time'),status_label(x));settext(tile.select_one('.chr-feature-card-next__category'),CATS[x['category']]);a=tile.select_one('.chr-feature-card-next__link');settext(a,display_title(x));a['href']=url(x)
for a in stories.select('header a,footer a'):a['href']='catalogue.html'
more=sections[5];settext(more.find('h2'),'More from FlintVellum')
for tile,(title,desc,target,id) in zip(more.select('.chr-promo-banner-next'),[('The auction archive','Objects with a past. A place to look closer.','catalogue.html','w-0031'),('How it works','Consignment, authentication, custody and settlement.','company.html#how-it-works','m-0002'),('About the house','A London auction house built for collectors and consignors.','company.html#about','m-0043')]):
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
careers_callout=fragment('<section id="careers" class="chr-section fv-home-careers"><div class="container-fluid"><div><p class="chr-label">CAREERS</p><h2 class="chr-heading-l-serif">The work behind the house.</h2><p>Explore draft role outlines in auctions, settlement and consignments.</p></div><a class="chr-button chr-button--secondary chr-button--lg chr-button--light" href="careers/"><span class="chr-button__text">Explore the roles</span></a></div></section>')
more.insert_before(careers_callout)

shell=copy.deepcopy(s);shell.main.clear();shell.main.attrs.pop('class',None)
def newpage(title,html):
    page=copy.deepcopy(shell);page.title.string=title+' | FlintVellum';appendhtml(page.main,html);return page

def write(page,path):
    if page.select_one('.fv-currency'):
        resource='assets/enquiry.js'
        version=hashlib.sha256((ROOT/resource).read_bytes()).hexdigest()[:12]
        page.select_one('script[src="fingerprint.js"]').insert_before(page.new_tag('script',src=resource+'?v='+version,defer=''))
    if path=='index.html':
        for resource in ['assets/experience.css','assets/experience.js']:
            version=hashlib.sha256((ROOT/resource).read_bytes()).hexdigest()[:12]
            if resource.endswith('.css'):page.head.append(page.new_tag('link',rel='stylesheet',href=resource+'?v='+version))
            else:page.select_one('script[src="fingerprint.js"]').insert_before(page.new_tag('script',src=resource+'?v='+version,defer=''))
    for node in page.select('script[src],link[href]'):
        attr='src' if node.name=='script' else 'href'
        resource=node[attr].split('?')[0]
        if resource in ['assets/catalogue.js','assets/mirror.js']:
            node[attr]=resource+'?v='+hashlib.sha256((ROOT/resource).read_bytes()).hexdigest()[:12]
    for text in page.main.find_all(string=True):
        if re.match(r'\s*(Showing \d|Item \d)',str(text)):text.replace_with('Explore the collection')
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

role_details=json.loads((ROOT/'docs/role-details.json').read_text())
careers=newpage('Careers', '<div class="container-fluid fv-careers"><header><p class="chr-label">THE WORK BEHIND THE HOUSE</p><h1 class="chr-heading-xl-serif">Careers at FlintVellum</h1><p>Explore the work of auctions, settlement and consignments.</p></header></div>')
careers.head.insert(0,careers.new_tag('base',href='../'))
careers.find('meta',attrs={'name':'description'})['content']='Draft role outlines for FlintVellum: backend engineering and consignments. UK or EU preferred; international candidates welcome. Must overlap UK hours.'
roles=copy.deepcopy(company.select_one('#roles'))
settext(roles.select_one('#roles-heading'),'The role outlines')
careers.select_one('.fv-careers header').append(fragment(f'<p class="fv-role-status">{E(role_details["status"])}</p>'))
for role,key in zip(roles.select('.role'),['backend','sales']):
    detail=role_details[key];role['id']=detail['id']
    responsibilities=''.join(f'<li>{E(item)}</li>' for item in detail['responsibilities'])
    requirements=''.join(f'<li>{E(item)}</li>' for item in detail['requirements'])
    appendhtml(role,f'<div class="fv-role-details"><p class="fv-role-intro">{E(detail["intro"])}</p><div class="fv-role-columns"><section><h4>What you would do</h4><ul>{responsibilities}</ul></section><section><h4>What you would bring</h4><ul>{requirements}</ul></section></div><section><h4>{E(detail["contextHeading"])}</h4><p>{E(detail["context"])}</p></section><section><h4>Working arrangements</h4><p>{E(detail["arrangements"])}</p></section></div>')
careers.select_one('.fv-careers').append(roles)
write(careers,'careers/index.html')
company.select_one('#roles-heading').insert_after(fragment(f'<p class="fv-role-status">{E(role_details["status"])}</p>'))
for role,key in zip(company.select('.role'),['backend','sales']):
    role.append(fragment(f'<a class="fv-source-link" href="careers/#{role_details[key]["id"]}">Read the role outline →</a>'))

intro='Objects with a past. Stories still unfolding.'
filter_options=lambda items:''.join(f'<option value="{E(v)}">{E(v)}</option>' for v in sorted(set(items)))
page=newpage('The archive',f'''<div class="container-fluid fv-catalogue">
<header class="fv-catalogue-heading"><div><p class="chr-label">THE FLINTVELLUM ARCHIVE</p><h1 class="chr-heading-xl-serif">Behind the glass.</h1><p>{intro}</p><p class="fv-archive-status">Historical objects. Private sourcing enquiries.</p></div><img src="img/w-0088/01.jpg" alt="Breguet Classique Perpetual Calendar" fetchpriority="high"></header>
<nav class="fv-category-tabs" aria-label="Collection categories"><a href="catalogue.html" data-category="all">All objects</a>{''.join(f'<a href="{caturl(k)}" data-category="{k}">{v}</a>' for k,v in CATS.items())}</nav>
<form class="fv-filters" id="catalogue-filters" role="search"><label class="fv-search-label">Search the archive<input name="q" type="search" placeholder="Maker, object or player"></label><label>Maker<select name="maker"><option value="">All makers</option>{filter_options(x['maker'] for x in lots)}</select></label><label class="fv-check"><input type="checkbox" name="saved" value="1"> Saved objects</label><button class="fv-text-button" type="reset">Clear filters</button><button class="fv-text-button" type="submit">Search</button></form>
<div class="fv-results-line"><p id="result-count" role="status" aria-live="polite">From the archive · Discover and enquire</p></div><div class="fv-lot-grid" id="lot-grid"></div>
<p class="fv-empty" hidden>No objects match your selection. <button type="button" data-clear-filters>Clear filters</button></p><nav class="fv-pagination" aria-label="Browse the collection"></nav>
<noscript><p>Explore the collection below. Enable JavaScript to search, filter and save objects.</p><style>.fv-result[hidden]{{display:block!important}}.fv-filters,.fv-pagination{{display:none}}</style></noscript>
<p class="fv-price-note">Historical objects from the original auction houses. Enquiry-only entries let you prepare a sourcing request for a similar piece. None of these archived objects is offered for bidding here.</p></div>''')
grid=page.find(id='lot-grid')
# Keep the additions easy to find, then interleave the rest in a stable shuffled order.
additions=['w-0101','c-0101','m-0053','w-0102','m-0051','w-0103','m-0052','m-0054','m-0055']
ordered=[byid[key] for key in additions]+sorted((x for x in lots if x['id'] not in additions),key=lambda x:hashlib.sha256(('flintvellum-selection:'+x['id']).encode()).hexdigest())
for i,x in enumerate(ordered):
    record=page.new_tag('article',attrs={'class':'fv-result','data-id':x['id'],'data-category':x['category'],'data-maker':x['maker'],'data-search':' '.join(str(x[k]) for k in ['id','title','maker','reference','year','specs','provenance']).casefold(),'data-subtype':next((n.split(': ',1)[1] for n in sources[x['id']]['notes'] if n.startswith('Memorabilia subtype:')),'')})
    if i>=24:record['hidden']=''
    record.append(lot_tile(x));grid.append(record)
write(page,'catalogue.html')
# Original photographs and catalogue links accompany clearly labelled historical price evidence.
for x in lots:
    src=sources[x['id']];name=display_title(x)
    source_name={'www.phillips.com':'Phillips','www.christies.com':'Christie’s','onlineonly.christies.com':'Christie’s','www.sothebys.com':'Sotheby’s','www.fanaticscollect.com':'Fanatics Collect'}.get(urlparse(src['url']).netloc,urlparse(src['url']).netloc)
    thumbs=''.join(f'<a class="fv-gallery-thumb" href="{E(path)}" data-gallery-index="{i}" aria-label="Select another view"><img src="{E(path)}" loading="lazy" alt="{E(name)} · catalogue photograph"></a>' for i,path in enumerate(x['images']))
    page=newpage(name,f'''<div class="container-fluid fv-detail"><nav class="fv-breadcrumb" aria-label="Breadcrumb"><a href="catalogue.html">Archive</a><span>/</span><a href="{caturl(x['category'])}">{CATS[x['category']]}</a></nav>
<div class="fv-detail-grid"><section class="fv-gallery" aria-label="Object photographs"><a class="fv-gallery-main" href="{x['images'][0]}" aria-label="Enlarge lot photograph"><img id="lot-image" src="{x['images'][0]}" alt="{E(name)}" fetchpriority="high"></a><p class="fv-gallery-count">Select a view, or look closer.</p><div class="fv-gallery-thumbs">{thumbs}</div></section>
<section class="fv-lot-summary"><p class="chr-label">FROM THE {CATS[x['category']].upper()} ARCHIVE</p><h1 class="chr-heading-l-serif">{E(name)}</h1><p class="fv-closed">{status_label(x)}</p>{price_detail(x)}{currency_reference(x)}<p class="fv-source-credit">From the {E(source_name)} catalogue.</p><p class="fv-price-note">A historical auction record. This object is not available to bid on here.</p>{enquiry_form(x)}<button class="chr-button chr-button--secondary chr-button--lg chr-button--light chr-button--full-width" data-save-lot="{x['id']}" data-lot-title="{E(name)}" aria-pressed="false"><span class="chr-button__text">Save lot</span></button><a class="fv-source-link" href="{E(src['url'])}" target="_blank" rel="noopener">View the original catalogue ↗</a><details class="fv-source-notes"><summary>About this object</summary><p>Descriptions, condition, provenance, signatures, grading and game or screen use remain attributions by the original auction house. FlintVellum has not independently inspected these archived objects. Refer to the original catalogue for the full description and supporting records.</p></details></section></div>
<section class="fv-related"><h2 class="chr-heading-l-serif">Further discoveries</h2><div class="fv-lot-grid"></div></section></div>''')
    page.head.insert(0,page.new_tag('base',href='../'))
    page.find('meta',attrs={'name':'description'})['content']=name+' · From the FlintVellum archive.'
    related=[v for v in lots if v['category']==x['category'] and v['id']!=x['id']]
    start=int(x['id'].split('-')[1])%len(related)
    for v in (related+related)[start:start+4]:page.select_one('.fv-related .fv-lot-grid').append(lot_tile(v))
    write(page,url(x))
archive=newpage('Inside the archive','''<article class="fv-archive-story"><div class="fv-archive-story-image"><img src="assets/editorial/cinema.jpg" alt="A projector's beam revealing the darkness" fetchpriority="high"></div><div class="fv-archive-story-copy"><p class="chr-label">THE FLINTVELLUM ARCHIVE</p><h1 class="chr-heading-xl-serif">There is always<br>more to the story.</h1><p>A familiar silhouette. An unexpected detail. Something that makes you look again.</p><a class="fv-source-link" href="catalogue.html">Step inside the archive →</a><p class="fv-archive-status">Historical objects. Closed auctions.</p></div></article>''')
write(archive,'archive.html');write(s,'index.html');write(company,'company.html')
manifest=json.loads((ROOT/'clone.json').read_text())
manifest['pages']=['/','catalogue.html','archive.html','company.html','careers/']+[url(x) for x in lots]
manifest['collection']={'lots':len(lots),'images':sum(len(x['images']) for x in lots),'status':'closed','buildData':'_catalogue/lots.json','buildSources':'_catalogue/sources.json'}
(ROOT/'clone.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built the photographic archive, all object galleries, company and careers pages.')
