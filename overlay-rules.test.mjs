import {test} from 'node:test';
import assert from 'node:assert/strict';
import {overlayRows} from './overlay-rules.mjs';
test('default overlay advertises the real default counts',()=>{
 assert.deepEqual(overlayRows().map(row=>row.text),['评论 666 打印小图一张','打印大图一张','打印大图两张','打印大图三张']);
});
test('custom counts, sizes and disabled triggers update the overlay',()=>{
 const rows=overlayRows({comment:false,gift:true,giftSize:'small',heartCount:5,beerCount:1,lollipopCount:10});
 assert.equal(rows.length,3);assert.equal(rows[0].text,'打印小图五张');assert.equal(rows[2].text,'打印小图十张');
 assert.deepEqual(overlayRows({comment:false,gift:false}),[]);
});
