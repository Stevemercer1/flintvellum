const {firefox}=require('playwright');
const fs=require('node:fs'),http=require('node:http'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.svg':'image/svg+xml','.jpg':'image/jpeg','.png':'image/png','.woff':'font/woff','.woff2':'font/woff2','.mp4':'video/mp4','.json':'application/json'};
const server=http.createServer((req,res)=>{
 const name=decodeURIComponent(new URL(req.url,'http://localhost').pathname).replace(/^\/flintvellum\//,'/');let file=path.join(root,name);
 if(!file.startsWith(root+path.sep)&&file!==root){res.writeHead(403).end();return}
 try{if(fs.statSync(file).isDirectory())file=path.join(file,'index.html');res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file))}catch{res.writeHead(404).end()}
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await firefox.launch({headless:true});
 try{
 const page=await browser.newPage(),errors=[],failed=[],badResponses=[],layouts=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>{if(!r.failure()?.errorText.includes('ABORTED'))failed.push({url:r.url(),error:r.failure()?.errorText})});page.on('response',r=>{if(r.status()>=400)badResponses.push({url:r.url(),status:r.status()})});
 await page.route('**/fingerprint.js',r=>r.fulfill({contentType:'text/javascript',body:''}));
 const base=`http://127.0.0.1:${server.address().port}/flintvellum/`;
 fs.mkdirSync(path.join(root,'docs/verify-shots'),{recursive:true});
 const go=async name=>{await page.goto(base+name,{waitUntil:'networkidle'});await page.evaluate(()=>document.fonts.ready)};
 async function layout(name,width){await page.setViewportSize({width,height:960});await page.waitForTimeout(150);const result=await page.evaluate(()=>({width:innerWidth,docWidth:document.documentElement.scrollWidth,broken:[...document.images].filter(i=>i.complete&&!i.naturalWidth).map(i=>i.src)}));layouts.push({page:name,...result});assert.equal(result.docWidth,width,`Overflow ${name} ${width}`);assert.deepEqual(result.broken,[],`Broken images ${name}`)}
 if(process.argv.includes('--motion')){
  await page.addInitScript(()=>{window.startedReveals=0;const animate=Element.prototype.animate;Element.prototype.animate=function(...args){window.startedReveals++;return animate.apply(this,args)}});
  await page.setViewportSize({width:1440,height:1000});await go('');
  const hero=page.locator('chr-header-carousel'),track=hero.locator('.glide__track');
  const box=await track.boundingBox();
  await page.mouse.move(box.x+box.width*.8,box.y+box.height*.5);await page.mouse.down();await page.mouse.move(box.x+box.width*.55,box.y+box.height*.5,{steps:15});await page.mouse.up();
  assert.equal(await hero.getByRole('button',{name:'Show watches',exact:true}).getAttribute('aria-pressed'),'true');assert.equal(page.url(),base);
  await hero.getByRole('button',{name:'Show discover',exact:true}).focus();await page.keyboard.press('Enter');
  assert.equal(await hero.locator('.glide__slides').evaluate(e=>e.style.transition),'none');
  await hero.getByRole('link',{name:/Berneron Mirage/}).click();await page.waitForURL(base+'lots/w-0001.html');
  await go('');await page.getByRole('link',{name:'Scroll to discover',exact:true}).click();await page.waitForFunction(()=>scrollY>100);
  await page.locator('#specialisms').scrollIntoViewIfNeeded();await page.waitForTimeout(100);
  assert.ok(await page.evaluate(()=>window.startedReveals)>0);
  assert.ok(await page.locator('.fv-specialism-image img').first().evaluate(e=>e.style.transform.includes('translateY')));
  await page.emulateMedia({reducedMotion:'reduce'});await page.waitForTimeout(100);
  assert.equal(await page.evaluate(()=>getComputedStyle(document.documentElement).scrollBehavior),'auto');
  assert.equal(await page.locator('.fv-specialism-image img').first().evaluate(e=>e.style.transform),'');
  assert.equal(await page.evaluate(()=>document.getAnimations().filter(a=>a.playState==='running').length),0);
  await go('');assert.equal(await page.evaluate(()=>window.startedReveals),0);
  const noJS=await browser.newPage({javaScriptEnabled:false,viewport:{width:390,height:844}});await noJS.goto(base);assert.equal(await noJS.locator('.fv-specialism').count(),3);assert.equal(await noJS.locator('chr-header-carousel-slide').first().getByRole('heading').isVisible(),true);await noJS.close();
  assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);assert.deepEqual(badResponses,[]);
  console.log('PASS: mouse drag, normal links, instant keyboard selection, scroll reveals, image movement, runtime reduced motion and content without JavaScript.');return;
 }
 if(process.argv.includes('--company')){
  for(const name of ['','company.html','careers/']){
   await go(name);
   for(const width of [320,390,768,1024,1440])await layout(name||'home',width);
   if(name==='careers/'){
    assert.equal(await page.locator('.role').count(),2);
    assert.equal(await page.locator('.recruiter a').getAttribute('href'),'mailto:stevelikejobs@proton.me?subject=FlintVellum%20role%20enquiry');
    await page.screenshot({path:path.join(root,'docs/verify-shots/careers-desktop.png'),fullPage:true,animations:'disabled'});
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:path.join(root,'docs/verify-shots/careers-mobile.png'),fullPage:true,animations:'disabled'});
   }
  }
  await go('');await page.setViewportSize({width:1440,height:1000});
  await page.locator('#how-it-works').screenshot({path:path.join(root,'docs/verify-shots/settlement-desktop.png')});
  await page.locator('#careers a').click();await page.waitForURL(base+'careers/');
  await page.locator('#headerHost').getByRole('link',{name:'FlintVellum home',exact:true}).click();await page.waitForURL(base);
  await page.setViewportSize({width:390,height:844});
  const header=page.locator('#headerHost');await header.getByRole('button',{name:'Menu',exact:true}).click();
  const house=header.locator('.fv-drawer-open details').filter({has:page.locator('summary',{hasText:'The house'})});
  await house.locator('summary').click();await house.getByRole('link',{name:'Careers',exact:true}).click();await page.waitForURL(base+'careers/');
  await page.locator('#headerHost').getByRole('button',{name:'Menu',exact:true}).click();
  const houseAgain=page.locator('#headerHost .fv-drawer-open details').filter({has:page.locator('summary',{hasText:'The house'})});
  await houseAgain.locator('summary').click();await houseAgain.getByRole('link',{name:'How it works',exact:true}).click();await page.waitForURL(base+'index.html#how-it-works');
  assert.equal(await page.locator('#how-it-works').isVisible(),true);
  await page.locator('#how-it-works').screenshot({path:path.join(root,'docs/verify-shots/settlement-mobile.png')});
  assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);assert.deepEqual(badResponses,[]);
  console.log(JSON.stringify({layouts,errors,failed,badResponses,careersNavigation:'passed'},null,2));return;
 }
 await go('');await page.locator('img[loading=lazy]').evaluateAll(es=>es.forEach(e=>e.loading='eager'));await page.waitForLoadState('networkidle');
 for(const width of [1440,390,320,768,1024]){await layout('home',width);if([1440,390].includes(width))await page.screenshot({path:path.join(root,`docs/verify-shots/${width}.png`),fullPage:true,animations:'disabled'})}
 await page.setViewportSize({width:1440,height:1000});const hero=page.locator('chr-header-carousel');await hero.hover();const before=await hero.locator('.glide__slides').evaluate(e=>e.style.transform);await hero.getByRole('button',{name:'Next Slide',exact:true}).click();assert.notEqual(await hero.locator('.glide__slides').evaluate(e=>e.style.transform),before);await hero.getByRole('button',{name:'Show discover',exact:true}).click();
 assert.equal(await page.locator('.fv-specialism img').count(),3);
 const header=page.locator('#headerHost');const archive=header.locator('nav[aria-label="Primary"] a[aria-controls]').first();await archive.hover();assert.equal(await archive.getAttribute('aria-expanded'),'true');await page.keyboard.press('Escape');
 await header.locator('input[type="search"]').fill('Berneron');await header.locator('input[type="search"]').press('Enter');await page.waitForURL('**/catalogue.html?q=Berneron');assert.equal(await page.locator('.fv-result:visible').count(),1);
 await page.locator('.fv-result:visible [data-save-lot]').click();assert.equal(await page.locator('.fv-result:visible [data-save-lot]').getAttribute('aria-pressed'),'true');await go('catalogue.html?saved=1');assert.equal(await page.locator('.fv-result:visible').count(),1);
 await page.locator('.fv-result:visible .chr-lot-tile__link').click();await page.waitForURL('**/lots/w-0001.html');assert.match(await page.locator('h1').textContent(),/Berneron/);assert.equal(await page.locator('.fv-lot-summary [data-save-lot]').getAttribute('aria-pressed'),'true');
 const thumbs=page.locator('[data-gallery-index]');await thumbs.nth(1).click();assert.match(await page.locator('#lot-image').getAttribute('src'),/02.jpg/);await page.locator('.fv-gallery-main').click();assert.equal(await page.locator('.fv-lightbox').evaluate(e=>e.open),true);await page.getByRole('button',{name:'Next image',exact:true}).click();assert.match(await page.locator('.fv-lightbox img').getAttribute('src'),/03.jpg/);await page.keyboard.press('Escape');assert.equal(await page.locator('.fv-lightbox').evaluate(e=>e.open),false);
 for(const width of [1440,390,320,768,1024])await layout('lot',width);await page.setViewportSize({width:1440,height:1000});await page.locator('img[loading=lazy]').evaluateAll(es=>es.forEach(e=>e.loading='eager'));await page.waitForLoadState('networkidle');await page.screenshot({path:path.join(root,'docs/verify-shots/lot.png'),fullPage:true,animations:'disabled'});
 await go('catalogue.html');assert.equal(await page.locator('.fv-result:visible').count(),24);await page.getByRole('button',{name:'Next',exact:true}).click();assert.match(page.url(),/page=2/);assert.equal(await page.locator('.fv-result:visible').count(),24);
 await page.locator('a[data-category="cards"]').click();assert.match(await page.locator('#result-count').textContent(),/Auctions closed/);assert.equal(await page.locator('.fv-result:visible').count(),24);await page.locator('select[name="maker"]').selectOption({label:'Topps (Bowman)'});assert.ok(await page.locator('.fv-result:visible').count()>0);assert.equal(await page.locator('.fv-result:visible').evaluateAll(es=>es.every(e=>e.dataset.maker==='Topps (Bowman)')),true);await page.getByRole('button',{name:'Clear filters',exact:true}).click();
 await go('catalogue.html?category=memorabilia&subtype=film');assert.equal(await page.locator('.fv-result:visible').count(),14);await go('catalogue.html?category=memorabilia&subtype=sports');assert.equal(await page.locator('.fv-result:visible').count(),24);
 await go('catalogue.html?q=zzzznonexistent');assert.equal(await page.locator('.fv-empty').isVisible(),true);await page.locator('[data-clear-filters]').click();assert.equal(await page.locator('.fv-result:visible').count(),24);
 assert.doesNotMatch(await page.locator('main').innerText(),/\d/);assert.equal(await page.locator('#footerHost a[href^="data/"]').count(),0);
 for(const width of [1440,390,320,768,1024]){await layout('catalogue',width);if([1440,390].includes(width))await page.screenshot({path:path.join(root,`docs/verify-shots/catalogue-${width}.png`),fullPage:true,animations:'disabled'})}
 await page.setViewportSize({width:390,height:844});const menu=header.getByRole('button',{name:'Menu',exact:true});await menu.click();assert.equal(await menu.getAttribute('aria-expanded'),'true');const detail=header.locator('.fv-drawer-open details').first();await detail.locator('summary').click();await detail.getByRole('link',{name:'Watches',exact:true}).click();await page.waitForURL('**/catalogue.html?category=watches');assert.match(await page.locator('#result-count').textContent(),/Auctions closed/);
 const footer=page.locator('#footerHost');assert.equal(await footer.getByRole('link',{name:'The archive',exact:true}).isVisible(),true);
 for(const id of ['c-0022','m-0036','m-0038','m-0045','m-0047','w-0021']){await go('lots/'+id+'.html');await layout(id,320);await page.locator('.fv-source-notes summary').click();assert.equal(await page.locator('.fv-source-notes').getAttribute('open'),'');assert.doesNotMatch(await page.locator('main').innerText(),/\d/)}
 await go('company.html');for(const width of [320,390,1440])await layout('company',width);assert.equal(await page.locator('.role').count(),2);assert.equal(await page.locator('.recruiter a').getAttribute('href'),'mailto:stevelikejobs@proton.me?subject=FlintVellum%20role%20enquiry');
 await go('archive.html');for(const width of [320,390,1440])await layout('archive',width);assert.doesNotMatch(await page.locator('main').innerText(),/\d/);await page.screenshot({path:path.join(root,'docs/verify-shots/archive.png'),fullPage:true,animations:'disabled'});
 await page.locator('#headerHost').getByRole('link',{name:'FlintVellum home',exact:true}).click();await page.waitForURL(base);
 assert.deepEqual(errors,[],'Browser errors');assert.deepEqual(failed,[],'Failed requests');assert.deepEqual(badResponses,[],'HTTP failures');
 const report={layouts,errors,failed,badResponses,interactions:'passed'};fs.writeFileSync(path.join(root,'docs/verify-shots/results.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
 }finally{await browser.close();server.close()}
})().catch(e=>{console.error(e);server.close();process.exitCode=1});
