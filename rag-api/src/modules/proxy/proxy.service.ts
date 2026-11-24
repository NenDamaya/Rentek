import { Injectable, HttpException, HttpStatus, Logger } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { firstValueFrom } from 'rxjs';
import { AxiosError } from 'axios';

import { ChatCompletionRequestDto } from './dto/chat-completion.dto';

@Injectable()
export class ProxyService {
  private readonly logger = new Logger(ProxyService.name);

  constructor(
    private httpService: HttpService,
    private configService: ConfigService,
  ) {}

  async chatCompletions(req: ChatCompletionRequestDto, authHeader?: string) {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
        'User-Agent': 'rentek-app/1.0',
      };

      if (authHeader) {
        headers['Authorization'] = authHeader;
      }

      const response = await firstValueFrom(
        this.httpService.post('/v1/chat/completions', req, { headers }),
      );

      return response.data;
    } catch (error: unknown) {
      const axiosError = error as AxiosError;
      this.logger.error(`Error proxying chat completions: ${axiosError.message}`);
      throw new HttpException(
        axiosError.response?.data || 'Error en el servicio de IA',
        axiosError.response?.status || HttpStatus.BAD_GATEWAY,
      );
    }
  }

  async chatCompletionsStream(req: ChatCompletionRequestDto, authHeader?: string) {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
        'User-Agent': 'rentek-app/1.0',
        Accept: 'text/event-stream',
      };

      if (authHeader) {
        headers['Authorization'] = authHeader;
      }

      const response = await firstValueFrom(
        this.httpService.post('/v1/chat/completions/stream', { ...req, stream: true }, {
          headers,
          responseType: 'stream',
        }),
      );

      return response.data;
    } catch (error: unknown) {
      const axiosError = error as AxiosError;
      this.logger.error(`Error proxying chat completions stream: ${axiosError.message}`);
      throw new HttpException(
        axiosError.response?.data || 'Error en el servicio de IA (stream)',
        axiosError.response?.status || HttpStatus.BAD_GATEWAY,
      );
    }
  }

  async getTools() {
    try {
      const response = await firstValueFrom(
        this.httpService.get('/v1/tools', {
          headers: {
            'ngrok-skip-browser-warning': 'true',
            'User-Agent': 'rentek-app/1.0',
          },
        }),
      );
      return response.data;
    } catch (error: unknown) {
      const axiosError = error as AxiosError;
      this.logger.error(`Error getting tools: ${axiosError.message}`);
      throw new HttpException(
        'Error obteniendo herramientas',
        axiosError.response?.status || HttpStatus.BAD_GATEWAY,
      );
    }
  }

  async queryRag(question: string, topK: number = 5) {
    try {
      const response = await firstValueFrom(
        this.httpService.post('/api/query', { question, top_k: topK }, {
          headers: {
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': 'true',
            'User-Agent': 'rentek-app/1.0',
          },
        }),
      );
      return response.data;
    } catch (error: unknown) {
      const axiosError = error as AxiosError;
      this.logger.error(`Error querying RAG: ${axiosError.message}`);
      throw new HttpException(
        'Error en consulta RAG',
        axiosError.response?.status || HttpStatus.BAD_GATEWAY,
      );
    }
  }

  async getRagStats() {
    try {
      const response = await firstValueFrom(
        this.httpService.get('/api/rag/stats', {
          headers: {
            'ngrok-skip-browser-warning': 'true',
            'User-Agent': 'rentek-app/1.0',
          },
        }),
      );
      return response.data;
    } catch (error: unknown) {
      const axiosError = error as AxiosError;
      this.logger.error(`Error getting RAG stats: ${axiosError.message}`);
      throw new HttpException(
        'Error obteniendo estadísticas RAG',
        axiosError.response?.status || HttpStatus.BAD_GATEWAY,
      );
    }
  }
}