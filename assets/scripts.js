// TerraBond Outdoor v2 - Shopify Theme Scripts
document.addEventListener('DOMContentLoaded', function() {
  // Mobile menu toggle
  const menuBtn = document.querySelector('.mobile-menu-btn');
  const navLinks = document.querySelector('.nav-links');
  if (menuBtn && navLinks) {
    menuBtn.addEventListener('click', () => {
      navLinks.classList.toggle('active');
      const isOpen = navLinks.classList.contains('active');
      menuBtn.setAttribute('aria-expanded', isOpen);
    });
  }

  // FAQ accordion
  document.querySelectorAll('.faq-q').forEach(q => {
    q.addEventListener('click', () => {
      const a = q.nextElementSibling;
      if (a) a.classList.toggle('open');
      const toggle = q.querySelector('.toggle');
      if (toggle) toggle.textContent = a.classList.contains('open') ? '−' : '+';
    });
  });

  // Cart drawer
  const cartBtn = document.querySelector('.nav-cart-btn');
  const cartDrawer = document.querySelector('.cart-drawer');
  const cartOverlay = document.querySelector('.cart-drawer-overlay');
  const cartClose = document.querySelector('.cart-drawer-close');

  function openCart() {
    if (cartDrawer) cartDrawer.classList.add('open');
    if (cartOverlay) cartOverlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeCart() {
    if (cartDrawer) cartDrawer.classList.remove('open');
    if (cartOverlay) cartOverlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  if (cartBtn) cartBtn.addEventListener('click', openCart);
  if (cartClose) cartClose.addEventListener('click', closeCart);
  if (cartOverlay) cartOverlay.addEventListener('click', closeCart);

  // Add to cart buttons (demo)
  document.querySelectorAll('[data-add-to-cart]').forEach(btn => {
    btn.addEventListener('click', () => {
      const name = btn.dataset.productName || 'Product';
      const price = parseFloat(btn.dataset.productPrice) || 0;
      addCartItem(name, price);
      openCart();
    });
  });

  // Lucide icons init
  if (window.lucide) lucide.createIcons();
});

// Demo cart functionality
let cartItems = [];

function addCartItem(name, price) {
  cartItems.push({ name, price });
  updateCartUI();
}

function removeCartItem(index) {
  cartItems.splice(index, 1);
  updateCartUI();
}

function updateCartUI() {
  const badge = document.querySelector('.cart-badge');
  if (badge) badge.textContent = cartItems.length;
  if (badge) badge.style.display = cartItems.length > 0 ? 'flex' : 'none';

  const body = document.querySelector('.cart-drawer-body');
  if (!body) return;

  if (cartItems.length === 0) {
    body.innerHTML = `
      <div class="cart-empty">
        <div class="icon"><i data-lucide="shopping-cart" style="width:48px;height:48px"></i></div>
        <p>Your cart is empty.</p>
        <a href="/sample-kit.html" class="btn btn-primary mt-6">Get a Sample Kit</a>
      </div>
    `;
  } else {
    let html = '<div class="space-y-3">';
    let total = 0;
    cartItems.forEach((item, i) => {
      total += item.price;
      html += `
        <div class="cart-item-drawer">
          <div class="cart-item-drawer-img">
            <img src="https://images.unsplash.com/photo-1622372738982-bdf473216834?w=200&q=80" alt="${item.name}">
          </div>
          <div class="cart-item-drawer-info">
            <h4>${item.name}</h4>
            <p class="qty">Quantity: 1</p>
            <div class="cart-item-drawer-meta">
              <span class="price">$${item.price.toFixed(2)}</span>
              <button class="remove" onclick="removeCartItem(${i})">Remove</button>
            </div>
          </div>
        </div>
      `;
    });

    if (total < 50) {
      html += `
        <div class="cart-upsell">
          <h4>Recommended for you</h4>
          <div class="cart-upsell-row">
            <div class="info">
              <p class="name">DIY 1 sq ft Test Kit</p>
              <p class="desc">Test application before a big project</p>
            </div>
            <button class="btn btn-dark btn-sm" onclick="addCartItem('DIY 1 sq ft Test Kit', 39.99)">+$39.99</button>
          </div>
        </div>
      `;
    }
    html += '</div>';
    body.innerHTML = html;
  }

  // Update footer
  const footer = document.querySelector('.cart-drawer-footer');
  if (footer) {
    const total = cartItems.reduce((s, i) => s + i.price, 0);
    if (cartItems.length > 0) {
      footer.innerHTML = `
        <div class="cart-shipping-note">Sample kit ships to the U.S. in 7–12 days.<br>Bulk orders are quoted separately.</div>
        <div class="cart-total-row"><span>Subtotal</span><span>$${total.toFixed(2)}</span></div>
        <p class="cart-tax-note">Taxes and shipping calculated at checkout</p>
        <button class="btn btn-primary" style="width:100%">Proceed to Checkout <i data-lucide="arrow-right" style="width:20px;height:20px"></i></button>
      `;
      footer.style.display = 'block';
    } else {
      footer.style.display = 'none';
    }
  }

  if (window.lucide) lucide.createIcons();
}
