import { Controller, Post, Get, Body, Param, UseGuards, Request } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth, ApiBody, ApiParam } from '@nestjs/swagger';

import { RequestsService } from './requests.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

interface RegistrarSolicitudDto {
  cliente: string;
  contacto: string;
  maquinas: Array<{ nombre: string; cantidad: number }>;
  fechaInicio: string;
  fechaFin: string;
}

@ApiTags('Requests')
@Controller('api')
export class RequestsController {
  constructor(private requestsService: RequestsService) {}

  @Post('solicitudes')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Registrar solicitud de renta' })
  @ApiBody({
    schema: {
      type: 'object',
      properties: {
        cliente: { type: 'string' },
        contacto: { type: 'string' },
        maquinas: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              nombre: { type: 'string' },
              cantidad: { type: 'number' },
            },
          },
        },
        fechaInicio: { type: 'string', format: 'date' },
        fechaFin: { type: 'string', format: 'date' },
      },
      required: ['cliente', 'contacto', 'maquinas', 'fechaInicio', 'fechaFin'],
    },
  })
  async registrarSolicitud(@Request() req: any, @Body() dto: RegistrarSolicitudDto) {
    return this.requestsService.registrarSolicitud(dto, req.user.sub);
  }

  @Get('solicitudes')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Obtener mis solicitudes' })
  async getMisSolicitudes(@Request() req: any) {
    return this.requestsService.getMisSolicitudes(req.user.sub);
  }

  @Get('solicitudes/:folio')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Obtener solicitud por folio' })
  @ApiParam({ name: 'folio', type: 'string' })
  async getSolicitudByFolio(@Param('folio') folio: string) {
    return this.requestsService.getSolicitudByFolio(folio);
  }

  @Post('solicitudes/:folio/cancelar')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Cancelar solicitud' })
  @ApiParam({ name: 'folio', type: 'string' })
  async cancelarSolicitud(@Request() req: any, @Param('folio') folio: string) {
    return this.requestsService.cancelarSolicitud(folio, req.user.sub);
  }

  @Post('carrito/checkout')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Convertir carrito en solicitud de renta' })
  async checkoutCarrito(@Request() req: any) {
    return this.requestsService.crearDesdeCarrito(req.user.sub);
  }
}