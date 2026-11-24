import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  ManyToOne,
  JoinColumn,
  Index,
} from 'typeorm';

@Entity('solicitudes_renta')
@Index(['estado'])
@Index(['fechaInicio', 'fechaFin'])
@Index(['userId'])
export class SolicitudRenta {
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

  @Column({ type: 'date' })
  fechaInicio: string;

  @Column({ type: 'date' })
  fechaFin: string;

  @Column({ length: 50, default: 'pendiente' })
  estado: string;

  @Column('text', { default: '' })
  notas: string;

  @Column({ nullable: true })
  userId: number;

  @CreateDateColumn()
  createdAt: Date;

  @ManyToOne('User', 'solicitudes', { onDelete: 'SET NULL' })
  @JoinColumn({ name: 'user_id' })
  user: any;
}