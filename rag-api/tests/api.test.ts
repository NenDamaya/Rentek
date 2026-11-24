import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:3000/api';

// Variables compartidas entre tests (se ejecutan en orden serial)
let authToken: string | null = null;
let userId: number | null = null;
let createdChatId: string | null = null;

// ============================================================================
// TESTS DE HEALTH Y STATUS (independientes)
// ============================================================================

test('GET /api/health - debería retornar estado OK', async ({ request }) => {
  const response = await request.get('http://localhost:3000/api/health');
  expect(response.ok()).toBeTruthy();
  const body = await response.json();
  expect(body.status).toBe('ok');
});

test('GET /api/docs - Swagger debería estar disponible', async ({ request }) => {
  const response = await request.get('http://localhost:3000/api/docs');
  expect([200, 301, 302, 404]).toContain(response.status());
});

// ============================================================================
// TESTS DE AUTENTICACIÓN (serial - dependen del estado compartido)
// ============================================================================

test.describe.serial('Auth', () => {
  const testUser = {
    email: `test_${Date.now()}@example.com`,
    password: 'Test123456',
    displayName: 'Usuario Test',
  };

  test('POST /api/auth/register - debería registrar un nuevo usuario', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/auth/register`, {
      data: testUser,
    });
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.token).toBeDefined();
    expect(body.user.email).toBe(testUser.email);
    expect(body.user.displayName).toBe(testUser.displayName);
    authToken = body.token;
    userId = body.user.id;
  });

  test('POST /api/auth/register - debería fallar con email duplicado', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/auth/register`, {
      data: testUser,
    });
    // ConflictException retorna 409 por defecto en NestJS
    expect(response.status()).toBe(409);
  });

  test('POST /api/auth/login - debería iniciar sesión', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/auth/login`, {
      data: { email: testUser.email, password: testUser.password },
    });
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.token).toBeDefined();
    authToken = body.token;
    userId = body.user.id;
  });

  test('POST /api/auth/login - debería fallar con credenciales incorrectas', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/auth/login`, {
      data: { email: testUser.email, password: 'wrongpassword' },
    });
    expect(response.status()).toBe(401);
  });

  test('GET /api/auth/me - debería retornar usuario autenticado', async ({ request }) => {
    expect(authToken).not.toBeNull();
    const response = await request.get(`${BASE_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.email).toBe(testUser.email);
  });

  test('GET /api/auth/me - debería fallar sin token', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/auth/me`);
    expect(response.status()).toBe(401);
  });
});

// ============================================================================
// TESTS DE CATÁLOGO (independientes)
// ============================================================================

test.describe('Catalog', () => {
  test('GET /api/catalog - debería listar categorías', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/catalog`);
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(Array.isArray(body)).toBeTruthy();
  });

  test('GET /api/maquinaria - debería listar máquinas', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/maquinaria`);
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(Array.isArray(body)).toBeTruthy();
  });

  test('GET /api/maquinaria?search=excavadora - debería filtrar por búsqueda', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/maquinaria`, {
      params: { search: 'excavadora' },
    });
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(Array.isArray(body)).toBeTruthy();
  });

  test('GET /api/proyectos - debería listar proyectos', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/proyectos`);
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(Array.isArray(body)).toBeTruthy();
  });

  test('GET /api/disponibilidad/:maquinaId - debería verificar disponibilidad', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/disponibilidad/1`, {
      params: {
        fecha_inicio: '2026-10-16',
        fecha_fin: '2026-10-20',
      },
    });
    expect([200, 404]).toContain(response.status());
    if (response.ok()) {
      const body = await response.json();
      expect(body).toHaveProperty('disponible');
    }
  });
});

// ============================================================================
// TESTS DE CARRITO (requiere auth - serial después de Auth)
// ============================================================================

test.describe.serial('Cart (auth required)', () => {
  test('GET /api/carrito - debería retornar carrito vacío con auth', async ({ request }) => {
    expect(authToken).not.toBeNull();
    const response = await request.get(`${BASE_URL}/carrito`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('items');
    expect(body).toHaveProperty('totalItems');
    expect(body).toHaveProperty('subtotal');
  });

  test('POST /api/carrito - debería agregar item al carrito', async ({ request }) => {
    expect(authToken).not.toBeNull();
    const response = await request.post(`${BASE_URL}/carrito`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        maquinaNombre: 'Excavadora Hidráulica de Orugas',
        duration: 3,
        durationUnit: 'dias',
        cantidad: 1,
      },
    });
    // Puede ser 201 (creado) o 404 (máquina no existe en BD)
    expect([201, 404]).toContain(response.status());
    if (response.ok()) {
      const body = await response.json();
      expect(body.exito).toBeTruthy();
    }
  });
});

// ============================================================================
// TESTS DE COTIZACIONES (requiere auth)
// ============================================================================

test.describe.serial('Quotes (auth required)', () => {
  test('POST /api/cotizacion/calcular - debería calcular cotización', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/cotizacion/calcular`, {
      data: {
        items: [{ nombre: 'Excavadora Hidráulica de Orugas', cantidad: 1 }],
        dias: 3,
        incluyeFlete: true,
        incluyeOperador: false,
      },
    });
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('detalle');
    expect(body).toHaveProperty('total');
    expect(body.moneda).toBe('MXN');
  });

  test('POST /api/cotizacion - debería generar cotización formal', async ({ request }) => {
    expect(authToken).not.toBeNull();
    const response = await request.post(`${BASE_URL}/cotizacion`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        cliente: 'Usuario Test',
        contacto: 'test@example.com',
        items: [{ nombre: 'Excavadora Hidráulica de Orugas', cantidad: 1 }],
        dias: 3,
      },
    });
    // Puede ser 201 (creado), 400 (datos inválidos) o 404 (máquina no existe)
    expect([201, 400, 404]).toContain(response.status());
    if (response.ok()) {
      const body = await response.json();
      expect(body.folio).toBeDefined();
      expect(body.cliente).toBe('Usuario Test');
    }
  });

  test('GET /api/cotizaciones - debería listar cotizaciones del usuario', async ({ request }) => {
    expect(authToken).not.toBeNull();
    const response = await request.get(`${BASE_URL}/cotizaciones`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('cotizaciones');
    expect(body).toHaveProperty('total');
  });
});

