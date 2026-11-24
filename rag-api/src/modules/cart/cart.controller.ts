import { Controller, Get, Post, Delete, Body, Param, UseGuards, Request } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth, ApiBody, ApiParam } from '@nestjs/swagger';

import { CartService } from './cart.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

interface AddToCartDto {
  maquinaNombre: string;
  duration: number;
  durationUnit: string;
  startDate?: string;
  endDate?: string;
  cantidad: number;
}

@ApiTags('Cart')
@Controller('api/carrito')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class CartController {
  constructor(private cartService: CartService) {}

  @Get()
  @ApiOperation({ summary: 'Obtener carrito del usuario' })
  async getCart(@Request() req: any) {
    return this.cartService.getCart(req.user.sub);
  }

  @Post()
  @ApiOperation({ summary: 'Agregar item al carrito' })
  @ApiBody({
    schema: {
      type: 'object',
      properties: {
        maquinaNombre: { type: 'string', example: 'Excavadora Hidráulica de Orugas' },
        duration: { type: 'number', example: 5 },
        durationUnit: { type: 'string', example: 'dias' },
        startDate: { type: 'string', example: '2026-01-15' },
        endDate: { type: 'string', example: '2026-01-20' },
        cantidad: { type: 'number', example: 1 },
      },
      required: ['maquinaNombre', 'duration', 'durationUnit', 'cantidad'],
    },
  })
  async addToCart(@Request() req: any, @Body() dto: AddToCartDto) {
    return this.cartService.addToCart(req.user.sub, dto);
  }

  @Delete(':itemId')
  @ApiOperation({ summary: 'Eliminar item del carrito por ID' })
  @ApiParam({ name: 'itemId', type: 'number' })
  async removeFromCart(@Request() req: any, @Param('itemId') itemId: number) {
    return this.cartService.removeFromCart(req.user.sub, itemId);
  }

  @Delete('maquina/:maquinaNombre')
  @ApiOperation({ summary: 'Eliminar todos los items de una máquina del carrito' })
  @ApiParam({ name: 'maquinaNombre', type: 'string' })
  async removeByMaquina(@Request() req: any, @Param('maquinaNombre') maquinaNombre: string) {
    return this.cartService.removeByMaquina(req.user.sub, maquinaNombre);
  }

  @Delete()
  @ApiOperation({ summary: 'Vaciar carrito completo' })
  async clearCart(@Request() req: any) {
    return this.cartService.clearCart(req.user.sub);
  }
}