  function togglePaymentDetails(paymentMethod) {
    const qrisDetails = document.getElementById('qris-details');
    const cashDetails = document.getElementById('cash-details');

    if (paymentMethod === 'QRIS') {
      qrisDetails.style.display = 'block';
      cashDetails.style.display = 'none';
    } else if (paymentMethod === 'Cash') {
      cashDetails.style.display = 'block';
      qrisDetails.style.display = 'none';
    } else {
      qrisDetails.style.display = 'none';
      cashDetails.style.display = 'none';
    }
  }

