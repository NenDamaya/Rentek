import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';

import { Cotizacion } from './entities/cotizacion.entity';
import { CatalogService } from '../catalog/catalog.service';

interface CotizacionItem {
  nombre: string;
  cantidad: number;
}

interface CalcularCotizacionDto {
  items: CotizacionItem[];
  dias: number;
  incluyeFlete?: boolean;
  incluyeOperador?: boolean;
}

@Injectable()
export class QuotesService {
  constructor(
    @InjectRepository(Cotizacion)
    private cotizacionesRepository: Repository<Cotizacion>,
    private catalogService: CatalogService,
  ) {}

  async calcularCotizacion(dto: CalcularCotizacionDto) {
    const { items, dias, incluyeFlete = true, incluyeOperador = false } = dto;

    if (!items || items.length === 0) {
      throw new Error('Debe proporcionar al menos una máquina');
    }
    if (dias <= 0 || dias > 365) {
      throw new Error('El periodo de renta debe ser entre 1 y 365 días');
    }

    const detalle = [];
    let subtotalTotal = 0;
    let totalMaquinasCnt = 0;

    for (const item of items) {
      const maquina = await this.catalogService.getMaquinaByNombre(item.nombre);
      if (!maquina) {
        detalle.push({ nombre: item.nombre, error: 'No encontrada' });
        continue;
      }

      const precioStr = maquina.precioRenta || '';
      const costo = this.calcularCosto(precioStr, dias, item.cantidad);
      detalle.push({
        nombre: maquina.nombre,
        cantidad: item.cantidad,
        ...costo,
      });
      subtotalTotal += costo.subtotal || 0;
      totalMaquinasCnt += item.cantidad;
    }

    const tasaDescuento = this.getDescuentoPorDias(dias);
    const descuentoTotal = Number((subtotalTotal * tasaDescuento).toFixed(2));
    const subtotalRentaFinal = Number((subtotalTotal - descuentoTotal).toFixed(2));

    const costoFlete = incluyeFlete ? 600 : 0;
    const costoOperador = incluyeOperador ? 400 * dias * totalMaquinasCnt : 0;
    const granTotal = Number((subtotalRentaFinal + costoFlete + costoOperador).toFixed(2));

    return {
      detalle,
      dias,
      subtotalRenta: Number(subtotalTotal.toFixed(2)),
      descuento: descuentoTotal,
      subtotalRentaConDescuento: subtotalRentaFinal,
      desgloseCostos: {
        rentaMaquinaria: `$${subtotalRentaFinal.toLocaleString()} MXN`,
        fleteEntregaRecoleccion: incluyeFlete ? `$${costoFlete.toLocaleString()} MXN` : '$0.00 MXN (No requerido)',
        operadorCapacitado: incluyeOperador ? `$${costoOperador.toLocaleString()} MXN (${dias} días)` : '$0.00 MXN (No requerido)',
        totalFinal: `$${granTotal.toLocaleString()} MXN`,
      },
      total: granTotal,
      moneda: 'MXN',
    };
  }

  async generarCotizacion(
    cliente: string,
    contacto: string,
    items: CotizacionItem[],
    dias: number,
    userId?: number,
  ) {
    const resultadoCosto = await this.calcularCotizacion({ items, dias });

    const folio = this.generarFolio('COT');
    const validaHasta = new Date();
    validaHasta.setDate(validaHasta.getDate() + 30);

    const maquinasCot = items.map((item) => {
      const machine = items.find((i) => i.nombre === item.nombre);
      return {
        nombre: item.nombre,
        cantidad: item.cantidad,
        precioUnitario: 0,
        subtotal: 0,
      };
    });

    const cotizacion = this.cotizacionesRepository.create({
      folio,
      cliente,
      contacto,
      maquinas: maquinasCot,
      dias,
      subtotal: resultadoCosto.subtotalRenta,
      descuento: resultadoCosto.descuento,
      total: resultadoCosto.total,
      validaHasta: validaHasta.toISOString().split('T')[0],
      userId,
    });

    const saved = await this.cotizacionesRepository.save(cotizacion);

    const { dias: _, ...costoSinDias } = resultadoCosto;
    return {
      exito: true,
      folio: saved.folio,
      cliente: saved.cliente,
      contacto: saved.contacto,
      maquinas: saved.maquinas,
      dias: saved.dias,
      ...costoSinDias,
      validaHasta: saved.validaHasta,
      mensaje: `Cotización ${saved.folio} generada. Válida hasta ${saved.validaHasta}.`,
    };
  }

  async getMisCotizaciones(userId: number) {
    const cotizaciones = await this.cotizacionesRepository.find({
      where: { userId },
      order: { createdAt: 'DESC' },
    });

    return {
      cotizaciones: cotizaciones.map((c) => ({
        folio: c.folio,
        cliente: c.cliente,
        contacto: c.contacto,
        maquinas: c.maquinas,
        dias: c.dias,
        subtotal: Number(c.subtotal),
        descuento: Number(c.descuento),
        total: Number(c.total),
        validaHasta: c.validaHasta,
        creada: c.createdAt,
      })),
      total: cotizaciones.length,
    };
  }

  async getCotizacionByFolio(folio: string) {
    const cotizacion = await this.cotizacionesRepository.findOne({ where: { folio } });
    if (!cotizacion) {
      throw new NotFoundException(`Cotización ${folio} no encontrada`);
    }
    return cotizacion;
  }

  private calcularCosto(precioStr: string, dias: number, cantidad: number) {
    const precioDia = this.parsePrecioPromedio(precioStr);
    const subtotal = precioDia * dias * cantidad;
    return { subtotal: Number(subtotal.toFixed(2)), precioDia };
  }

  private getDescuentoPorDias(dias: number): number {
    if (dias >= 30) return 0.2;
    if (dias >= 14) return 0.15;
    if (dias >= 7) return 0.1;
    if (dias >= 3) return 0.05;
    return 0;
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

  private generarFolio(tipo: string): string {
    const now = new Date();
    const num = Math.random().toString(36).substring(2, 8).toUpperCase();
    return `${tipo}-${now.getFullYear()}-${num}`;
  }
}