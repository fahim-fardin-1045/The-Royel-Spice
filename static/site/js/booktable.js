/* ============================================
   PUREMENT — Book a Table JS
   ============================================ */

document.addEventListener('DOMContentLoaded', function () {

  // ── Time Slot Selection ────────────────────
  const slots = document.querySelectorAll('.time-slot');
  slots.forEach(function (slot) {
    slot.addEventListener('click', function () {
      slots.forEach(function (s) { s.classList.remove('selected'); });
      slot.classList.add('selected');
    });
  });

  // ── Book Now Popup ─────────────────────────
  const openBtn = document.querySelector('.book-btn');
  const popup = document.getElementById('myForm');
  const closeBtn = document.querySelector('.btn.cancel');

  if (openBtn && popup) {
    openBtn.addEventListener('click', function () {
      popup.classList.add('active');
    });
  }

  if (closeBtn && popup) {
    closeBtn.addEventListener('click', function () {
      popup.classList.remove('active');
    });
  }

  // Close popup on overlay click
  if (popup) {
    popup.addEventListener('click', function (e) {
      if (e.target === popup) {
        popup.classList.remove('active');
      }
    });
  }

});
