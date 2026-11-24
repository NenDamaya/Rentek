import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  ManyToOne,
  JoinColumn,
  Index,
  OneToMany,
} from 'typeorm';

@Entity('conversations')
@Index(['chatId'])
@Index(['userId'])
export class Conversation {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ length: 36 })
  chatId: string;

  @Column({ nullable: true })
  userId: number;

  @CreateDateColumn()
  createdAt: Date;

  @ManyToOne('Chat', 'conversations', { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'chat_id' })
  chat: any;

  @ManyToOne('User', { onDelete: 'SET NULL' })
  @JoinColumn({ name: 'user_id' })
  user: any;

  @OneToMany('ConversationMessage', 'conversation')
  messages: any[];
}