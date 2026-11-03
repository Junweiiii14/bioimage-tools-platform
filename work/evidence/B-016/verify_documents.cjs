const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL,fileURLToPath}=require('node:url');
const {chromium}=require('C:/Users/70236/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'../../..');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
 const results=[];
 const qa=path.join(root,'.local/deliveries/B-016/qa');fs.mkdirSync(qa,{recursive:true});
 for(const [key,file,count,query] of [
  ['main','docs/plans/research-platform-rd.html',9,'模块'],
  ['workflow','docs/plans/workflow-development.html',8,'操作'],
  ['maintenance','docs/maintenance-plan.html',7,'版本'],
  ['roadmap','docs/plans/experiment-research-roadmap.html',3,'qPCR'],
  ['wb','docs/research/2026-11-02-wb-workflow-audit.html',7,'归一化'],
 ]){
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[],network=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url())});
  await page.goto(pathToFileURL(path.join(root,file)).href);await page.emulateMedia({reducedMotion:'reduce'});
  const structure=await page.evaluate(()=>({headings:document.querySelectorAll('article h2').length,
    broken:[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(a.hash.slice(1))).map(a=>a.hash),
    local:[...document.querySelectorAll('a[href]')].map(a=>a.href).filter(u=>u.startsWith('file:')),
    overflow:document.documentElement.scrollWidth>innerWidth}));
  const missing=structure.local.filter(u=>!fs.existsSync(fileURLToPath(new URL(u))));
  await page.screenshot({path:path.join(qa,key+'-desktop.png')});
  if(key==='maintenance'){await page.locator('#section-3').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(qa,'maintenance-navigation.png')});}
  await page.locator('#search').fill(query);await page.waitForFunction(()=>document.querySelector('#results a'));
  const hits=await page.locator('#results a').count();
  await page.setViewportSize({width:390,height:844});await page.evaluate(()=>scrollTo(0,0));
  const mobileOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
  await page.locator('#menu-toggle').click();await page.locator('.toc a').last().click();
  const menuClosed=await page.locator('#menu-toggle').getAttribute('aria-expanded')==='false';
  await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(qa,key+'-mobile.png')});
  await page.emulateMedia({media:'print'});
  const printHidden=await page.locator('.sidebar').evaluate(e=>getComputedStyle(e).display==='none');
  const pass=structure.headings===count&&!structure.broken.length&&!structure.overflow&&!missing.length&&!mobileOverflow&&menuClosed&&printHidden&&hits>0&&!errors.length&&!network.length;
  results.push({key,headings:structure.headings,brokenAnchors:structure.broken,missingLocalLinks:missing,desktopOverflow:structure.overflow,mobileOverflow,menuClosed,printHidden,hits,errors,network,pass});
  await page.close();
 }
 await browser.close();
 fs.writeFileSync(path.join(__dirname,'html-validation.json'),JSON.stringify(results,null,2));
 console.log(JSON.stringify(results,null,2));
 if(results.some(r=>!r.pass))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
