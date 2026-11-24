import { Controller, Post, Body, Get, Request, UseGuards, Res, HttpCode, HttpStatus } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth, ApiBody } from '@nestjs/swagger';
import { Response } from 'express';

import { AuthService } from './auth.service';
import { RegisterDto } from './dto/register.dto';
import { LoginDto } from './dto/login.dto';
import { JwtAuthGuard } from './guards/jwt-auth.guard';
import { GoogleAuthGuard } from './guards/google-auth.guard';

@ApiTags('Auth')
@Controller('api/auth')
export class AuthController {
  constructor(private authService: AuthService) {}

  @Post('register')
  @ApiOperation({ summary: 'Registrar nuevo usuario' })
  @ApiBody({ type: RegisterDto })
  async register(@Body() registerDto: RegisterDto) {
    return this.authService.register(registerDto);
  }

  @Post('login')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Iniciar sesión' })
  @ApiBody({ type: LoginDto })
  async login(@Body() loginDto: LoginDto) {
    return this.authService.login(loginDto);
  }

  @Post('logout')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Cerrar sesión' })
  async logout() {
    return { mensaje: 'Sesión cerrada exitosamente' };
  }

  @Get('me')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Obtener usuario actual' })
  async getMe(@Request() req: any) {
    const user = await this.authService.validateUser(req.user.sub);
    if (!user) {
      return { id: req.user.sub, username: req.user.username, displayName: req.user.username, role: 'user', blocked: false };
    }
    const { passwordHash, ...sanitized } = user;
    return { ...sanitized, name: sanitized.displayName, blocked: sanitized.blocked || false };
  }

  @Get('google/login')
  @UseGuards(GoogleAuthGuard)
  @ApiOperation({ summary: 'Iniciar sesión con Google' })
  async googleLogin() {}

  @Get('google/callback')
  @UseGuards(GoogleAuthGuard)
  @ApiOperation({ summary: 'Callback de Google OAuth' })
  async googleCallback(@Request() req: any, @Res() res: Response) {
    const user = req.user;
    const frontendUrl = this.authService['configService'].get('app.frontendUrl');

    const token = user.token;
    const userPayload = Buffer.from(JSON.stringify({
      id: user.id,
      username: user.username,
      displayName: user.displayName,
      role: user.role,
      token,
      picture: user.avatarUrl,
      email: user.email,
      blocked: user.blocked,
    })).toString('base64');

    return res.redirect(`${frontendUrl}/?oauth_user=${encodeURIComponent(userPayload)}`);
  }
}