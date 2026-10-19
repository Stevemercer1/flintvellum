/* Static interaction layer for the mirrored HTML; no source analytics or auction API calls. */
(() => {
  const all = (q, root = document) => [...root.querySelectorAll(q)];
  all('template[shadowrootmode]').forEach(template => {
    const host = template.parentElement;
    if (!host.shadowRoot) host.attachShadow({ mode: 'open' }).append(template.content.cloneNode(true));
    template.remove();
  });
  all('button[data-fv-video]').forEach(button => {
    const video = button.closest('chr-header-carousel-slide').querySelector('video');
    const label = () => button.setAttribute('aria-label', video.paused ? 'Play Video' : 'Pause Video');
    video.addEventListener('play',label); video.addEventListener('pause',label);
    button.addEventListener('click',()=>{if(video.paused)video.play().catch(()=>{});else video.pause()});label();
    if(matchMedia('(prefers-reduced-motion: reduce)').matches)video.pause();
  });
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  all('chr-carousel').forEach(carousel => {
    const track = carousel.querySelector('.glide__track');
    const slides = carousel.querySelector('.glide__slides');
    if (!slides || !track) return;
    const items = [...slides.children];
    const hero = !!carousel.closest('chr-header-carousel');
    const lots = carousel.dataset.namespace === 'trendingLots';
    const upcoming = !!carousel.closest('chr-upcoming-auctions');
    let index = 0, step = 0, visible = 1;
    const bullets = all('.glide__bullet', carousel);
    const update = (instant = false) => {
      const activeItems = items.filter(item => !item.hidden);
      const width = track.clientWidth;
      visible = hero ? 1 : upcoming ? (innerWidth < 768 ? 1.15 : 2.4) : lots ? (innerWidth < 768 ? 1.4 : innerWidth < 1224 ? 3.3 : 4.3) : (innerWidth < 768 ? 1.15 : innerWidth < 1224 ? 2.2 : 3.2);
      const gap = lots ? 0 : 10;
      const itemWidth = hero ? width : (width + gap) / visible - gap;
      step = itemWidth + gap;
      slides.style.width = `${step * activeItems.length}px`;
      activeItems.forEach((item, i) => {
        item.style.width = `${itemWidth}px`;
        item.style.marginLeft = i ? `${gap / 2}px` : '0';
        item.style.marginRight = i < activeItems.length - 1 ? `${gap / 2}px` : '0';
      });
      index = Math.min(index, Math.max(0, activeItems.length - Math.floor(visible)));
      slides.style.transform = `translate3d(${-index * step}px,0,0)`;
      slides.style.transition = reduced.matches || instant ? 'none' : `transform ${hero ? 600 : 420}ms cubic-bezier(.23,1,.32,1)`;
      bullets.forEach((bullet, i) => {
        bullet.classList.toggle('glide__bullet--active', i === index);
        bullet.setAttribute('aria-pressed', String(i === index));
      });
      items.forEach((item, i) => { if (hero) item.inert = i !== index; });
      const announcement = carousel.querySelector('.glide > .visually-hidden');
      if (announcement) announcement.textContent = hero ? items[index].querySelector('h2')?.textContent || 'Selected story' : 'More from the archive';
    };
    const move = (delta, instant = false) => {
      const max = Math.max(0, items.filter(item => !item.hidden).length - Math.floor(visible));
      index = hero ? (index + delta + items.length) % items.length : Math.max(0, Math.min(max, index + delta));
      update(instant);
    };
    all('button', carousel).filter(b => !b.closest('.glide__slides')).forEach(button => {
      const label = `${button.getAttribute('aria-label') || ''} ${button.textContent}`.toLowerCase();
      if (label.includes('previous')) button.addEventListener('click', e => move(-1,e.detail===0));
      if (label.includes('next')) button.addEventListener('click', e => move(1,e.detail===0));
    });
    bullets.forEach((bullet, i) => {
      const select = e => { index = i; update(e?.detail===0); };
      bullet.addEventListener('click', select);
      if(bullet.tagName!=='BUTTON')bullet.addEventListener('keydown', e => { if (['Enter', ' '].includes(e.key)) { e.preventDefault(); select(e); } });
    });
    let start;
    track.addEventListener('touchstart', e => { start = e.changedTouches[0].clientX; }, { passive: true });
    track.addEventListener('touchend', e => { const delta = e.changedTouches[0].clientX - start; if (Math.abs(delta) > 45) move(delta < 0 ? 1 : -1); }, { passive: true });
    // Mouse dragging complements native touch scrolling and the keyboard controls.
    track.classList.add('fv-draggable');
    let drag=null,suppressClick=false;
    track.addEventListener('dragstart',e=>e.preventDefault());
    track.addEventListener('pointerdown',e=>{
      if(e.pointerType!=='mouse'||e.button!==0||e.target.closest('button,input,select'))return;
      suppressClick=false;drag={id:e.pointerId,x:e.clientX,y:e.clientY,moved:false};
    });
    track.addEventListener('pointermove',e=>{
      if(!drag||drag.id!==e.pointerId)return;
      const dx=e.clientX-drag.x,dy=e.clientY-drag.y;
      if(!drag.moved){if(Math.abs(dx)<8||Math.abs(dx)<Math.abs(dy))return;drag.moved=true;track.setPointerCapture(e.pointerId);track.classList.add('fv-dragging')}
      const max=Math.max(0,items.length-Math.floor(visible))*step;
      let position=-index*step+dx;if(position>0)position*=.25;if(position<-max)position=-max+(position+max)*.25;
      slides.style.transition='none';slides.style.transform=`translate3d(${position}px,0,0)`;
    });
    const finishDrag=e=>{
      if(!drag||drag.id!==e.pointerId)return;
      const moved=drag.moved,delta=e.clientX-drag.x;drag=null;track.classList.remove('fv-dragging');
      if(track.hasPointerCapture(e.pointerId))track.releasePointerCapture(e.pointerId);
      if(moved){suppressClick=true;if(e.type==='pointerup'&&Math.abs(delta)>45)move(delta<0?1:-1);else update();setTimeout(()=>suppressClick=false,0)}
    };
    track.addEventListener('pointerup',finishDrag);track.addEventListener('pointercancel',finishDrag);
    track.addEventListener('pointerleave',()=>{if(drag&&!drag.moved)drag=null});
    track.addEventListener('click',e=>{if(suppressClick){e.preventDefault();e.stopImmediatePropagation()}},true);
    carousel.addEventListener('fv:filtered', () => { index = 0; update(); });
    new ResizeObserver(()=>update(true)).observe(track);
    reduced.addEventListener('change',()=>update(true));
    update();
  });
  all('chr-upcoming-auctions').forEach(section => {
    all('[data-category-filter]', section).forEach(button => button.addEventListener('click', () => {
      const filter = button.dataset.categoryFilter;
      all('[data-category-filter]',section).forEach(b=>{const active=b===button;b.classList.toggle('chr-button--selected',active);b.setAttribute('aria-pressed',String(active));});
      const items=all('[data-auction-category]',section);
      items.forEach(item=>item.hidden=filter!=='all'&&item.dataset.auctionCategory!==filter);
      const status=section.querySelector('[role="status"]');if(status)status.textContent=`${items.filter(i=>!i.hidden).length} sales`;
      section.querySelector('chr-carousel')?.dispatchEvent(new Event('fv:filtered'));
    }));
  });
  const dialog = document.createElement('dialog');
  dialog.className = 'fv-dialog';
  dialog.innerHTML = '<button class="fv-dialog-close" aria-label="Close">×</button><div class="fv-dialog-body"></div>';
  document.body.insertBefore(dialog, document.querySelector('script[src="fingerprint.js"]'));
  dialog.querySelector('button').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', e => { if (e.target === dialog) { const r = dialog.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dialog.close(); } });
  const openDialog = (title, text, href, label) => {
    const body = dialog.querySelector('.fv-dialog-body');
    body.replaceChildren();
    const h = document.createElement('h2'); h.textContent = title; body.append(h);
    if (text) { const p = document.createElement('p'); p.textContent = text; body.append(p); }
    if (href) { const a = document.createElement('a'); a.href = href; a.textContent = label; body.append(a); }
    if (!dialog.open) dialog.showModal();
    return body;
  };
  function showSearch(query = '') {
    const body = openDialog('Search the archive');
    const form = document.createElement('form');form.className='fv-search-form';form.action='catalogue.html';form.method='get';
    form.innerHTML='<input name="q" type="search" aria-label="Search by keyword" placeholder="Maker, object, player or reference"><button type="submit">Search</button>';
    form.querySelector('input').value=query;body.append(form);form.querySelector('input').focus();
  }
  const header = document.querySelector('#headerHost')?.shadowRoot;
  if (header) {
    const style = document.createElement('style');
    style.textContent = '.fv-menu-open{height:auto!important;z-index:60!important;overflow:visible!important}.fv-menu-open>div{opacity:1!important;transform:none!important}.fv-drawer-open{transform:translateX(0)!important;overflow:auto;padding:24px}.fv-drawer-open details{border-bottom:1px solid var(--fv-rule);padding:16px 0;font-family:ABCArizonaSans,Arial,sans-serif}.fv-drawer-open summary{cursor:pointer;text-transform:uppercase}.fv-drawer-open details a{display:block;padding:10px 0;font-size:16px}.fv-drawer-open details div{margin:0!important;width:100%!important;padding:8px 0!important;display:block!important}.fv-drawer-open details ul{display:block!important}.fv-drawer-open details img{display:none}';
    header.append(style);
    const links = all('nav[aria-label="Primary"] a[aria-controls]', header);
    const closeMenus = () => { all('.fv-menu-open', header).forEach(e => { e.classList.remove('fv-menu-open'); e.inert = true; }); links.forEach(a => a.setAttribute('aria-expanded', 'false')); };
    links.forEach(link => {
      const menu = header.getElementById(link.getAttribute('aria-controls'))?.parentElement;
      if (!menu) return;
      const open = () => { closeMenus(); menu.classList.add('fv-menu-open'); menu.inert = false; link.setAttribute('aria-expanded', 'true'); };
      link.addEventListener('mouseenter', open);
      link.addEventListener('focus', open);
      link.addEventListener('click', e => { if (link.getAttribute('aria-expanded') !== 'true') { e.preventDefault(); open(); } });
    });
    header.querySelector('header').addEventListener('mouseleave', closeMenus);
    header.addEventListener('keydown', e => { if (e.key === 'Escape') closeMenus(); });
    const drawer = header.querySelector('nav[aria-label="Primary Navigation Drawer"]');
    const menuButton = header.querySelector('button[aria-label="Menu"]');
    if (drawer && menuButton) {
      links.forEach(link => {
        const details = document.createElement('details'); const summary = document.createElement('summary'); summary.textContent = link.textContent.trim(); details.append(summary);
        const panel = header.getElementById(link.getAttribute('aria-controls'));
        if (panel) { const content = panel.cloneNode(true); content.removeAttribute('id'); content.style.opacity = '1'; content.style.transform = 'none'; details.append(content); }
        drawer.append(details);
      });
      const closeDrawer = () => { drawer.classList.remove('fv-drawer-open'); menuButton.setAttribute('aria-expanded', 'false'); drawer.inert = true; };
      drawer.inert = true;
      menuButton.addEventListener('click', () => { const open = !drawer.classList.contains('fv-drawer-open'); drawer.classList.toggle('fv-drawer-open', open); menuButton.setAttribute('aria-expanded', String(open)); drawer.inert = !open; });
      header.addEventListener('keydown', e => { if (e.key === 'Escape') closeDrawer(); });
    }
    all('button', header).forEach(button => {
      const label = `${button.textContent} ${button.getAttribute('aria-label') || ''}`.trim().toLowerCase();
      if (label.includes('skip to main')) button.addEventListener('click', () => { const main = document.querySelector('main'); main.tabIndex = -1; main.focus(); main.scrollIntoView(); });
      if (label.includes('search') && !button.closest('form')) button.addEventListener('click', e => { e.preventDefault(); showSearch(header.querySelector('input[type="search"]')?.value || ''); });

      if (button.hasAttribute('aria-controls') && button.getAttribute('aria-controls') === 'language-menu') button.addEventListener('click', () => { const panel = header.getElementById('language-menu').parentElement; const open = button.getAttribute('aria-expanded') !== 'true'; panel.style.cssText = open ? 'display:block;opacity:1;transform:none;pointer-events:auto' : ''; button.setAttribute('aria-expanded', String(open)); });
    });
    all('form', header).forEach(form => form.addEventListener('submit', e => { e.preventDefault(); const target=new URL('catalogue.html',document.baseURI);target.searchParams.set('q',form.querySelector('input').value);location.href=target.href; }));
  }
  const footer = document.querySelector('#footerHost')?.shadowRoot;
  if (footer) all('button', footer).forEach(button => button.addEventListener('click', () => {
    if (button.textContent.includes('Privacy')) openDialog('Privacy','This site uses FlintVellum’s existing analytics. Saved lots are stored in this browser.');
  }));
})();
