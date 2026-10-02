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
  function imagePrompt(onlyIndex = null) {
    const count = Number(tools.dataset.imageCount) || 5;
    const template = tools.querySelector('.reader-prompt-template')?.value || '';
    const instructions = template.replaceAll('{{count}}', String(count)).replaceAll('{{panels}}', String(count * 3));
    const digits = number => String(number).padStart(3, '0');
    const storyId = location.pathname.split('/').pop().replace(/\.html$/, '') || 'story';
    const manifest = Array.from({length:count}, (_,offset) => {
      const index=offset+1;
      return `大图${digits(index)}/${digits(count)}；自上而下格号 ${digits(offset*3+1)} → ${digits(offset*3+2)} → ${digits(offset*3+3)}；文件名 ${storyId}-${digits(index)}.png`;
    }).join('\n');
    const ordering = `【强制顺序协议】\n先规划完整故事，再按下列清单输出。每张大图顶部必须有清晰中文“第X张 / 共${count}张”，每格文字栏前写连续格号“第Y格”。全组格号从1连续到${count*3}，阅读方向固定从上到下，不能左右混排。每张提示词必须包含本图编号、文件名、三个格号、承接上一张与引出下一张的情节。图片输出必须与清单一一对应，不遗漏、不重复、不交换次序。文件名是建议保存名称，不声称已自动重命名。\n${manifest}\n批量生成请按001、002顺序逐张执行，不以返回顺序判断故事顺序；在画面内显示图号、格号作为识别依据。`;
    const task = onlyIndex ? `\n【本次仅执行】仅生成第${onlyIndex}张大图（文件名 ${storyId}-${digits(onlyIndex)}.png），必须包含第${(onlyIndex-1)*3+1}、${(onlyIndex-1)*3+2}、${onlyIndex*3}格。参考全文规划其在故事中的位置，保持全组人物与场景一致，不生成其他大图。若已有上一张，请以它作为人物参考。` : '';
    return `${instructions}\n\n${ordering}${task}\n\n【文章开始】\n${title}\n\n${content()}\n【文章结束】\n\n文章来源：${location.href}`;
  }
  tools.querySelectorAll('[data-reader-action]').forEach(button => {
    button.addEventListener('click', async () => {
      const action = button.dataset.readerAction;
      if (action === 'share' && navigator.share) {
        try { await navigator.share({title, text:title, url:location.href}); feedback.textContent='分享完成。'; return; }
        catch (error) { if (error.name === 'AbortError') { feedback.textContent='已取消分享。'; return; } }
      }
      const value = action === 'image-one' ? imagePrompt(Number(tools.querySelector('.reader-image-index').value)) : action === 'image' ? imagePrompt() : action === 'copy' ? text() : action === 'link' ? location.href : `${title}\n${location.href}`;
      const success = await copy(value);
      feedback.textContent = success ? (action.startsWith('image') ? '正文与转图提示词已复制，粘贴到绘图模型即可使用。' : action === 'copy' ? '文章正文已复制。' : '分享链接已复制。') : '浏览器未允许自动复制，请在下方文本框中手动复制。';
    });
  });
})();
