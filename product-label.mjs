// Keep lettering legible in dim scenes; the material displaying this texture is unlit.
export function paintProductLabel(ctx, job, score, dark = false) {
  const {width, height} = ctx.canvas;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = dark ? '#202729' : '#f5efe3';
  ctx.fillRect(0, 0, width, height);
  ctx.fillStyle = dark ? '#fff4dc' : '#181b1b';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'alphabetic';
  const name = String(job.name || '').slice(0, 40);
  let size = 94;
  while (size > 28) {
    ctx.font = `800 ${size}px "PingFang SC","Microsoft YaHei",sans-serif`;
    if (ctx.measureText(name).width <= width-60) break;
    size -= 2;
  }
  ctx.fillText(name, width/2, 119);
  ctx.globalAlpha = .24;ctx.fillRect(44, 148, width-88, 3);ctx.globalAlpha = 1;
  ctx.font = `900 ${score === null ? 110 : 194}px "PingFang SC","Microsoft YaHei",sans-serif`;
  ctx.fillText(score === null ? (job.language === 'en' ? 'PRINTING' : '打印中') : score+(job.language === 'en' ? ' pts' : '分'), width/2, 345);
}
