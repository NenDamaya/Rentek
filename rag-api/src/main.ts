import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { ConfigService } from '@nestjs/config';

import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  const configService = app.get(ConfigService);

  // CORS (no global prefix - los controllers manejan sus propios prefijos)
  const frontendUrl = configService.get('app.frontendUrl');
  const allowedOrigins = configService.get('app.cors.allowedOrigins');
  
  const corsOrigins = allowedOrigins.length > 0 
    ? allowedOrigins 
    : [frontendUrl];

  app.enableCors({
    origin: corsOrigins,
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
    allowedHeaders: ['*'],
  });

  // Validation pipe
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      transformOptions: { enableImplicitConversion: true },
    }),
  );

  // Swagger documentation
  const swaggerConfig = new DocumentBuilder()
    .setTitle('Rentek API')
    .setDescription('API para renta de maquinaria pesada - NestJS Backend')
    .setVersion('1.0.0')
    .addBearerAuth()
    .addTag('Auth', 'Autenticación y autorización')
    .addTag('Users', 'Gestión de usuarios')
    .addTag('Catalog', 'Catálogo de maquinaria')
    .addTag('Cart', 'Carrito de compras')
    .addTag('Quotes', 'Cotizaciones')
    .addTag('Requests', 'Solicitudes de renta')
    .addTag('Chats', 'Historial de chats')
    .addTag('AI Proxy', 'Proxy al servicio de IA (Python FastAPI)')
    .build();

  const document = SwaggerModule.createDocument(app, swaggerConfig);
  SwaggerModule.setup('docs', app, document);

  const port = configService.get('app.port');
  await app.listen(port);
  
  console.log(`🚀 NestJS Backend running on http://localhost:${port}`);
  console.log(`📚 Swagger docs: http://localhost:${port}/api/docs`);
}

bootstrap();