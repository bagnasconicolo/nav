const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:1});
for(const [h,out,omit] of [['','overlay.png',true],['#bg','storia.png',false]]){
 await p.goto('file://'+process.cwd()+'/story.html'+h);await p.reload();await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(300);
 await p.screenshot({path:out,omitBackground:omit});}
await b.close();})();
