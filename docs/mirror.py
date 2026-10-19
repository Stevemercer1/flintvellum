#!/usr/bin/env python3
"""Christie's adapter for the framer-clone skill's mirror/detach/staticise passes.
Uses captured rendered HTML and shadow roots, not a reconstruction from text.
Raw downloads are cached. A normal visitor needs no build step.
"""
from pathlib import Path
from urllib.parse import urljoin,urlsplit,unquote
import hashlib,json,os,re,subprocess
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent.parent
CACHE=ROOT/'.mirror-cache'
SOURCE='https://www.christies.com/'
manifest={}

def asset(url,base=SOURCE):
    url=urljoin(base,url)
    if url.startswith('data:'): return url
    if url in manifest: return manifest[url]
    ext=Path(urlsplit(url).path).suffix.lower()
    if ext not in {'.css','.woff','.woff2','.ttf','.otf','.svg','.png','.jpg','.jpeg','.webp','.avif','.gif','.mp4'}: ext='.bin'
    folder='css' if ext=='.css' else 'fonts' if ext in {'.woff','.woff2','.ttf','.otf'} else 'video' if ext=='.mp4' else 'images'
    stem=re.sub(r'[^a-zA-Z0-9_-]','-',Path(unquote(urlsplit(url).path)).stem)[:65] or 'asset'
    rel=f'assets/{folder}/{stem}-{hashlib.sha256(url.encode()).hexdigest()[:10]}{ext}'
    manifest[url]=rel
    cached=CACHE/'downloads'/Path(rel).name
    cached.parent.mkdir(parents=True,exist_ok=True)
    out=ROOT/rel
    out.parent.mkdir(parents=True,exist_ok=True)
    if not cached.exists():
        result=subprocess.run(['curl','-fLsS','--retry','2','--max-time','40',url,'-o',str(cached)],capture_output=True)
        if result.returncode: raise RuntimeError(f'Cannot mirror {url}: {result.stderr.decode()[:200]}')
    data=cached.read_bytes()
    if ext=='.css':
        text=data.decode('utf8',errors='replace')
        def replace(m):
            ref=m[1].strip(' \"\'')
            if ref.startswith(('data:','#')): return m[0]
            if ref.startswith('%23'): return 'url(#'+ref[3:]+')'
            target=asset(ref,url)
            return 'url("'+os.path.relpath(ROOT/target,out.parent)+'")'
        text=re.sub(r'url\(([^)]+)\)',replace,text)
        out.write_text(text)
    else:out.write_bytes(data)
    print('Mirrored',rel,flush=True)
    return rel

def image_url(img):
    candidates=[]
    parent=img.find_parent('picture')
    nodes=([*parent.find_all('source'),img] if parent else [img])
    for node in nodes:
        raw=node.get('data-srcset') or node.get('srcset') or ''
        for item in raw.split(', '):
            match=re.match(r'\s*(https?://\S+)\s+(\d+)w\s*$',item)
            if match:candidates.append((int(match[2]),match[1]))
    if candidates:
        target=1440 if img.find_parent('chr-header-carousel') else 700
        return min(candidates,key=lambda p:abs(p[0]-target))[1]
    return img.get('data-src') or img.get('src')

def detach(s):
    for link in s.select('link[rel~=stylesheet]'):link['rel']=['stylesheet']
    for tag in list(s.find_all(['script','noscript'])):tag.decompose()
    for tag in list(s.select('#onetrust-consent-sdk, .chr-header-footer, .chr-live-chat')):tag.decompose()
    for tag in list(s.select('link[rel="canonical"],link[rel="preload"],link[rel="preconnect"],link[rel="dns-prefetch"],link[rel="icon"],link[rel="apple-touch-icon"],meta[property^="og:"],meta[name^="twitter:"]')):tag.decompose()
    for tag in s.find_all():
        for attr in list(tag.attrs):
            if attr.startswith('on') or attr.startswith('data-track') or attr.startswith('data-analytics') or attr in ['integrity','nonce']:del tag[attr]
    for link in list(s.find_all('link',href=True)):
        if 'stylesheet' not in link.get('rel',[]) or 'fast.fonts.net' in link['href']:link.decompose()
    return s

