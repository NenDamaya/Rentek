import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  Index,
} from 'typeorm';

@Entity('proyectos')
@Index(['nombre'], { unique: true })
export class Proyecto {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ length: 255, unique: true })
  nombre: string;

  @Column('text', { array: true, default: [] })
  maquinarias: string[];

  @Column('text', { default: '' })
  consideraciones: string;

  @CreateDateColumn()
  createdAt: Date;
}