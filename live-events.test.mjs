import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

for(const file of ['index.html','index-en.html']){
 const source=fs.readFileSync(new URL(file,import.meta.url),'utf8');
 const code=source.slice(source.indexOf('function add(v)'),source.indexOf('let bridgeConnecting'));
 function setup(rules){
  const spoken=[],printed=[];
  const env={printRules:rules,printAllowed:()=>true,lastLiveMsgAt:0,liveRoom:'',liveStats:{gift:0,like:0,comment:0},updateLiveStats(){},
   giftSpeech:{follow:name=>spoken.push(['follow',name]),say:(...args)=>spoken.push(['gift',...args]),welcome:name=>spoken.push(['join',name])},
   RULES:{heart:{priority:true,label:'小心心'},other:{priority:true,label:'礼物'}},liveEvent:(...args)=>printed.push(args)};
  vm.createContext(env);vm.runInContext(code,env);
  return {add:env.add,spoken,printed};
 }
 test(`${file}: follow voice works with follow printing off`,()=>{
  const env=setup({followVoice:true,follow:false});env.add({type:'follow',name:'小熊'});
  assert.deepEqual(env.spoken,[['follow','小熊']]);assert.equal(env.printed.length,0);
 });
 test(`${file}: follow voice can be muted independently`,()=>{
  const env=setup({followVoice:false,follow:true});env.add({type:'follow',name:'小熊'});
  assert.equal(env.spoken.length,0);assert.equal(env.printed.length,1);
 });
 test(`${file}: gift thanks work with gift printing off`,()=>{
  const env=setup({giftVoice:true,gift:false});env.add({type:'gift',gift:'heart',raw:'小心心',name:'小熊',count:2});
  assert.deepEqual(env.spoken,[['gift','小熊','小心心',2]]);assert.equal(env.printed.length,0);
 });
 test(`${file}: automatic bridge recovery stays off after manual stop`,()=>{
  const start=source.indexOf('function autoStartBridge()');const end=source.indexOf('async function connectBridge()',start);
  let calls=0;const env={captureWanted:false,fetch:()=>{calls++;throw new Error('must stay stopped')}};
  vm.createContext(env);vm.runInContext(source.slice(start,end)+';autoStartBridge();',env);assert.equal(calls,0);
 });
}

for(const file of ['index.html','index-en.html']){
 test(`${file}: offline demo never connects to the running live bridge`,async()=>{
  const source=fs.readFileSync(new URL(file,import.meta.url),'utf8');
  const start=source.indexOf('async function connectBridge()');
  const end=source.indexOf('connectBridge();requestAnimate()',start);
  let requests=0;const env={DEMO_ONLY:true,fetch:()=>{requests++;throw new Error('unexpected live request')}};
  vm.createContext(env);vm.runInContext(source.slice(start,end),env);
  await env.connectBridge();assert.equal(requests,0);
 });
}
