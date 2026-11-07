import { test } from 'node:test';
import assert from 'node:assert/strict';
import { GiftSpeech } from './gift-speech.mjs';
import { GiftSpeech as EnglishSpeech } from './gift-speech-en.mjs';

for (const [language, Speech] of [['中文', GiftSpeech], ['English', EnglishSpeech]]) {
 test(`${language}: follow thanks include the viewer and do not repeat consecutively`, () => {
   const speech = new Speech();
   const messages = [];
   speech.enqueue = text => messages.push(text);
   for (let i = 0; i < 30; i++) speech.follow('小熊<\n>');
   assert.equal(messages.length, 30);
   for (const text of messages) {
     assert.ok(text.includes('小熊'));
     assert.ok(!/[<>\n]/.test(text));
     assert.match(text, language === '中文' ? /关注/ : /follow/i);
   }
   for (let i = 1; i < messages.length; i++) assert.notEqual(messages[i], messages[i-1]);
 });
}
