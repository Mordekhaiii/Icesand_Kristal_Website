// Footer Semua Halaman
const footer = document.getElementById("footer");
footer.innerHTML = showFooter();

function showFooter() {
  return `<div class="container-fluid footer">
            <div class="row justify-content-center">
              <div class="col-12 text-center footer-content">
                <div class="footer-title">
                  <h1 class="fw-bold">PT. ICESAND KRISTAL PERKASA</h1>
                  <ul class="list-unstyled text-uppercase">
                    <li>Open from 08:30 AM - 17:30 PM</li>
                    <li class="mb-3">Jl. Waliwis No.1, Tanah Sareal, Kota Bogor, Jawa Barat 16161</li>
                  </ul>
                  <span class="me-3">
                    <!-- Instagram icon using Feather -->
                    <i data-feather="instagram"></i> icesand_kristal 
                  </span>

                  <span>
                    <!-- WhatsApp icon using Feather -->
                    <i data-feather="message-square"></i> 0811-1165-221
                  </span>
                </div>
              </div>
            </div>
            <div class="text-footer text-white text-center">
              <p class="m-0">
                Created by 
                <a href="https://www.instagram.com/icesand_kristal/" target="_blank" class="text-warning">PT. ICESAND KRISTAL PERKASA</a> 
                © 2026 Copyright | All Rights Reserved
              </p>
            </div>
          </div>`;
}
