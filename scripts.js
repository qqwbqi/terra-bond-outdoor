// TerraBond Outdoor - Prototype Scripts
document.addEventListener('DOMContentLoaded', function() {
  const menuBtn = document.querySelector('.mobile-menu-btn');
  const navLinks = document.querySelector('.nav-links');
  if (menuBtn && navLinks) {
    menuBtn.addEventListener('click', () => { navLinks.classList.toggle('active'); });
  }
  document.querySelectorAll('.faq-q').forEach(q => {
    q.addEventListener('click', () => { const a = q.nextElementSibling; if (a) a.classList.toggle('open'); });
  });
  const stickyCta = document.querySelector('.sticky-cta');
  if (stickyCta && window.innerWidth <= 768) {
    window.addEventListener('scroll', () => {
      stickyCta.style.display = window.scrollY > 300 ? 'flex' : 'none';
    });
  }
});
