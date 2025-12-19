'use client';

import { useState, useEffect, useRef } from 'react';
import ChatMessage from '@/components/ChatMessage';
import ChatInput from '@/components/ChatInput';
import Sidebar from '@/components/Sidebar';
import { Message, Conversation } from '@/types';
import { askQuestion, uploadPDF } from '@/lib/api';
import {
  createConversation,
  getConversation,
  getAllConversations,
  addMessageToConversation,
} from '@/lib/firestore';
import { Loader2, Bot, PanelLeftOpen, CheckCircle2, AlertCircle } from 'lucide-react';

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  
  // NOUVEAU : État pour la notification (Toast)
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadConversations();
    if (window.innerWidth < 1024) {
      setIsSidebarOpen(false);
    }
  }, []);

  useEffect(() => {
    if (notification) {
      // La notification disparaît après 3 secondes
      const timer = setTimeout(() => setNotification(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    } else {
      setMessages([]);
    }
  }, [currentConversationId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading]);

  const loadConversations = async () => {
    try {
      const convs = await getAllConversations();
      setConversations(convs);
    } catch (error) {
      console.error('Erreur chargement conversations:', error);
    }
  };

  const loadConversation = async (id: string) => {
    try {
      const conv = await getConversation(id);
      if (conv) setMessages(conv.messages);
    } catch (error) {
      console.error('Erreur chargement conversation:', error);
    }
  };

  const handleNewConversation = async () => {
    try {
      const newId = await createConversation();
      setCurrentConversationId(newId);
      setMessages([]);
      await loadConversations();
      if (window.innerWidth < 1024) setIsSidebarOpen(false);
    } catch (error) {
      console.error('Erreur création conversation:', error);
    }
  };

  const handleSelectConversation = (id: string) => {
    setCurrentConversationId(id);
    if (window.innerWidth < 1024) setIsSidebarOpen(false);
  };

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    let convId = currentConversationId;
    if (!convId) {
      try {
        convId = await createConversation();
        setCurrentConversationId(convId);
        await loadConversations();
      } catch (error) {
        console.error('Erreur init conversation:', error);
        return;
      }
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      await addMessageToConversation(convId, userMessage);
      const history = [...messages, userMessage].map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));
      const response = await askQuestion(content, history);
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      await addMessageToConversation(convId, assistantMessage);
      await loadConversations();
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `❌ Erreur: ${error instanceof Error ? error.message : 'Erreur inconnue'}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUploadPDF = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setIsUploading(true);
    try {
      for (let i = 0; i < files.length; i++) {
        await uploadPDF(files[i]);
      }
      // SUCCÈS : On affiche la notification verte
      setNotification({
        message: `${files.length} document(s) analysé(s) avec succès !`,
        type: 'success'
      });
    } catch (error) {
      console.error('Erreur upload:', error);
      // ERREUR : On affiche la notification rouge
      setNotification({
        message: "Erreur lors de l'envoi du document.",
        type: 'error'
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex h-full overflow-hidden bg-white dark:bg-[#343541]">
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onNewConversation={handleNewConversation}
        onSelectConversation={handleSelectConversation}
        onUploadPDF={handleUploadPDF}
        isUploading={isUploading}
        isOpen={isSidebarOpen}
        toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
      />

      <main 
        className={`flex-1 flex flex-col h-full relative transition-all duration-300 ${
            isSidebarOpen ? 'lg:pl-[260px]' : 'lg:pl-0'
        }`}
      >
        <header className="absolute top-0 w-full z-10 p-2 flex items-start">
            {!isSidebarOpen && (
                <button 
                    onClick={() => setIsSidebarOpen(true)}
                    className="p-2 m-2 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-500 transition-colors bg-white/50 backdrop-blur-sm border border-gray-200 dark:border-gray-700"
                >
                    <PanelLeftOpen size={24} />
                </button>
            )}
            
            <button 
                 onClick={() => setIsSidebarOpen(true)}
                 className={`lg:hidden p-2 m-2 rounded-md hover:bg-gray-200 text-gray-500 bg-white/80 border ${isSidebarOpen ? 'hidden' : 'block'}`}
            >
                <PanelLeftOpen size={24} />
            </button>
        </header>

        {/* NOUVEAU : Notification Toast (Centrée en haut) */}
        {notification && (
          <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-50 animate-in fade-in slide-in-from-top-4">
            <div className={`flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg border ${
              notification.type === 'success' 
                ? 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/90 dark:border-green-800 dark:text-green-100' 
                : 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/90 dark:border-red-800 dark:text-red-100'
            }`}>
              {notification.type === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
              <span className="text-sm font-medium">{notification.message}</span>
            </div>
          </div>
        )}

        <div className="flex-1 overflow-y-auto w-full scroll-smooth">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center px-4 text-center animate-in fade-in duration-500">
              <div className="bg-white dark:bg-[#444654] p-4 rounded-full shadow-sm mb-6">
                <Bot size={48} className="text-gray-400 dark:text-gray-200" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-100 mb-2">
                Assistant Médical Intelligent
              </h2>
              <p className="text-gray-500 dark:text-gray-400 max-w-md mb-8">
                Posez une question clinique ou glissez un dossier patient PDF dans la barre latérale.
              </p>
            </div>
          ) : (
            <div className="flex flex-col h-full">
              <div className="h-12 w-full flex-shrink-0" />
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              {isLoading && (
                <div className="w-full py-6 bg-gray-50/50 dark:bg-[#444654]/20 border-b border-black/5 dark:border-white/5">
                  <div className="max-w-3xl mx-auto px-4 flex gap-4">
                     <div className="h-8 w-8 bg-green-500 rounded-sm flex items-center justify-center">
                        <Bot size={20} className="text-white" />
                     </div>
                     <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm">Analyse du dossier en cours...</span>
                     </div>
                  </div>
                </div>
              )}
              <div className="h-32 w-full flex-shrink-0" ref={scrollRef} />
            </div>
          )}
        </div>

        <div className={`${isSidebarOpen ? 'lg:pl-0' : ''} transition-all duration-300`}>
             <ChatInput 
                onSend={handleSendMessage} 
                onUpload={handleUploadPDF}
                disabled={isLoading || isUploading} 
             />
        </div>
      </main>
    </div>
  );
}