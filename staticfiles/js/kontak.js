  const navbar = document.querySelector("nav");
  const navToggler = document.getElementById("navToggler");
  const navLink = document.querySelectorAll(".nav-link");

  if (window.innerWidth < 991) {
    navbar.classList.add("nav-scrolled");
    navbar.classList.remove("nav-scrolled-text-shadow");
    navToggler.classList.replace("navbar-dark", "navbar-light");
    navLink.forEach((e) => e.classList.remove("bawah"));
  }

  document.addEventListener("scroll", function () {
    if (this.body.scrollTop > 1 || this.documentElement.scrollTop > 1) {
      navbar.classList.add("nav-scrolled");
      navbar.classList.remove("nav-scrolled-text-shadow");
      navToggler.classList.replace("navbar-dark", "navbar-light");
      navLink.forEach((e) => e.classList.remove("bawah"));
    } else {
      if (window.innerWidth > 992) {
        navbar.classList.add("nav-scrolled-text-shadow");
        navbar.classList.remove("nav-scrolled");
        navToggler.classList.replace("navbar-light", "navbar-dark");
        navLink.forEach((e) => e.classList.add("bawah"));
      }
    }
  });


  // Scroll Up
  $(document).ready(function () {
    $(window).scroll(function () {
      if ($(this).scrollTop() > 40) {
        $(".go-top-btn").fadeIn();
      } else {
        $(".go-top-btn").fadeOut();
      }
    });
    $(".go-top-btn").click(function () {
      $("html, body").animate({ scrollTop: 0 }, 800);
    });
  });
