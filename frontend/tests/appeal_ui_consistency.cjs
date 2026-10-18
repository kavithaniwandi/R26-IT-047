// Run: node frontend/tests/appeal_ui_consistency.cjs <built frontend directory>
// Every API response is served locally; no request is forwarded to Gemini or a real backend.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const http = require('node:http');
const {spawn} = require('node:child_process');
const assert = require('node:assert/strict');
const build = process.argv[2];
const delay = ms => new Promise(r => setTimeout(r, ms));
let scenario = 'normal', requests = [], errors = [], consoleMessages = [];
const base = 'Affected families in Malabe require water bottles and tents for 20 people. Please donate today to support affected families and help the community in need.';
function text(style, words = 80) {
 const tokens = [style, ...base.split(' ')];
 while (tokens.length < words) tokens.push(...base.split(' '));
 return tokens.slice(0, words).join(' ');
}
function variant(style) {
 const tables = {
  'band-first': {formal:['high',true,.9,4.8,52],community:['medium',true,.6,2.9,80],urgent:['high',false,.95,4.9,80]},
  agreement: {formal:['high',false,.9,4.8,80],community:['medium',true,.6,2.9,80],urgent:['high',false,.95,4.9,80]},
  label: {formal:['low',true,.99,2,80],community:['medium',true,.5,3,80],urgent:['high',true,.4,4,80]},
  confidence: {formal:['high',true,.5,4.9,80],community:['high',true,.6,3.9,80],urgent:['high',true,.6,4.1,80]},
  score: {formal:['high',true,.6,3.9,80],community:['high',true,.6,4.1,80],urgent:['high',true,.6,4.8,80]},
  'none-agree': {formal:['medium',false,.99,2.9,80],community:['high',false,.6,3.7,80],urgent:['high',false,.6,4.2,80]},
  disagreement: {formal:['high',false,.57,3.9,80],community:['high',false,.57,3.9,80],urgent:['high',false,.57,3.9,80]},
  '52-word': {formal:['medium',true,.8,2.9,52],community:['medium',true,.8,2.9,52],urgent:['medium',true,.8,2.9,52]},
 };
 const defaults = {formal:['medium',true,.7,3,80],community:['high',true,.8,4.8,80],urgent:['high',true,.8,4.2,80]};
 const [label,agreement,confidence,score,words] = (tables[scenario] || defaults)[style];
 const classifier = agreement ? label : label === 'high' ? 'medium' : 'low';
 const probs = {low:(1-confidence)/2,medium:(1-confidence)/2,high:(1-confidence)/2}; probs[classifier] = confidence;
 if (scenario === 'disagreement') Object.assign(probs, {low:.3,medium:.57,high:.13});
 const short = words < 65;
 return {style,appeal_text:text(style,words),model:'mock-provider-name',temperature:.5,
  quality_score:score,quality_label:label,final_label:label,confidence,classifier_confidence:confidence,
  predicted_class:classifier,classifier_top_class:classifier,
  label_agreement:agreement,agreement_note:agreement?null:'Rating and classifier disagree',confidence_level:'moderate',
  class_probs:probs,top_classes:Object.entries(probs).sort((a,b)=>b[1]-a[1]).slice(0,2).map(([k,v])=>({class:k,probability:v})),
  generator_status:'live',word_count:words,
  suggestions:[{check:short?'length':'fund_use',message:short?`This appeal has ${words} words. Appeals under about 65 words tend to rate lower.`:'Say how the donation will be used.',evidence:short?'':'Appears in 80% of high-rated and 20% of low-rated English appeals.'}],
  length_warning:short?`Generated ${words} words; requested band is 65-100 words.`:null};
}
function analysis(payload) {
 const words = payload.appeal_text.trim().split(/\s+/).length;
 return {score:3.9,label:'high',final_label:'high',classifier_confidence:.57,
  label_agreement:false,agreement_note:'Rating and classifier disagree',class_probs:{low:.1,medium:.57,high:.33},
  original_appeal:payload.appeal_text,remaining_improve_uses:10,gap_statistics_available:true,
  suggestions:words<60?[{check:'length',message:`This appeal has ${words} words. High-rated appeals in the data are usually about 60 or more.`,evidence:'Appears in 43.0% of high-rated and 4.2% of low-rated English appeals.'}]:[]};
}
const server = http.createServer(async(req,res) => {
 const pathname = new URL(req.url,'http://localhost').pathname;
 if(pathname.startsWith('/api/') || pathname === '/health') {
  let raw = ''; for await (const chunk of req) raw += chunk;
  const payload = raw ? JSON.parse(raw) : null; requests.push({path:pathname,payload});
  res.setHeader('Content-Type','application/json'); let data = {};
  if(pathname === '/api/system/credit-status') data = {health:'degraded',message:'Status reflects recorded requests, not a live quota check.',providers:[{provider:'GEMINI_KEY_1',exhausted:true,status_label:'Rate limited',last_status:'429',calls_today:0},{provider:'GEMINI_KEY_2',exhausted:false,status_label:'Last request OK',last_status:'200',calls_today:2}]};
  else if(pathname === '/api/generate-appeal-variants') {
   if(scenario === '503') {res.statusCode=503;data={detail:'Quality model unavailable (mock).'};}
   else data={variants:[variant('formal')],partial:false};
  } else if(pathname.endsWith('/remaining')) {
   if(scenario === 'remaining503') {res.statusCode=503;data={detail:'Later styles unavailable.'};}
   else if(scenario === 'retryable') data={variants:[],partial:true,generation_error:'Provider unavailable (ReadTimeout)',retry_after_seconds:30};
   else data=['partial','52-word'].includes(scenario)?{variants:[],partial:true}:{variants:[variant('community'),variant('urgent')],partial:false};
  } else if(pathname === '/api/quality/evaluate') {
   const style = payload.appeal_text.split(' ')[0]; const v = variant(style);
   data={...v,score:v.quality_score,status:v.final_label,method:'ml_model'};
   for(const key of ['style','appeal_text','model','temperature','generator_status']) delete data[key];
  } else if(pathname === '/api/quality/analyse') data=analysis(payload);
  else if(pathname === '/api/quality/improve') {
   const before={...analysis(payload),raw_quality_score:3.95}, kept=!['analyzer-rejected','analyzer-no-improvement','analyzer-429','analyzer-503'].includes(scenario);
   const after=kept?{...before,score:4.1,quality_score:4.1,class_probs:{low:.1,medium:.1,high:.8},label_agreement:true}:before;
   data={kept,before,after,original_appeal:payload.appeal_text,improved_appeal:kept?text('Families',85):payload.appeal_text,
    original_score:3.9,improved_score:kept?4.1:3.9,original_label:'high',improved_label:'high',
    remaining_improve_uses:kept?9:10,rejection_reason:kept?null:'facts_guard',
    candidate_assessment:kept?null:{score:{quality_score:4.5,raw_quality_score:4.7},facts_passed:false,length_passed:true,guard_reason:'changed_amount'},
    message:kept?null:'Original retained: a monetary amount changed.'};
   if(scenario==='analyzer-429')Object.assign(data,{diagnostic_id:'offline-429',provider_status:'429',provider_attempts:1,rejection_reason:'provider_error',candidate_assessment:null,message:'Original retained: Gemini is rate-limited. Try again later.'});
   if(scenario==='analyzer-503')Object.assign(data,{diagnostic_id:'offline-503',provider_status:'503',provider_attempts:2,rejection_reason:'provider_error',candidate_assessment:null,message:'Original retained: provider unavailable.'});
   if(scenario==='analyzer-no-improvement')Object.assign(data,{rejection_reason:'no_improvement',message:'Original retained: no score gain.'});
   if(scenario==='analyzer-malformed')data={...data,before:{score:'invalid score'}};
  } else if(!['/api/log-copy','/health'].includes(pathname)) {res.statusCode=404; data={detail:'Unmocked API route'};}
  res.end(JSON.stringify(data));return;
 }
 const requested=path.resolve(build,'.'+decodeURIComponent(pathname));
 const file=requested.startsWith(path.resolve(build)+path.sep)&&fs.existsSync(requested)&&fs.statSync(requested).isFile()?requested:path.join(build,'index.html');
 const type={'.html':'text/html','.js':'text/javascript','.css':'text/css','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.ico':'image/x-icon'}[path.extname(file)]||'application/octet-stream';
 res.setHeader('Content-Type',type);res.end(fs.readFileSync(file));
});
class CDP {
 constructor(ws){this.ws=ws;this.next=1;this.pending=new Map();ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id){const p=this.pending.get(m.id);if(p){this.pending.delete(m.id);if(m.error) p.reject(new Error(m.error.message)); else p.resolve(m.result);}}else if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text+': '+(m.params.exceptionDetails.exception?.description||''));else if(m.method==='Runtime.consoleAPICalled')consoleMessages.push({type:m.params.type,text:m.params.args[0]?.value});});}
 send(method,params={},sessionId){const id=this.next++;return new Promise((resolve,reject)=>{this.pending.set(id,{resolve,reject});this.ws.send(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})}));});}
}
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const origin=`http://127.0.0.1:${server.address().port}`;
 const profile=fs.mkdtempSync(path.join(os.tmpdir(),'generator-chrome-'));
 const chrome=spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',['--headless=new','--remote-debugging-port=0',`--user-data-dir=${profile}`,'--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-sync','--disable-component-update','--disable-extensions','about:blank'],{windowsHide:true,stdio:'ignore'});
 let cdp,session,ws;
 try{
  const active=path.join(profile,'DevToolsActivePort');for(let i=0;i<100&&!fs.existsSync(active);i++)await delay(100);
  const lines=fs.readFileSync(active,'utf8').split('\n');ws=new WebSocket(`ws://127.0.0.1:${lines[0]}${lines[1]}`);await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true});});cdp=new CDP(ws);
  const {targetId}=await cdp.send('Target.createTarget',{url:'about:blank'});({sessionId:session}=await cdp.send('Target.attachToTarget',{targetId,flatten:true}));
  await cdp.send('Page.enable',{},session);await cdp.send('Runtime.enable',{},session);
  await cdp.send('Browser.grantPermissions',{origin,permissions:['clipboardReadWrite','clipboardSanitizedWrite']});
  const evaluate=async(expression)=>{const result=await cdp.send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true},session);if(result.exceptionDetails)throw new Error(result.exceptionDetails.exception?.description||result.exceptionDetails.text);return result.result.value;};
  const wait=async(expression)=>{for(let i=0;i<100;i++){if(await evaluate(expression))return;await delay(100);}throw new Error('Timeout waiting: '+expression+'\n'+await evaluate('document.body.innerText'));};
  const click=label=>evaluate(`(()=>{const b=[...document.querySelectorAll('button')].find(b=>b.textContent.trim()===${JSON.stringify(label)});if(!b||b.disabled)throw Error('Button unavailable: '+${JSON.stringify(label)});b.click();})()`);
  const fill=async(id,value)=>{await evaluate(`(()=>{const el=document.getElementById(${JSON.stringify(id)});Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el,${JSON.stringify(value)});el.dispatchEvent(new Event('input',{bubbles:true}));})()`);await delay(40);};
  const results=[];
  const expected={normal:['community','urgent','formal'],'band-first':['community','urgent','formal'],agreement:['community','urgent','formal'],label:['urgent','community','formal'],confidence:['urgent','community','formal'],score:['urgent','community','formal'],'none-agree':['urgent','community','formal'],disagreement:['formal','community','urgent']};
  for(const current of ['normal','generator-mobile','band-first','agreement','label','confidence','score','none-agree','disagreement','52-word','partial','503','remaining503','retryable','analyzer-52','analyzer-60','analyzer-disagreement','analyzer-kept','analyzer-rejected','analyzer-no-improvement','analyzer-mobile','analyzer-429','analyzer-503','analyzer-malformed']) {
   scenario=current; requests=[]; errors=[]; consoleMessages=[];
   const analyzer=current.startsWith('analyzer-');
   await cdp.send('Emulation.setDeviceMetricsOverride',{width:current.endsWith('-mobile')?390:1280,height:900,deviceScaleFactor:1,mobile:current.endsWith('-mobile')},session);
   await cdp.send('Page.navigate',{url:origin+(analyzer?'/donation-appeal-analyzer':'/donation-appeal')},session);
   if(analyzer) {
    await wait(`!!document.querySelector('.daa-textarea')`);
    const appeal=text('Families',current==='analyzer-60'?60:52);
    await evaluate(`(()=>{const el=document.querySelector('.daa-textarea');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(el,${JSON.stringify(appeal)});el.dispatchEvent(new Event('input',{bubbles:true}));})()`);
    await delay(60);await click('Analyze Appeal');await wait(`!!document.querySelector('.daa-rating-card .daa-classifier-result')`);
    const body=await evaluate('document.body.innerText');
    assert.equal(await evaluate(`document.querySelector('.daa-textarea').spellcheck`),false);
    assert.deepEqual(await evaluate(`[...document.querySelectorAll('.daa-section-num')].map(x=>x.textContent)`),['1','2','3']);
    assert.equal(await evaluate(`document.querySelectorAll('.appeal-scorecard, .appeal-scorecard-score').length`),0);
    assert.equal(await evaluate(`document.querySelector('.daa-classifier-label').textContent.trim()`),'medium');
    assert.equal(await evaluate(`document.querySelectorAll('.appeal-scorecard [role=meter], .appeal-scorecard-confidence').length`),0);
    const expectedTip=`This appeal has ${current==='analyzer-60'?60:52} words. High-rated appeals in the data are usually about 60 or more.`;
    assert.equal(body.includes(expectedTip),current!=='analyzer-60');
    assert(!body.includes('Appears in'));
    assert.equal(await evaluate(`document.querySelectorAll('.daa-suggestion p').length`),0);
    const layout=await evaluate(`(()=>{const r=document.querySelector('.daa-rating-card').getBoundingClientRect(),s=document.querySelector('.daa-suggestions-card').getBoundingClientRect(),i=document.querySelector('.daa-input-card').getBoundingClientRect(),g=document.querySelector('.daa-results-grid').getBoundingClientRect();return {rx:r.x,ry:r.y,rw:r.width,sx:s.x,sy:s.y,sw:s.width,iw:i.width,gw:g.width,overflow:document.documentElement.scrollWidth>innerWidth};})()`);
    assert(Math.abs(layout.iw-layout.gw)<2);assert.equal(layout.overflow,false);
    assert(layout.sy>layout.ry);assert(Math.abs(layout.rx-layout.sx)<2);
    assert(Math.abs(layout.rw-layout.iw)<2);assert(Math.abs(layout.sw-layout.iw)<2);
    assert.equal(await evaluate(`document.querySelectorAll('.appeal-scorecard-accuracy, .appeal-rating-details').length`),0);
    assert(!(await evaluate('document.body.innerText')).includes('improve uses remaining today'));
    if(current==='analyzer-malformed') {
     await click('Improve this appeal');await wait(`!!document.querySelector('.daa-improve-row [role="alert"]')`);
     assert((await evaluate('document.body.innerText')).includes('invalid improvement response'));
     assert.equal(await evaluate(`!!document.querySelector('.daa-improved-card')`),false);
     assert(consoleMessages.some(m=>m.type==='error' && m.text==='[Appeal Improve] Invalid response'));
     assert.equal(errors.length,0);
     results.push({scenario:current,invalidResponseVisible:true,consoleDiagnostic:true,runtimeErrors:0});continue;
    }
    if(['analyzer-429','analyzer-503'].includes(current)) {
     await click('Improve this appeal');await wait(`!!document.querySelector('.daa-improve-row [role="alert"]')`);
     const message=await evaluate(`document.querySelector('.daa-improve-row [role="alert"]').textContent`);
     assert(message.includes(current==='analyzer-429'?'rate-limited':'temporarily unavailable'));
     assert.equal(await evaluate(`document.querySelectorAll('.daa-improved-card').length`),0);
     assert.equal(errors.length,0);
     results.push({scenario:current,providerFailureVisible:true,noDuplicateOriginal:true,runtimeErrors:0});continue;
    }
    if(['analyzer-no-improvement','analyzer-rejected'].includes(current)) {
     await click('Improve this appeal');
     if(current==='analyzer-no-improvement') {
      for(let i=0;i<100&&!consoleMessages.some(m=>m.text==='[Appeal Improve] Original retained');i++)await delay(50);
      assert(consoleMessages.some(m=>m.text==='[Appeal Improve] Original retained'));
      await wait(`document.querySelector('.daa-improve-row button').textContent.trim()==='Improve this appeal'`);
      assert(!(await evaluate('document.body.innerText')).includes('No higher-scoring rewrite found'));
     } else await wait(`document.body.innerText.includes('No fact-preserving rewrite found.')`);
     assert.equal(await evaluate(`document.querySelectorAll('.daa-improved-card').length`),0);
     assert.equal(await evaluate(`document.querySelector('.daa-textarea').value`),appeal);
     assert.equal(await evaluate(`document.querySelectorAll('.daa-improve-row [role="alert"]').length`),0);
     assert.equal(errors.length,0);
     results.push({scenario:current,clearOutcome:true,noDuplicateOriginal:true,runtimeErrors:0});continue;
    }
    if(['analyzer-kept','analyzer-mobile'].includes(current)) {
     await click('Improve this appeal');await wait(`!!document.querySelector('.daa-improved-card')`);
     assert.deepEqual(await evaluate(`[...document.querySelectorAll('.daa-section-num')].map(x=>x.textContent)`),['1','2','3','4']);
     assert.equal(await evaluate(`document.querySelectorAll('.daa-improved-card .daa-classifier-result').length`),2);
     assert.deepEqual(await evaluate(`[...document.querySelectorAll('.daa-improved-card .daa-classifier-label')].map(el=>el.textContent.trim())`),['medium','high']);
     assert.equal(await evaluate(`document.querySelectorAll('.appeal-scorecard, .appeal-scorecard-score').length`),0);
     assert((await evaluate(`document.querySelector('.daa-improved-card').textContent`)).includes(text('Families',85)));
     assert.equal(await evaluate(`Math.abs(document.querySelector('.daa-improved-card').getBoundingClientRect().width-document.querySelector('.daa-input-card').getBoundingClientRect().width)<2`),true);
     const copyStyles=await evaluate(`['.daa-original-copy-btn','.daa-copy-row .daa-copy-btn'].map(selector=>{const s=getComputedStyle(document.querySelector(selector));return [s.backgroundColor,s.color,s.borderRadius,s.fontSize,s.fontWeight,s.padding,s.minHeight];})`);
     assert.deepEqual(copyStyles[0],copyStyles[1]);
     assert.equal(await evaluate(`document.querySelector('.daa-original-copy-btn').textContent`),'Copy Original Appeal');
     await evaluate(`document.querySelector('.daa-original-copy-btn').click()`);
     await wait(`document.body.innerText.includes('Original copied')`);
     assert.equal(await evaluate(`navigator.clipboard.readText()`),appeal);
     assert(!(await evaluate(`document.querySelector('.daa-improved-card').textContent`)).includes('Underlying model score'));
     assert.equal(await evaluate(`document.querySelectorAll('.daa-underlying-score').length`),0);
     const resultBody=await evaluate('document.body.innerText');
     assert(!resultBody.includes('improve uses remaining today'));
     assert(!resultBody.includes('Original retained:'));
     assert(!resultBody.includes('Reason:'));
     assert(!resultBody.includes('Improvement diagnostics'));
     assert.equal(await evaluate(`document.querySelectorAll('.daa-improvement-diagnostic, .daa-candidate-assessment').length`),0);
     assert.equal(await evaluate(`document.querySelector('.daa-copy-btn').textContent`),'Copy Improved Appeal');
     assert(consoleMessages.some(m=>m.text?.startsWith('[Appeal Improve]')));
     assert.equal(await evaluate(`new Set([...document.querySelectorAll('.daa-primary-btn')].map(x=>getComputedStyle(x).backgroundColor)).size`),1);
    }
    for(const req of requests.filter(r=>r.path==='/api/quality/analyse'||r.path==='/api/quality/improve'))assert.deepEqual(Object.keys(req.payload).sort(),['appeal_text','language']);
    assert.equal(await evaluate(`document.querySelectorAll('.appeal-scorecard-accuracy, .appeal-rating-details').length`),0);
    assert.equal(errors.length,0,errors.join('\n'));
    results.push({scenario:current,labelAndScoreOnly:true,correctSectionOrder:true,layout, runtimeErrors:errors.length});continue;
   }
   await wait(`!!document.getElementById('location')`);
   const checkGeneratorLayout=async()=>assert.equal(await evaluate(`(()=>{const form=document.querySelector('.campaign-form').getBoundingClientRect(),result=document.querySelector('.appeal-results').getBoundingClientRect();return Math.abs(form.x-result.x)<2 && Math.abs(form.width-result.width)<2 && document.documentElement.scrollWidth<=innerWidth;})()`),true);
   await checkGeneratorLayout();
   assert.equal(await evaluate(`document.getElementById('campaign_goal').value`),'Support affected families and help the community in need');
   assert.equal(await evaluate(`document.querySelector('label[for="verified_need"]').textContent`),'Specific need');
   const options=await evaluate(`[...document.getElementById('length_category').options].map(x=>x.textContent)`);
   assert.deepEqual(options,['Short (about 65-100 words)','Medium (about 105-150 words)','Long (about 185-250 words)']);
   assert.equal(await evaluate(`getComputedStyle(document.getElementById('length_category')).fontSize===getComputedStyle(document.getElementById('length_category').options[0]).fontSize`),true);
   await fill('location','Malabe');await fill('verified_need','water bottles and tents for 20 people');await click('Generate Appeal');
   if(current==='503') {await wait(`document.body.innerText.includes('HTTP 503: Quality model unavailable')`);assert(!requests.some(r=>r.path.endsWith('/remaining')));results.push({scenario:current,httpStatusVisible:true});continue;}
   await wait(`!!document.querySelector('.variant-count') && !document.querySelector('.appeal-final-progress')`);await delay(60);
   await checkGeneratorLayout();
   const count=parseInt((await evaluate(`document.querySelector('.variant-count').innerText`)).split('/')[1]),order=[];
   for(let index=0;index<count;index++) {
    const style=await evaluate(`document.querySelector('.variant-meta span').textContent`);order.push(style);
    assert.equal(await evaluate(`document.querySelectorAll('.variant-card .appeal-scorecard').length`),1);
    assert.equal(await evaluate(`document.querySelector('.variant-card > p').nextElementSibling.className`),'appeal-scorecard');
    assert.equal(await evaluate(`document.querySelector('.appeal-scorecard-score').textContent`),variant(style).quality_score.toFixed(2));
    assert.equal(await evaluate(`document.querySelectorAll('.appeal-scorecard [role=meter], .appeal-scorecard-confidence').length`),0);
    assert.equal(await evaluate(`document.querySelectorAll('.appeal-scorecard-accuracy, .appeal-rating-details').length`),0);
    const body=await evaluate('document.body.innerText');
    assert(!body.includes('mock-provider-name')&&!body.includes('T 0.5')&&!body.includes('Association, not a guarantee.'));
    assert(!body.includes('Appears in'));
    assert.equal(await evaluate(`document.querySelectorAll('.appeal-guidance').length`),0);
    assert(!body.includes('Say how the donation will be used.'));
    assert(!body.includes('This appeal has 52 words. Appeals under about 65 words tend to rate lower.'));
    if(current==='52-word')assert(body.includes('Generated 52 words; requested band is 65-100 words.'));
    if(index+1<count) {await evaluate(`document.querySelector('[aria-label="Next appeal variant"]').click()`);await wait(`document.querySelector('.variant-count').innerText.trim().startsWith('${index+2}/') && !document.body.innerText.includes('Evaluating selected appeal...')`);}
   }
   if(expected[current])assert.deepEqual(order,expected[current]);
   if(current==='partial')assert.equal(count,1);
   if(current==='remaining503')assert((await evaluate('document.body.innerText')).includes('HTTP 503: Later styles unavailable'));
   if(current==='retryable') {
    const message=await evaluate(`document.querySelector('.appeal-partial-note').textContent`);
    assert(message.includes('ReadTimeout') && message.includes('30 seconds'));
    assert.equal(count,1);
   }
   if(current==='normal') {
    await evaluate(`document.querySelector('[aria-label="Provider status"]').click()`);
    await wait(`document.body.innerText.includes('Last result: 429')`);
    const status=await evaluate('document.body.innerText');
    assert(status.toLowerCase().includes('not a live quota check') && status.includes('Last result: 429') && status.toLowerCase().includes('last request ok'),status);
    await evaluate(`document.querySelector('[aria-label="Provider status"]').click()`);
   }
   assert.equal(requests.filter(r=>r.path.endsWith('/improve')).length,0);
   await click('Copy Text');await wait(`document.body.innerText.includes('Appeal copied to clipboard')`);
   assert.equal(errors.length,0,errors.join('\n'));
   results.push({scenario:current,order,allVariantsAvailable:true,labelAndScoreOnly:true,runtimeErrors:errors.length});
  }
  const report={localMockBackend:origin,realBackendForwarded:false,realGeminiCalls:0,results};
  const output=path.join(os.tmpdir(),'appeal_ui_consistency_browser_report.json');fs.writeFileSync(output,JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));console.log('Report: '+output);
 }finally{try{if(cdp)await cdp.send('Browser.close');}catch{}if(ws)ws.close();chrome.kill();server.closeAllConnections();server.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
