import { Injectable, UnauthorizedException, ConflictException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import * as bcrypt from 'bcryptjs';
import { ConfigService } from '@nestjs/config';

import { User } from '../users/entities/user.entity';
import { RegisterDto } from './dto/register.dto';
import { LoginDto } from './dto/login.dto';

@Injectable()
export class AuthService {
  constructor(
    @InjectRepository(User)
    private usersRepository: Repository<User>,
    private jwtService: JwtService,
    private configService: ConfigService,
  ) {}

  async register(registerDto: RegisterDto) {
    const { email, password, displayName } = registerDto;

    const existingUser = await this.usersRepository.findOne({ where: { email } });
    if (existingUser) {
      throw new ConflictException('El correo electrónico ya está registrado');
    }

    const passwordHash = await bcrypt.hash(password, 10);
    const username = email.split('@')[0];

    const user = this.usersRepository.create({
      email,
      username,
      passwordHash,
      displayName: displayName || username,
      role: 'user',
      provider: 'local',
    });

    const savedUser = await this.usersRepository.save(user);
    const token = this.generateToken(savedUser);

    return {
      token,
      user: this.sanitizeUser(savedUser),
    };
  }

  async login(loginDto: LoginDto) {
    const { email, password } = loginDto;

    const user = await this.usersRepository.findOne({
      where: [{ email }, { username: email }],
      select: {
        id: true,
        username: true,
        email: true,
        passwordHash: true,
        displayName: true,
        role: true,
        blocked: true,
      },
    });

    if (!user || !(await bcrypt.compare(password, user.passwordHash))) {
      throw new UnauthorizedException('Credenciales incorrectas');
    }

    if (user.blocked) {
      throw new UnauthorizedException('Tu cuenta ha sido bloqueada por medidas de seguridad');
    }

    await this.usersRepository.update(user.id, { lastLogin: new Date() });

    const token = this.generateToken(user);

    return {
      token,
      user: this.sanitizeUser(user),
    };
  }

  async validateUser(userId: number): Promise<User | null> {
    return this.usersRepository.findOne({ where: { id: userId } });
  }

  async findOrCreateGoogleUser(googleUser: any): Promise<User> {
    let user = await this.usersRepository.findOne({
      where: { provider: 'google', providerId: googleUser.providerId },
    });

    if (!user) {
      user = await this.usersRepository.findOne({ where: { email: googleUser.email } });
      if (user) {
        user.provider = 'google';
        user.providerId = googleUser.providerId;
        user.avatarUrl = googleUser.picture;
        await this.usersRepository.save(user);
      } else {
        const username = googleUser.email.split('@')[0];
        user = this.usersRepository.create({
          email: googleUser.email,
          username,
          passwordHash: '',
          displayName: googleUser.name,
          role: 'user',
          provider: 'google',
          providerId: googleUser.providerId,
          avatarUrl: googleUser.picture,
        });
        user = await this.usersRepository.save(user);
      }
    }

    return user;
  }

  private generateToken(user: User): string {
    const payload = { sub: user.id, username: user.username, email: user.email };
    return this.jwtService.sign(payload);
  }

  private sanitizeUser(user: User) {
    const { passwordHash, ...sanitized } = user;
    return {
      ...sanitized,
      name: sanitized.displayName,
      blocked: sanitized.blocked || false,
    };
  }
}