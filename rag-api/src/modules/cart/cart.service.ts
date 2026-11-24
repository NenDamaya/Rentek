import { Injectable, NotFoundException, BadRequestException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';

import { CarritoItem } from './entities/carrito-item.entity';
import { CatalogService } from '../catalog/catalog.service';

interface AddToCartDto {
  maquinaNombre: string;
  duration: number;
  durationUnit: string;
  startDate?: string;
  endDate?: string;
  cantidad: number;
}

@Injectable()
export class CartService {
  constructor(
    @InjectRepository(CarritoItem)
    private cartRepository: Repository<CarritoItem>,
    private catalogService: CatalogService,
  ) {}

  async getCart(userId: number) {
    const items = await this.cartRepository.find({
      where: { userId },
      order: { createdAt: 'ASC' },
    });

    const subtotal = items.reduce((sum, item) => sum + Number(item.precioDia) * item.duration, 0);

    return {
      items: items.map((item) => ({
        id: item.id,
        maquinaNombre: item.maquinaNombre,
        maquinaJson: item.maquinaJson,
        duration: item.duration,
        durationUnit: item.durationUnit,
        startDate: item.startDate,
        endDate: item.endDate,
        precioDia: Number(item.precioDia),
        totalEstimado: Number(item.precioDia) * item.duration,
        creado: item.createdAt,
      })),
      totalItems: items.length,
      subtotal: Number(subtotal.toFixed(2)),
    };
  }

  async addToCart(userId: number, dto: AddToCartDto) {
    const maquina = await this.catalogService.getMaquinaByNombre(dto.maquinaNombre);
    if (!maquina) {
      throw new NotFoundException(`Máquina '${dto.maquinaNombre}' no encontrada`);
    }

    const precioStr = maquina.precioRenta || '';
    const precioDia = this.parsePrecioPromedio(precioStr);

    const startDate = dto.startDate || new Date().toISOString().split('T')[0];
    let endDate = dto.endDate;
    if (!endDate) {
      const start = new Date(startDate);
      if (dto.durationUnit === 'dias') {
        start.setDate(start.getDate() + dto.duration);
      } else if (dto.durationUnit === 'semanas') {
        start.setDate(start.getDate() + dto.duration * 7);
      } else if (dto.durationUnit === 'meses') {
        start.setMonth(start.getMonth() + dto.duration);
      }
      endDate = start.toISOString().split('T')[0];
    }

    const maquinaJson = {
      nombre: maquina.nombre,
      nombreComun: maquina.nombreComun,
      categoria: maquina.categoria?.nombre || '',
      precioRenta: maquina.precioRenta,
      imagen: maquina.especificaciones?.imagen || `/images/${maquina.nombre.toLowerCase().replace(/\s+/g, '_')}.jpg`,
    };

    const items = [];
    for (let i = 0; i < dto.cantidad; i++) {
      const item = this.cartRepository.create({
        userId,
        maquinaNombre: maquina.nombre,
        maquinaJson,
        duration: dto.duration,
        durationUnit: dto.durationUnit,
        startDate,
        endDate,
        precioDia,
      });
      items.push(await this.cartRepository.save(item));
    }

    return {
      exito: true,
      itemsAgregados: dto.cantidad,
      maquina: maquina.nombre,
      duration: dto.duration,
      durationUnit: dto.durationUnit,
      startDate,
      endDate,
      precioDia,
      mensaje: `${maquina.nombre} agregada al carrito (${dto.duration} ${dto.durationUnit}, $${precioDia.toLocaleString()}/día).`,
    };
  }

  async removeFromCart(userId: number, itemId: number) {
    const result = await this.cartRepository.delete({ id: itemId, userId });
    if (result.affected === 0) {
      throw new NotFoundException('Item no encontrado en el carrito');
    }
    return { exito: true, eliminados: result.affected, mensaje: 'Item eliminado del carrito' };
  }

  async removeByMaquina(userId: number, maquinaNombre: string) {
    const result = await this.cartRepository.delete({ userId, maquinaNombre });
    return { exito: true, eliminados: result.affected, mensaje: `Se eliminaron ${result.affected} item(s) del carrito` };
  }

  async clearCart(userId: number) {
    const result = await this.cartRepository.delete({ userId });
    return { exito: true, eliminados: result.affected, mensaje: 'Carrito vaciado' };
  }

  private parsePrecioPromedio(precioStr: string): number {
    if (!precioStr) return 0;
    const match = precioStr.match(/\$?([\d,]+)\s*[-–]\s*\$?([\d,]+)/);
    if (match) {
      const min = parseFloat(match[1].replace(/,/g, ''));
      const max = parseFloat(match[2].replace(/,/g, ''));
      return (min + max) / 2;
    }
    const single = precioStr.match(/\$?([\d,]+)/);
    if (single) {
      return parseFloat(single[1].replace(/,/g, ''));
    }
    return 0;
  }
}