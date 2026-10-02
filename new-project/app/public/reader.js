(() => {
  const dialog = document.querySelector('.reader-lightbox');
  if (!dialog) return;
  const image = dialog.querySelector('.reader-lightbox-image');
  const title = dialog.querySelector('h2');
  let opener;
  document.querySelectorAll('.reader-code-button').forEach(button => {
    button.addEventListener('click', () => {
      opener = button;
      const thumbnail = button.querySelector('img');
      image.src = thumbnail.src;
      image.alt = thumbnail.alt.replace('，点击查看大图', '');
      title.textContent = button.closest('figure').querySelector('figcaption').textContent;
      dialog.showModal();
      document.documentElement.classList.add('reader-modal-open');
    });
  });
  dialog.querySelector('.reader-lightbox-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
  dialog.addEventListener('close', () => {
    document.documentElement.classList.remove('reader-modal-open');
    opener?.focus();
  });
})();

(() => {
  const tools = document.querySelector('.reader-tools');
  if (!tools) return;
  const feedback = tools.querySelector('.reader-tools-feedback');
  const fallback = tools.querySelector('textarea');
  const title = document.querySelector('.reading h1')?.innerText.trim() || document.title;
  const content = () => document.querySelector('.reading .prose')?.innerText.trim() || '';
  const text = () => `${title}\n\n${content()}\n\n来源链接：${location.href}`;
  async function copy(value) {
    fallback.hidden = true;
    if (navigator.clipboard && window.isSecureContext) {
      try { await navigator.clipboard.writeText(value); return true; } catch (_) {}
    }
    fallback.value = value;
    fallback.hidden = false;
    fallback.focus(); fallback.select();
    let success = false;
    try { success = document.execCommand('copy'); } catch (_) {}
    if (success) fallback.hidden = true;
    return success;
  }
  function imagePrompt() {
    const count = Number(tools.dataset.imageCount) || 5;
    const template = tools.querySelector('.reader-prompt-template')?.value || '';
    const instructions = template.replaceAll('{{count}}', String(count)).replaceAll('{{panels}}', String(count * 3));
    return `${instructions}\n\n【文章开始】\n${title}\n\n${content()}\n【文章结束】\n\n文章来源：${location.href}`;
  }
  tools.querySelectorAll('[data-reader-action]').forEach(button => {
    button.addEventListener('click', async () => {
      const action = button.dataset.readerAction;
      if (action === 'share' && navigator.share) {
        try { await navigator.share({title, text:title, url:location.href}); feedback.textContent='分享完成。'; return; }
        catch (error) { if (error.name === 'AbortError') { feedback.textContent='已取消分享。'; return; } }
      }
      const value = action === 'image' ? imagePrompt() : action === 'copy' ? text() : action === 'link' ? location.href : `${title}\n${location.href}`;
      const success = await copy(value);
      feedback.textContent = success ? (action === 'image' ? '正文与转图提示词已复制，粘贴到绘图模型即可使用。' : action === 'copy' ? '文章正文已复制。' : '分享链接已复制。') : '浏览器未允许自动复制，请在下方文本框中手动复制。';
    });
  });
})();
