import {
  Entity,
  PrimaryColumn,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  ManyToOne,
  JoinColumn,
  Index,
  OneToMany,
} from 'typeorm';

@Entity('chats')
@Index(['userId', 'updatedAt'])
@Index(['status'])
export class Chat {
  @PrimaryColumn('uuid')
  id: string;

  @Column()
  userId: number;

  @Column({ length: 255, default: 'Nuevo chat' })
  title: string;

  @Column({ length: 20, default: 'active' })
  status: string;

  @Column({ default: 0 })
  offTopicStrikes: number;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  @ManyToOne('User', 'chats', { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'user_id' })
  user: any;

  @OneToMany('Conversation', 'chat')
  conversations: any[];
}