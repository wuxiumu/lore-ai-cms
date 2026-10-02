(async () => {
  const input = document.getElementById('search-q');
  const status = document.getElementById('search-status');
  const results = document.getElementById('search-results');
  const q = (new URLSearchParams(location.search).get('q') || '').trim().slice(0, 100);
  input.value = q;
  if (!q) return;
  try {
    const response = await fetch('/search-index.json');
    if (!response.ok) throw new Error('unavailable');
    const data = await response.json();
    const words = q.toLocaleLowerCase().split(/\s+/);
    const matches = data.filter(a => words.every(w => (a.title + a.description + a.category).toLocaleLowerCase().includes(w)));
    status.textContent = `找到 ${matches.length} 篇文章`;
    for (const a of matches.slice(0, 100)) {
      const card = document.createElement('article'); card.className = 'card';
      const category = document.createElement('p'); category.className = 'eyebrow'; category.textContent = a.category;
      const heading = document.createElement('h2');
      const link = document.createElement('a'); link.href = a.url; link.textContent = a.title; heading.append(link);
      const description = document.createElement('p'); description.textContent = a.description;
      card.append(category, heading, description); results.append(card);
    }
  } catch (_) { status.textContent = '搜索暂时不可用，请从首页分类浏览。'; }
})();
