import { chromium } from '../../frontend/node_modules/playwright/index.mjs';
import { mkdirSync, existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
const directory=fileURLToPath(new URL('./',import.meta.url));
const frames='/tmp/farmos-full-mock-frames';
const sunFrames='/tmp/farmos-sun-mock-frames';
mkdirSync(frames,{recursive:true});mkdirSync(sunFrames,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH || (existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined)});
const page=await browser.newPage({viewport:{width:1440,height:1080},deviceScaleFactor:1});
await page.setContent(readFileSync(new URL('./concept-preview.html',import.meta.url),'utf8'));
const slugs=['dashboard','farm-designer','sunlight-simulation','crop-library','planting-calendar','resource-balances','customers-baskets','economics-stage-gates','scenarios-optimizer','operations-actuals','reports-provenance'];
for(let i=0;i<slugs.length;i++){
 await page.evaluate(index=>window.show(index),i);
 await page.screenshot({path:directory+`${String(i+5).padStart(2,'0')}-${slugs[i]}.jpg`,type:'jpeg',quality:91,animations:'disabled',fullPage:true});
 await page.screenshot({path:frames+`/${String(i+1).padStart(2,'0')}.png`,animations:'disabled'});
}
await page.evaluate(()=>window.show(2));
for(let i=0;i<49;i++){
 await page.evaluate(t=>window.setSun(t),6+i*.25);
 await page.screenshot({path:sunFrames+`/${String(i+1).padStart(2,'0')}.png`,animations:'disabled'});
}
await browser.close();
function gif(path,out,rate){execFileSync('ffmpeg',['-y','-framerate',rate,'-start_number','1','-i',path+'/%02d.png','-filter_complex','fps=8,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse','-loop','0',directory+out],{stdio:['ignore','ignore','pipe']});}
gif(frames,'full-product-walkthrough.gif','1/2');gif(sunFrames,'sunlight-shadow-simulation.gif','6');
console.log('Saved 11 JPG previews, full-product GIF and sunlight/shadow GIF.');
