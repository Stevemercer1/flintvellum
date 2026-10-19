const {firefox}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..'),file=path.join(__dirname,'linkedin-role-pack.html');
(async()=>{
 const browser=await firefox.launch({headless:true});
 try{
  const page=await browser.newPage({acceptDownloads:true}),errors=[],external=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))external.push(r.url())});
  await page.addInitScript(()=>{
   window.copiedText=null;Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>window.copiedText=text}});
  });
  await page.goto(pathToFileURL(file).href);
  assert.equal(await page.locator('#panel-backend').isVisible(),true);assert.equal(await page.locator('#panel-sales').isVisible(),false);
  assert.equal(await page.locator('.copy-text').count(),26);
  for(const width of [320,390,768,1440]){
   await page.setViewportSize({width,height:960});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),width);
  }
  await page.locator('[data-copy="backend-description"]').first().click();
  let copied=await page.evaluate(()=>window.copiedText);
  assert.match(copied,/£90,000–£170,000/);assert.match(copied,/international candidates welcome/);assert.match(copied,/fictional brief, not a live vacancy/);assert.match(copied,/Bitcoin, Ethereum, USDC and USDT/);assert.match(copied,/Stage one is a technical test/);assert.match(copied,/one to two working days/);assert.match(copied,/AI-native/);assert.match(copied,/stevemercer1@proton.me/);
  assert.equal((await page.locator('#founder-linkedin').inputValue()).split(/\s+/).length,25);
  await page.locator('#backend-feed').fill('Edited LinkedIn copy\n\nSecond paragraph & <angle brackets>.');
  await page.locator('[data-copy="backend-feed"]').click();assert.equal(await page.evaluate(()=>window.copiedText),'Edited LinkedIn copy\n\nSecond paragraph & <angle brackets>.');
  await page.getByRole('tab',{name:/Sales & consignments/}).click();
  assert.equal(await page.locator('#panel-sales').isVisible(),true);
  await page.locator('[data-copy="sales-description"]').first().click();copied=await page.evaluate(()=>window.copiedText);
  assert.match(copied,/£55,000 annual base plus £95,000 variable commission/);assert.match(copied,/OTE is not a guaranteed salary/);assert.match(copied,/Must overlap UK hours/);
  await page.getByRole('tab',{name:/Sales & consignments/}).focus();await page.keyboard.press('ArrowLeft');assert.equal(await page.locator('#tab-backend').getAttribute('aria-selected'),'true');
  // Clipboard denial falls back to selection and browser copy, with an honest manual-copy message if both fail.
  await page.evaluate(()=>{navigator.clipboard.writeText=async()=>{throw Error('Denied')};document.execCommand=()=>false});
  await page.locator('[data-copy="backend-title"]').click();assert.match(await page.locator('.toast').innerText(),/Text selected/);
  assert.equal(await page.locator('#backend-title').evaluate(e=>e.selectionEnd-e.selectionStart),(await page.locator('#backend-title').inputValue()).length);
  const downloading=page.waitForEvent('download');await page.getByRole('button',{name:'Save edited HTML',exact:true}).click();const download=await downloading;
  const downloaded=path.join(root,'.git','FlintVellum-role-pack-test.html');await download.saveAs(downloaded);
  await page.goto(pathToFileURL(downloaded).href);assert.equal(await page.locator('#backend-feed').inputValue(),'Edited LinkedIn copy\n\nSecond paragraph & <angle brackets>.');
  await page.locator('[data-copy="backend-feed"]').click();assert.match(await page.evaluate(()=>window.copiedText),/Edited LinkedIn copy/);
  await page.emulateMedia({media:'print'});await page.evaluate(()=>window.dispatchEvent(new Event('beforeprint')));
  assert.equal(await page.locator('#panel-sales').isVisible(),true);assert.equal(await page.locator('.print-copy').count(),26);
  await page.emulateMedia({media:'screen'});await page.goto(pathToFileURL(file).href);
  fs.mkdirSync(path.join(__dirname,'verify-shots'),{recursive:true});
  for(const width of [1440,390]){await page.setViewportSize({width,height:1000});await page.screenshot({path:path.join(__dirname,'verify-shots',`role-pack-${width}.png`),fullPage:false})}
  await page.getByRole('tab',{name:/Sales & consignments/}).click();await page.setViewportSize({width:1440,height:1000});await page.screenshot({path:path.join(__dirname,'verify-shots','role-pack-sales.png'),fullPage:false});
  const noJS=await browser.newPage({javaScriptEnabled:false});await noJS.goto(pathToFileURL(file).href);
  assert.equal(await noJS.locator('#panel-backend').isVisible(),true);assert.equal(await noJS.locator('#panel-sales').isVisible(),true);assert.equal(await noJS.locator('.copy-text').count(),26);await noJS.close();
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  console.log('PASS: both roles, protected pay/policy copy, editing, plain-text copying, denied clipboard fallback, saved HTML round-trip, keyboard tabs, print, no-JS access and offline layouts at 320–1440px.');
 }finally{await browser.close()}
})().catch(error=>{console.error(error);process.exitCode=1});
