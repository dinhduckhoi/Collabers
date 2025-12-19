import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { applicationsApi } from '../api/client';
import { Application } from '../types';

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  under_review: 'bg-blue-100 text-blue-800',
  accepted: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  withdrawn: 'bg-gray-100 text-gray-800',
};

export function MyApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchApplications = async () => {
      try {
        const data = await applicationsApi.getMyApplications();
        setApplications(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load applications');
      } finally {
        setLoading(false);
      }
    };
    fetchApplications();
  }, []);

  const handleWithdraw = async (id: number) => {
    if (!confirm('Are you sure you want to withdraw this application?')) {
      return;
    }
    try {
      await applicationsApi.updateApplication(id, { status: 'withdrawn' });
      setApplications(prev =>
        prev.map(app => app.id === id ? { ...app, status: 'withdrawn' } : app)
      );
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to withdraw application');
    }
  };

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
        <h1 className="text-3xl font-bold text-gray-900 mb-8">My Applications</h1>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {applications.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">No applications yet</h3>
            <p className="text-gray-600 mb-4">Browse projects and apply to start collaborating.</p>
            <Link
              to="/projects"
              className="inline-block bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
            >
              Browse Projects
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {applications.map(application => (
              <div key={application.id} className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center space-x-2 mb-2">
                      <Link
                        to={`/projects/${application.project_id}`}
                        className="text-xl font-semibold text-gray-900 hover:text-indigo-600"
                      >
                        {application.project?.title || `Project #${application.project_id}`}
                      </Link>
                      <span className={`px-2 py-1 text-xs rounded-full ${statusColors[application.status]}`}>
                        {application.status.replace('_', ' ')}
                      </span>
                    </div>
                    {application.cover_letter && (
                      <p className="text-gray-600 text-sm line-clamp-2">{application.cover_letter}</p>
                    )}
                    {application.proposed_role && (
                      <p className="text-sm text-indigo-600 mt-1">Role: {application.proposed_role}</p>
                    )}
                  </div>
                  <div className="flex flex-col items-end space-y-2">
                    <span className="text-sm text-gray-500">
                      {new Date(application.created_at).toLocaleDateString()}
                    </span>
                    {application.status === 'pending' && (
                      <button
                        onClick={() => handleWithdraw(application.id)}
                        className="text-sm text-red-600 hover:underline"
                      >
                        Withdraw
                      </button>
                    )}
                  </div>
                </div>

                {application.status === 'accepted' && (
                  <div className="mt-4 p-3 bg-green-50 rounded-md">
                    <p className="text-green-800 text-sm">
                      Congratulations! Your application was accepted. Check your collaborations to get started.
                    </p>
                    <Link
                      to="/collaborations"
                      className="text-sm text-green-700 hover:underline mt-1 inline-block"
                    >
                      View Collaborations
                    </Link>
                  </div>
                )}

                {application.status === 'rejected' && (
                  <div className="mt-4 p-3 bg-red-50 rounded-md">
                    <p className="text-red-800 text-sm">
                      This application was not accepted. Don't give up - keep applying to other projects!
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
