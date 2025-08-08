document.addEventListener('DOMContentLoaded', function() {
  // Inicializa componentes
  M.AutoInit();
  
  // Efecto de paralaje bro
  var elems = document.querySelectorAll('.parallax');
  M.Parallax.init(elems);
  
  // Tooltips iconos
  var tooltips = document.querySelectorAll('.tooltipped');
  M.Tooltip.init(tooltips);

      // Menú móvil (hamborgor y side nav)
    var sidenavs = document.querySelectorAll('.sidenav');
    M.Sidenav.init(sidenavs);
  
  // Animación al hacer click en los butonS xd
  document.querySelectorAll('.btn').forEach(btn => {
    btn.addEventListener('click', function() {
      this.classList.add('animate__animated', 'animate__rubberBand');
      setTimeout(() => {
        this.classList.remove('animate__animated', 'animate__rubberBand');
      }, 2000);
    });
  });
});