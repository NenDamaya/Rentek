import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  ManyToOne,
  JoinColumn,
  Index,
} from 'typeorm';

@Entity('carrito_items')
@Index(['userId'])
export class CarritoItem {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  userId: number;

  @Column({ length: 255 })
  maquinaNombre: string;

  @Column('jsonb')
  maquinaJson: any;

  @Column({ default: 1 })
  duration: number;

  @Column({ length: 20, default: 'dias' })
  durationUnit: string;

  @Column({ type: 'date' })
  startDate: string;

  @Column({ type: 'date' })
  endDate: string;

  @Column('numeric', { precision: 10, scale: 2, default: 0 })
  precioDia: number;

  @CreateDateColumn()
  createdAt: Date;

  @ManyToOne('User', 'carritoItems', { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'user_id' })
  user: any;
}