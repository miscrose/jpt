'use client';

import { useState, useEffect } from 'react';
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
import { Loader2 } from 'lucide-react';

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  // Charger les conversations au démarrage
  useEffect(() => {
    loadConversations();
  }, []);

  // Charger les messages de la conversation courante
  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    } else {
      setMessages([]);
    }
  }, [currentConversationId]);

  const loadConversations = async () => {
    try {
      const convs = await getAllConversations();
      setConversations(convs);
    } catch (error) {
      console.error('Erreur lors du chargement des conversations:', error);
    }
  };

  const loadConversation = async (id: string) => {
    try {
      const conv = await getConversation(id);
      if (conv) {
        setMessages(conv.messages);
      }
    } catch (error) {
      console.error('Erreur lors du chargement de la conversation:', error);
    }
  };

  const handleNewConversation = async () => {
    try {
      const newId = await createConversation();
      setCurrentConversationId(newId);
      setMessages([]);
      await loadConversations();
    } catch (error) {
      console.error('Erreur lors de la création de la conversation:', error);
      alert('Erreur lors de la création de la conversation');
    }
  };

  const handleSelectConversation = (id: string) => {
    setCurrentConversationId(id);
  };

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    // Créer une conversation si nécessaire
    let convId = currentConversationId;
    if (!convId) {
      try {
        convId = await createConversation();
        setCurrentConversationId(convId);
        await loadConversations();
      } catch (error) {
        console.error('Erreur lors de la création de la conversation:', error);
        alert('Erreur lors de la création de la conversation');
        return;
      }
    }

    // Créer le message utilisateur
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    // Ajouter le message utilisateur immédiatement
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Sauvegarder le message utilisateur dans Firestore
      await addMessageToConversation(convId, userMessage);

      // Préparer l'historique pour l'API
      const history = [...messages, userMessage].map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      // Appeler l'API pour obtenir la réponse
      const response = await askQuestion(content, history);

      // Créer le message assistant
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        timestamp: new Date(),
      };

      // Ajouter le message assistant
      setMessages((prev) => [...prev, assistantMessage]);

      // Sauvegarder le message assistant dans Firestore
      await addMessageToConversation(convId, assistantMessage);

      // Mettre à jour la liste des conversations
      await loadConversations();
    } catch (error) {
      console.error('Erreur lors de l\'envoi du message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Erreur: ${error instanceof Error ? error.message : 'Erreur inconnue'}`,
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
        const file = files[i];
        // Uploader vers le microservice Python pour l'indexation (stockage local)
        await uploadPDF(file);
      }

      alert(`${files.length} PDF(s) uploadé(s) et indexé(s) avec succès !`);
    } catch (error) {
      console.error('Erreur lors de l\'upload du PDF:', error);
      alert(`Erreur lors de l'upload: ${error instanceof Error ? error.message : 'Erreur inconnue'}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex h-screen bg-white dark:bg-gray-950">
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onNewConversation={handleNewConversation}
        onSelectConversation={handleSelectConversation}
        onUploadPDF={handleUploadPDF}
        isUploading={isUploading}
      />

      <main className="flex-1 flex flex-col lg:ml-64">
        {/* Header */}
        <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 p-4">
          <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
            Assistant Médical Intelligent
          </h1>
        </header>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center space-y-4">
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
                  Commencez une nouvelle conversation
                </h2>
                <p className="text-gray-500 dark:text-gray-400">
                  Posez une question ou uploadez un document PDF pour commencer
                </p>
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              {isLoading && (
                <div className="flex gap-4 p-4">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-200 dark:bg-gray-800">
                    <Loader2 className="h-4 w-4 animate-spin text-gray-600 dark:text-gray-400" />
                  </div>
                  <div className="text-gray-500 dark:text-gray-400">Réflexion en cours...</div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Input */}
        <ChatInput onSend={handleSendMessage} disabled={isLoading} />
      </main>
    </div>
  );
}
