import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  OneToMany,
  Index,
} from 'typeorm';

@Entity('categorias')
@Index(['nombre'], { unique: true })
export class Categoria {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ length: 255, unique: true })
  nombre: string;

  @Column('text', { default: '' })
  descripcion: string;

  @CreateDateColumn()
  createdAt: Date;

  @OneToMany('Maquina', 'categoria')
  maquinas: any[];
}