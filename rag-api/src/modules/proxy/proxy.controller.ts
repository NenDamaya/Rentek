import { Controller, Post, Get, Body, Req, Headers, Res, HttpCode, HttpStatus } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth, ApiHeader } from '@nestjs/swagger';
import { Response } from 'express';

import { ProxyService } from './proxy.service';
import { ChatCompletionRequestDto } from './dto/chat-completion.dto';

@ApiTags('AI Proxy')
@Controller('v1')
export class ProxyController {
  constructor(private proxyService: ProxyService) {}

  @Post('chat/completions')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Chat completions (proxy a Python FastAPI)' })
  @ApiBearerAuth()
  @ApiHeader({ name: 'Authorization', required: false })
  async chatCompletions(
    @Body() req: ChatCompletionRequestDto,
    @Headers('authorization') authHeader: string,
  ) {
    return this.proxyService.chatCompletions(req, authHeader);
  }

  @Post('chat/completions/stream')
  @ApiOperation({ summary: 'Chat completions streaming (proxy a Python FastAPI)' })
  @ApiBearerAuth()
  @ApiHeader({ name: 'Authorization', required: false })
  async chatCompletionsStream(
    @Body() body: ChatCompletionRequestDto,
    @Headers('authorization') authHeader: string,
    @Req() req: any,
    @Res() res: Response,
  ) {
    try {
      const stream = await this.proxyService.chatCompletionsStream({ ...body, stream: true }, authHeader);

      res.setHeader('Content-Type', 'text/event-stream');
      res.setHeader('Cache-Control', 'no-cache');
      res.setHeader('Connection', 'keep-alive');
      res.setHeader('Access-Control-Allow-Origin', '*');

      stream.pipe(res);

      req.on('close', () => {
        stream.destroy();
      });
    } catch (error: any) {
      res.status(HttpStatus.BAD_GATEWAY).json({ error: error.message });
    }
  }

  @Get('tools')
  @ApiOperation({ summary: 'Obtener esquemas de herramientas (proxy a Python FastAPI)' })
  async getTools() {
    return this.proxyService.getTools();
  }

  @Post('rag/query')
  @ApiOperation({ summary: 'Consulta RAG directa (proxy a Python FastAPI)' })
  async queryRag(@Body() body: { question: string; top_k?: number }) {
    return this.proxyService.queryRag(body.question, body.top_k);
  }

  @Get('rag/stats')
  @ApiOperation({ summary: 'Estadísticas de RAG (proxy a Python FastAPI)' })
  async getRagStats() {
    return this.proxyService.getRagStats();
  }
}