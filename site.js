/* BIVA · interacciones compartidas */

(function() {
  // Nav: dark cuando arriba sobre hero oscuro
  const nav = document.querySelector('.nav');
  if (nav && nav.dataset.heroDark === 'true') {
    const onScroll = () => {
      const scrolled = window.scrollY > window.innerHeight * 0.65;
      nav.classList.toggle('dark', !scrolled);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // Reveal on scroll
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('in');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.15, rootMargin: '0px 0px -8% 0px' });
  document.querySelectorAll('.reveal').forEach(el => io.observe(el));

  // Parallax sutil (elementos con data-parallax)
  const parallaxEls = document.querySelectorAll('[data-parallax]');
  if (parallaxEls.length) {
    const onParallax = () => {
      const sy = window.scrollY;
      parallaxEls.forEach(el => {
        const speed = parseFloat(el.dataset.parallax) || 0.15;
        const rect = el.getBoundingClientRect();
        const offset = (rect.top + sy - window.innerHeight) * speed;
        el.style.transform = `translate3d(0, ${(-offset).toFixed(2)}px, 0)`;
      });
    };
    onParallax();
    window.addEventListener('scroll', onParallax, { passive: true });
  }
})();
