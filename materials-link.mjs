const header = document.querySelector('.stagehead');
if (header) {
  const link = document.createElement('a');
  link.href = './materials.html';
  link.target = '_blank';
  link.rel = 'noopener';
  link.className = 'secondary';
  link.textContent = document.documentElement.lang?.startsWith('en') ? 'Live overlays ↗' : '直播素材 ↗';
  link.style.cssText = 'padding:8px 12px;font-size:13px;text-decoration:none;white-space:nowrap;color:inherit';
  header.append(link);
}
