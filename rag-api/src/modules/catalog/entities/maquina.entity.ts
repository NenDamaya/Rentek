import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  ManyToOne,
  JoinColumn,
  CreateDateColumn,
  Index,
} from 'typeorm';

@Entity('maquinas')
@Index(['nombre'])
@Index(['categoriaId'])
export class Maquina {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ length: 255 })
  nombre: string;

  @Column({ length: 255, default: '' })
  nombreComun: string;

  @Column('text', { default: '' })
  marcas: string;

  @Column('text', { default: '' })
  modelosTipicos: string;

  @Column({ length: 255, default: '' })
  precioRenta: string;

  @Column('text', { array: true, default: [] })
  sinonimos: string[];

  @Column('text', { default: '' })
  perfilCliente: string;

  @Column('jsonb', { default: {} })
  especificaciones: Record<string, any>;

  @Column('text', { array: true, default: [] })
  recomendado: string[];

  @Column('text', { array: true, default: [] })
  noRecomendado: string[];

  @Column('text', { array: true, default: [] })
  casosUso: string[];

  @Column('jsonb', { default: [] })
  preguntasFrecuentes: any[];

  @Column('text', { array: true, default: [] })
  reglasNegocio: string[];

  @Column('numeric', { precision: 10, scale: 2, nullable: true })
  precioDia: number;

  @Column('numeric', { precision: 10, scale: 2, nullable: true })
  precioSemana: number;

  @Column('numeric', { precision: 10, scale: 2, nullable: true })
  precioMes: number;

  @Column({ length: 10, default: 'MXN' })
  moneda: string;

  @Column({ length: 50, default: 'disponible' })
  estado: string;

  @Column({ length: 255, default: '' })
  ubicacion: string;

  @Column({ nullable: true })
  anioFabricacion: number;

  @Column({ length: 100, nullable: true })
  numeroSerie: string;

  @Column('numeric', { precision: 10, scale: 2, nullable: true })
  costoOperadorDia: number;

  @Column('numeric', { precision: 10, scale: 2, nullable: true })
  costoTransporte: number;

  @Column({ default: false })
  incluyeOperador: boolean;

  @Column({ default: false })
  incluyeTransporte: boolean;

  @CreateDateColumn()
  createdAt: Date;

  @ManyToOne('Categoria', 'maquinas', { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'categoria_id' })
  categoria: any;

  @Column()
  categoriaId: number;
}