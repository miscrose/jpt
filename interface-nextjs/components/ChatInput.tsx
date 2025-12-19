'use client';

import { useState, KeyboardEvent, useRef, useEffect, ChangeEvent } from 'react';
import { Send, Loader2, Paperclip } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  // NOUVEAU : On ajoute la fonction d'upload ici
  onUpload: (files: FileList | null) => void; 
  disabled?: boolean;
}

export default function ChatInput({ onSend, onUpload, disabled }: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // NOUVEAU : Référence pour le input file caché
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'inherit';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
      if (textareaRef.current) textareaRef.current.style.height = '56px';
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // NOUVEAU : Fonction pour déclencher le clic sur l'input caché
  const handlePaperclipClick = () => {
    fileInputRef.current?.click();
  };

  // NOUVEAU : Quand un fichier est sélectionné
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onUpload(e.target.files);
    }
    // Reset pour permettre de re-uploader le même fichier si besoin
    if (e.target) e.target.value = '';
  };

  return (
    <div className="fixed bottom-0 left-0 w-full bg-gradient-to-t from-white via-white to-transparent dark:from-gray-950 dark:via-gray-950 pb-6 pt-10 px-4 z-10 lg:pl-72">
      <div className="mx-auto max-w-3xl relative">
        <div className="relative flex items-end w-full p-3 bg-white dark:bg-[#2f2f2f] border border-gray-200 dark:border-gray-700 shadow-xl rounded-2xl ring-offset-2 focus-within:ring-2 focus-within:ring-blue-500/50">
          
          {/* NOUVEAU : L'input caché qui fait le travail */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".pdf"
            multiple
            className="hidden"
          />

          {/* Bouton Trombone actif */}
          <button 
            type="button"
            onClick={handlePaperclipClick}
            disabled={disabled}
            className="p-2 mr-2 text-gray-400 hover:text-gray-600 dark:text-gray-400 dark:hover:text-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Ajouter un document PDF"
          >
            <Paperclip size={20} />
          </button>

          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Posez une question sur vos documents..."
            disabled={disabled}
            rows={1}
            className="flex-1 max-h-[200px] min-h-[24px] bg-transparent border-none focus:ring-0 resize-none py-3 text-base text-gray-900 dark:text-gray-100 placeholder:text-gray-400"
            style={{ minHeight: '24px' }}
          />
          
          <button
            onClick={handleSend}
            disabled={disabled || !input.trim()}
            className={`p-2 rounded-lg transition-all duration-200 mb-0.5 ${
              input.trim() 
                ? 'bg-black dark:bg-white text-white dark:text-black hover:opacity-80' 
                : 'bg-gray-100 dark:bg-gray-800 text-gray-400 cursor-not-allowed'
            }`}
          >
            {disabled ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </div>
        <p className="text-center text-xs text-gray-400 dark:text-gray-500 mt-2">
          L'IA peut faire des erreurs. Vérifiez les informations importantes.
        </p>
      </div>
    </div>
  );
}