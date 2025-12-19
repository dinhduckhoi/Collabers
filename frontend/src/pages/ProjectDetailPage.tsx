import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { projectsApi, applicationsApi } from '../api/client';
import { Project } from '../types';
import { useAuth } from '../hooks/useAuth';

const categoryColors: Record<string, string> = {
  coursework: 'bg-blue-100 text-blue-800',
  hackathon: 'bg-purple-100 text-purple-800',
  startup: 'bg-green-100 text-green-800',
  learning: 'bg-yellow-100 text-yellow-800',
  open_source: 'bg-orange-100 text-orange-800',
};

const durationLabels: Record<string, string> = {
  less_than_1_month: '< 1 month',
  '1_to_3_months': '1-3 months',
  '3_to_6_months': '3-6 months',
  ongoing: 'Ongoing',
};

const statusColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  open: 'bg-green-100 text-green-800',
  in_progress: 'bg-blue-100 text-blue-800',
  filled: 'bg-purple-100 text-purple-800',
  completed: 'bg-indigo-100 text-indigo-800',
  cancelled: 'bg-red-100 text-red-800',
};

export function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [selectedRole, setSelectedRole] = useState('');
  const [coverMessage, setCoverMessage] = useState('');
  const [applying, setApplying] = useState(false);
  const [applyError, setApplyError] = useState('');

  useEffect(() => {
    const fetchProject = async () => {
      if (!id) return;
      try {
        const data = await projectsApi.getProject(parseInt(id));
        setProject(data);
        if (data.roles_needed && data.roles_needed.length > 0) {
          setSelectedRole(data.roles_needed[0]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load project');
      } finally {
        setLoading(false);
      }
    };
    fetchProject();
  }, [id]);

  const handleApply = async () => {
    if (!project) return;
    if (coverMessage.length < 50) {
      setApplyError('Cover message must be at least 50 characters');
      return;
    }

    setApplying(true);
    setApplyError('');
    try {
      await applicationsApi.createApplication({
        project_id: project.id,
        proposed_role: selectedRole,
        cover_letter: coverMessage,
      });
      setShowApplyModal(false);
      navigate('/applications');
    } catch (err) {
      setApplyError(err instanceof Error ? err.message : 'Failed to apply');
    } finally {
      setApplying(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Project Not Found</h2>
          <p className="text-gray-600 mb-4">{error || 'The project you are looking for does not exist.'}</p>
          <Link to="/projects" className="text-indigo-600 hover:underline">
            Browse all projects
          </Link>
        </div>
      </div>
    );
  }

  const isCreator = user?.id === project.creator_id;
  const canApply = user && !isCreator && project.status === 'open';

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="p-6 border-b">
            <div className="flex justify-between items-start mb-4">
              <div>
                <div className="flex items-center space-x-3 mb-2">
                  <span className={`px-3 py-1 text-sm rounded-full ${categoryColors[project.category] || 'bg-gray-100'}`}>
                    {project.category}
                  </span>
                  <span className={`px-3 py-1 text-sm rounded-full ${statusColors[project.status] || 'bg-gray-100'}`}>
                    {project.status}
                  </span>
                </div>
                <h1 className="text-3xl font-bold text-gray-900">{project.title}</h1>
              </div>
              {isCreator && (
                <Link
                  to={`/projects/${project.id}/edit`}
                  className="text-indigo-600 hover:underline"
                >
                  Edit Project
                </Link>
              )}
            </div>

            <p className="text-gray-700 text-lg mb-4">{project.description}</p>

            {project.detailed_description && (
              <div className="prose max-w-none mb-4">
                <p className="text-gray-600 whitespace-pre-wrap">{project.detailed_description}</p>
              </div>
            )}

            <div className="flex items-center space-x-6 text-sm text-gray-500 mb-4">
              <span>{project.commitment_hours}</span>
              <span>{durationLabels[project.duration] || project.duration}</span>
              <span>Looking for {project.team_size} people</span>
              <span>{project.views_count} views</span>
            </div>

            {canApply && (
              <button
                onClick={() => setShowApplyModal(true)}
                className="w-full md:w-auto bg-indigo-600 text-white px-6 py-3 rounded-md hover:bg-indigo-700 font-medium"
              >
                Apply to This Project
              </button>
            )}
          </div>

          <div className="p-6 border-b">
            <h2 className="text-lg font-semibold mb-3">Tech Stack</h2>
            <div className="flex flex-wrap gap-2">
              {project.tech_stack?.map(tech => (
                <span key={tech} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                  {tech}
                </span>
              ))}
            </div>
          </div>

          <div className="p-6 border-b">
            <h2 className="text-lg font-semibold mb-3">Roles Needed</h2>
            <div className="flex flex-wrap gap-2">
              {project.roles_needed?.map(role => (
                <span key={role} className="px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full text-sm">
                  {role}
                </span>
              ))}
            </div>
          </div>

          {project.creator?.profile && (
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold mb-3">Project Creator</h2>
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center text-lg">
                  {project.creator.profile.full_name?.[0]?.toUpperCase() || '?'}
                </div>
                <div>
                  <Link
                    to={`/users/${project.creator_id}`}
                    className="font-medium text-gray-900 hover:text-indigo-600"
                  >
                    {project.creator.profile.full_name}
                  </Link>
                  {project.creator.profile.headline && (
                    <p className="text-sm text-gray-500">{project.creator.profile.headline}</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {project.creator?.profile && (
            <div className="p-6">
              <p className="text-sm text-gray-500">
                Posted {new Date(project.created_at).toLocaleDateString()}
              </p>
            </div>
          )}
        </div>
      </div>

      {showApplyModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-lg w-full p-6">
            <h2 className="text-xl font-bold mb-4">Apply to {project.title}</h2>
            
            {applyError && (
              <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded mb-4">
                {applyError}
              </div>
            )}

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Role you're applying for
              </label>
              <select
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              >
                {project.roles_needed?.map(role => (
                  <option key={role} value={role}>{role}</option>
                ))}
              </select>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Why do you want to join? (min 50 characters)
              </label>
              <textarea
                value={coverMessage}
                onChange={(e) => setCoverMessage(e.target.value)}
                rows={5}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Tell the project creator why you're interested and what you'd bring to the team..."
              />
              <p className="text-sm text-gray-500 mt-1">{coverMessage.length} / 50 characters minimum</p>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowApplyModal(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
              >
                Cancel
              </button>
              <button
                onClick={handleApply}
                disabled={applying || coverMessage.length < 50}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
              >
                {applying ? 'Submitting...' : 'Submit Application'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
