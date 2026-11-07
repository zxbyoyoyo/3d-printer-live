import {PRINT_DEFAULTS} from './print-settings.mjs';
const numerals=['','一','两','三','四','五','六','七','八','九','十'];
export function overlayRows(settings={}) {
 const s={...PRINT_DEFAULTS,comment:true,gift:true,...settings};
 const describe=(size,count)=>`打印${size==='large'?'大':'小'}图${numerals[Number(count)]||'一'}张`;
 const rows=[];
 if(s.comment)rows.push({icon:null,text:'评论 666 '+describe(s.commentSize,s.commentCount)});
 if(s.gift)for(const [key,icon] of [['heart','heart'],['beer','beer'],['lollipop','lollipop']])
  rows.push({icon:`assets/generated/original-icons/${icon}.png`,text:describe(s.giftSize,s[key+'Count'])});
 return rows;
}
export function savedOverlaySettings(){
 try{return JSON.parse(localStorage.getItem('printRules')||'{}')||{}}catch{return {}}
}
