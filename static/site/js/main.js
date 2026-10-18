/* ============================================
   SPICE HAVEN — Main JavaScript
   Handles: Nav toggle, hero margin, scroll shadow
   ============================================ */

document.addEventListener('DOMContentLoaded', function () {

  var nav       = document.getElementById('myTopnav');
  var hamburger = document.getElementById('navHamburger');
  var hero      = document.getElementById('heroSection');

  // ── Set hero margin = navbar height ───────
  function setHeroMargin() {
    if (nav && hero) {
      hero.style.marginTop = nav.offsetHeight + 'px';
    }
  }
  setHeroMargin();
  window.addEventListener('resize', function () {
    setHeroMargin();
  });

  // ── Mobile hamburger toggle ────────────────
  if (hamburger && nav) {
    hamburger.addEventListener('click', function () {
      nav.classList.toggle('open');
      // Recalculate hero offset after menu expands/collapses
      setTimeout(setHeroMargin, 10);
    });
  }

  // ── Close nav when link clicked (mobile) ──
  if (nav) {
    nav.querySelectorAll('.nav-links a').forEach(function (link) {
      link.addEventListener('click', function () {
        nav.classList.remove('open');
        setTimeout(setHeroMargin, 10);
      });
    });
  }

  // ── Scroll: deepen nav shadow ─────────────
  window.addEventListener('scroll', function () {
    if (nav) {
      nav.style.boxShadow = window.scrollY > 10
        ? '0 2px 14px rgba(0,0,0,0.14)'
        : '0 1px 4px rgba(0,0,0,0.08)';
    }
  });

  // ── Highlight active nav link ──────────────
  var page = window.location.pathname.split('/').pop() || 'index.html';
  if (nav) {
    nav.querySelectorAll('.nav-links a').forEach(function (a) {
      var href = a.getAttribute('href');
      if (href && href !== '#' && page === href) {
        a.classList.add('active');
      }
    });
  }

});
