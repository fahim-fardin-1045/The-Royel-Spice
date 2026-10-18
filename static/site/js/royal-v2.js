(() => {
  const toggle = document.getElementById('navHamburger');
  const menu = document.getElementById('navLinks');
  if (toggle && menu) {
    toggle.addEventListener('click', () => {
      const expanded = menu.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(expanded));
    });
    menu.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
      menu.classList.remove('is-open'); toggle.setAttribute('aria-expanded', 'false');
    }));
  }
  const search = document.getElementById('menuSearch');
  const filters = document.querySelectorAll('[data-category]');
  const items = document.querySelectorAll('.rs-menu-card');
  const noResults = document.getElementById('noMenuResults');
  let selected = 'all';
  function filterMenu() {
    const query = (search?.value || '').trim().toLocaleLowerCase();
    let count = 0;
    items.forEach(card => {
      const matches = (selected === 'all' || card.dataset.category === selected) &&
                      (card.dataset.search || '').includes(query);
      card.hidden = !matches;
      if (matches) count++;
    });
    if (noResults) noResults.hidden = count > 0;
  }
  if (search) search.addEventListener('input', filterMenu);
  filters.forEach(button => button.addEventListener('click', () => {
    selected = button.dataset.category;
    filters.forEach(b => b.classList.toggle('active', b === button));
    filterMenu();
  }));
})();