def localise(s):
    for link in s.select('link[rel="stylesheet"]'):link['href']=asset(link['href'])
    for img in s.find_all('img'):
        src=image_url(img)
        if src and not src.startswith('blob:'):img['src']=asset(src)
        for key in ['srcset','data-srcset','data-src','sizes','data-sizes','loading']:
            img.attrs.pop(key,None)
        img['decoding']='async'
        img['class']=[c for c in img.get('class',[]) if c not in ['lazyload','lazyloading']]+['lazyloaded']
    for source in list(s.select('picture source')):source.decompose()
    for a in s.select('a[href]'):
        if a['href'].startswith(('javascript:', '#')):continue
        a['href']=urljoin(SOURCE,a['href'])
    return s

def main():
    s=BeautifulSoup((CACHE/'homepage.html').read_text(),'html.parser')
    detach(s)
    for style in list(s.find_all('style')):
        if 'onetrust' in style.get_text().lower() or 'video-js' in style.get_text()[:500]:style.decompose()
    # Personalised ad slots cannot resolve without the source publisher's marketing backend.
    for tile in list(s.select('chr-braze-carousel-tile-banner')):
        slide=tile.find_parent(class_='glide__slide')
        if slide:slide.decompose()
    for host in list(s.select('chr-braze-generic-banner')):
        section=host.find_parent('section')
        if section:section.decompose()
    for slide in s.select('chr-header-carousel-slide'):
        video=slide.find('video')
        if video:
            poster=video.get('poster')
            container=slide.select_one('video-js')
            img=s.new_tag('img',src=poster,alt='Works from the Paris twentieth and twenty-first century art auctions')
            img['style']='width:100%;height:100%;object-fit:cover;display:block'
            if (ROOT/'assets/video/hero.mp4').exists():
                native=s.new_tag('video',src='assets/video/hero.mp4',poster=asset(poster),autoplay='',muted='',loop='',playsinline='',preload='metadata')
                native['class']=['fv-hero-video']
                native['style']='width:100%;height:100%;object-fit:cover;display:block'
                container.replace_with(native)
                for control in slide.select('chr-button-media-control button'):control['data-fv-video']='true'
            else:
                container.replace_with(img)
                for control in slide.select('chr-button-media-control'):control.decompose()
    localise(s)
    mobile_file=CACHE/'upcoming-mobile.html'
    if mobile_file.exists():
        desktop=s.select_one('chr-upcoming-auctions')
        desktop['class']=desktop.get('class',[])+['fv-upcoming-desktop']
        mobile=BeautifulSoup(mobile_file.read_text(),'html.parser')
        detach(mobile);localise(mobile)
        mobile.select_one('chr-upcoming-auctions')['class']=['hydrated','fv-upcoming-mobile']
        desktop.insert_after(mobile)
    capture=json.loads((CACHE/'capture.json').read_text())
    for host in capture['hosts']:
        shadow=BeautifulSoup(host['html'],'html.parser')
        detach(shadow);localise(shadow)
        template=s.new_tag('template',attrs={'shadowrootmode':'open'})
        for node in list(shadow.contents):template.append(node)
        s.find(id=host['id']).append(template)
    for track in s.select('.glide__slides'):
        track.attrs.pop('style',None)
        for child in track.find_all(recursive=False):child.attrs.pop('style',None)
    for loader in s.select('chr-loader-next'):loader.attrs.pop('style',None)
    for bullet in s.select('.glide__bullet'):
        bullet['role']='button';bullet['tabindex']='0'
    for i,bullet in enumerate(s.select('chr-header-carousel .glide__bullet')):bullet['aria-label']=f'Show slide {i+1}'
    s.head.append(s.new_tag('link',rel='stylesheet',href='assets/mirror.css'))
    s.body.append(s.new_tag('script',src='assets/mirror.js',defer=''))
    s.body.append(s.new_tag('script',src='fingerprint.js',defer=''))
    # The existing analytics hook is the final element before </body>.
    text=str(s).replace('<script defer="" src="fingerprint.js"></script>','<script src="fingerprint.js" defer></script>\n')
    (ROOT/'index.html').write_text(text)
    (ROOT/'clone.json').write_text(json.dumps({'source':SOURCE,'pages':['/'],'method':'Rendered HTML mirror with preserved shadow roots, original CSS, and local assets','assets':manifest},indent=2)+'\n')
    print('Mirror ready:',len(manifest),'local assets')
if __name__=='__main__':main()
