import { Controller, Get, Post, Put, Delete, Body, Param, UseGuards, Request, Query } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth, ApiParam, ApiQuery, ApiBody } from '@nestjs/swagger';

import { ChatsService } from './chats.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';

interface CreateChatDto {
  title?: string;
}

interface UpdateChatDto {
  title?: string;
}

@ApiTags('Chats')
@Controller('api/chats')
@UseGuards(JwtAuthGuard)
@ApiBearerAuth()
export class ChatsController {
  constructor(private chatsService: ChatsService) {}

  @Get()
  @ApiOperation({ summary: 'Listar chats del usuario' })
  async getChats(@Request() req: any) {
    return this.chatsService.getChats(req.user.sub);
  }

  @Post()
  @ApiOperation({ summary: 'Crear nuevo chat' })
  @ApiBody({
    schema: {
      type: 'object',
      properties: {
        title: { type: 'string' },
      },
    },
  })
  async createChat(@Request() req: any, @Body() dto: CreateChatDto) {
    return this.chatsService.createChat(req.user.sub, dto);
  }

  @Put(':chatId')
  @ApiOperation({ summary: 'Actualizar chat' })
  @ApiParam({ name: 'chatId', type: 'string' })
  @ApiBody({
    schema: {
      type: 'object',
      properties: {
        title: { type: 'string' },
      },
    },
  })
  async updateChat(@Request() req: any, @Param('chatId') chatId: string, @Body() dto: UpdateChatDto) {
    return this.chatsService.updateChat(chatId, req.user.sub, dto);
  }

  @Delete(':chatId')
  @ApiOperation({ summary: 'Eliminar chat' })
  @ApiParam({ name: 'chatId', type: 'string' })
  async deleteChat(@Request() req: any, @Param('chatId') chatId: string) {
    return this.chatsService.deleteChat(chatId, req.user.sub);
  }

  @Get(':chatId/messages')
  @ApiOperation({ summary: 'Obtener mensajes de un chat' })
  @ApiParam({ name: 'chatId', type: 'string' })
  async getChatMessages(@Request() req: any, @Param('chatId') chatId: string) {
    return this.chatsService.getChatMessages(chatId, req.user.sub);
  }
}