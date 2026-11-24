import { Injectable, UnauthorizedException } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { ExtractJwt, Strategy, StrategyOptionsWithoutRequest } from 'passport-jwt';
import { ConfigService } from '@nestjs/config';
import { AuthService } from '../auth.service';

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy, 'jwt') {
  constructor(
    private configService: ConfigService,
    private authService: AuthService,
  ) {
    const secret = configService.get('app.jwt.secret');
    if (!secret) {
      throw new Error('JWT_SECRET is not defined in configuration');
    }

    const options: StrategyOptionsWithoutRequest = {
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false,
      secretOrKey: secret,
    };
    super(options);
  }

  async validate(payload: any) {
    const user = await this.authService.validateUser(payload.sub);
    if (!user || user.blocked) {
      throw new UnauthorizedException();
    }
    return { sub: user.id, username: user.username, email: user.email };
  }
}