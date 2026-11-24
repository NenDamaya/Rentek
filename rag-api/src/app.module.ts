import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';

import { DatabaseModule } from './database/database.module';
import { AuthModule } from './modules/auth/auth.module';
import { UsersModule } from './modules/users/users.module';
import { CatalogModule } from './modules/catalog/catalog.module';
import { CartModule } from './modules/cart/cart.module';
import { QuotesModule } from './modules/quotes/quotes.module';
import { RequestsModule } from './modules/requests/requests.module';
import { ChatsModule } from './modules/chats/chats.module';
import { ProxyModule } from './modules/proxy/proxy.module';
import { HealthModule } from './health/health.module';

import configuration from './config/configuration';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      load: [configuration],
      envFilePath: ['.env.local', '.env'],
    }),
    DatabaseModule,
    AuthModule,
    UsersModule,
    CatalogModule,
    CartModule,
    QuotesModule,
    RequestsModule,
    ChatsModule,
    ProxyModule,
    HealthModule,
  ],
})
export class AppModule {}