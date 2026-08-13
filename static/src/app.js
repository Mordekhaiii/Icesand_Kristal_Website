document.addEventListener("alpine:init", () => {
  // Data Produk
  Alpine.data("products", () => ({
    items: [
      { id: 1, name: "Es Kristal Bulat Besar", img: "bulat_besar.png", price: 20000, stock: 100 },
      { id: 2, name: "Es Kristal Bulat Kecil", img: "bulat_kecil.jpg", price: 20000, stock: 100 },
    ],
    rupiah(number) {
      return new Intl.NumberFormat("id-ID", {
        style: "currency",
        currency: "IDR",
        minimumFractionDigits: 0,
      }).format(number);
    },
  }));

  // Store Keranjang Belanja
  Alpine.store("cart", {
    items: [],
    total: 0,
    quantity: 0,

    add(newItem) {
      if (newItem.stock <= 0) {
        alert("Maaf, stok item ini sedang habis!");
        return;
      }

      const cartItem = this.items.find((item) => item.id === newItem.id);

      if (!cartItem) {
        this.items.push({ ...newItem, quantity: 1, total: newItem.price });
        this.quantity++;
        this.total += newItem.price;
      } else {
        if (cartItem.quantity >= newItem.stock) {
          alert("Jumlah pesanan melebihi stok yang tersedia!");
          return;
        }

        this.items = this.items.map((item) => {
          if (item.id !== newItem.id) return item;
          item.quantity++;
          item.total = item.price * item.quantity;
          this.quantity++;
          this.total += item.price;
          return item;
        });
      }
    },

    remove(id) {
      const cartItem = this.items.find((item) => item.id === id);
      if (cartItem.quantity > 1) {
        this.items = this.items.map((item) => {
          if (item.id !== id) return item;
          item.quantity--;
          item.total = item.price * item.quantity;
          this.quantity--;
          this.total -= item.price;
          return item;
        });
      } else {
        this.items = this.items.filter((item) => item.id !== id);
        this.quantity--;
        this.total -= cartItem.price;
      }
    },

    rupiah(number) {
      return new Intl.NumberFormat("id-ID", {
        style: "currency",
        currency: "IDR",
        minimumFractionDigits: 0,
      }).format(number);
    },

    async checkout() {
      if (this.items.length === 0) {
        alert("Keranjang masih kosong!");
        return;
      }

      try {
        const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
        
        if (!csrfToken) {
          alert("CSRF Token tidak ditemukan. Pastikan ada {% csrf_token %} di HTML.");
          return;
        }

        const response = await fetch("/products/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({
            total: this.total,
            items: this.items, // Data ini yang akan disimpan ke DetailTransaksi di Django
          }),
        });

        const data = await response.json();

        if (data.status === "success") {
          // KOSONGKAN KERANJANG SETELAH BERHASIL (PENTING)
          this.items = [];
          this.total = 0;
          this.quantity = 0;
          
          window.location.href = data.redirect_url;
        } else {
          alert("Gagal: " + data.message);
        }
      } catch (error) {
        console.error("Checkout error:", error);
        alert("Terjadi kesalahan koneksi saat checkout.");
      }
    },
  });
});