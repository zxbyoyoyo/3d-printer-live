import {test} from 'node:test';
import assert from 'node:assert/strict';
import {PresentationState, giftMotion, revealValue} from './presentation-state.mjs';
import {PORTRAIT_FRAME} from './portrait-framing.mjs';

test('gift entry only runs for the first copy of a gift',()=>{
 const p=new PresentationState();p.begin({name:'小熊',priority:true,copy:1,total:3});
 assert.equal(p.giftVisible,true);
 p.tick(2);assert.equal(p.giftVisible,false);
 p.begin({name:'小熊',priority:true,copy:2,total:3});assert.equal(p.giftVisible,false);
 p.begin({name:'评论',priority:false});assert.equal(p.giftVisible,false);
});
test('real time reveal settles at the exact score and holds before transfer',()=>{
 const p=new PresentationState();p.begin({name:'小熊'});p.complete(79);
 p.tick(.35);assert.ok(p.score>0&&p.score<79);assert.equal(p.revealDone,false);
 p.tick(.4);assert.equal(p.score,79);assert.equal(p.revealDone,false);
 p.tick(.9);assert.equal(p.revealDone,true);assert.equal(p.score,79);
});
test('pause freezes both effects and cancelled jobs leave no stale state',()=>{
 const p=new PresentationState();p.begin({name:'小熊',priority:true});p.complete(95);
 p.tick(.3);const value=p.score,age=p.giftAge;p.tick(2,true);
 assert.equal(p.score,value);assert.equal(p.giftAge,age);
 p.cancel();assert.equal(p.job,null);assert.equal(p.giftVisible,false);assert.equal(p.resultAge,null);
});
test('disabling effects keeps exact results and releases the transfer immediately',()=>{
 const p=new PresentationState();p.enabled=false;p.begin({name:'小熊',priority:true});p.complete(88);
 assert.equal(p.giftVisible,false);assert.equal(p.score,88);assert.equal(p.revealDone,true);
});
test('gift motion and count-up are bounded and deterministic',()=>{
 for(let t=0;t<2;t+=.01){const m=giftMotion(t);assert.ok(m.opacity>=0&&m.opacity<=1);assert.ok(m.scale>=.85&&m.scale<=1.15)}
 assert.equal(revealValue(95,10),95);assert.equal(revealValue(79,0),0);
 assert.deepEqual(PORTRAIT_FRAME.output,[1080,1920]);assert.equal(PORTRAIT_FRAME.fps,30);
 assert.ok([...PORTRAIT_FRAME.position,...PORTRAIT_FRAME.target].every(Number.isFinite));
});

test('gift effects still work when priority insertion is disabled',()=>{
 const p=new PresentationState();p.begin({name:'小熊',gift:'heart',priority:false,copy:1});
 assert.equal(p.giftVisible,true);
});

import {paintProductLabel} from './product-label.mjs';
test('printed plinth hides the score during printing and reveals the actual result',()=>{
 const labels=[];
 const ctx={canvas:{width:1024,height:420},clearRect(){},fillRect(){},measureText:text=>({width:text.length*50}),fillText:text=>labels.push(text)};
 const job={name:'测试观众'};
 paintProductLabel(ctx,job,null);assert.deepEqual(labels,['测试观众','打印中']);
 labels.length=0;paintProductLabel(ctx,job,79);assert.deepEqual(labels,['测试观众','79分']);
});
