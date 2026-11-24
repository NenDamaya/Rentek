import { IsArray, IsOptional, IsString, IsBoolean, ValidateNested } from 'class-validator';
import { Type } from 'class-transformer';
import { ApiProperty } from '@nestjs/swagger';

export class ChatMessageDto {
  @ApiProperty({ enum: ['user', 'assistant', 'system', 'tool'] })
  @IsString()
  role: 'user' | 'assistant' | 'system' | 'tool';

  @ApiProperty({ required: false })
  @IsOptional()
  @IsString()
  content?: string;

  @ApiProperty({ required: false })
  @IsOptional()
  @IsArray()
  toolCalls?: any[];

  @ApiProperty({ required: false })
  @IsOptional()
  @IsString()
  toolCallId?: string;

  @ApiProperty({ required: false })
  @IsOptional()
  @IsString()
  name?: string;
}

export class ChatCompletionRequestDto {
  @ApiProperty({ required: false })
  @IsOptional()
  @IsString()
  model?: string;

  @ApiProperty({ type: [ChatMessageDto] })
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => ChatMessageDto)
  messages: ChatMessageDto[];

  @ApiProperty({ required: false })
  @IsOptional()
  @IsArray()
  tools?: any[];

  @ApiProperty({ required: false, enum: ['auto', 'none', 'required'] })
  @IsOptional()
  @IsString()
  toolChoice?: string;

  @ApiProperty({ required: false })
  @IsOptional()
  @IsString()
  conversationId?: string;

  @ApiProperty({ required: false })
  @IsOptional()
  @IsString()
  chatId?: string;

  @ApiProperty({ required: false, default: false })
  @IsOptional()
  @IsBoolean()
  stream?: boolean;

  @ApiProperty({ required: false })
  @IsOptional()
  @IsString()
  userName?: string;

  @ApiProperty({ required: false })
  @IsOptional()
  @IsString()
  userEmail?: string;
}