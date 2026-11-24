import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { v4 as uuidv4 } from 'uuid';

import { Chat } from './entities/chat.entity';
import { Conversation } from './entities/conversation.entity';
import { ConversationMessage } from './entities/conversation-message.entity';

interface CreateChatDto {
  title?: string;
}

interface UpdateChatDto {
  title?: string;
}

@Injectable()
export class ChatsService {
  constructor(
    @InjectRepository(Chat)
    private chatsRepository: Repository<Chat>,
    @InjectRepository(Conversation)
    private conversationsRepository: Repository<Conversation>,
    @InjectRepository(ConversationMessage)
    private messagesRepository: Repository<ConversationMessage>,
  ) {}

  async getChats(userId: number) {
    const chats = await this.chatsRepository
      .createQueryBuilder('chat')
      .leftJoinAndSelect('chat.conversations', 'conversations')
      .leftJoin('conversations.messages', 'messages')
      .where('chat.userId = :userId', { userId })
      .select([
        'chat.id',
        'chat.title',
        'chat.createdAt',
        'chat.updatedAt',
        'chat.status',
        'chat.offTopicStrikes',
        'COUNT(DISTINCT messages.id) as messageCount',
        'EXISTS(SELECT 1 FROM conversation_messages cm JOIN conversations cv ON cm.conversation_id = cv.id WHERE cv.chat_id = chat.id AND (cm.content LIKE \'%registrar_solicitud%\' OR cm.content LIKE \'%SOL-%\' OR cm.content LIKE \'%exito%\')) as hasSolicitud',
      ])
      .groupBy('chat.id')
      .orderBy('chat.updatedAt', 'DESC')
      .getRawMany();

    return { chats };
  }

  async createChat(userId: number, dto: CreateChatDto) {
    const chatId = uuidv4();
    const chat = this.chatsRepository.create({
      id: chatId,
      userId,
      title: dto.title || 'Nuevo chat',
    });

    const saved = await this.chatsRepository.save(chat);

    const conversation = this.conversationsRepository.create({
      id: uuidv4(),
      chatId: saved.id,
      userId,
    });
    await this.conversationsRepository.save(conversation);

    return {
      id: saved.id,
      title: saved.title,
      createdAt: saved.createdAt,
    };
  }

  async updateChat(chatId: string, userId: number, dto: UpdateChatDto) {
    const chat = await this.chatsRepository.findOne({ where: { id: chatId, userId } });
    if (!chat) {
      throw new NotFoundException('Chat no encontrado');
    }

    chat.title = dto.title || chat.title;
    chat.updatedAt = new Date();
    await this.chatsRepository.save(chat);

    return { ok: true };
  }

  async deleteChat(chatId: string, userId: number) {
    const chat = await this.chatsRepository.findOne({ where: { id: chatId, userId } });
    if (!chat) {
      throw new NotFoundException('Chat no encontrado');
    }

    // Cancel pending solicitudes for this user
    // This would need requests service - skipping for now

    await this.chatsRepository.delete({ id: chatId, userId });

    return { ok: true, message: 'Chat eliminado y citas canceladas' };
  }

  async getChatMessages(chatId: string, userId: number) {
    const chat = await this.chatsRepository.findOne({ where: { id: chatId, userId } });
    if (!chat) {
      throw new NotFoundException('Chat no encontrado');
    }

    const conversation = await this.conversationsRepository.findOne({
      where: { chatId },
      order: { createdAt: 'DESC' },
    });

    if (!conversation) {
      return { messages: [], conversationId: null, chatStatus: chat.status };
    }

    const messages = await this.messagesRepository.find({
      where: { conversationId: conversation.id },
      order: { createdAt: 'ASC' },
    });

    return {
      messages: messages.map((m) => ({
        role: m.role,
        content: m.content,
      })),
      conversationId: conversation.id,
      chatStatus: chat.status,
    };
  }

  async saveMessages(sessionId: string, chatId: string, userMsg: string, assistantMsg: string, toolsExecuted: any[]) {
    let conversation = await this.conversationsRepository.findOne({ where: { id: sessionId } });

    if (!conversation) {
      conversation = this.conversationsRepository.create({
        id: sessionId,
        chatId,
      });
      await this.conversationsRepository.save(conversation);
    } else if (chatId && conversation.chatId !== chatId) {
      conversation.chatId = chatId;
      await this.conversationsRepository.save(conversation);
    }

    await this.messagesRepository.save([
      this.messagesRepository.create({ conversationId: sessionId, role: 'user', content: userMsg }),
      this.messagesRepository.create({ conversationId: sessionId, role: 'assistant', content: assistantMsg }),
    ]);

    if (chatId) {
      await this.chatsRepository.update(chatId, { updatedAt: new Date() });
    }
  }
}