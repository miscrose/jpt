'use client';

// CORRECTION : On importe useState directement ici
import { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { Plus, MessageSquare, UploadCloud, PanelLeftClose } from 'lucide-react';
import { Conversation } from '@/types';

interface SidebarProps {
  conversations: Conversation[];
  currentConversationId: string | null;
  onNewConversation: () => void;
  onSelectConversation: (id: string) => void;
  onUploadPDF: (files: FileList | null) => void;
  isUploading: boolean;
  isOpen: boolean;
  toggleSidebar: () => void; 
}

export default function Sidebar({
  conversations,
  currentConversationId,
  onNewConversation,
  onSelectConversation,
  onUploadPDF,
  isUploading,
  isOpen,
  toggleSidebar,
}: SidebarProps) {
  
  // CORRECTION : Utilisation directe de useState (plus besoin de React.useState)
  const [isDragging, setIsDragging] = useState(false); 
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    onUploadPDF(e.target.files);
    if (e.target) e.target.value = '';
  };

  const handleDragOver = (e: DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onUploadPDF(e.dataTransfer.files);
    }
  };

  return (
    <>
      {/* Sidebar Container */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-[260px] bg-[#202123] text-gray-100 transform transition-transform duration-300 ease-in-out border-r border-white/10 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-full flex-col p-3">
          
          {/* Header avec boutons */}
          <div className="flex items-center justify-between mb-4 px-2">
             {/* New Chat Button */}
            <button
                onClick={onNewConversation}
                className="flex-1 flex items-center gap-2 rounded-md border border-white/20 px-3 py-3 text-sm text-white hover:bg-gray-500/10 transition-colors mr-2"
            >
                <Plus size={16} />
                Nouvelle conv.
            </button>

            {/* Close Button */}
            <button 
                onClick={toggleSidebar}
                className="p-2 text-gray-400 hover:text-white border border-transparent hover:border-white/20 rounded-md transition-all"
                title="Fermer la barre latérale"
            >
                <PanelLeftClose size={20} />
            </button>
          </div>

          {/* Drop Zone Upload Area */}
          <div className="mb-6 px-1">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 pl-2">
              Base de connaissances
            </h3>
            <label
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-xl cursor-pointer transition-all duration-200 ${
                isDragging 
                  ? 'border-blue-500 bg-blue-500/10 scale-[1.02]' 
                  : 'border-gray-600 hover:border-gray-500 hover:bg-gray-700/30'
              }`}
            >
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                {isUploading ? (
                  <div className="animate-pulse flex flex-col items-center">
                    <UploadCloud className="w-8 h-8 mb-2 text-blue-400" />
                    <p className="text-xs text-gray-400">Traitement...</p>
                  </div>
                ) : (
                  <>
                    <UploadCloud className={`w-8 h-8 mb-2 ${isDragging ? 'text-blue-400' : 'text-gray-400'}`} />
                    <p className="mb-1 text-xs text-gray-400 text-center px-2">
                      <span className="font-semibold">PDF</span> Drag & Drop
                    </p>
                  </>
                )}
              </div>
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

          {/* History List */}
          <div className="flex-1 overflow-y-auto overflow-x-hidden">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 pl-2 sticky top-0 bg-[#202123] py-2">
              Historique
            </h3>
            <div className="space-y-1">
              {conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => onSelectConversation(conv.id)}
                  className={`group relative flex w-full items-center gap-3 rounded-md px-3 py-3 text-sm transition-colors ${
                    currentConversationId === conv.id
                      ? 'bg-[#343541] text-white'
                      : 'text-gray-100 hover:bg-[#2A2B32]'
                  }`}
                >
                  <MessageSquare size={16} className="text-gray-400 group-hover:text-white" />
                  <div className="flex-1 truncate text-left relative z-10">
                    {conv.title || "Nouvelle conversation"}
                  </div>
                </button>
              ))}
            </div>
          </div>

        
        </div>
      </aside>

      {/* Overlay mobile (cliquer dehors ferme le menu) */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-gray-900/80 z-30 lg:hidden backdrop-blur-sm"
          onClick={toggleSidebar}
        />
      )}
    </>
  );
}