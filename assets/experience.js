/* Progressive motion: content stays readable when JavaScript or motion is unavailable. */
(() => {
 const home=document.querySelector('.fv-home');if(!home)return;
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 const desktop=matchMedia('(min-width: 768px)');
 const animated=new Set(),seen=new WeakSet();
 const candidates=[...home.querySelectorAll('section h2,.fv-specialism,.fv-home-process .steps li,.fv-home-careers .container-fluid,.chr-feature-card-next')];
 let observer;
 if('IntersectionObserver' in window){
  observer=new IntersectionObserver(entries=>{
   for(const entry of entries){if(!entry.isIntersecting)continue;const el=entry.target;observer.unobserve(el);if(seen.has(el))continue;seen.add(el);
    if(!reduced.matches){const siblings=[...el.parentElement.children],delay=el.matches('.fv-specialism')?siblings.indexOf(el)*80:0;
     const animation=el.animate([{opacity:0,transform:'translateY(24px)'},{opacity:1,transform:'translateY(0)'}],{duration:650,delay,easing:'cubic-bezier(.23,1,.32,1)',fill:'backwards'});
     animated.add(animation);animation.finished.then(()=>animated.delete(animation)).catch(()=>animated.delete(animation));
    }
   }
  },{threshold:.12,rootMargin:'0px 0px -24px 0px'});
  candidates.forEach(el=>observer.observe(el));
 }
 const progress=document.createElement('div');progress.className='fv-scroll-progress';progress.setAttribute('aria-hidden','true');document.body.insertBefore(progress,home.parentElement===document.body?home:document.body.firstChild);
 const frames=[...home.querySelectorAll('.fv-specialism-image')];
 let frame=0;
 function paint(){frame=0;if(reduced.matches||document.hidden)return;
  const available=document.documentElement.scrollHeight-innerHeight;progress.style.transform=`scaleX(${available>0?Math.min(1,Math.max(0,scrollY/available)):0})`;
  for(const wrapper of frames){const img=wrapper.querySelector('img');if(!desktop.matches){img.style.removeProperty('transform');continue}const rect=wrapper.getBoundingClientRect();if(rect.bottom<0||rect.top>innerHeight)continue;const travel=Math.max(-14,Math.min(14,(innerHeight/2-rect.top-rect.height/2)*.04));img.style.transform=`translateY(${travel}px) scale(1.09)`;}
 }
 const schedule=()=>{if(!frame&&!reduced.matches)frame=requestAnimationFrame(paint)};
 function preference(){document.documentElement.classList.toggle('fv-smooth-scroll',!reduced.matches);if(reduced.matches){if(frame)cancelAnimationFrame(frame);frame=0;animated.forEach(a=>a.cancel());animated.clear();frames.forEach(e=>e.querySelector('img').style.removeProperty('transform'));progress.style.transform='scaleX(0)'}else schedule()}
 addEventListener('scroll',schedule,{passive:true});addEventListener('resize',schedule,{passive:true});document.addEventListener('visibilitychange',schedule);reduced.addEventListener('change',preference);desktop.addEventListener('change',schedule);preference();
 // Focus never lands on a moving target during keyboard navigation.
 home.addEventListener('focusin',()=>{animated.forEach(a=>a.finish());animated.clear()});
})();
