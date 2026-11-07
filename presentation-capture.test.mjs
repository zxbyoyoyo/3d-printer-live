import {test} from 'node:test';
import assert from 'node:assert/strict';
import {SceneOutput} from './scene-output.mjs';
test('capture renders the presentation into the same canvas after the final scene',()=>{
 const calls=[];
 const renderer={shadowMap:{},setRenderTarget:t=>calls.push(t),render:scene=>calls.push(scene)};
 const out=Object.assign(Object.create(SceneOutput.prototype),{renderer,target:'hdr',scene:'final',camera:'camera'});
 const overlay={render:r=>{assert.equal(r,renderer);calls.push('overlay')}};
 out.render('printer','camera',overlay);
 assert.deepEqual(calls,['hdr','printer',null,'final','overlay']);
});

import {LivePresentation} from './live-presentation.mjs';
import {PresentationState} from './presentation-state.mjs';
test('ordinary printing and completed results leave the scene free of overlay panels',()=>{
 const state=new PresentationState();state.begin({name:'测试观众',priority:false});
 const overlay=Object.assign(Object.create(LivePresentation.prototype),{state,scene:{},camera:{}});
 let renders=0;
 const renderer={autoClear:true,clearDepth(){},render(){renders++}};
 overlay.render(renderer);state.complete(79);state.tick(1);overlay.render(renderer);
 assert.equal(renders,0,'no permanent avatar/progress/score panel may cover the printer');
});
test('gift compositing restores renderer state even if a render fails',()=>{
 const state=new PresentationState();state.begin({name:'测试观众',gift:'heart'});
 const overlay=Object.assign(Object.create(LivePresentation.prototype),{state,scene:{},camera:{}});
 const renderer={autoClear:true,clearDepth(){},render(){assert.equal(this.autoClear,false);throw new Error('context lost')}};
 assert.throws(()=>overlay.render(renderer),/context lost/);assert.equal(renderer.autoClear,true);
});
