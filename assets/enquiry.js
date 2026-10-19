/* Private sourcing drafts and indicative currency references. No bids or payments are sent. */
(() => {
 const panel=document.querySelector('.fv-currency');
 if(!panel)return;
 const form=panel.querySelector('form'),amount=form.elements.amount,asset=form.elements.asset;
 const output=panel.querySelector('[data-conversion]'),status=panel.querySelector('[data-rate-status]');
 const refresh=panel.querySelector('[data-refresh-rates]');
 let snapshot=null,pending=null,expiry;
 const lifetime=5*60*1000;
 const validAmount=()=>amount.value!==''&&amount.validity.valid&&Number.isFinite(amount.valueAsNumber)&&amount.valueAsNumber>0;
 function render(){
  output.textContent='';
  if(!validAmount()){status.textContent='Enter a positive GBP amount, with up to two decimal places.';return}
  if(!snapshot){status.textContent=pending?'Fetching reference rates…':'Rates unavailable. Your GBP amount is unchanged. Try refreshing.';return}
  if(Date.now()-snapshot.at>=lifetime){status.textContent='Reference rates have expired. Refresh to see a new conversion.';return}
  const value=amount.valueAsNumber*snapshot.rates[asset.value];
  const digits=asset.value==='BTC'?8:asset.value==='ETH'?6:2;
  output.textContent=`Approximately ${value.toLocaleString('en-GB',{minimumFractionDigits:digits,maximumFractionDigits:digits})} ${asset.value}`;
  status.textContent=`Reference rates retrieved at ${new Date(snapshot.at).toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit',timeZoneName:'short'})}.`;
 }
 async function rates(force=false){
  if(pending)return pending;
  if(!force&&snapshot&&Date.now()-snapshot.at<lifetime){render();return}
  snapshot=null;clearTimeout(expiry);refresh.disabled=true;
  const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),10000);
  pending=(async()=>{
   try{
    const response=await fetch('https://api.coinbase.com/v2/exchange-rates?currency=GBP',{signal:controller.signal,cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer'});
    if(!response.ok)throw new Error('Rates unavailable');
    const data=(await response.json()).data;
    if(data?.currency!=='GBP')throw new Error('Unexpected base currency');
    const converted={};
    for(const code of ['BTC','ETH','USDC','USDT']){
     const rate=Number(data.rates?.[code]);
     if(!Number.isFinite(rate)||rate<=0)throw new Error('Missing rate');
     converted[code]=rate;
    }
    snapshot={rates:converted,at:Date.now()};
    expiry=setTimeout(render,lifetime+50);
   }catch{snapshot=null}
   finally{clearTimeout(timeout);pending=null;refresh.disabled=false;render()}
  })();
  render();return pending;
 }
 form.hidden=false;
 form.addEventListener('submit',e=>{e.preventDefault();rates(true)});
 amount.addEventListener('input',render);asset.addEventListener('change',()=>rates());
 panel.addEventListener('toggle',()=>{if(panel.open)rates()});
 document.addEventListener('visibilitychange',()=>{if(!document.hidden&&panel.open)render()});
 const enquiry=document.querySelector('[data-enquiry-form]');
 if(!enquiry)return;
 enquiry.hidden=false;
 const result=document.querySelector('[data-enquiry-result]'),draft=result.querySelector('textarea');
 const confirmation=result.querySelector('[data-copy-status]');
 enquiry.addEventListener('submit',e=>{
  e.preventDefault();
  const budget=enquiry.elements.budget.valueAsNumber;
  if(!enquiry.reportValidity()||!Number.isFinite(budget)||budget<=0)return;
  const name=enquiry.dataset.title,preference=enquiry.elements.preference.selectedOptions[0].textContent;
  const notes=enquiry.elements.notes.value.trim();
  draft.value=`Private sourcing enquiry: ${name}\n\nI am looking for a similar piece.\nProposed budget: ${budget.toLocaleString('en-GB',{style:'currency',currency:'GBP'})}\nPreferred settlement asset: ${preference}\n\n${notes?notes+'\n\n':''}Reference: ${location.href.split('?')[0].split('#')[0]}\n\nPlease confirm availability, condition, fees and escrow terms before any commitment. This is an enquiry, not a binding bid.`;
  result.querySelector('[data-email-draft]').href=`mailto:?subject=${encodeURIComponent('FlintVellum private sourcing enquiry: '+name)}&body=${encodeURIComponent(draft.value)}`;
  result.hidden=false;confirmation.textContent='Draft prepared. Nothing has been sent. Add your chosen recipient in your email app.';
  draft.focus();
 });
 enquiry.addEventListener('input',()=>{result.hidden=true;draft.value=''});
 result.querySelector('[data-copy-draft]').addEventListener('click',async()=>{
  try{await navigator.clipboard.writeText(draft.value);confirmation.textContent='Enquiry copied. Nothing has been sent.'}
  catch{draft.focus();draft.select();confirmation.textContent='Select and copy the enquiry below.'}
 });
})();