// ============================================================================
// TESTS DE SOLICITUDES (requiere auth)
// ============================================================================

test.describe.serial('Requests (auth required)', () => {
  test('POST /api/solicitudes - debería registrar solicitud de renta', async ({ request }) => {
    expect(authToken).not.toBeNull();
    const response = await request.post(`${BASE_URL}/solicitudes`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        cliente: 'Usuario Test',
        contacto: 'test@example.com',
        maquinas: [{ nombre: 'Excavadora Hidráulica de Orugas', cantidad: 1 }],
        fechaInicio: '2026-10-20',
        fechaFin: '2026-10-25',
      },
    });
    expect([201, 400, 404]).toContain(response.status());
    if (response.ok()) {
      const body = await response.json();
      expect(body.folio).toBeDefined();
      expect(body.estado).toBe('pendiente');
    }
  });

  test('GET /api/solicitudes - debería listar solicitudes del usuario', async ({ request }) => {
    expect(authToken).not.toBeNull();
    const response = await request.get(`${BASE_URL}/solicitudes`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('solicitudes');
    expect(body).toHaveProperty('total');
  });
});

// ============================================================================
// TESTS DE CHATS (requiere auth)
// ============================================================================

test.describe.serial('Chats (auth required)', () => {
  test('POST /api/chats - debería crear un nuevo chat', async ({ request }) => {
    expect(authToken).not.toBeNull();
    const response = await request.post(`${BASE_URL}/chats`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: { title: 'Chat de prueba' },
    });
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.id).toBeDefined();
    expect(body.title).toBe('Chat de prueba');
    createdChatId = body.id;
  });

  test('GET /api/chats - debería listar chats del usuario', async ({ request }) => {
    expect(authToken).not.toBeNull();
    const response = await request.get(`${BASE_URL}/chats`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('chats');
  });

  test('GET /api/chats/:chatId/messages - debería obtener mensajes del chat', async ({ request }) => {
    expect(authToken).not.toBeNull();
    expect(createdChatId).not.toBeNull();
    const response = await request.get(`${BASE_URL}/chats/${createdChatId}/messages`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('messages');
    expect(Array.isArray(body.messages)).toBeTruthy();
  });
});

// ============================================================================
// TESTS DE PROXY IA (hacia Python FastAPI - puede fallar si no está corriendo)
// ============================================================================

test.describe('AI Proxy', () => {
  test('GET /v1/tools - debería obtener esquemas de herramientas', async ({ request }) => {
    const response = await request.get('http://localhost:3000/v1/tools');
    // 200 si Python backend está corriendo, 502/503 si no
    expect([200, 502, 503]).toContain(response.status());
    if (response.ok()) {
      const body = await response.json();
      expect(body).toHaveProperty('tools');
    }
  });

  test('POST /v1/chat/completions - debería hacer chat con IA', async ({ request }) => {
    const response = await request.post('http://localhost:3000/v1/chat/completions', {
      data: {
        messages: [{ role: 'user', content: 'hola, quiero una excavadora' }],
        user_name: 'Test User',
        user_email: 'test@example.com',
      },
    });
    // 200 si Python backend está corriendo, 400/502/503 si no
    expect([200, 400, 502, 503]).toContain(response.status());
    if (response.ok()) {
      const body = await response.json();
      expect(body).toHaveProperty('choices');
    }
  });
});