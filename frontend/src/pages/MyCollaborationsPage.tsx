import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { collaborationsApi } from '../api/client';
import { Collaboration } from '../types';

const roleColors: Record<string, string> = {
  creator: 'bg-purple-100 text-purple-800',
  collaborator: 'bg-blue-100 text-blue-800',
};

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-800',
  completed: 'bg-indigo-100 text-indigo-800',
  left: 'bg-gray-100 text-gray-800',
  removed: 'bg-red-100 text-red-800',
};

export function MyCollaborationsPage() {
  const [collaborations, setCollaborations] = useState<Collaboration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchCollaborations = async () => {
      try {
        const data = await collaborationsApi.getMyCollaborations();
        setCollaborations(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load collaborations');
      } finally {
        setLoading(false);
      }
    };
    fetchCollaborations();
  }, []);

  const handleLeave = async (id: number) => {
    if (!confirm('Are you sure you want to leave this collaboration? You may not be able to rejoin.')) {
      return;
    }
    try {
      await collaborationsApi.leaveCollaboration(id);
      setCollaborations(prev =>
        prev.map(c => c.id === id ? { ...c, status: 'left' } : c)
      );
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to leave collaboration');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  const activeCollabs = collaborations.filter(c => c.status === 'active');
  const pastCollabs = collaborations.filter(c => c.status !== 'active');

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">My Collaborations</h1>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {collaborations.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">No collaborations yet</h3>
            <p className="text-gray-600 mb-4">
              Apply to projects or have your applications accepted to start collaborating.
            </p>
            <Link
              to="/projects"
              className="inline-block bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
            >
              Browse Projects
            </Link>
          </div>
        ) : (
          <div className="space-y-8">
            {activeCollabs.length > 0 && (
              <section>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Active ({activeCollabs.length})
                </h2>
                <div className="space-y-4">
                  {activeCollabs.map(collab => (
                    <div key={collab.id} className="bg-white rounded-lg shadow-sm p-6">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="flex items-center space-x-2 mb-2">
                            <Link
                              to={`/projects/${collab.project_id}`}
                              className="text-xl font-semibold text-gray-900 hover:text-indigo-600"
                            >
                              {collab.project?.title || `Project #${collab.project_id}`}
                            </Link>
                            <span className={`px-2 py-1 text-xs rounded-full ${roleColors[collab.role]}`}>
                              {collab.role}
                            </span>
                            <span className={`px-2 py-1 text-xs rounded-full ${statusColors[collab.status]}`}>
                              {collab.status}
                            </span>
                          </div>
                          {collab.project?.description && (
                            <p className="text-gray-600 text-sm line-clamp-2">{collab.project.description}</p>
                          )}
                        </div>
                        <div className="flex space-x-2">
                          <Link
                            to={`/messages/${collab.project_id}`}
                            className="px-3 py-1.5 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 text-sm"
                          >
                            Team Chat
                          </Link>
                          {collab.role !== 'creator' && (
                            <button
                              onClick={() => handleLeave(collab.id)}
                              className="px-3 py-1.5 border border-red-300 text-red-600 rounded-md hover:bg-red-50 text-sm"
                            >
                              Leave
                            </button>
                          )}
                        </div>
                      </div>
                      <div className="mt-4 text-sm text-gray-500">
                        Joined {new Date(collab.joined_at).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {pastCollabs.length > 0 && (
              <section>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Past ({pastCollabs.length})
                </h2>
                <div className="space-y-4">
                  {pastCollabs.map(collab => (
                    <div key={collab.id} className="bg-white rounded-lg shadow-sm p-6 opacity-75">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="flex items-center space-x-2 mb-2">
                            <Link
                              to={`/projects/${collab.project_id}`}
                              className="text-lg font-semibold text-gray-900 hover:text-indigo-600"
                            >
                              {collab.project?.title || `Project #${collab.project_id}`}
                            </Link>
                            <span className={`px-2 py-1 text-xs rounded-full ${statusColors[collab.status]}`}>
                              {collab.status}
                            </span>
                          </div>
                        </div>
                        <span className="text-sm text-gray-500">
                          {new Date(collab.joined_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
