import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, In } from 'typeorm';

import { Categoria } from './entities/categoria.entity';
import { Maquina } from './entities/maquina.entity';
import { Proyecto } from './entities/proyecto.entity';
import { Disponibilidad } from './entities/disponibilidad.entity';
import { Sucursal } from './entities/sucursal.entity';
import { InventarioSucursal } from './entities/inventario-sucursal.entity';

@Injectable()
export class CatalogService {
  constructor(
    @InjectRepository(Categoria)
    private categoriasRepository: Repository<Categoria>,
    @InjectRepository(Maquina)
    private maquinasRepository: Repository<Maquina>,
    @InjectRepository(Proyecto)
    private proyectosRepository: Repository<Proyecto>,
    @InjectRepository(Disponibilidad)
    private disponibilidadRepository: Repository<Disponibilidad>,
    @InjectRepository(Sucursal)
    private sucursalesRepository: Repository<Sucursal>,
    @InjectRepository(InventarioSucursal)
    private inventarioRepository: Repository<InventarioSucursal>,
  ) {}

  // Categorías
  async getCategorias(): Promise<Categoria[]> {
    const categorias = await this.categoriasRepository.find({
      relations: { maquinas: true },
      order: { nombre: 'ASC' },
    });
    return categorias.map((cat) => ({
      ...cat,
      totalMaquinas: cat.maquinas?.length || 0,
    }));
  }

  async getCategoriaByNombre(nombre: string): Promise<Categoria | null> {
    return this.categoriasRepository.findOne({
      where: { nombre },
      relations: { maquinas: true },
    });
  }

  // Máquinas
  async getMaquinas(filters?: { categoriaId?: number; estado?: string; search?: string }): Promise<Maquina[]> {
    const query = this.maquinasRepository.createQueryBuilder('maquina')
      .leftJoinAndSelect('maquina.categoria', 'categoria');

    if (filters?.categoriaId) {
      query.andWhere('maquina.categoriaId = :categoriaId', { categoriaId: filters.categoriaId });
    }
    if (filters?.estado) {
      query.andWhere('maquina.estado = :estado', { estado: filters.estado });
    }
    if (filters?.search) {
      query.andWhere(
        '(maquina.nombre ILIKE :search OR maquina.nombreComun ILIKE :search OR maquina.marcas ILIKE :search)',
        { search: `%${filters.search}%` },
      );
    }

    return query.orderBy('maquina.nombre', 'ASC').getMany();
  }

  async getMaquinaById(id: number): Promise<Maquina> {
    const maquina = await this.maquinasRepository.findOne({
      where: { id },
      relations: { categoria: true },
    });
    if (!maquina) {
      throw new NotFoundException(`Máquina con ID ${id} no encontrada`);
    }
    return maquina;
  }

  async getMaquinaByNombre(nombre: string): Promise<Maquina | null> {
    return this.maquinasRepository.findOne({
      where: { nombre },
      relations: { categoria: true },
    });
  }

  async buscarMaquinaria(termino: string): Promise<Maquina[]> {
    return this.maquinasRepository
      .createQueryBuilder('maquina')
      .leftJoinAndSelect('maquina.categoria', 'categoria')
      .where(
        '(maquina.nombre ILIKE :term OR maquina.nombreComun ILIKE :term OR maquina.marcas ILIKE :term OR maquina.modelosTipicos ILIKE :term)',
        { term: `%${termino}%` },
      )
      .orderBy('maquina.nombre', 'ASC')
      .getMany();
  }

  // Proyectos
  async getProyectos(): Promise<Proyecto[]> {
    return this.proyectosRepository.find({ order: { nombre: 'ASC' } });
  }

  async getProyectoByNombre(nombre: string): Promise<Proyecto | null> {
    return this.proyectosRepository.findOne({ where: { nombre } });
  }

  // Disponibilidad
  async verificarDisponibilidad(maquinaId: number, fechaInicio: string, fechaFin: string) {
    const fechas = this.generateDateRange(fechaInicio, fechaFin);
    const disponibilidad = await this.disponibilidadRepository.find({
      where: {
        maquinaId,
        fecha: In(fechas),
      },
    });

    const fechasOcupadas = disponibilidad
      .filter((d) => !d.disponible)
      .map((d) => ({ fecha: d.fecha, notas: d.notas }));

    const fechasDisponibles = fechas.filter(
      (f) => !disponibilidad.some((d) => d.fecha === f && !d.disponible),
    );

    return {
      maquinaId,
      fechaInicio,
      fechaFin,
      disponible: fechasOcupadas.length === 0,
      totalDiasSolicitados: fechas.length,
      diasDisponibles: fechasDisponibles.length,
      diasOcupados: fechasOcupadas.length,
      fechasOcupadas: fechasOcupadas.slice(0, 10),
    };
  }

  // Sucursales e Inventario
  async getSucursales(): Promise<Sucursal[]> {
    return this.sucursalesRepository.find({ where: { activa: true }, order: { nombre: 'ASC' } });
  }

  async getInventarioPorSucursal(sucursalId: number): Promise<InventarioSucursal[]> {
    return this.inventarioRepository.find({
      where: { sucursalId },
      relations: { maquina: { categoria: true } },
    });
  }

  private generateDateRange(inicio: string, fin: string): string[] {
    const fechas: string[] = [];
    const start = new Date(inicio);
    const end = new Date(fin);
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      fechas.push(d.toISOString().split('T')[0]);
    }
    return fechas;
  }
}