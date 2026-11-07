const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
for(const [h,out,omit] of [['#bg','storia-oggi-domenica.png',false],['#nobg','overlay-oggi-domenica.png',true],['#bg-domani','storia-domani-domenica.png',false],['#domani','overlay-domani-domenica.png',true]]){
 await p.goto('about:blank');await p.goto('file://'+process.cwd()+'/story.html'+h);await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);
 if(out.startsWith('storia'))console.log(out,await p.evaluate(()=>{const r=document.querySelector('.panel').getBoundingClientRect();return [r.top,r.bottom,Math.max(...[...document.querySelectorAll('.with')].map(e=>e.scrollWidth-e.clientWidth))]}));
 await p.screenshot({path:out,omitBackground:omit});}
await b.close();})();
