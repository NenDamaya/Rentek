import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from './entities/user.entity';

@Injectable()
export class UsersService {
  constructor(
    @InjectRepository(User)
    private usersRepository: Repository<User>,
  ) {}

  async findAll(): Promise<User[]> {
    return this.usersRepository.find({
      select: {
        id: true,
        username: true,
        email: true,
        displayName: true,
        role: true,
        provider: true,
        avatarUrl: true,
        createdAt: true,
        lastLogin: true,
        blocked: true,
        closedChats: true,
      },
      order: { createdAt: 'DESC' },
    });
  }

  async findById(id: number): Promise<User> {
    const user = await this.usersRepository.findOne({
      where: { id },
      select: {
        id: true,
        username: true,
        email: true,
        displayName: true,
        role: true,
        provider: true,
        avatarUrl: true,
        createdAt: true,
        lastLogin: true,
        blocked: true,
        closedChats: true,
      },
    });
    if (!user) {
      throw new NotFoundException(`Usuario con ID ${id} no encontrado`);
    }
    return user;
  }

  async update(id: number, updateData: Partial<User>): Promise<User> {
    await this.usersRepository.update(id, updateData);
    return this.findById(id);
  }

  async blockUser(id: number): Promise<User> {
    return this.update(id, { blocked: true, blockedAt: new Date() });
  }

  async unblockUser(id: number): Promise<User> {
    return this.update(id, { blocked: false, blockedAt: undefined, closedChats: 0 });
  }
}