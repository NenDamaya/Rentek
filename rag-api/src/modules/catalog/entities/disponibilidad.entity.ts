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

@Entity('disponibilidad')
@Index(['maquinaId', 'fecha'])
@Index(['fecha'])
@Unique(['maquinaId', 'fecha'])
export class Disponibilidad {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  maquinaId: number;

  @Column({ type: 'date' })
  fecha: string;

  @Column({ default: true })
  disponible: boolean;

  @Column('text', { default: '' })
  notas: string;

  @CreateDateColumn()
  createdAt: Date;

  @ManyToOne('Maquina', { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'maquina_id' })
  maquina: any;
}