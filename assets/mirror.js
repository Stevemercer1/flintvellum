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
    const update = () => {
      const width = track.clientWidth;
      visible = hero ? 1 : upcoming ? (innerWidth < 768 ? 1.15 : 2.4) : lots ? (innerWidth < 768 ? 1.4 : innerWidth < 1224 ? 3.3 : 4.3) : (innerWidth < 768 ? 1.15 : innerWidth < 1224 ? 2.2 : 3.2);
      const gap = lots ? 0 : 10;
      const itemWidth = hero ? width : (width + gap) / visible - gap;
      step = itemWidth + gap;
      slides.style.width = `${step * items.length}px`;
      items.forEach((item, i) => {
        item.style.width = `${itemWidth}px`;
        item.style.marginLeft = i ? `${gap / 2}px` : '0';
        item.style.marginRight = i < items.length - 1 ? `${gap / 2}px` : '0';
      });
      index = Math.min(index, Math.max(0, items.length - Math.floor(visible)));
      slides.style.transform = `translate3d(${-index * step}px,0,0)`;
      slides.style.transition = reduced.matches ? 'none' : 'transform 400ms cubic-bezier(.165,.84,.44,1)';
      bullets.forEach((bullet, i) => {
        bullet.classList.toggle('glide__bullet--active', i === index);
        bullet.setAttribute('aria-pressed', String(i === index));
      });
      items.forEach((item, i) => { if (hero) item.inert = i !== index; });
      const announcement = carousel.querySelector('.glide > .visually-hidden');
      if (announcement) announcement.textContent = `Showing ${index + 1} of ${items.length}`;
    };
    const move = delta => {
      const max = Math.max(0, items.length - Math.floor(visible));
      index = hero ? (index + delta + items.length) % items.length : Math.max(0, Math.min(max, index + delta));
      update();
    };
    all('button', carousel).filter(b => !b.closest('.glide__slides')).forEach(button => {
      const label = `${button.getAttribute('aria-label') || ''} ${button.textContent}`.toLowerCase();
      if (label.includes('previous')) button.addEventListener('click', () => move(-1));
      if (label.includes('next')) button.addEventListener('click', () => move(1));
    });
    bullets.forEach((bullet, i) => {
      const select = () => { index = i; update(); };
      bullet.addEventListener('click', select);
      bullet.addEventListener('keydown', e => { if (['Enter', ' '].includes(e.key)) { e.preventDefault(); select(); } });
    });
    let start;
    track.addEventListener('touchstart', e => { start = e.changedTouches[0].clientX; }, { passive: true });
    track.addEventListener('touchend', e => { const delta = e.changedTouches[0].clientX - start; if (Math.abs(delta) > 45) move(delta < 0 ? 1 : -1); }, { passive: true });
    carousel.addEventListener('fv:filtered', () => { index = 0; update(); });
    new ResizeObserver(update).observe(track);
    update();
  });
  all('chr-upcoming-auctions').forEach(section => {
    const tiles = all('chr-auction-tile-next', section);
    all('chr-quick-filters button', section).forEach(button => button.addEventListener('click', () => {
      const filter = button.textContent.trim().toLowerCase();
      if (filter.includes('near')) { showSearch('London'); return; }
      all('chr-quick-filters button', section).forEach(b => { b.classList.toggle('chr-button--selected', b.textContent.trim() === button.textContent.trim()); b.setAttribute('aria-pressed', String(b.textContent.trim() === button.textContent.trim())); });
      tiles.forEach(tile => { const item = tile.closest('.glide__slides > *') || tile.parentElement; item.hidden = filter !== 'all' && !tile.textContent.toLowerCase().includes(`${filter} auction`); });
    }));
  });
  all('chr-button-save-lot button').forEach((button, i) => {
    const key = `flintvellum-follow-${i}`;
    const render = followed => {
      const label = button.querySelector('.chr-button__text');
      if (label) label.textContent = followed ? 'Following' : 'Follow';
      button.setAttribute('aria-pressed', String(followed));
    };
    let followed = false;
    try { followed = localStorage.getItem(key) === 'true'; } catch {}
    render(followed);
    button.addEventListener('click', () => { followed = !followed; render(followed); try { localStorage.setItem(key, String(followed)); } catch {} });
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
  const catalogue = all('main a[href]').map(a => ({text:a.textContent.trim(),href:a.href})).filter(a => a.text.length > 15 && !/view all|discover now/i.test(a.text));
  function showSearch(query = '') {
    const body = openDialog('Search the collection');
    const form = document.createElement('form'); form.className = 'fv-search-form';
    form.innerHTML = '<input type="search" aria-label="Search by keyword" placeholder="Search by keyword"><button type="submit">Search</button>';
    const results = document.createElement('ul'); results.className = 'fv-search-results';
    body.append(form, results); form.querySelector('input').value = query;
    const search = () => {
      results.replaceChildren(); const value = form.querySelector('input').value.toLowerCase().trim();
      const seen = new Set();
      const matches = catalogue.filter(item => value && item.text.toLowerCase().includes(value) && !seen.has(item.href) && seen.add(item.href));
      for (const item of matches) { const li = document.createElement('li'); const a = document.createElement('a'); a.href = item.href; a.textContent = item.text; li.append(a); results.append(li); }
      if (value && !matches.length) results.textContent = 'No matching items. Try an artist, collection or category.';
    };
    form.addEventListener('submit', e => { e.preventDefault(); search(); });
    form.querySelector('input').addEventListener('input', search); search();
    form.querySelector('input').focus();
  }
  const header = document.querySelector('#headerHost')?.shadowRoot;
  if (header) {
    const style = document.createElement('style');
    style.textContent = '.fv-menu-open{height:auto!important;z-index:60!important;overflow:visible!important}.fv-menu-open>div{opacity:1!important;transform:none!important}.fv-drawer-open{transform:translateX(0)!important;overflow:auto;padding:24px}.fv-drawer-open details{border-bottom:1px solid #ddd;padding:16px 0;font-family:ABCArizonaSans,Arial,sans-serif}.fv-drawer-open summary{cursor:pointer;text-transform:uppercase}.fv-drawer-open details a{display:block;padding:10px 0;font-size:16px}.fv-drawer-open details div{margin:0!important;width:100%!important;padding:8px 0!important;display:block!important}.fv-drawer-open details ul{display:block!important}.fv-drawer-open details img{display:none}';
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
      if (label.includes('search')) button.addEventListener('click', e => { e.preventDefault(); showSearch(header.querySelector('input[type="search"]')?.value || ''); });
      if (label === 'sign in' || label.includes('user navigation')) button.addEventListener('click', () => openDialog('Account access','Auction accounts and bidding are managed by the source auction house.','https://www.christies.com/','Visit Christie’s'));
      if (button.hasAttribute('aria-controls') && button.getAttribute('aria-controls') === 'language-menu') button.addEventListener('click', () => { const panel = header.getElementById('language-menu').parentElement; const open = button.getAttribute('aria-expanded') !== 'true'; panel.style.cssText = open ? 'display:block;opacity:1;transform:none;pointer-events:auto' : ''; button.setAttribute('aria-expanded', String(open)); });
    });
    all('form', header).forEach(form => form.addEventListener('submit', e => { e.preventDefault(); showSearch(form.querySelector('input').value); }));
  }
  const footer = document.querySelector('#footerHost')?.shadowRoot;
  if (footer) {
    const style = document.createElement('style');
    style.textContent = '@media(max-width:1023px){nav[aria-label="Footer"]>div:nth-child(-n+3){border-bottom:1px solid #333}nav[aria-label="Footer"]>div:nth-child(-n+3) h3{padding:22px 0;cursor:pointer;display:flex;justify-content:space-between}nav[aria-label="Footer"]>div:nth-child(-n+3) h3:after{content:"+"}nav[aria-label="Footer"]>div:nth-child(-n+3):not(.fv-expanded)>:not(h3){display:none}nav[aria-label="Footer"]>div:nth-child(4) h3{display:none}nav[aria-label="Footer"]>div:nth-child(4){padding-top:28px;text-align:center}}';
    footer.append(style);
    all('nav[aria-label="Footer"]>div', footer).slice(0,3).forEach(group => {
      const heading = group.querySelector('h3');
      if (!heading) return;
      heading.tabIndex = 0; heading.setAttribute('role','button'); heading.setAttribute('aria-label',heading.textContent.trim()); heading.setAttribute('aria-expanded','false');
      const toggle = () => { const open = group.classList.toggle('fv-expanded'); heading.setAttribute('aria-expanded',String(open)); };
      heading.addEventListener('click',toggle);
      heading.addEventListener('keydown',e=>{if(['Enter',' '].includes(e.key)){e.preventDefault();toggle()}});
    });
  }
  if (footer) all('button', footer).forEach(button => button.addEventListener('click', () => {
    if (button.textContent.includes('Cookie')) openDialog('Privacy','This page uses FlintVellum’s existing analytics. Christie’s advertising and marketing scripts are not included.');
    else if (button.getAttribute('aria-label') === 'WeChat') openDialog('WeChat','Visit the source auction house for its social channels.','https://www.christies.com/','Visit Christie’s');
  }));
  all('main button').filter(button => button.textContent.trim().toLowerCase() === 'sign up').forEach(button => button.addEventListener('click', () => openDialog('Email updates','Newsletter subscriptions are managed by the source auction house.','https://www.christies.com/','Visit Christie’s')));
})();
