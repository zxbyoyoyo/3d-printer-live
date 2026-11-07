import {overlayRows,savedOverlaySettings} from './overlay-rules.mjs';
const status=document.querySelector('#status');
for(const button of document.querySelectorAll('[data-mode]'))button.onclick=async()=>{
 const url=new URL('overlay.html?mode='+button.dataset.mode,location.href).href;
 try{await navigator.clipboard.writeText(url);status.textContent='已复制：'+url}
 catch{status.textContent='请复制此地址：'+url}
};
document.querySelector('#download-current').onclick=async()=>{
 try{
  await document.fonts.ready;
  const rows=overlayRows(savedOverlaySettings());
  if(!rows.length){status.textContent='请先在打印台开启评论或礼物打印。';return}
  const canvas=document.createElement('canvas');canvas.width=1200;canvas.height=1040;const c=canvas.getContext('2d');c.scale(2,2);c.textBaseline='middle';c.lineJoin='round';
  for(const [i,row] of rows.entries()){
   let x=22;const y=76+i*120;
   if(row.icon){const image=new Image();image.src=row.icon;await image.decode();const scale=Math.min(104/image.width,104/image.height);c.drawImage(image,22+(104-image.width*scale)/2,y-image.height*scale/2,image.width*scale,image.height*scale);x=146}
   c.font=`900 ${row.icon?58:49}px "PingFang SC","Microsoft YaHei",sans-serif`;c.strokeStyle='#694a0c';c.lineWidth=3;c.strokeText(row.text,x,y);c.fillStyle='#ffe327';c.fillText(row.text,x,y);
  }
  const link=document.createElement('a');link.download='当前直播打印规则.png';link.href=canvas.toDataURL('image/png');link.click();status.textContent='已下载当前规则，透明背景 PNG。';
 }catch(error){status.textContent='生成失败：'+error.message}
};
