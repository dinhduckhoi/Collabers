import { useState, useEffect, useRef, FormEvent } from 'react';
import { useParams, Link } from 'react-router-dom';
import { conversationsApi } from '../api/client';
import { Conversation, Message } from '../types';
import { useAuth } from '../hooks/useAuth';
import { Avatar } from '../components';

export function ConversationPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    const fetchConversation = async () => {
      try {
        const data = await conversationsApi.getConversation(Number(id));
        setConversation(data);
        setMessages(data.messages || []);
        // Mark as read
        await conversationsApi.markAsRead(Number(id));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load conversation');
      } finally {
        setLoading(false);
      }
    };
    fetchConversation();
  }, [id]);

  // Real-time polling for new messages
  useEffect(() => {
    if (!id || loading) return;

    const pollInterval = setInterval(async () => {
      try {
        const data = await conversationsApi.getConversation(Number(id));
        const newMessages = data.messages || [];
        
        // Only update if there are new messages
        if (newMessages.length > messages.length) {
          setMessages(newMessages);
          // Mark as read when new messages arrive
          await conversationsApi.markAsRead(Number(id));
        }
      } catch (err) {
        // Silent fail on polling errors to not disrupt the user
        console.error('Failed to poll messages:', err);
      }
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(pollInterval);
  }, [id, loading, messages.length]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e: FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || sending) return;

    setSending(true);
    try {
      const message = await conversationsApi.sendMessage(Number(id), newMessage.trim());
      setMessages(prev => [...prev, message]);
      setNewMessage('');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to send message');
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error || !conversation) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded">
            {error || 'Conversation not found'}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-4 py-3 flex items-center">
        <Link to="/messages" className="text-gray-600 hover:text-gray-900 mr-4">
          Back
        </Link>
        <div>
          <h1 className="font-semibold text-gray-900">
            {conversation.project?.title || `Conversation #${conversation.id}`}
          </h1>
          <p className="text-sm text-gray-500">
            {conversation.type === 'project_team' ? 'Team Chat' : 'Direct Message'}
          </p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            No messages yet. Start the conversation!
          </div>
        ) : (
          messages.map(message => {
            const isOwn = message.sender_id === user?.id;
            const profile = message.sender_profile || message.sender?.profile;
            const senderName = profile?.full_name || message.sender?.email || 'User';
            const senderAvatar = profile?.avatar_url;
            
            return (
              <div
                key={message.id}
                className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex items-end space-x-2 ${isOwn ? 'flex-row-reverse space-x-reverse' : ''}`}>
                  {/* Avatar */}
                  {!isOwn && (
                    <Avatar src={senderAvatar} name={senderName} size="sm" />
                  )}
                  
                  {/* Message bubble */}
                  <div
                    className={`max-w-xs md:max-w-md lg:max-w-lg rounded-lg px-4 py-2 ${
                      isOwn
                        ? 'bg-indigo-600 text-white'
                        : 'bg-white text-gray-900 shadow-sm'
                    }`}
                  >
                    {!isOwn && (
                      <p className="text-xs font-medium text-indigo-600 mb-1">
                        {senderName}
                      </p>
                    )}
                    <p className="whitespace-pre-wrap break-words">{message.content}</p>
                    <p
                      className={`text-xs mt-1 ${
                        isOwn ? 'text-indigo-200' : 'text-gray-500'
                      }`}
                    >
                      {new Date(message.created_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="bg-white border-t p-4">
        <div className="flex space-x-4">
          <input
            type="text"
            value={newMessage}
            onChange={e => setNewMessage(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:ring-indigo-500 focus:border-indigo-500"
          />
          <button
            type="submit"
            disabled={!newMessage.trim() || sending}
            className="px-6 py-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 disabled:opacity-50"
          >
            {sending ? '...' : 'Send'}
          </button>
        </div>
      </form>
    </div>
  );
}
