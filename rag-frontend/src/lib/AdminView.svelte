<script>
  import { onMount } from 'svelte'
  import LucideIcons from './LucideIcons.svelte'
  import { getAdminUsers, getObservabilityLogs, blockUser, unblockUser } from './api.js'

  export let user = null

  let activeTab = 'users'
  let users = []
  let logs = []
  let loading = false
  let logsLoading = false
  let error = ''
  let actionMessage = ''
  let busyUserId = null

  $: totalUsers = users.length
  $: adminCount = users.filter(u => u.role === 'admin').length
  $: blockedCount = users.filter(u => u.blocked).length

  function token() {
    return localStorage.getItem('rentek_token')
  }

  async function loadUsers() {
    loading = true
    error = ''
    try {
      const data = await getAdminUsers(token())
      users = data.users || []
    } catch (e) {
      error = e.message || 'No se pudieron cargar los usuarios'
    } finally {
      loading = false
    }
  }

  async function loadLogs() {
    logsLoading = true
    error = ''
    try {
      const data = await getObservabilityLogs(50, token())
      logs = data.logs || []
    } catch (e) {
      error = e.message || 'No se pudieron cargar los registros'
    } finally {
      logsLoading = false
    }
  }

  async function refresh() {
    actionMessage = ''
    if (activeTab === 'users') await loadUsers()
    else await loadLogs()
  }

  function selectTab(tab) {
    activeTab = tab
    error = ''
    actionMessage = ''
    if (tab === 'users' && users.length === 0) loadUsers()
    if (tab === 'logs' && logs.length === 0) loadLogs()
  }

  async function toggleBlock(target) {
    busyUserId = target.id
    error = ''
    actionMessage = ''
    try {
      const result = target.blocked
        ? await unblockUser(target.id, token())
        : await blockUser(target.id, token())
      actionMessage = result.message || 'Usuario actualizado'
      await loadUsers()
    } catch (e) {
      error = e.message || 'No se pudo actualizar el usuario'
    } finally {
      busyUserId = null
    }
  }

  function formatDate(value) {
    if (!value) return '—'
    try {
      return new Date(value).toLocaleString('es-MX', { dateStyle: 'short', timeStyle: 'short' })
    } catch {
      return value
    }
  }

  function roleLabel(role) {
    if (role === 'admin') return 'Administrador'
    if (role === 'cliente') return 'Cliente'
    return 'Usuario'
  }

  onMount(loadUsers)
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
  <div class="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
    <div class="space-y-2">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-semibold uppercase">
        <LucideIcons icon="lock" class="w-3.5 h-3.5" />
        Área restringida
      </div>
      <h2 class="text-2xl font-extrabold text-text tracking-tight">Administración</h2>
      <p class="text-xs text-text-faint max-w-2xl">
        Sección disponible únicamente para cuentas con rol <strong class="text-amber-400">admin</strong>.
        Las consultas se validan de nuevo en el servidor.
      </p>
    </div>
    <button
      on:click={refresh}
      class="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-surface border border-border text-xs font-bold text-text-muted hover:text-amber-400 hover:bg-surface-hover transition-colors"
    >
      <LucideIcons icon="refresh" class="w-4 h-4" />
      Actualizar
    </button>
  </div>

  <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
    <div class="p-4 rounded-2xl bg-surface border border-border">
      <p class="text-[10px] uppercase tracking-wider font-bold text-text-faint">Usuarios registrados</p>
      <p class="text-2xl font-black text-text mt-1">{totalUsers}</p>
    </div>
    <div class="p-4 rounded-2xl bg-surface border border-border">
      <p class="text-[10px] uppercase tracking-wider font-bold text-text-faint">Administradores</p>
      <p class="text-2xl font-black text-amber-400 mt-1">{adminCount}</p>
    </div>
    <div class="p-4 rounded-2xl bg-surface border border-border">
      <p class="text-[10px] uppercase tracking-wider font-bold text-text-faint">Cuentas bloqueadas</p>
      <p class="text-2xl font-black text-rose-400 mt-1">{blockedCount}</p>
    </div>
  </div>

  <div class="flex gap-2 border-b border-border pb-2">
    <button
      on:click={() => selectTab('users')}
      class="px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-all {activeTab === 'users' ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30' : 'text-text-muted hover:text-text hover:bg-surface-hover'}"
    >
      <LucideIcons icon="users" class="w-4 h-4" />
      Usuarios
    </button>
    <button
      on:click={() => selectTab('logs')}
      class="px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-all {activeTab === 'logs' ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30' : 'text-text-muted hover:text-text hover:bg-surface-hover'}"
    >
      <LucideIcons icon="activity" class="w-4 h-4" />
      Observabilidad
    </button>
  </div>

  {#if error}
    <div class="px-4 py-3 rounded-xl text-sm bg-red-light border border-red-border text-red flex items-center gap-2">
      <LucideIcons icon="alert-triangle" class="w-4 h-4 shrink-0" />
      {error}
    </div>
  {/if}

  {#if actionMessage}
    <div class="px-4 py-3 rounded-xl text-sm bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center gap-2">
      <LucideIcons icon="check-circle" class="w-4 h-4 shrink-0" />
      {actionMessage}
    </div>
  {/if}

  {#if activeTab === 'users'}
    <div class="rounded-2xl bg-surface border border-border overflow-hidden">
      {#if loading}
        <p class="p-8 text-center text-sm text-text-faint">Cargando usuarios...</p>
      {:else if users.length === 0}
        <p class="p-8 text-center text-sm text-text-faint">No hay usuarios registrados.</p>
      {:else}
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-surface-hover text-text-faint uppercase tracking-wider text-[10px]">
              <tr>
                <th class="px-4 py-3 font-bold">Usuario</th>
                <th class="px-4 py-3 font-bold">Rol</th>
                <th class="px-4 py-3 font-bold">Estado</th>
                <th class="px-4 py-3 font-bold">Registro</th>
                <th class="px-4 py-3 font-bold text-right">Acción</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border">
              {#each users as row}
                <tr class="hover:bg-surface-hover/50">
                  <td class="px-4 py-3">
                    <p class="font-bold text-text">{row.display_name || row.username}</p>
                    <p class="text-[11px] text-text-faint">{row.email}</p>
                  </td>
                  <td class="px-4 py-3">
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold border {row.role === 'admin' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' : 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30'}">
                      {roleLabel(row.role)}
                    </span>
                  </td>
                  <td class="px-4 py-3">
                    {#if row.blocked}
                      <span class="text-rose-400 font-bold">Bloqueado</span>
                    {:else}
                      <span class="text-emerald-400 font-bold">Activo</span>
                    {/if}
                  </td>
                  <td class="px-4 py-3 text-text-muted">{formatDate(row.created_at)}</td>
                  <td class="px-4 py-3 text-right">
                    {#if row.id === user?.id || row.role === 'admin'}
                      <span class="text-[10px] text-text-faint">Sin acciones</span>
                    {:else}
                      <button
                        on:click={() => toggleBlock(row)}
                        disabled={busyUserId === row.id}
                        class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-bold border transition-colors disabled:opacity-50 {row.blocked ? 'text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/10' : 'text-rose-400 border-rose-500/30 hover:bg-rose-500/10'}"
                      >
                        <LucideIcons icon={row.blocked ? 'check-circle' : 'ban'} class="w-3.5 h-3.5" />
                        {row.blocked ? 'Desbloquear' : 'Bloquear'}
                      </button>
                    {/if}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </div>
  {:else}
    <div class="rounded-2xl bg-surface border border-border overflow-hidden">
      {#if logsLoading}
        <p class="p-8 text-center text-sm text-text-faint">Cargando registros...</p>
      {:else if logs.length === 0}
        <p class="p-8 text-center text-sm text-text-faint">No hay registros de observabilidad.</p>
      {:else}
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-surface-hover text-text-faint uppercase tracking-wider text-[10px]">
              <tr>
                <th class="px-4 py-3 font-bold">Fecha</th>
                <th class="px-4 py-3 font-bold">Consulta</th>
                <th class="px-4 py-3 font-bold">Latencia</th>
                <th class="px-4 py-3 font-bold">Estado</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border">
              {#each logs as log}
                <tr class="hover:bg-surface-hover/50">
                  <td class="px-4 py-3 text-text-muted whitespace-nowrap">{formatDate(log.timestamp)}</td>
                  <td class="px-4 py-3 text-text max-w-md">
                    <p class="truncate" title={log.user_prompt}>{log.user_prompt || '—'}</p>
                    <p class="text-[11px] text-text-faint truncate" title={log.system_response}>{log.system_response || ''}</p>
                  </td>
                  <td class="px-4 py-3 text-text-muted whitespace-nowrap">
                    {Math.round(log.total_latency_ms || 0)} ms
                  </td>
                  <td class="px-4 py-3">
                    {#if log.was_blocked}
                      <span class="text-rose-400 font-bold">Bloqueado</span>
                    {:else}
                      <span class="text-emerald-400 font-bold">Normal</span>
                    {/if}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </div>
  {/if}
</div>
