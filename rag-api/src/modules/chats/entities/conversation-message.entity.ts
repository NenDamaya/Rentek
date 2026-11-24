import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  ManyToOne,
  JoinColumn,
  Index,
} from 'typeorm';

@Entity('conversation_messages')
@Index(['conversationId', 'createdAt'])
export class ConversationMessage {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ length: 36 })
  conversationId: string;

  @Column({ length: 20 })
  role: 'user' | 'assistant' | 'system' | 'tool';

  @Column('text', { nullable: true })
  content: string;

  @Column('jsonb', { nullable: true })
  toolCalls: any[];

  @Column({ length: 50, nullable: true })
  toolCallId: string;

  @Column({ length: 100, nullable: true })
  name: string;

  @CreateDateColumn()
  createdAt: Date;

  @ManyToOne('Conversation', 'messages', { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'conversation_id' })
  conversation: any;
}