import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  ManyToOne,
  JoinColumn,
  Index,
} from 'typeorm';

@Entity('cotizaciones')
@Index(['folio'], { unique: true })
@Index(['userId'])
export class Cotizacion {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ length: 20, unique: true })
  folio: string;

  @Column({ length: 255 })
  cliente: string;

  @Column({ length: 255 })
  contacto: string;

  @Column('jsonb')
  maquinas: any[];

  @Column()
  dias: number;

  @Column('numeric', { precision: 12, scale: 2 })
  subtotal: number;

  @Column('numeric', { precision: 12, scale: 2, default: 0 })
  descuento: number;

  @Column('numeric', { precision: 12, scale: 2 })
  total: number;

  @Column({ type: 'date' })
  validaHasta: string;

  @Column({ nullable: true })
  userId: number;

  @CreateDateColumn()
  createdAt: Date;

  @ManyToOne('User', 'cotizaciones', { onDelete: 'SET NULL' })
  @JoinColumn({ name: 'user_id' })
  user: any;
}