const {firefox}=require('playwright');
const fs=require('node:fs');
const http=require('node:http');
const path=require('node:path');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.svg':'image/svg+xml','.jpg':'image/jpeg','.png':'image/png','.woff':'font/woff','.woff2':'font/woff2','.mp4':'video/mp4'};
const server=http.createServer((req,res)=>{
 const name=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
 let file=path.join(root,name);
 if(!file.startsWith(root+path.sep)&&file!==root){res.writeHead(403).end();return;}
 try{if(fs.statSync(file).isDirectory())file=path.join(file,'index.html');res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));}catch{res.writeHead(404).end();}
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await firefox.launch({headless:true});
 try{
 const page=await browser.newPage();const errors=[],failed=[],remote=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('requestfailed',r=>failed.push({url:r.url(),error:r.failure()?.errorText}));
 page.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1')&&!r.url().startsWith('data:'))remote.push(r.url())});
 await page.route('**/fingerprint.js',r=>r.fulfill({contentType:'text/javascript',body:''}));
 const base=`http://127.0.0.1:${server.address().port}/`;
 await page.setViewportSize({width:1440,height:1000});
 await page.goto(base,{waitUntil:'networkidle'});await page.evaluate(()=>document.fonts.ready);
 fs.mkdirSync(path.join(root,'docs/verify-shots'),{recursive:true});
 const layouts=[];
 for(const width of [1440,390,320,768,1024]){
  await page.setViewportSize({width,height:1000});await page.waitForTimeout(150);
  layouts.push(await page.evaluate(()=>({width:innerWidth,docWidth:document.documentElement.scrollWidth,heading:document.querySelector('h1')?.textContent,header:!!document.querySelector('#headerHost').shadowRoot,brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src),fonts:[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family)})));
  if([1440,390].includes(width))await page.screenshot({path:path.join(root,`docs/verify-shots/${width}.png`),fullPage:true});
 }
 for(const result of layouts){assert.equal(result.docWidth,result.width,'Narrow-screen overflow');assert.deepEqual(result.brokenImages,[],'Broken local image');}
 await page.setViewportSize({width:1440,height:1000});
 const hero=page.locator('chr-header-carousel');
 await hero.hover();
 const before=await hero.locator('.glide__slides').evaluate(e=>e.style.transform);
 await hero.getByRole('button',{name:'Next Slide',exact:true}).click();
 assert.notEqual(await hero.locator('.glide__slides').evaluate(e=>e.style.transform),before);
 await hero.getByRole('button',{name:'Show slide 1',exact:true}).click();
 const desktop=page.locator('chr-upcoming-auctions.fv-upcoming-desktop');
 await desktop.getByRole('button',{name:'Online',exact:true}).click();
 assert.equal(await desktop.locator('chr-auction-tile-next:visible').count(),2);
 await desktop.getByRole('button',{name:'All',exact:true}).click();
 const follow=page.locator('chr-button-save-lot button').first();
 await follow.click();assert.equal(await follow.getAttribute('aria-pressed'),'true');
 const header=page.locator('#headerHost');
 await header.locator('input[type="search"]').fill('Monet');
 await header.locator('input[type="search"]').press('Enter');
 assert.ok(await page.locator('.fv-search-results a').count()>0);
 await page.getByRole('button',{name:'Close',exact:true}).click();
 const auctions=header.locator('nav[aria-label="Primary"] a[aria-controls]').first();
 await auctions.hover();assert.equal(await auctions.getAttribute('aria-expanded'),'true');
 await page.keyboard.press('Escape');
 await page.setViewportSize({width:390,height:844});
 const menu=header.getByRole('button',{name:'Menu',exact:true});
 await menu.click();assert.equal(await menu.getAttribute('aria-expanded'),'true');
 assert.ok(await header.locator('.fv-drawer-open details').count()>0);
 await menu.click();
 const mobile=page.locator('chr-upcoming-auctions.fv-upcoming-mobile');
 assert.ok(await mobile.locator('.glide__slides').count()>0);
 await mobile.getByRole('button',{name:'Online',exact:true}).click();
 await mobile.getByRole('button',{name:'All',exact:true}).click();
 const footer=page.locator('#footerHost');
 await footer.getByRole('button',{name:/^help$/i}).click();
 assert.equal(await footer.getByRole('button',{name:/^help$/i}).getAttribute('aria-expanded'),'true');
 await page.goto(base+'company.html',{waitUntil:'networkidle'});
 const company=[];
 for(const width of [320,390,1440]){
   await page.setViewportSize({width,height:900});
   const layout=await page.evaluate(()=>({width:innerWidth,docWidth:document.documentElement.scrollWidth,roles:document.querySelectorAll('.role').length,mailto:document.querySelector('.recruiter a').getAttribute('href'),analytics:document.querySelectorAll('script[src="fingerprint.js"]').length}));
   assert.equal(layout.width,layout.docWidth);assert.equal(layout.roles,2);assert.equal(layout.analytics,1);
   company.push(layout);
   if(width===1440)await page.screenshot({path:path.join(root,'docs/verify-shots/company.png'),fullPage:true});
 }
 const home=page.locator('#headerHost').getByRole('link',{name:'FlintVellum home'});
 await home.click();await page.waitForURL(base);
 assert.deepEqual(errors,[],'Browser errors');assert.deepEqual(failed,[],'Failed requests');
 console.log(JSON.stringify({layouts,errors,failed,remote,company,interactions:'passed'},null,2));
 fs.writeFileSync(path.join(root,'docs/verify-shots/results.json'),JSON.stringify({layouts,errors,failed,remote},null,2));
 }finally{await browser.close();server.close()}
})().catch(e=>{console.error(e);server.close();process.exitCode=1});
