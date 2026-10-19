/* Archive interactions. Every lot also has a static, directly addressable page. */
(() => {
 const all=(q,root=document)=>[...root.querySelectorAll(q)];
 const key='flintvellum-saved-lots';
 const read=()=>{try{return new Set(JSON.parse(localStorage.getItem(key)||'[]').filter(x=>typeof x==='string'))}catch{return new Set()}};
 let saved=read();
 const buttons=all('[data-save-lot]');
 function paintSaved(){buttons.forEach(b=>{const on=saved.has(b.dataset.saveLot);b.setAttribute('aria-pressed',String(on));b.setAttribute('aria-label',`${on?'Unsave':'Save'} ${b.dataset.lotTitle}`);const text=b.querySelector('.chr-button__text');if(text)text.textContent=on?'Saved':'Save lot'})}
 buttons.forEach(b=>b.addEventListener('click',()=>{const id=b.dataset.saveLot;saved.has(id)?saved.delete(id):saved.add(id);try{localStorage.setItem(key,JSON.stringify([...saved]))}catch{}paintSaved();document.dispatchEvent(new Event('fv:saved'))}));paintSaved();
 addEventListener('storage',e=>{if(e.key===key){saved=read();paintSaved();document.dispatchEvent(new Event('fv:saved'))}});
 const form=document.querySelector('#catalogue-filters');
 if(form){
  const grid=document.querySelector('#lot-grid'),records=all('.fv-result',grid),pager=document.querySelector('.fv-pagination');
  const norm=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  let category='all',subtype='',currentPage=1;
  const fields=['q','maker','auction','sort','result','saved'];
  function fromURL(){const p=new URLSearchParams(location.search);category=p.get('category')||'all';if(!['all','watches','cards','memorabilia'].includes(category))category='all';subtype=p.get('subtype')||'';currentPage=Math.max(1,parseInt(p.get('page'),10)||1);fields.forEach(name=>{const field=form.elements[name];if(field.type==='checkbox')field.checked=p.get(name)==='1';else field.value=p.get(name)||(name==='sort'?'curated':'')})}
  function updateURL(){const p=new URLSearchParams();if(category!=='all')p.set('category',category);if(subtype)p.set('subtype',subtype);fields.forEach(name=>{const f=form.elements[name];const value=f.type==='checkbox'?(f.checked?'1':''):f.value;if(value&&value!=='curated')p.set(name,value)});if(currentPage>1)p.set('page',currentPage);const query=p.toString();history.replaceState(null,'',location.pathname+(query?'?'+query:''))}
  function render(sync=true){
   const q=norm(form.elements.q.value.trim()).split(/\s+/).filter(Boolean),maker=form.elements.maker.value,auction=form.elements.auction.value;
   const matches=records.filter(e=>{const d=e.dataset;return(category==='all'||d.category===category)&&(!subtype||d.subtype===subtype)&&(!maker||d.maker===maker)&&(!auction||d.auction===auction)&&(!form.elements.result.checked||d.result!=='')&&(!form.elements.saved.checked||saved.has(d.id))&&q.every(word=>norm(d.search).includes(word))});
   const sort=form.elements.sort.value;
   if(sort!=='curated'){const [field,direction]=sort.split('-');matches.sort((a,b)=>{const va=a.dataset[field],vb=b.dataset[field];if(va===''&&vb==='')return 0;if(va==='')return 1;if(vb==='')return -1;return(Number(va)-Number(vb))*(direction==='asc'?1:-1)})}
   const pages=Math.max(1,Math.ceil(matches.length/24));currentPage=Math.min(currentPage,pages);records.forEach(e=>e.hidden=true);
   matches.forEach((e,i)=>{grid.append(e);e.hidden=i<(currentPage-1)*24||i>=currentPage*24});
   document.querySelector('#result-count').textContent=`${matches.length} ${matches.length===1?'lot':'lots'}${subtype?' · '+subtype:''} · All auctions closed`;
   document.querySelector('.fv-empty').hidden=matches.length!==0;
   all('[data-category]').filter(e=>e.matches('a')).forEach(a=>{if(a.dataset.category===category)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current')});
   pager.replaceChildren();
   if(pages>1){const add=(label,target,disabled=false)=>{const b=document.createElement('button');b.type='button';b.textContent=label;b.disabled=disabled;b.setAttribute('aria-label',typeof label==='number'?`Page ${label}`:label);if(target===currentPage&&typeof label==='number')b.setAttribute('aria-current','page');b.addEventListener('click',()=>{currentPage=target;render();document.querySelector('.fv-results-line').scrollIntoView({block:'start'});document.querySelector('#result-count').tabIndex=-1;document.querySelector('#result-count').focus({preventScroll:true})});pager.append(b)};add('Previous',currentPage-1,currentPage===1);for(let i=1;i<=pages;i++)if(i===1||i===pages||Math.abs(i-currentPage)<=1)add(i,i);add('Next',currentPage+1,currentPage===pages)}
   if(sync)updateURL();
  }
  const clear=()=>{form.reset();category='all';subtype='';currentPage=1;render()};
  all('.fv-category-tabs a').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();category=a.dataset.category;subtype='';form.elements.maker.value='';form.elements.auction.value='';currentPage=1;render()}));
  let timer;form.addEventListener('input',e=>{if(e.target.name==='q'){clearTimeout(timer);timer=setTimeout(()=>{currentPage=1;render()},160)}});
  form.addEventListener('change',()=>{currentPage=1;render()});form.addEventListener('submit',e=>{e.preventDefault();clearTimeout(timer);currentPage=1;render()});
  form.addEventListener('reset',()=>setTimeout(()=>{category='all';subtype='';currentPage=1;render()},0));document.querySelector('[data-clear-filters]').addEventListener('click',clear);
  document.addEventListener('fv:saved',()=>render());addEventListener('popstate',()=>{fromURL();render(false)});fromURL();render();
 }
 const gallery=document.querySelector('.fv-gallery');
 if(gallery){
  const links=all('[data-gallery-index]',gallery),main=gallery.querySelector('.fv-gallery-main'),img=main.querySelector('img');let index=0;
  const dialog=document.createElement('dialog');dialog.className='fv-lightbox';dialog.setAttribute('aria-label','Lot image gallery');
  dialog.innerHTML='<div class="fv-lightbox-bar"><span aria-live="polite"></span><button type="button" aria-label="Close image gallery">Close ×</button></div><img alt=""><div class="fv-lightbox-controls"><button type="button" aria-label="Previous image">← Previous</button><button type="button" aria-label="Next image">Next →</button></div>';
  document.body.insertBefore(dialog,document.querySelector('script[src="fingerprint.js"]'));
  function show(i){index=(i+links.length)%links.length;img.src=links[index].href;img.alt=links[index].querySelector('img').alt;main.href=links[index].href;gallery.querySelector('.fv-gallery-count').textContent=`${index+1} / ${links.length} · Select a view, or enlarge the photograph`;links.forEach((a,j)=>{if(j===index)a.setAttribute('aria-current','true');else a.removeAttribute('aria-current')});dialog.querySelector('img').src=links[index].href;dialog.querySelector('img').alt=img.alt;dialog.querySelector('.fv-lightbox-bar span').textContent=`${index+1} / ${links.length}`}
  links.forEach((a,i)=>a.addEventListener('click',e=>{e.preventDefault();show(i)}));main.addEventListener('click',e=>{e.preventDefault();dialog.showModal()});
  dialog.querySelector('[aria-label="Close image gallery"]').addEventListener('click',()=>dialog.close());dialog.querySelector('[aria-label="Previous image"]').addEventListener('click',()=>show(index-1));dialog.querySelector('[aria-label="Next image"]').addEventListener('click',()=>show(index+1));
  dialog.addEventListener('keydown',e=>{if(e.key==='ArrowRight'){e.preventDefault();show(index+1)}if(e.key==='ArrowLeft'){e.preventDefault();show(index-1)}});
  let start;dialog.addEventListener('touchstart',e=>start=e.changedTouches[0].clientX,{passive:true});dialog.addEventListener('touchend',e=>{const delta=e.changedTouches[0].clientX-start;if(Math.abs(delta)>45)show(index+(delta<0?1:-1))},{passive:true});show(0);
 }
})();
