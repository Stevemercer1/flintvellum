#!/usr/bin/env python3
"""Rebuild the FlintVellum branding from the saved pristine mirror, without cumulative edits."""
from pathlib import Path
from bs4 import BeautifulSoup
import copy,json,re,subprocess
ROOT=Path(__file__).resolve().parent.parent

def git_file(ref):
    return subprocess.check_output(['git','show',ref],cwd=ROOT,text=True)

def document(text):return BeautifulSoup(text,'html.parser')

pristine=git_file('christies-pristine:index.html')
original=document(git_file('christies-pristine^:index.html'))
approved=json.loads((ROOT/'docs/site-copy.json').read_text())
original.select_one('.hero-copy .intro').string=approved['companyHeroSubtitle']
original.select('#how-it-works .steps li')[2].find('p').string=approved['settlementStep']
for location in original.select('.role-location'):
    location.string=approved['roleLocation']
original.select_one('#roles-heading').string='Careers'
original.select('.role')[0].find_all('p',recursive=False)[1].string=approved['backendSalary']
contact=original.select_one('.recruiter');contact.clear();contact.append(approved['contactLine']);contact.append(original.new_tag('br'))
email=original.new_tag('a',href=approved['contactMailto']);email.string=approved['contactEmail'];contact.append(email)
founder=json.loads((ROOT/'docs/founder-copy.json').read_text())
about=original.select_one('#about');about['class']=['content','wrap','fv-founder','fv-founder-grid']
about.select_one('#about-heading').string=founder['heading']
about.select_one('.section-label').string='About the founder'
line=original.new_tag('p',attrs={'class':'fv-founder-line'});line.string=founder['founderLine'];about.find('h2').insert_after(line)
body=about.select_one('.about-copy');body['class']=['fv-founder-copy'];body.clear()
for paragraph in founder['paragraphs']:
    node=original.new_tag('p');node.string=paragraph;body.append(node)
s=document(pristine)
mark=document((ROOT/'assets/brand/monogram.svg').read_text()).svg
word=document((ROOT/'assets/brand/wordmark.svg').read_text()).svg
mark['x']='0';mark['y']='10';mark['width']='80';mark['height']='80'
word['x']='105';word['y']='0';word['width']='480';word['height']='100'
logo='<svg class="fv-full-logo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 100" role="img" aria-label="FlintVellum">'+str(mark)+str(word)+'</svg>'
(ROOT/'flintvellum-logo.svg').write_text(logo.replace('viewbox=', 'viewBox=').replace('textlength=', 'textLength=').replace('lengthadjust=', 'lengthAdjust=')+'\n')
s.title.string='FlintVellum | Auctions & Collectibles'
s.find('h1').string='FlintVellum Auction House Home Page'
meta=s.find('meta',attrs={'name':'description'})
if meta:meta['content']=original.find('meta',attrs={'name':'description'})['content']
s.head.append(s.new_tag('link',rel='stylesheet',href='https://fonts.googleapis.com/css2?family=DM+Serif+Display&display=swap'))
s.head.append(s.new_tag('link',rel='icon',type='image/svg+xml',href='assets/brand/monogram.svg'))
header=s.find(id='headerHost').find('template')
anchor=header.select_one('[data-qa="header-logo-link"]')
anchor.clear();anchor.append(document(logo).svg);anchor['href']='./';anchor['aria-label']='FlintVellum home'
style=s.new_tag('style');style.string='''
.fv-full-logo{display:block;width:188px;height:auto;max-width:100%;color:inherit}
@media(max-width:1023px){.fv-full-logo{width:164px}}
@media(min-width:1024px) and (max-width:1199px){nav[aria-label="Primary"]>div>ul>li>a{padding-left:12px;padding-right:12px}.fv-full-logo{width:164px}}
''';header.append(style)
footer=s.find(id='footerHost').find('template')
for a in s.select('a[href]'):
    href=a['href']
    if '/about/careers/' in href:a['href']='company.html#roles'
    elif '/about/overview' in href:
        a['href']='company.html#about'
        for text in list(a.find_all(string=True)):
            text.replace_with(str(text).replace('Christie’s','FlintVellum').replace("Christie's",'FlintVellum'))
    elif '/help/selling-guide/' in href or '/auction-estimates' in href:a['href']='company.html#how-it-works'
for text in footer.find_all(string=True):
    if '©' in text:text.replace_with(re.sub(r'CHRISTIE[’\']S|Christie[’\']s','FlintVellum',str(text)))
footer_style=s.new_tag('style');footer_style.string='''
.fv-contact{display:flex;align-items:center;justify-content:space-between;gap:32px;padding:30px 48px;background:var(--fv-ink);color:var(--fv-paper);font:300 14px/1.6 ABCArizonaSans,Arial,sans-serif}
.fv-contact .fv-full-logo{width:188px;height:auto;flex-shrink:0}.fv-contact p{margin:0}.fv-contact a{text-decoration:underline;text-underline-offset:3px}
@media(max-width:767px){.fv-contact{padding:28px 20px;flex-direction:column;align-items:flex-start;gap:20px}}
''';footer.append(footer_style)
contact=s.new_tag('div',attrs={'class':'fv-contact'})
contact.append(document(logo).svg)
contact.append(copy.deepcopy(original.select_one('.recruiter')))
footer.append(contact)
# Keep the original company information and both protected roles intact on their own page.
company=copy.deepcopy(s)
company.title.string='FlintVellum | About the house & careers'
company.find('main').replace_with(copy.deepcopy(original.find('main')))
company.main['class']=['fv-legacy']
company.main.append(copy.deepcopy(original.select_one('footer .footer-location')))
company.find(id='footerHost').select_one('.fv-contact').decompose()
for a in company.select('a[href="company.html#how-it-works"],a[href="company.html#about"],a[href="company.html#roles"]'):
    a['href']='#'+a['href'].split('#')[1]
for page,name in [(s,'index.html'),(company,'company.html')]:
    text=str(page).replace('<script defer="" src="fingerprint.js"></script>','<script src="fingerprint.js" defer></script>\n')
    if text.count('fingerprint.js')!=1 or not re.search(r'<script src="fingerprint.js" defer></script>\s*</body>',text):raise RuntimeError('Analytics hook misplaced')
    (ROOT/name).write_text(text)
print('Rebuilt index.html, company.html and flintvellum-logo.svg from the pristine mirror.')
