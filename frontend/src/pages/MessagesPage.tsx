import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { conversationsApi } from '../api/client';
import { Conversation } from '../types';

export function MessagesPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const data = await conversationsApi.getConversations();
        setConversations(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load conversations');
      } finally {
        setLoading(false);
      }
    };
    fetchConversations();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Messages</h1>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {conversations.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">No conversations yet</h3>
            <p className="text-gray-600 mb-4">
              Join a project collaboration to start messaging with your team.
            </p>
            <Link
              to="/collaborations"
              className="inline-block bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
            >
              View Collaborations
            </Link>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm divide-y">
            {conversations.map(conversation => (
              <Link
                key={conversation.id}
                to={`/messages/${conversation.id}`}
                className="block p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h3 className="font-semibold text-gray-900">
                        {conversation.project?.title || `Conversation #${conversation.id}`}
                      </h3>
                      <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                        {conversation.type}
                      </span>
                    </div>
                    {conversation.last_message && (
                      <p className="text-sm text-gray-600 mt-1 line-clamp-1">
                        {conversation.last_message.content}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col items-end ml-4">
                    {conversation.last_message && (
                      <span className="text-xs text-gray-500">
                        {new Date(conversation.last_message.created_at).toLocaleDateString()}
                      </span>
                    )}
                    {conversation.unread_count && conversation.unread_count > 0 && (
                      <span className="mt-1 px-2 py-0.5 bg-indigo-600 text-white text-xs rounded-full">
                        {conversation.unread_count}
                      </span>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
