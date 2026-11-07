export class GiftSpeech {
 constructor(onStatus=()=>{}){this.enabled=true;this.volume=.85;this.rate=1.08;this.voiceURI='';this.onStatus=onStatus;this.unlocked=false;this.previous=-1;this.queue=[];this.speaking=false;this.generation=0}
 voices(){return globalThis.speechSynthesis?.getVoices()||[]}
 preferred(){const voices=this.voices();return voices.find(v=>v.voiceURI===this.voiceURI)||voices.find(v=>/zh|cmn/i.test(v.lang)&&/xiaoxiao|xiaoyi|huihui|yaoyao|female|女/i.test(v.name))||voices.find(v=>/zh-CN/i.test(v.lang))||voices.find(v=>/^zh/i.test(v.lang))}
 text(name,gift,amount=1){
  const safe=this.safeName(name);
  const label=(amount>1?amount+'个':'')+String(gift).replace(/[<>\n\r]/g,'').slice(0,30);
  return this.choose('previous',[
   `感谢${safe}送出的${label}！`,
   `谢谢${safe}的${label}，爱你哦！`,
   `${safe}，${label}收到啦，谢谢！`,
   `谢谢${safe}支持，${label}收到啦！`,
   `感谢${safe}的${label}，太感谢啦！`,
   `${safe}送来${label}，爱你哦！`,
   `谢谢${safe}送的${label}，比心！`,
   `${safe}，谢谢你的${label}呀！`,
   `收到${safe}的${label}，开心！`,
   `感谢${safe}支持，${label}收下啦！`,
   `${safe}的${label}收到，谢谢啦！`,
   `哇，谢谢${safe}的${label}！`
  ]);
 }
 safeName(name){return String(name).replace(/[<>\n\r]/g,'').slice(0,24)}
 choose(key,lines){
  let n=Math.floor(Math.random()*lines.length);
  if(n===this[key])n=(n+1)%lines.length;
  this[key]=n;
  return lines[n];
 }
 printing(name,finished=false){
  if(!this.unlocked||!this.enabled||this.speaking||this.queue.length)return;
  const safe=this.safeName(name);
  const lines=finished?[`${safe}，头像打印好啦！`,`${safe}，快看你的头像！`,`${safe}，新鲜出炉啦！`,`${safe}，打印完成，喜欢吗？`]:[`${safe}，开始打印啦！`,`${safe}，轮到你啦！`,`${safe}，头像安排上啦！`,`${safe}，马上就好哦！`];
  this.enqueue(this.choose(finished?'lastFinished':'lastPrinting',lines));
 }
 welcome(name){
  this.unlocked=true;const safe=this.safeName(name);
  this.enqueue(this.choose('lastWelcome',[
   `欢迎${safe}，来啦！`,`${safe}来啦，欢迎欢迎！`,
   `欢迎${safe}，进来坐坐呀！`,`${safe}，欢迎来到直播间！`,
   `欢迎${safe}，今天也要开心哦！`,`${safe}来啦，很高兴见到你！`,
   `欢迎${safe}，一起玩呀！`,`${safe}，欢迎你呀！`
  ]));
 }
 follow(name){
  this.unlocked=true;const safe=this.safeName(name);
  this.enqueue(this.choose('lastFollow',[
   `感谢${safe}关注了我，我也会回关你的哈！`,
   `谢谢${safe}的关注，爱你哦！`,
   `${safe}关注啦，谢谢支持！`,
   `感谢${safe}点关注，太感谢啦！`,
   `谢谢${safe}关注，比心！`,
   `${safe}，关注收到啦，爱你哦！`,
   `感谢${safe}关注，常来玩呀！`,
   `谢谢${safe}关注，我也会回关你的哈！`,
   `${safe}，谢谢你的关注呀！`,
   `感谢${safe}的关注，开心！`
  ]));
 }
 enqueue(text){if(!this.enabled)return;if(!globalThis.speechSynthesis){this.onStatus('当前浏览器不支持语音播报');return}if(this.queue.length>=12){this.onStatus('播报队列已满，本次仅显示字幕：'+text);return}this.queue.push(text);this.pump()}
 say(name,gift,amount=1){this.unlocked=true;this.enqueue(this.text(name,gift,amount))}
 pump(){if(!this.enabled||this.speaking||!this.queue.length)return;const text=this.queue.shift(),u=new SpeechSynthesisUtterance(text),token=this.generation;const voice=this.preferred();if(voice)u.voice=voice;u.lang=voice?.lang||'zh-CN';u.rate=this.rate;u.pitch=1.16;u.volume=this.volume;this.speaking=true;this.onStatus(text);u.onend=()=>{if(token!==this.generation)return;this.speaking=false;this.pump()};u.onerror=e=>{if(token!==this.generation)return;this.speaking=false;this.onStatus('语音播放失败：'+e.error+'，请点击试听或更换语音');this.queue=[]};speechSynthesis.speak(u)}
 stop(){this.generation++;this.queue=[];this.speaking=false;globalThis.speechSynthesis?.cancel()}
}
