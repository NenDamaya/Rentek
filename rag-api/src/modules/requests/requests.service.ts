import { Injectable, NotFoundException, BadRequestException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';

import { SolicitudRenta } from './entities/solicitud-renta.entity';
import { CatalogService } from '../catalog/catalog.service';
import { CartService } from '../cart/cart.service';

interface SolicitudItem {
  nombre: string;
  cantidad: number;
}

interface RegistrarSolicitudDto {
  cliente: string;
  contacto: string;
  maquinas: SolicitudItem[];
  fechaInicio: string;
  fechaFin: string;
}

@Injectable()
export class RequestsService {
  constructor(
    @InjectRepository(SolicitudRenta)
    private solicitudesRepository: Repository<SolicitudRenta>,
    private catalogService: CatalogService,
    private cartService: CartService,
  ) {}

  async registrarSolicitud(dto: RegistrarSolicitudDto, userId?: number) {
    const { cliente, contacto, maquinas, fechaInicio, fechaFin } = dto;

    if (!cliente || !contacto || !maquinas || maquinas.length === 0) {
      throw new BadRequestException('Faltan datos: cliente, contacto y maquinas son requeridos');
    }

    const placeholdersCliente = ['cliente', 'cliente ', 'nombre', 'desconocido', ''];
    const placeholdersContacto = ['9999999999', '999-999-9999', 'teléfono', 'telefono', 'contacto', ''];

    if (placeholdersCliente.includes(cliente.toLowerCase()) || placeholdersContacto.includes(contacto)) {
      throw new BadRequestException('No puedo registrar la solicitud sin tus datos reales');
    }

    const fInicio = new Date(fechaInicio);
    const fFin = new Date(fechaFin);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (fInicio <= today) {
      throw new BadRequestException(`La fecha de inicio (${fechaInicio}) debe ser al menos un día después de hoy`);
    }
    if (fFin < fInicio) {
      throw new BadRequestException('La fecha de fin no puede ser anterior a la fecha de inicio');
    }

    // Validate machines exist
    for (const item of maquinas) {
      const maquina = await this.catalogService.getMaquinaByNombre(item.nombre);
      if (!maquina) {
        throw new NotFoundException(`Máquina '${item.nombre}' no encontrada`);
      }
    }

    const folio = this.generarFolio('SOL');
    const solicitud = this.solicitudesRepository.create({
      folio,
      cliente,
      contacto,
      maquinas,
      fechaInicio,
      fechaFin,
      estado: 'pendiente',
      userId,
    });

    const saved = await this.solicitudesRepository.save(solicitud);

    return {
      exito: true,
      folio: saved.folio,
      cliente: saved.cliente,
      maquinas: saved.maquinas,
      fechaInicio: saved.fechaInicio,
      fechaFin: saved.fechaFin,
      estado: saved.estado,
      mensaje: `Solicitud ${saved.folio} creada exitosamente. Un asesor se pondrá en contacto.`,
    };
  }

  async getMisSolicitudes(userId: number) {
    const solicitudes = await this.solicitudesRepository.find({
      where: { userId },
      order: { createdAt: 'DESC' },
    });

    return {
      solicitudes: solicitudes.map((s) => ({
        folio: s.folio,
        cliente: s.cliente,
        contacto: s.contacto,
        maquinas: s.maquinas,
        fechaInicio: s.fechaInicio,
        fechaFin: s.fechaFin,
        estado: s.estado,
        notas: s.notas,
        creada: s.createdAt,
      })),
      total: solicitudes.length,
    };
  }

  async getSolicitudByFolio(folio: string) {
    const solicitud = await this.solicitudesRepository.findOne({ where: { folio } });
    if (!solicitud) {
      throw new NotFoundException(`Solicitud ${folio} no encontrada`);
    }
    return solicitud;
  }

  async cancelarSolicitud(folio: string, userId: number) {
    const solicitud = await this.solicitudesRepository.findOne({ where: { folio, userId } });
    if (!solicitud) {
      throw new NotFoundException(`Solicitud ${folio} no encontrada`);
    }
    if (solicitud.estado !== 'pendiente') {
      throw new BadRequestException('Solo se pueden cancelar solicitudes pendientes');
    }

    solicitud.estado = 'cancelada';
    await this.solicitudesRepository.save(solicitud);

    return { exito: true, mensaje: `Solicitud ${folio} cancelada` };
  }

  async crearDesdeCarrito(userId: number) {
    const cart = await this.cartService.getCart(userId);
    if (cart.totalItems === 0) {
      throw new BadRequestException('El carrito está vacío. Agrega máquinas antes de comprar.');
    }

    // Get user info
    // This would need user service - for now use placeholder
    const cliente = `Usuario #${userId}`;
    const contacto = 'email@ejemplo.com';

    interface CartItem {
      maquinaNombre: string;
      precioDia: number;
      duration: number;
      durationUnit: string;
      startDate: string;
      endDate: string;
    }

    const maquinasList = cart.items.map((item: CartItem) => ({
      nombre: item.maquinaNombre,
      cantidad: 1,
      precioDia: item.precioDia,
      duration: item.duration,
      durationUnit: item.durationUnit,
    }));

    const fechasInicio = cart.items.map((i: CartItem) => i.startDate).filter(Boolean);
    const fechasFin = cart.items.map((i: CartItem) => i.endDate).filter(Boolean);
    const fechaInicio = fechasInicio.length > 0 ? fechasInicio.sort()[0] : new Date().toISOString().split('T')[0];
    const fechaFin = fechasFin.length > 0 ? fechasFin.sort().reverse()[0] : new Date().toISOString().split('T')[0];

    const folio = this.generarFolio('SOL');
    const solicitud = this.solicitudesRepository.create({
      folio,
      cliente,
      contacto,
      maquinas: maquinasList,
      fechaInicio,
      fechaFin,
      estado: 'pendiente',
      notas: `Compra generada desde carrito. ${cart.totalItems} item(s), subtotal $${cart.subtotal.toLocaleString()}`,
      userId,
    });

    const saved = await this.solicitudesRepository.save(solicitud);
    await this.cartService.clearCart(userId);

    return {
      exito: true,
      folio: saved.folio,
      cliente: saved.cliente,
      contacto: saved.contacto,
      maquinas: saved.maquinas,
      fechaInicio: saved.fechaInicio,
      fechaFin: saved.fechaFin,
      subtotal: cart.subtotal,
      mensaje: `¡Compra realizada! Folio ${folio}. Te contactaremos para confirmar.`,
    };
  }

  private generarFolio(tipo: string): string {
    const now = new Date();
    const num = Math.random().toString(36).substring(2, 8).toUpperCase();
    return `${tipo}-${now.getFullYear()}-${num}`;
  }
}