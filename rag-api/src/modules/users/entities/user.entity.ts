import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  Index,
  OneToMany,
} from 'typeorm';

@Entity('users')
@Index(['username'], { unique: true })
@Index(['email'])
@Index(['provider', 'providerId'])
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ length: 100, unique: true })
  username: string;

  @Column({ length: 255, default: '' })
  email: string;

  @Column({ length: 255, default: '', select: false })
  passwordHash: string;

  @Column({ length: 255, default: '' })
  displayName: string;

  @Column({ length: 20, default: 'user' })
  role: 'admin' | 'user';

  @Column({ length: 50, default: 'local' })
  provider: string;

  @Column({ length: 255, default: '' })
  providerId: string;

  @Column('text', { default: '' })
  avatarUrl: string;

  @Column({ default: false })
  blocked: boolean;

  @Column({ nullable: true })
  blockedAt: Date;

  @Column({ default: 0 })
  closedChats: number;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  lastLogin: Date;

  @OneToMany('Chat', 'user')
  chats: any[];

  @OneToMany('SolicitudRenta', 'user')
  solicitudes: any[];

  @OneToMany('Cotizacion', 'user')
  cotizaciones: any[];

  @OneToMany('CarritoItem', 'user')
  carritoItems: any[];
}