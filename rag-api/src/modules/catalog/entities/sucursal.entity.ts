import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  OneToMany,
  Index,
} from 'typeorm';

@Entity('sucursales')
@Index(['activa'])
export class Sucursal {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ length: 255 })
  nombre: string;

  @Column('text', { default: '' })
  direccion: string;

  @Column({ length: 50, default: '' })
  telefono: string;

  @Column({ length: 255, default: '' })
  email: string;

  @Column({ length: 255, default: '' })
  horario: string;

  @Column('numeric', { precision: 10, scale: 7, nullable: true })
  latitud: number;

  @Column('numeric', { precision: 10, scale: 7, nullable: true })
  longitud: number;

  @Column({ default: true })
  activa: boolean;

  @CreateDateColumn()
  createdAt: Date;

  @OneToMany('InventarioSucursal', 'sucursal')
  inventario: any[];
}