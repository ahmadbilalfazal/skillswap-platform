function toggleDarkMode() {
  const root = document.documentElement;
  root.classList.toggle('dark');
  localStorage.theme = root.classList.contains('dark') ? 'dark' : 'light';
}
