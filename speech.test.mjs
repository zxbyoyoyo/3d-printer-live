import {test} from 'node:test';
import assert from 'node:assert/strict';
import {GiftSpeech} from './gift-speech.mjs';

test('gift thanks are short, name the gift, and do not repeat consecutively',()=>{
 const speech=new GiftSpeech();let previous='';const variants=new Set();
 for(let i=0;i<300;i++){
  const line=speech.text('小熊','小心心',1);
  assert.ok(line.includes('小熊')&&line.includes('小心心'));
  assert.ok(!line.includes('1个'));
  assert.ok(line.length<=30, line);
  assert.notEqual(line,previous);previous=line;variants.add(line);
 }
 assert.ok(variants.size>=10);
 assert.ok([...variants].some(line=>line.includes('爱你哦')));
 assert.ok([...variants].some(line=>line.includes('太感谢')));
});
test('multiple gifts preserve their actual count and names are cleaned',()=>{
 const speech=new GiftSpeech();
 for(let i=0;i<60;i++){
  const line=speech.text('小熊<\n>','啤酒',3);
  assert.ok(line.includes('小熊')&&line.includes('3个啤酒'));
  assert.ok(!/[<>\n]/.test(line));
 }
});
test('follow and welcome messages remain short, with a follow-back variant',()=>{
 const speech=new GiftSpeech();const lines=[];speech.enqueue=text=>lines.push(text);
 for(let i=0;i<200;i++)speech.follow('小熊');
 assert.ok(lines.every(line=>line.length<=32));
 assert.ok(lines.some(line=>line.includes('我也会回关你的哈')));
 const welcomes=[];speech.enqueue=text=>welcomes.push(text);
 for(let i=0;i<100;i++)speech.welcome('小熊');
 assert.ok(welcomes.every(line=>line.length<=22));
});
