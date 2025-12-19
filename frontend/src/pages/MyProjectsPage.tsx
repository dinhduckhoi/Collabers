import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { projectsApi } from '../api/client';
import { Project } from '../types';

const statusColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  open: 'bg-green-100 text-green-800',
  in_progress: 'bg-blue-100 text-blue-800',
  filled: 'bg-purple-100 text-purple-800',
  completed: 'bg-indigo-100 text-indigo-800',
  cancelled: 'bg-red-100 text-red-800',
};

export function MyProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const data = await projectsApi.getMyProjects();
        setProjects(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load projects');
      } finally {
        setLoading(false);
      }
    };
    fetchProjects();
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
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">My Projects</h1>
          <Link
            to="/projects/new"
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
          >
            New Project
          </Link>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {projects.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
            <p className="text-gray-600 mb-4">Create your first project to start finding collaborators.</p>
            <Link
              to="/projects/new"
              className="inline-block bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
            >
              Post a Project
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {projects.map(project => (
              <div key={project.id} className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center space-x-2 mb-2">
                      <Link
                        to={`/projects/${project.id}`}
                        className="text-xl font-semibold text-gray-900 hover:text-indigo-600"
                      >
                        {project.title}
                      </Link>
                      <span className={`px-2 py-1 text-xs rounded-full ${statusColors[project.status]}`}>
                        {project.status}
                      </span>
                    </div>
                    <p className="text-gray-600 line-clamp-2">{project.description}</p>
                  </div>
                  <div className="flex space-x-2">
                    <Link
                      to={`/applications/project/${project.id}`}
                      className="text-sm text-indigo-600 hover:underline"
                    >
                      Applications ({project.application_count || 0})
                    </Link>
                    <Link
                      to={`/projects/${project.id}/edit`}
                      className="text-sm text-gray-600 hover:underline"
                    >
                      Edit
                    </Link>
                  </div>
                </div>
                <div className="mt-4 flex items-center text-sm text-gray-500 space-x-4">
                  <span>{project.commitment_hours}</span>
                  <span>•</span>
                  <span>{project.views_count} views</span>
                  <span>•</span>
                  <span>Created {new Date(project.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
