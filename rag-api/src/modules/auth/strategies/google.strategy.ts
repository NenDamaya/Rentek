import { Injectable } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { Strategy, StrategyOptions, VerifyCallback } from 'passport-google-oauth20';
import { ConfigService } from '@nestjs/config';
import { AuthService } from '../auth.service';

@Injectable()
export class GoogleStrategy extends PassportStrategy(Strategy, 'google') {
  constructor(
    private configService: ConfigService,
    private authService: AuthService,
  ) {
    const options: StrategyOptions = {
      clientID: configService.get('app.google.clientId') || '',
      clientSecret: configService.get('app.google.clientSecret') || '',
      callbackURL: configService.get('app.google.redirectUri') || 'http://localhost:3000/api/auth/google/callback',
      scope: ['email', 'profile'],
    };
    super(options);
  }

  async validate(
    accessToken: string,
    refreshToken: string,
    profile: any,
    done: VerifyCallback,
  ): Promise<any> {
    const { id, name, emails, photos } = profile;

    const googleUser = {
      providerId: id,
      email: emails[0].value,
      name: `${name.givenName} ${name.familyName}`,
      picture: photos[0]?.value,
    };

    const user = await this.authService.findOrCreateGoogleUser(googleUser);
    const token = this.authService['generateToken'](user);

    done(null, {
      ...user,
      token,
    });
  }
}