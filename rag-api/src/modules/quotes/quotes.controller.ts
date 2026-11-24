import { Controller, Post, Get, Body, Param, UseGuards, Request } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth, ApiBody, ApiParam } from '@nestjs/swagger';

import { QuotesService } from './quotes.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

interface CalcularCotizacionDto {
  items: Array<{ nombre: string; cantidad: number }>;
  dias: number;
  incluyeFlete?: boolean;
  incluyeOperador?: boolean;
}

interface GenerarCotizacionDto {
  cliente: string;
  contacto: string;
  items: Array<{ nombre: string; cantidad: number }>;
  dias: number;
}

@ApiTags('Quotes')
@Controller('api')
export class QuotesController {
  constructor(private quotesService: QuotesService) {}

  @Post('cotizacion/calcular')
  @ApiOperation({ summary: 'Calcular cotización sin guardar' })
  @ApiBody({
    schema: {
      type: 'object',
      properties: {
        items: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              nombre: { type: 'string' },
              cantidad: { type: 'number' },
            },
          },
        },
        dias: { type: 'number' },
        incluyeFlete: { type: 'boolean' },
        incluyeOperador: { type: 'boolean' },
      },
      required: ['items', 'dias'],
    },
  })
  async calcularCotizacion(@Body() dto: CalcularCotizacionDto) {
    return this.quotesService.calcularCotizacion(dto);
  }

  @Post('cotizacion')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Generar cotización formal con folio' })
  @ApiBody({
    schema: {
      type: 'object',
      properties: {
        cliente: { type: 'string' },
        contacto: { type: 'string' },
        items: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              nombre: { type: 'string' },
              cantidad: { type: 'number' },
            },
          },
        },
        dias: { type: 'number' },
      },
      required: ['cliente', 'contacto', 'items', 'dias'],
    },
  })
  async generarCotizacion(@Request() req: any, @Body() dto: GenerarCotizacionDto) {
    return this.quotesService.generarCotizacion(
      dto.cliente,
      dto.contacto,
      dto.items,
      dto.dias,
      req.user.sub,
    );
  }

  @Get('cotizaciones')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Obtener mis cotizaciones' })
  async getMisCotizaciones(@Request() req: any) {
    return this.quotesService.getMisCotizaciones(req.user.sub);
  }

  @Get('cotizaciones/:folio')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Obtener cotización por folio' })
  @ApiParam({ name: 'folio', type: 'string' })
  async getCotizacionByFolio(@Param('folio') folio: string) {
    return this.quotesService.getCotizacionByFolio(folio);
  }
}