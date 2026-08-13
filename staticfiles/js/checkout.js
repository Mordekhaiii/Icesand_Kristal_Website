document.addEventListener("alpine:init", () => {
  Alpine.store("cart", {
    items: [],
    total: 0,
    add(newItem) {
      const cartItem = this.items.find(item => item.id === newItem.id);
      if (!cartItem) {
        this.items.push({ ...newItem, quantity: 1 });
        this.total += newItem.price;
      } else {
        cartItem.quantity += 1;
        this.total += newItem.price;
      }
    },
    clear() {
      this.items = [];
      this.total = 0;
    },
  });
});


document.addEventListener("DOMContentLoaded", () => {
  const checkoutForm = document.getElementById("checkoutForm");

  if (checkoutForm) {
    checkoutForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const items = Alpine.store("cart").items;
      const total = Alpine.store("cart").total;

      try {
        const response = await fetch("/checkout/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify({ items, total }),
        });

        if (response.ok) {
          const data = await response.json();
          alert(`Order placed successfully! Order ID: ${data.order_id}`);
          Alpine.store("cart").clear();
        } else {
          const errorData = await response.json();
          alert(`Error: ${errorData.error}`);
        }
      } catch (error) {
        alert(`An unexpected error occurred: ${error}`);
      }
    });
  } else {
    console.error("checkoutForm element not found.");
  }
});


document.getElementById("checkoutForm").addEventListener("submit", async (e) => {
  e.preventDefault(); // Mencegah reload halaman

  const items = $store.cart.items;
  const total = $store.cart.total;

  try {
    const response = await fetch('/checkout/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') // Fungsi untuk mendapatkan token CSRF
      },
      body: JSON.stringify({ items, total })
    });

    if (response.ok) {
      const data = await response.json();
      alert(`Order placed successfully! Order ID: ${data.order_id}`);
      $store.cart.clear(); // Hapus keranjang setelah checkout berhasil
    } else {
      const errorData = await response.json();
      alert(`Error: ${errorData.error}`);
    }
  } catch (error) {
    alert(`An unexpected error occurred: ${error}`);
  }
});

