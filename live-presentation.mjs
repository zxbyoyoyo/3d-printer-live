import * as THREE from './assets/three.module.js';
import {PresentationState, giftMotion} from './presentation-state.mjs';

const font = '"PingFang SC","Microsoft YaHei",sans-serif';
function panel(width, height) {
  const canvas = document.createElement('canvas');
  canvas.width = width;canvas.height = height;
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.generateMipmaps = false;
  texture.minFilter = THREE.LinearFilter;
  const material = new THREE.MeshBasicMaterial({map:texture, transparent:true, depthTest:false, depthWrite:false, toneMapped:false});
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), material);
  mesh.frustumCulled = false;
  return {canvas, ctx:canvas.getContext('2d'), texture, mesh};
}
function rounded(ctx, x, y, width, height, radius) {
  ctx.beginPath();ctx.roundRect(x, y, width, height, radius);
}
function fitText(ctx, text, maxWidth) {
  let label = String(text || '');
  while(label.length && ctx.measureText(label).width > maxWidth) label = label.slice(0,-1);
  return label === String(text || '') ? label : label.slice(0,-1)+'…';
}

export class LivePresentation {
  constructor(language = 'zh') {
    this.language = language;
    this.state = new PresentationState();
    this.scene = new THREE.Scene();
    this.camera = new THREE.OrthographicCamera(0, 1, 1, 0, -10, 10);
    this.gift = panel(1024, 256);
    this.scene.add(this.gift.mesh);
    this.images = new Map();
    this.heartTexture = new THREE.TextureLoader().load('./assets/overlays/heart.png');
    this.heartTexture.colorSpace = THREE.SRGBColorSpace;
    this.particles = Array.from({length:8},()=>{
      const material = new THREE.SpriteMaterial({map:this.heartTexture,transparent:true,depthTest:false,depthWrite:false,toneMapped:false});
      const sprite = new THREE.Sprite(material);sprite.visible = false;this.scene.add(sprite);return sprite;
    });
    for(const [key,src] of [['heart','assets/overlays/heart.png'],['beer','assets/generated/original-icons/beer.png'],['lollipop','assets/generated/original-icons/lollipop.png']]) {
      const image = new Image();image.onload = ()=>{this.images.set(key,image);this.paintGift();};image.src=src;
    }
    this.configure(1280,720);
  }
  configure(width, height) {
    this.width = width;this.height = height;this.portrait = height > width;
    Object.assign(this.camera,{left:0,right:width,top:height,bottom:0});this.camera.updateProjectionMatrix();
    const giftWidth = Math.min(width * (this.portrait ? .86 : .5),900);
    this.gift.mesh.scale.set(giftWidth,giftWidth/4,1);
    this.gift.mesh.position.set(width/2,height*(this.portrait ? .79 : .83),2);
  }
  begin(job) {this.state.begin(job);this.paintGift();}
  complete(score) {this.state.complete(score);}
  cancel() {this.state.cancel();this.update(0,false);}
  paintGift() {
    const ctx=this.gift.ctx, job=this.state.job;
    ctx.clearRect(0,0,1024,256);
    if(!job)return;
    rounded(ctx,8,8,1008,240,42);ctx.fillStyle='rgba(39,19,36,.94)';ctx.fill();ctx.strokeStyle='#ee94c2';ctx.lineWidth=3;ctx.stroke();
    const icon=this.images.get(job.gift||'heart');
    if(icon)ctx.drawImage(icon,34,28,200,200);
    ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillStyle='#ffe4f2';ctx.font=`800 48px ${font}`;
    ctx.fillText(fitText(ctx,this.language==='en'?'Thank you, '+job.name:'感谢 '+job.name,720),252,92);
    ctx.fillStyle='#f6bad8';ctx.font=`600 34px ${font}`;
    const label=job.giftLabel || ({heart:'小心心',beer:'啤酒',lollipop:'棒棒糖'}[job.gift] || '小心心');
    ctx.fillText(fitText(ctx,this.language==='en'?'Gift received · printing your avatar':label+'收到啦，爱你哦！',710),252,165);
    this.gift.texture.needsUpdate=true;
  }
  update(dt, paused) {
    this.state.tick(dt,paused);
    const motion=giftMotion(this.state.giftAge);
    this.gift.mesh.visible=this.state.giftVisible;
    this.gift.mesh.material.opacity=motion.opacity;
    const base=Math.min(this.width*(this.portrait ? .86 : .5),900);
    this.gift.mesh.scale.set(base*motion.scale,base/4*motion.scale,1);
    for(const [i,particle] of this.particles.entries()) {
      particle.visible=this.state.giftVisible&&(!this.state.job.gift||this.state.job.gift==='heart');
      if(!particle.visible)continue;
      const u=(i+.5)/this.particles.length;
      const phase=this.state.giftAge/1.8;
      const size=this.width*(this.portrait ? .05 : .025)*(1+u*.5);
      particle.position.set(this.width*(.12+u*.76)+Math.sin(phase*5+i)*12,this.height*(this.portrait ? .72 : .73)+phase*this.height*.18-(i%3)*16,3);
      particle.scale.set(size,size,1);particle.material.opacity=motion.opacity*(.35+u*.4);
    }
  }
  render(renderer) {
    if(!this.state.giftVisible)return;
    const clear=renderer.autoClear;
    renderer.autoClear=false;
    try {renderer.clearDepth();renderer.render(this.scene,this.camera);}
    finally {renderer.autoClear=clear;}
  }
}
