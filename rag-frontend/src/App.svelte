<script>
  import { onMount } from 'svelte'
  import Login from './lib/Login.svelte'
  import Navbar from './lib/Navbar.svelte'
  import Catalog from './lib/Catalog.svelte'
  import ProjectsView from './lib/ProjectsView.svelte'
  import QuotesView from './lib/QuotesView.svelte'
  import AdminView from './lib/AdminView.svelte'
  import CartDrawer from './lib/CartDrawer.svelte'
  import ChatDrawer from './lib/ChatDrawer.svelte'
  import LucideIcons from './lib/LucideIcons.svelte'

  let user = null
  let checked = false

  let activeTab = 'catalog'
  let isCartOpen = false
  let isChatOpen = false
  let cart = []

  onMount(() => {
    const stored = localStorage.getItem('rentek_user')
    const token = localStorage.getItem('rentek_token')
    if (stored && token) {
      try {
        user = JSON.parse(stored)
      } catch {}
    }

    try {
      const storedCart = localStorage.getItem('rentek_cart')
      if (storedCart) cart = JSON.parse(storedCart)
    } catch {}

    checked = true
  })

  function saveCart(newCart) {
    cart = newCart
    try {
      localStorage.setItem('rentek_cart', JSON.stringify(cart))
    } catch {}
  }

  async function handleAddToCart(e) {
    const cartItem = e.detail
    saveCart([...cart, cartItem])
    const token = localStorage.getItem('rentek_token')
    if (token && user) {
      try {
        const { addToCart } = await import('./lib/api.js')
        await addToCart({
          maquina_nombre: cartItem.item?.nombre || cartItem.maquina_nombre,
          duration: cartItem.duration || 1,
          duration_unit: cartItem.durationUnit || 'dias',
          start_date: cartItem.startDate || '',
          cantidad: 1,
        }, token)
      } catch {}
    }
    isCartOpen = true
  }

  function handleRemoveFromCart(e) {
    const idx = e.detail
    saveCart(cart.filter((_, i) => i !== idx))
    const token = localStorage.getItem('rentek_token')
    const removedItem = cart[idx]
    if (token && removedItem?.id) {
      import('./lib/api.js').then(m => m.removeFromCart(removedItem.id, token)).catch(() => {})
    }
  }

  function handleClearCart() {
    saveCart([])
  }

  let initialChatQuery = ''

  function handleConsultAI(e) {
    const item = e.detail?.item || e.detail
    if (item && item.nombre) {
      initialChatQuery = `Hola, necesito asesoría sobre la máquina "${item.nombre}" (${item.categoria || 'Maquinaria'}). ¿Podrías darme sus especificaciones técnicas clave y recomendarme si es adecuada para mi obra?`
    } else if (typeof e.detail === 'string') {
      initialChatQuery = e.detail
    } else {
      initialChatQuery = ''
    }
    isChatOpen = true
  }

  function handleLogin(e) {
    user = e.detail
    activeTab = 'catalog'
  }

  function handleLogout() {
    localStorage.removeItem('rentek_token')
    localStorage.removeItem('rentek_user')
    user = null
    activeTab = 'catalog'
  }
</script>

{#if !checked}
  <div class="flex flex-col items-center justify-center h-screen gap-3 bg-bg text-text-faint">
    <span class="animate-pulse text-accent"><img src="/rentek-white.png" alt="Rentek" class="w-[72px] h-[72px] object-contain" /></span>
    <p>Cargando Rentek E-Commerce...</p>
  </div>
{:else if user}
  <div class="min-h-screen bg-bg text-text flex flex-col font-sans">
    <Navbar
      {user}
      cartItemsCount={cart.length}
      {activeTab}
      {isChatOpen}
      on:navigate={(e) => activeTab = e.detail}
      on:toggleCart={() => isCartOpen = !isCartOpen}
      on:toggleChat={() => isChatOpen = !isChatOpen}
      on:logout={handleLogout}
    />

    <main class="flex-1 pb-16 md:pb-0">
      {#if activeTab === 'catalog'}
        <Catalog
          on:addToCart={handleAddToCart}
          on:consultAI={handleConsultAI}
          on:toggleChat={() => isChatOpen = true}
        />
      {:else if activeTab === 'projects'}
        <ProjectsView
          on:consultAI={handleConsultAI}
        />
      {:else if activeTab === 'orders'}
        <QuotesView />
      {:else if activeTab === 'admin'}
        {#if user?.role === 'admin'}
          <AdminView {user} />
        {:else}
          <div class="max-w-3xl mx-auto px-4 py-20 text-center space-y-3">
            <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 mx-auto">
              <LucideIcons icon="lock" class="w-6 h-6" />
            </div>
            <h2 class="text-xl font-extrabold text-text">Acceso denegado</h2>
            <p class="text-sm text-text-faint">Esta sección requiere permisos de administrador.</p>
            <button
              on:click={() => activeTab = 'catalog'}
              class="px-4 py-2 rounded-xl bg-amber-500 text-slate-950 text-xs font-bold hover:bg-amber-400 transition-colors"
            >
              Volver al catálogo
            </button>
          </div>
        {/if}
      {/if}
    </main>

    <CartDrawer
      {cart}
      {user}
      isOpen={isCartOpen}
      on:close={() => isCartOpen = false}
      on:removeFromCart={handleRemoveFromCart}
      on:clearCart={handleClearCart}
      on:orderCreated={() => {
        saveCart([])
        activeTab = 'orders'
      }}
    />

    <ChatDrawer
      isOpen={isChatOpen}
      {user}
      on:close={() => isChatOpen = false}
      on:logout={handleLogout}
    />
  </div>
{:else}
  <Login on:login={handleLogin} />
{/if}
