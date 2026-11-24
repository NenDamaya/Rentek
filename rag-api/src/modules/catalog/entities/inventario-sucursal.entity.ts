import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  ManyToOne,
  JoinColumn,
  Index,
  Unique,
} from 'typeorm';

@Entity('inventario_sucursal')
@Index(['sucursalId'])
@Index(['maquinaId'])
@Unique(['sucursalId', 'maquinaId'])
export class InventarioSucursal {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  sucursalId: number;

  @Column()
  maquinaId: number;

  @Column({ default: 1 })
  cantidadTotal: number;

  @Column({ default: 1 })
  cantidadDisponible: number;

  @Column({ default: 0 })
  cantidadRentada: number;

  @Column({ default: 0 })
  cantidadMantenimiento: number;

  @CreateDateColumn()
  createdAt: Date;

  @ManyToOne('Sucursal', 'inventario', { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'sucursal_id' })
  sucursal: any;

  @ManyToOne('Maquina', { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'maquina_id' })
  maquina: any;
}