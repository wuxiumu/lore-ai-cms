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
