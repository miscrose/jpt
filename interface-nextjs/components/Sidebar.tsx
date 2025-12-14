'use client';

import { useState, useRef } from 'react';
import { Plus, FileText, X, Upload } from 'lucide-react';
import { Conversation } from '@/types';

interface SidebarProps {
  conversations: Conversation[];
  currentConversationId: string | null;
  onNewConversation: () => void;
  onSelectConversation: (id: string) => void;
  onUploadPDF: (files: FileList | null) => void;
  isUploading: boolean;
}

export default function Sidebar({
  conversations,
  currentConversationId,
  onNewConversation,
  onSelectConversation,
  onUploadPDF,
  isUploading,
}: SidebarProps) {
  const [isOpen, setIsOpen] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onUploadPDF(e.target.files);
    // Reset input
    if (e.target) {
      e.target.value = '';
    }
  };

  return (
    <>
      {/* Mobile toggle button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed left-4 top-4 z-50 lg:hidden rounded-lg bg-white dark:bg-gray-900 p-2 shadow-lg"
      >
        {isOpen ? <X size={20} /> : <FileText size={20} />}
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 h-full w-64 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transform transition-transform duration-300 z-40 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0`}
      >
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-800">
            <button
              onClick={onNewConversation}
              className="w-full flex items-center gap-2 rounded-lg bg-blue-500 px-4 py-2 text-white hover:bg-blue-600 transition-colors"
            >
              <Plus size={18} />
              Nouvelle conversation
            </button>
          </div>

          {/* PDF Upload */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-800">
            <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              Documents PDF
            </label>
            <label className="flex items-center gap-2 rounded-lg border border-gray-300 dark:border-gray-700 px-4 py-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
              <Upload size={18} />
              <span className="text-sm">
                {isUploading ? 'Upload en cours...' : 'Ajouter PDF'}
              </span>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                multiple
                onChange={handleFileChange}
                disabled={isUploading}
                className="hidden"
              />
            </label>
          </div>

          {/* Conversations list */}
          <div className="flex-1 overflow-y-auto p-2">
            <div className="space-y-1">
              {conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => onSelectConversation(conv.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                    currentConversationId === conv.id
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
                  }`}
                >
                  <div className="truncate">{conv.title}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    {conv.messages.length} message{conv.messages.length > 1 ? 's' : ''}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
}

