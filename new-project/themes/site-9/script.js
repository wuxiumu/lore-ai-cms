(() => {
  const copyStory = document.getElementById('copy-story');
  if (!copyStory) return;
  const title = document.querySelector('.reading h1')?.textContent.trim() || document.title;
  const text = () => title + '\n\n' + (document.querySelector('.reading .prose')?.innerText || '') + '\n\n沪上异闻 · ' + location.href;
  const feedback = message => { document.getElementById('story-feedback').textContent = message; };
  async function copy(value) {
    if (navigator.clipboard && window.isSecureContext) {
      try { await navigator.clipboard.writeText(value); return; } catch (_) {}
    }
    const field = document.createElement('textarea');
    field.value = value; field.setAttribute('aria-label', '待复制的故事');
    document.body.append(field); field.focus(); field.select();
    const ok = document.execCommand('copy'); field.remove();
    if (!ok) throw new Error('copy unavailable');
  }
  copyStory.addEventListener('click', async () => {
    try { await copy(text()); feedback('全文已复制，包含原创虚构标注。'); }
    catch (_) { feedback('浏览器未允许复制，请长按正文或选中文字后复制。'); }
  });
  document.getElementById('copy-link').addEventListener('click', async () => {
    try { await copy(location.href); feedback('故事链接已复制。'); }
    catch (_) { feedback('请复制浏览器地址栏中的链接。'); }
  });
  document.getElementById('share-story').addEventListener('click', async () => {
    if (navigator.share) {
      try { await navigator.share({ title, text: '沪上异闻：' + title, url: location.href }); feedback('分享完成。'); return; }
      catch (error) { if (error.name === 'AbortError') { feedback('已取消分享。'); return; } }
    }
    try { await copy(title + '\n' + location.href); feedback('标题与链接已复制，可以粘贴分享给朋友。'); }
    catch (_) { feedback('请复制地址栏链接分享给朋友。'); }
  });
})();
