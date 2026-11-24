import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  ManyToOne,
  JoinColumn,
  Index,
} from 'typeorm';

@Entity('precios_especiales')
@Index(['maquinaId'])
@Index(['tipo'])
export class PrecioEspecial {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  maquinaId: number;

  @Column({ length: 50 })
  tipo: string;

  @Column({ nullable: true })
  minDias: number;

  @Column({ nullable: true })
  maxDias: number;

  @Column('numeric', { precision: 5, scale: 2 })
  descuentoPorcentaje: number;

  @Column('text', { default: '' })
  descripcion: string;

  @Column({ default: true })
  activo: boolean;

  @Column({ type: 'date', nullable: true })
  fechaInicio: string;

  @Column({ type: 'date', nullable: true })
  fechaFin: string;

  @CreateDateColumn()
  createdAt: Date;

  @ManyToOne('Maquina', { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'maquina_id' })
  maquina: any;
}