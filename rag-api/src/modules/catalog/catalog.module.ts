import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { CatalogService } from './catalog.service';
import { CatalogController } from './catalog.controller';
import { Categoria } from './entities/categoria.entity';
import { Maquina } from './entities/maquina.entity';
import { Proyecto } from './entities/proyecto.entity';
import { Disponibilidad } from './entities/disponibilidad.entity';
import { PrecioEspecial } from './entities/precio-especial.entity';
import { Sucursal } from './entities/sucursal.entity';
import { InventarioSucursal } from './entities/inventario-sucursal.entity';

@Module({
  imports: [
    TypeOrmModule.forFeature([
      Categoria,
      Maquina,
      Proyecto,
      Disponibilidad,
      PrecioEspecial,
      Sucursal,
      InventarioSucursal,
    ]),
  ],
  controllers: [CatalogController],
  providers: [CatalogService],
  exports: [CatalogService],
})
export class CatalogModule {}