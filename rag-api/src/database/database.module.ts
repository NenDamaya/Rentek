import { Module, Global } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ConfigModule, ConfigService } from '@nestjs/config';
import configuration from '../config/configuration';

@Global()
@Module({
  imports: [
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule.forFeature(configuration)],
      inject: [ConfigService],
      useFactory: (configService: ConfigService) => {
        const dbConfig = configService.get('app.database');
        return {
          type: 'postgres',
          host: dbConfig.host,
          port: dbConfig.port,
          username: dbConfig.username,
          password: dbConfig.password,
          database: dbConfig.name,
          entities: [__dirname + '/../modules/**/*.entity{.ts,.js}'],
          synchronize: dbConfig.synchronize,
          logging: dbConfig.logging,
          ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
          extra: {
            max: 20,
            idleTimeoutMillis: 30000,
            connectionTimeoutMillis: 5000,
          },
        };
      },
    }),
  ],
  exports: [TypeOrmModule],
})
export class DatabaseModule {}