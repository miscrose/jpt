'use client';

import { Message } from '@/types';
import { Bot, User } from 'lucide-react';
import { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const messageRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll vers le dernier message
    messageRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, []);

  return (
    <div
      ref={messageRef}
      className={`flex gap-4 p-4 ${
        isUser ? 'bg-gray-50 dark:bg-gray-900/50' : 'bg-white dark:bg-gray-950'
      }`}
    >
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          isUser
            ? 'bg-blue-500 text-white'
            : 'bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
        }`}
      >
        {isUser ? <User size={18} /> : <Bot size={18} />}
      </div>
      <div className="flex-1 space-y-2">
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        {message.sources && message.sources.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">Sources:</span>
            {message.sources.map((source, idx) => (
              <span
                key={idx}
                className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded"
              >
                {source}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

