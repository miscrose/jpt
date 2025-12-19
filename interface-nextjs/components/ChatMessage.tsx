'use client';

import { Message } from '@/types';
import { Bot, User, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm'; // <--- C'est lui le sauveur

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`group w-full text-gray-800 dark:text-gray-100 border-b border-black/5 dark:border-white/5 ${
      isUser ? 'bg-transparent' : 'bg-gray-50/50 dark:bg-[#444654]/40'
    }`}>
      <div className="text-base gap-4 md:gap-6 md:max-w-3xl lg:max-w-[40rem] xl:max-w-[48rem] p-4 md:py-6 flex lg:px-0 m-auto">
        
        {/* Avatar */}
        <div className="flex-shrink-0 flex flex-col relative items-end">
          <div className={`relative flex h-8 w-8 items-center justify-center rounded-sm`}>
            {isUser ? (
               <div className="h-8 w-8 bg-purple-600 rounded-sm flex items-center justify-center text-white">
                 <User size={20} />
               </div>
            ) : (
              <div className="h-8 w-8 bg-green-500 rounded-sm flex items-center justify-center text-white">
                <Bot size={20} />
              </div>
            )}
          </div>
        </div>

        {/* Contenu */}
        <div className="relative flex-1 overflow-hidden">
          <div className="font-semibold text-sm mb-1 opacity-90 block">
            {isUser ? 'Vous' : 'Assistant'}
          </div>

          <div className="prose prose-slate dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-gray-800 prose-pre:rounded-lg">
            
            {/* ICI : On active le plugin et on stylise le tableau */}
            <ReactMarkdown 
                remarkPlugins={[remarkGfm]} 
                components={{
                    // Style du cadre du tableau
                    table: ({node, ...props}) => (
                        <div className="overflow-x-auto my-4 rounded-lg border border-gray-300 dark:border-gray-700 shadow-sm">
                            <table className="min-w-full divide-y divide-gray-300 dark:divide-gray-700" {...props} />
                        </div>
                    ),
                    // Style de l'en-tête (Gris clair)
                    thead: ({node, ...props}) => (
                        <thead className="bg-gray-100 dark:bg-gray-800" {...props} />
                    ),
                    // Style des cellules d'en-tête (Gras)
                    th: ({node, ...props}) => (
                        <th className="px-4 py-3 text-left text-xs font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider" {...props} />
                    ),
                    // Style du corps
                    tbody: ({node, ...props}) => (
                        <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-transparent" {...props} />
                    ),
                    // Style des lignes (Hover effect)
                    tr: ({node, ...props}) => (
                        <tr className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors" {...props} />
                    ),
                    // Style des cellules normales
                    td: ({node, ...props}) => (
                        <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 whitespace-normal" {...props} />
                    ),
                }}
            >
              {message.content}
            </ReactMarkdown>
          </div>

          {/* Sources */}
          {message.sources && message.sources.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700/50">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
                <FileText size={12} /> 
                <span>Sources utilisées :</span>
              </p>
              <div className="flex flex-wrap gap-2">
                {message.sources.map((source, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-blue-600 dark:text-blue-400 border border-gray-200 dark:border-gray-700"
                  >
                    {source}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}