import { Controller, Get, Query, Param, UseGuards, Request } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiQuery, ApiParam, ApiBearerAuth } from '@nestjs/swagger';

import { CatalogService } from './catalog.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

@ApiTags('Catalog')
@Controller('api')
export class CatalogController {
  constructor(private catalogService: CatalogService) {}

  @Get('catalog')
  @ApiOperation({ summary: 'Listar todas las categorías con resumen de máquinas' })
  async getCategorias() {
    return this.catalogService.getCategorias();
  }

  @Get('maquinaria')
  @ApiOperation({ summary: 'Listar máquinas con filtros opcionales' })
  @ApiQuery({ name: 'categoriaId', required: false, type: Number })
  @ApiQuery({ name: 'estado', required: false })
  @ApiQuery({ name: 'search', required: false })
  async getMaquinas(
    @Query('categoriaId') categoriaId?: number,
    @Query('estado') estado?: string,
    @Query('search') search?: string,
  ) {
    return this.catalogService.getMaquinas({ categoriaId, estado, search });
  }

  @Get('maquinaria/:id')
  @ApiOperation({ summary: 'Obtener máquina por ID' })
  @ApiParam({ name: 'id', type: Number })
  async getMaquinaById(@Param('id') id: number) {
    return this.catalogService.getMaquinaById(id);
  }

  @Get('maquinaria/nombre/:nombre')
  @ApiOperation({ summary: 'Obtener máquina por nombre exacto' })
  @ApiParam({ name: 'nombre', type: 'string' })
  async getMaquinaByNombre(@Param('nombre') nombre: string) {
    return this.catalogService.getMaquinaByNombre(nombre);
  }

  @Get('maquinaria/buscar/:termino')
  @ApiOperation({ summary: 'Buscar maquinaria por término' })
  @ApiParam({ name: 'termino', type: 'string' })
  async buscarMaquinaria(@Param('termino') termino: string) {
    return this.catalogService.buscarMaquinaria(termino);
  }

  @Get('proyectos')
  @ApiOperation({ summary: 'Listar todos los proyectos' })
  async getProyectos() {
    return this.catalogService.getProyectos();
  }

  @Get('proyectos/:nombre')
  @ApiOperation({ summary: 'Obtener proyecto por nombre' })
  @ApiParam({ name: 'nombre', type: 'string' })
  async getProyectoByNombre(@Param('nombre') nombre: string) {
    return this.catalogService.getProyectoByNombre(nombre);
  }

  @Get('disponibilidad/:maquinaId')
  @ApiOperation({ summary: 'Verificar disponibilidad de una máquina en rango de fechas' })
  @ApiParam({ name: 'maquinaId', type: Number })
  @ApiQuery({ name: 'fecha_inicio', required: true })
  @ApiQuery({ name: 'fecha_fin', required: true })
  async verificarDisponibilidad(
    @Param('maquinaId') maquinaId: number,
    @Query('fecha_inicio') fechaInicio: string,
    @Query('fecha_fin') fechaFin: string,
  ) {
    return this.catalogService.verificarDisponibilidad(maquinaId, fechaInicio, fechaFin);
  }

  @Get('sucursales')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Listar sucursales activas' })
  async getSucursales() {
    return this.catalogService.getSucursales();
  }

  @Get('sucursales/:id/inventario')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Obtener inventario de una sucursal' })
  @ApiParam({ name: 'id', type: Number })
  async getInventarioPorSucursal(@Param('id') id: number) {
    return this.catalogService.getInventarioPorSucursal(id);
  }
}