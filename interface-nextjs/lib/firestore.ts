import { 
  collection, 
  doc, 
  addDoc, 
  updateDoc, 
  getDoc, 
  getDocs, 
  deleteDoc,
  query,
  orderBy,
  Timestamp,
  serverTimestamp 
} from 'firebase/firestore';
import { db } from './firebase';
import { Conversation, Message } from '@/types';

const CONVERSATIONS_COLLECTION = 'conversations';

// Créer une nouvelle conversation
export async function createConversation(title: string = 'Nouvelle conversation'): Promise<string> {
  const conversationData = {
    title,
    messages: [],
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
  };

  const docRef = await addDoc(collection(db, CONVERSATIONS_COLLECTION), conversationData);
  return docRef.id;
}

// Récupérer une conversation
export async function getConversation(conversationId: string): Promise<Conversation | null> {
  const docRef = doc(db, CONVERSATIONS_COLLECTION, conversationId);
  const docSnap = await getDoc(docRef);

  if (!docSnap.exists()) {
    return null;
  }

  const data = docSnap.data();
  return {
    id: docSnap.id,
    title: data.title || 'Sans titre',
    messages: (data.messages || []).map((msg: any) => ({
      ...msg,
      timestamp: msg.timestamp?.toDate() || new Date(),
    })),
    createdAt: data.createdAt?.toDate() || new Date(),
    updatedAt: data.updatedAt?.toDate() || new Date(),
  };
}

// Récupérer toutes les conversations
export async function getAllConversations(): Promise<Conversation[]> {
  const q = query(
    collection(db, CONVERSATIONS_COLLECTION),
    orderBy('updatedAt', 'desc')
  );
  
  const querySnapshot = await getDocs(q);
  return querySnapshot.docs.map((doc) => {
    const data = doc.data();
    return {
      id: doc.id,
      title: data.title || 'Sans titre',
      messages: (data.messages || []).map((msg: any) => ({
        ...msg,
        timestamp: msg.timestamp?.toDate() || new Date(),
      })),
      createdAt: data.createdAt?.toDate() || new Date(),
      updatedAt: data.updatedAt?.toDate() || new Date(),
    };
  });
}

// Ajouter un message à une conversation
export async function addMessageToConversation(
  conversationId: string,
  message: Message
): Promise<void> {
  const docRef = doc(db, CONVERSATIONS_COLLECTION, conversationId);
  const docSnap = await getDoc(docRef);

  if (!docSnap.exists()) {
    throw new Error('Conversation introuvable');
  }

  const data = docSnap.data();
  const messages = data.messages || [];
  
  // Générer un titre automatique à partir du premier message utilisateur
  let title = data.title;
  if (messages.length === 0 && message.role === 'user') {
    title = message.content.substring(0, 50) + (message.content.length > 50 ? '...' : '');
  }

  await updateDoc(docRef, {
    messages: [...messages, {
      ...message,
      timestamp: Timestamp.fromDate(message.timestamp),
    }],
    title,
    updatedAt: serverTimestamp(),
  });
}

// Mettre à jour une conversation complète
export async function updateConversation(
  conversationId: string,
  messages: Message[]
): Promise<void> {
  const docRef = doc(db, CONVERSATIONS_COLLECTION, conversationId);
  
  await updateDoc(docRef, {
    messages: messages.map((msg) => ({
      ...msg,
      timestamp: Timestamp.fromDate(msg.timestamp),
    })),
    updatedAt: serverTimestamp(),
  });
}

// Supprimer une conversation
export async function deleteConversation(conversationId: string): Promise<void> {
  const docRef = doc(db, CONVERSATIONS_COLLECTION, conversationId);
  await deleteDoc(docRef);
}

