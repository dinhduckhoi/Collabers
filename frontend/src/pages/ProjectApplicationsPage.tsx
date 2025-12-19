import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { applicationsApi } from '../api/client';
import { Application } from '../types';
import { Avatar } from '../components';

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  under_review: 'bg-blue-100 text-blue-800',
  accepted: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  withdrawn: 'bg-gray-100 text-gray-800',
};

export function ProjectApplicationsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [processingId, setProcessingId] = useState<number | null>(null);

  useEffect(() => {
    const fetchApplications = async () => {
      try {
        const data = await applicationsApi.getProjectApplications(Number(projectId));
        setApplications(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load applications');
      } finally {
        setLoading(false);
      }
    };
    fetchApplications();
  }, [projectId]);

  const handleUpdateStatus = async (id: number, status: 'accepted' | 'rejected' | 'under_review') => {
    setProcessingId(id);
    try {
      const updated = await applicationsApi.updateApplication(id, { status });
      setApplications(prev =>
        prev.map(app => app.id === id ? updated : app)
      );
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update application');
    } finally {
      setProcessingId(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  const pendingApps = applications.filter(a => a.status === 'pending' || a.status === 'under_review');
  const decidedApps = applications.filter(a => a.status === 'accepted' || a.status === 'rejected' || a.status === 'withdrawn');

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Applications</h1>
          <Link
            to={`/projects/${projectId}`}
            className="text-indigo-600 hover:underline"
          >
            Back to Project
          </Link>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {applications.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">No applications yet</h3>
            <p className="text-gray-600">Applications will appear here when students apply to your project.</p>
          </div>
        ) : (
          <div className="space-y-8">
            {pendingApps.length > 0 && (
              <section>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Pending Review ({pendingApps.length})
                </h2>
                <div className="space-y-4">
                  {pendingApps.map(application => (
                    <div key={application.id} className="bg-white rounded-lg shadow-sm p-6">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <Avatar 
                              src={application.applicant?.profile?.avatar_url} 
                              name={application.applicant?.profile?.full_name || application.applicant?.email || '?'} 
                              size="md" 
                            />
                            <div>
                              <Link
                                to={`/users/${application.applicant_id}`}
                                className="text-lg font-semibold text-gray-900 hover:text-indigo-600"
                              >
                                {application.applicant?.profile?.full_name ||
                                 application.applicant?.email ||
                                 `User #${application.applicant_id}`}
                              </Link>
                              <span className={`ml-2 px-2 py-1 text-xs rounded-full ${statusColors[application.status]}`}>
                                {application.status.replace('_', ' ')}
                              </span>
                            </div>
                          </div>

                          {application.applicant?.profile && (
                            <div className="text-sm text-gray-600 mb-2">
                              {application.applicant.profile.headline}
                            </div>
                          )}

                          {application.proposed_role && (
                            <div className="text-sm text-indigo-600 mb-2">
                              Proposed Role: {application.proposed_role}
                            </div>
                          )}

                          {application.cover_letter && (
                            <div className="mt-3 p-3 bg-gray-50 rounded-md">
                              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                                {application.cover_letter}
                              </p>
                            </div>
                          )}

                          {application.applicant?.profile?.skills && (
                            <div className="mt-3">
                              <span className="text-sm text-gray-500">Skills: </span>
                              <div className="inline-flex flex-wrap gap-1">
                                {application.applicant.profile.skills.slice(0, 5).map(skill => (
                                  <span key={skill} className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded-full">
                                    {skill}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>

                        <div className="flex flex-col space-y-2 ml-4">
                          <button
                            onClick={() => handleUpdateStatus(application.id, 'accepted')}
                            disabled={processingId === application.id}
                            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 text-sm"
                          >
                            Accept
                          </button>
                          <button
                            onClick={() => handleUpdateStatus(application.id, 'rejected')}
                            disabled={processingId === application.id}
                            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 text-sm"
                          >
                            Reject
                          </button>
                          {application.status === 'pending' && (
                            <button
                              onClick={() => handleUpdateStatus(application.id, 'under_review')}
                              disabled={processingId === application.id}
                              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50 text-sm"
                            >
                              Mark Reviewing
                            </button>
                          )}
                        </div>
                      </div>

                      <div className="mt-4 text-sm text-gray-500">
                        Applied {new Date(application.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {decidedApps.length > 0 && (
              <section>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Decided ({decidedApps.length})
                </h2>
                <div className="space-y-4">
                  {decidedApps.map(application => (
                    <div key={application.id} className="bg-white rounded-lg shadow-sm p-6 opacity-75">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="flex items-center space-x-3 mb-2">
                            <Avatar 
                              src={application.applicant?.profile?.avatar_url} 
                              name={application.applicant?.profile?.full_name || application.applicant?.email || '?'} 
                              size="md" 
                            />
                            <div>
                              <Link
                                to={`/users/${application.applicant_id}`}
                                className="text-lg font-semibold text-gray-900 hover:text-indigo-600"
                              >
                                {application.applicant?.profile?.full_name ||
                                 application.applicant?.email ||
                                 `User #${application.applicant_id}`}
                              </Link>
                              <span className={`ml-2 px-2 py-1 text-xs rounded-full ${statusColors[application.status]}`}>
                                {application.status.replace('_', ' ')}
                              </span>
                            </div>
                          </div>
                          {application.proposed_role && (
                            <p className="text-sm text-gray-600 ml-13">Role: {application.proposed_role}</p>
                          )}
                        </div>
                        <span className="text-sm text-gray-500">
                          {new Date(application.updated_at).toLocaleDateString()}
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
