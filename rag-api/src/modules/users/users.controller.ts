import { Controller, Get, Param, Patch, Body, UseGuards, Request, Delete } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth, ApiParam } from '@nestjs/swagger';

import { UsersService } from './users.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

@ApiTags('Users')
@Controller('api/users')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class UsersController {
  constructor(private usersService: UsersService) {}

  @Get()
  @ApiOperation({ summary: 'Obtener todos los usuarios (admin)' })
  async findAll() {
    return this.usersService.findAll();
  }

  @Get(':id')
  @ApiOperation({ summary: 'Obtener usuario por ID' })
  @ApiParam({ name: 'id', type: 'number' })
  async findById(@Param('id') id: number) {
    return this.usersService.findById(id);
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Actualizar usuario' })
  @ApiParam({ name: 'id', type: 'number' })
  async update(@Param('id') id: number, @Body() updateData: any) {
    return this.usersService.update(id, updateData);
  }

  @Patch(':id/block')
  @ApiOperation({ summary: 'Bloquear usuario (admin)' })
  @ApiParam({ name: 'id', type: 'number' })
  async blockUser(@Param('id') id: number) {
    return this.usersService.blockUser(id);
  }

  @Patch(':id/unblock')
  @ApiOperation({ summary: 'Desbloquear usuario (admin)' })
  @ApiParam({ name: 'id', type: 'number' })
  async unblockUser(@Param('id') id: number) {
    return this.usersService.unblockUser(id);
  }
}