// Offline browser regression tests. All API calls use synthetic responses.
// Run: node frontend/tests/triage_persistence_ui.cjs <built frontend directory>
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const http = require('node:http');
const {spawn} = require('node:child_process');
const assert = require('node:assert/strict');
const build = process.argv[2];
const delay = ms => new Promise(r => setTimeout(r, ms));
let errors = [], consoleMessages = [], saves = [], records = [], failSave = true, failLoad = false, failArchive = true, shouldQueue = true, readDelay = 0, readRequests = 0;
const fixtureSession = {session_id:'synthetic-session',camp:{id:'synthetic-camp',name:'Synthetic Camp'},mos:[{id:'synthetic-mo',name:'Synthetic Officer',role:'Senior MO',specialty:'General Practice',skills:[],supervisor:'yes',queueDepth:0}]};
const server = http.createServer(async(req,res)=>{
 const pathname = new URL(req.url,'http://localhost').pathname;
 if(pathname.startsWith('/api/') || pathname==='/health'){
  let body='';for await(const chunk of req)body+=chunk;
  const payload=body?JSON.parse(body):{};
  let data={};res.setHeader('Content-Type','application/json');
  if(pathname==='/api/severity/extract')data={valid:true,extracted_symptoms:['headache'],condition_group:'General Practice',specialty:'General Practice'};
  else if(pathname==='/api/severity/classify')data={suggested_specialty:{primary:'General Practice',secondary:[],reason:'Synthetic patient evidence explanation',fallback:false,evidence:{'General Practice':['synthetic test evidence']},review_reasons:['Synthetic review notice']},severity:'LOW',should_queue:shouldQueue,risk_score:12,priority_score:12,method:'test',queue_title:'Synthetic complaint',queue_description:'Synthetic classification',scores:{LOW:0.9},matched_rules:[],vitals_warnings:[]};
  else if(pathname==='/api/v1/triage/patient/save'){
   saves.push(payload);
   if(failSave){res.statusCode=503;data={detail:'Synthetic database unavailable'};}
   else {if(!records.some(p=>p.id===payload.id))records.push(payload);data={status:'saved',doc_id:payload.id};}
  }
  else if(pathname==='/api/v1/triage/patients'){
   readRequests++;if(readDelay)await delay(readDelay);
   if(failLoad){res.statusCode=503;data={detail:'Synthetic list unavailable'};}
   else data={patients:records,total:records.length};
  }
  else if(pathname==='/api/v1/triage/session/end'){
   if(failArchive){res.statusCode=503;data={detail:'Synthetic archive unavailable'};}
   else data={status:'archived',doc_id:'synthetic-archive'};
  }
  else if(pathname==='/api/v1/auth/me')data={id:'synthetic-user',name:'Synthetic Tester',role:'admin'};
  else if(pathname==='/api/v1/camps')data=[];
  else if(pathname==='/api/credits/status')data={};
  res.end(JSON.stringify(data));return;
 }
 const requested=path.resolve(build,'.'+decodeURIComponent(pathname));
 const file=requested.startsWith(path.resolve(build)+path.sep)&&fs.existsSync(requested)&&fs.statSync(requested).isFile()?requested:path.join(build,'index.html');
 const type={'.html':'text/html','.js':'text/javascript','.css':'text/css','.svg':'image/svg+xml','.png':'image/png'}[path.extname(file)]||'application/octet-stream';
 res.setHeader('Content-Type',type);res.end(fs.readFileSync(file));
});
class CDP {
 constructor(ws){this.ws=ws;this.next=1;this.pending=new Map();ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id){const p=this.pending.get(m.id);if(p){this.pending.delete(m.id);if(m.error) p.reject(new Error(m.error.message)); else p.resolve(m.result);}}else if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text+': '+(m.params.exceptionDetails.exception?.description||''));else if(m.method==='Runtime.consoleAPICalled')consoleMessages.push({type:m.params.type,text:m.params.args[0]?.value});});}
 send(method,params={},sessionId){const id=this.next++;return new Promise((resolve,reject)=>{this.pending.set(id,{resolve,reject});this.ws.send(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})}));});}
}
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const origin=`http://127.0.0.1:${server.address().port}`;
 const profile=fs.mkdtempSync(path.join(os.tmpdir(),'triage-chrome-'));
 const chrome=spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',['--headless=new','--remote-debugging-port=0',`--user-data-dir=${profile}`,'--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-sync','--disable-component-update','--disable-extensions','about:blank'],{windowsHide:true,stdio:'ignore'});
 let cdp,session,ws;
 try{
  const active=path.join(profile,'DevToolsActivePort');for(let i=0;i<100&&!fs.existsSync(active);i++)await delay(100);
  const lines=fs.readFileSync(active,'utf8').split('\n');ws=new WebSocket(`ws://127.0.0.1:${lines[0]}${lines[1]}`);await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true});});cdp=new CDP(ws);
  const {targetId}=await cdp.send('Target.createTarget',{url:'about:blank'});({sessionId:session}=await cdp.send('Target.attachToTarget',{targetId,flatten:true}));
  await cdp.send('Page.enable',{},session);await cdp.send('Runtime.enable',{},session);
  await cdp.send('Browser.grantPermissions',{origin,permissions:['clipboardReadWrite','clipboardSanitizedWrite']});
  const evaluate=async(expression)=>{const result=await cdp.send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true},session);if(result.exceptionDetails)throw new Error(result.exceptionDetails.exception?.description||result.exceptionDetails.text);return result.result.value;};
  const wait=async(expression)=>{for(let i=0;i<100;i++){if(await evaluate('!!document.body && ('+expression+')'))return;await delay(100);}throw new Error('Timeout waiting: '+expression+'\n'+await evaluate('document.body.innerText'));};
  const click=label=>evaluate(`(()=>{const b=[...document.querySelectorAll('button')].find(b=>b.textContent.trim()===${JSON.stringify(label)});if(!b||b.disabled)throw Error('Button unavailable: '+${JSON.stringify(label)});b.click();})()`);
  const fill=async(id,value)=>{await evaluate(`(()=>{const el=document.getElementById(${JSON.stringify(id)});Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el,${JSON.stringify(value)});el.dispatchEvent(new Event('input',{bubbles:true}));})()`);await delay(40);};

  await cdp.send('Page.addScriptToEvaluateOnNewDocument',{source:`localStorage.setItem('dr_token','synthetic-offline-token');localStorage.setItem('dr_user',JSON.stringify({id:'synthetic-user',name:'Synthetic Tester',role:'admin'}));if(!sessionStorage.getItem('seeded')){localStorage.setItem('severityQueueSession',${JSON.stringify(JSON.stringify(fixtureSession))});sessionStorage.setItem('seeded','yes');}`},session);
  const navigate=async(route)=>{await cdp.send('Page.navigate',{url:origin+route},session);};
  const fillField=async(id,value)=>{
   await evaluate(`(()=>{const el=document.getElementById(${JSON.stringify(id)});const proto=el instanceof HTMLTextAreaElement?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;Object.getOwnPropertyDescriptor(proto,'value').set.call(el,${JSON.stringify(value)});el.dispatchEvent(new Event('input',{bubbles:true}));})()`);
   await delay(50);
  };
  const fillPatient=async()=>{
   await wait(`!!document.getElementById('symptoms')`);
   await fillField('age','30');await fillField('symptoms','Synthetic mild headache');
   await fillField('clinicalNote','Synthetic headache assessment for testing only.');
   await fillField('vital_spo2','99');await fillField('pain_score','0');
  };
  const pendingCount=()=>evaluate(`Object.keys(localStorage).filter(k=>k.startsWith('pendingTriagePatient:')).length`);
  await navigate('/priority-application');await fillPatient();
  await click('Classify and Assign');await wait(`!![...document.querySelectorAll('button')].find(b=>b.textContent==='Save and Submit to Queue')`);
  await wait(`!!document.querySelector('.priority-suggested-specialty')`);
  await evaluate(`document.querySelector('.priority-specialty-details').open=true`);
  assert.equal(await evaluate(`document.body.innerText.includes('General Practice: synthetic test evidence')`),true);
  assert.equal(await evaluate(`document.body.innerText.includes('Synthetic review notice')`),true);
  assert.equal(await evaluate(`document.body.innerText.includes('routed by suggested specialty')`),true);
  console.log('PASS specialty evidence, review notice and unified routing render in the browser');
  // Edits must invalidate the previous classification.
  await fillField('symptoms','Synthetic headache changed');
  assert.equal(await evaluate(`!![...document.querySelectorAll('button')].find(b=>b.textContent==='Save and Submit to Queue')`),false);
  await click('Classify and Assign');await wait(`!![...document.querySelectorAll('button')].find(b=>b.textContent==='Save and Submit to Queue')`);
  await evaluate(`(()=>{const f=document.querySelector('.priority-application-form');f.requestSubmit();f.requestSubmit();})()`);
  await wait(`document.body.innerText.includes('Save not confirmed')`);
  assert.equal(saves.length,1);assert.equal(await evaluate('location.pathname'),'/priority-application');assert.equal(await pendingCount(),1);
  assert.equal(saves[0].clinical_note,'Synthetic headache assessment for testing only.');
  assert.deepEqual(saves[0].vitals,{vital_spo2:99,pain_score:0});
  await navigate('/priority-application');await wait(`document.body.innerText.includes('Retry pending complaint')`);
  failSave=false;await click('Retry pending complaint');
  await wait(`location.pathname==='/priority-queue' && document.body.innerText.includes('Synthetic headache changed')`);
  assert.equal(saves.length,2);assert.equal(saves[0].id,saves[1].id);assert.equal(records.length,1);assert.equal(await pendingCount(),0);
  console.log('PASS save failure stays visible, double submit blocked, reload recovers, retry reuses ID, notes/vitals retained');

  await cdp.send('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false},session);
  await delay(100);
  const buttonLayout=()=>evaluate(`(()=>{const a=document.querySelector('.priority-header-actions');return {bounds:a.getBoundingClientRect().toJSON(),buttons:[...a.children].map(b=>({label:b.textContent.trim(),...b.getBoundingClientRect().toJSON()}))};})()`);
  const desktop=await buttonLayout();
  assert.equal(new Set(desktop.buttons.map(b=>Math.round(b.y))).size,1);
  assert.equal(new Set(desktop.buttons.map(b=>Math.round(b.height))).size,1);
  assert.ok(desktop.buttons[1].x-desktop.buttons[0].right>=7);
  assert.equal(await evaluate(`getComputedStyle(document.querySelector('.priority-btn-refresh')).borderTopStyle`),'solid');
  const captureHeader=async(name)=>{
    const clip=await evaluate(`(()=>{const r=document.querySelector('.priority-header').getBoundingClientRect();return {x:Math.max(0,r.x),y:Math.max(0,r.y),width:r.width,height:r.height,scale:1};})()`);
    const screenshot=await cdp.send('Page.captureScreenshot',{format:'png',clip},session);
    fs.writeFileSync(path.join(path.dirname(path.resolve(build)),name),Buffer.from(screenshot.data,'base64'));
  };
  await captureHeader('queue-header-desktop.png');
  await cdp.send('Emulation.setDeviceMetricsOverride',{width:390,height:900,deviceScaleFactor:1,mobile:true},session);
  await delay(100);
  const mobile=await buttonLayout();
  for(const button of mobile.buttons){assert.ok(button.x>=mobile.bounds.x-1);assert.ok(button.right<=mobile.bounds.right+1);}
  if(mobile.bounds.width<280){
    assert.equal(new Set(mobile.buttons.map(b=>Math.round(b.width))).size,1);
    assert.ok(mobile.buttons[2].y>mobile.buttons[0].y);
  }else{
    assert.ok(mobile.buttons[1].width>mobile.buttons[0].width);
    assert.equal(Math.round(mobile.buttons[0].y),Math.round(mobile.buttons[2].y));
  }
  assert.equal(await evaluate(`[...document.querySelector('.priority-header-actions').children].every(b=>b.scrollWidth<=b.clientWidth)`),true);
  await captureHeader('queue-header-mobile.png');
  await cdp.send('Emulation.setDeviceMetricsOverride',{width:1280,height:900,deviceScaleFactor:1,mobile:false},session);
  const historyBefore=await evaluate('history.length'), requestsBefore=readRequests;
  readDelay=500;await click('Refresh');
  await wait(`document.querySelector('.priority-btn-refresh').disabled && document.querySelector('.priority-btn-refresh').getAttribute('aria-busy')==='true'`);
  assert.equal(await evaluate(`document.querySelector('.priority-btn-refresh').textContent.trim()`),'Refreshing...');
  await wait(`!document.querySelector('.priority-btn-refresh').disabled`);
  readDelay=0;
  assert.ok(readRequests>requestsBefore);
  assert.equal(await evaluate('history.length'),historyBefore);
  console.log('PASS desktop/mobile action spacing, styled refresh, busy feedback, real reload and stable browser history');
  // Corrupt the browser cache: queue must still display server records.
  await evaluate(`localStorage.setItem('priorityApplications','broken json')`);
  await click('Refresh');await delay(200);
  assert.equal(await evaluate(`document.body.innerText.includes('Synthetic headache changed')`),true);
  failLoad=true;await click('Refresh');await wait(`document.body.innerText.includes('Unable to load confirmed records')`);
  assert.equal(await evaluate(`[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='End Session').disabled`),true);
  failLoad=false;await click('Retry loading');await wait(`!document.body.innerText.includes('Unable to load confirmed records') && !document.body.innerText.includes('Loading saved complaints')`);
  await click('End Session');await click('End Session & Archive');await wait(`document.body.innerText.includes('Unable to end session')`);
  assert.equal(await evaluate(`!!localStorage.getItem('severityQueueSession')`),true);
  assert.equal(await evaluate(`JSON.parse(localStorage.getItem('priorityApplications')).length`),1);
  console.log('PASS queue loads from server despite broken cache, load errors visible, archive failure preserves session');
  // Even a legacy classification response excluding LOW must follow the new workflow.
  shouldQueue=false;await navigate('/priority-application');await fillPatient();
  await click('Classify and Assign');await wait(`document.body.innerText.includes('Save and Submit to Queue')`);
  await click('Save and Submit to Queue');await wait(`location.pathname==='/priority-queue' && !document.body.innerText.includes('Loading saved complaints') && document.querySelectorAll('.priority-patient-card').length===2`);
  assert.equal(records.length,2);assert.equal(records[1].should_queue,true);assert.equal(records[1].assigned_mo_id,'synthetic-mo');
  for(const severity of ['MEDIUM','HIGH','CRITICAL']) records.push({id:'ordered-'+severity,severity,symptoms:'Synthetic '+severity+' queue test',assigned_mo_id:'synthetic-mo',session_id:fixtureSession.session_id});
  records.push({id:'old-excluded-patient',severity:'LOW',symptoms:'Synthetic older unassigned patient',should_queue:false,assigned_mo_id:null,session_id:fixtureSession.session_id});
  await click('Refresh');await wait(`document.querySelectorAll('.priority-patient-card').length===6`);
  assert.deepEqual(await evaluate(`[...document.querySelectorAll('.priority-mo-card:not(.priority-unassigned) .ppc-sev-badge')].map(e=>e.textContent.trim())`),['CRITICAL','HIGH','MEDIUM','LOW','LOW']);
  assert.equal(await evaluate(`document.body.innerText.includes('Synthetic older unassigned patient')`),true);
  console.log('PASS LOW patients are assigned and queued after higher severities; older excluded records remain visible');
  await evaluate(`localStorage.setItem('priorityApplications',JSON.stringify([{id:'legacy-patient',camp:${JSON.stringify(fixtureSession.camp)},symptoms:'Synthetic legacy complaint',complaint_text:'Synthetic legacy complaint',severity:'LOW',assigned_mo_id:'synthetic-mo'}]))`);
  await click('Refresh');await wait(`document.body.innerText.includes('locally stored complaint(s) need save confirmation')`);
  await navigate('/priority-application');await wait(`document.body.innerText.includes('Retry pending complaint')`);
  await click('Retry pending complaint');await wait(`location.pathname==='/priority-queue' && document.body.innerText.includes('Synthetic legacy complaint')`);
  assert.equal(records.length,7);assert.equal(await pendingCount(),0);
  console.log('PASS legacy browser-only complaint is preserved for review and confirmed retry');
  failArchive=false;await click('Refresh');await delay(150);await click('End Session');await click('End Session & Archive');
  await wait(`location.pathname==='/camp-setup'`);
  assert.equal(await evaluate(`localStorage.getItem('severityQueueSession')`),null);
  assert.equal(await evaluate(`localStorage.getItem('priorityApplications')`),null);
  assert.equal(errors.length,0,errors.join('\n'));
  console.log('PASS successful archive clears active state only after acknowledgement; no uncaught browser errors');
 }finally{try{if(cdp)await cdp.send('Browser.close');}catch{}if(ws)ws.close();chrome.kill();server.closeAllConnections();server.close();}
})().catch(err=>{console.error(err);process.exitCode=1;});
