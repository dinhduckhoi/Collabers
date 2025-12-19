import { useState, useEffect } from 'react';
import { projectsApi, ProjectFilters } from '../api/client';
import { Project } from '../types';
import { ProjectCard } from '../components/ProjectCard';
import { Link } from 'react-router-dom';

const CATEGORY_OPTIONS = [
  { value: '', label: 'All Categories' },
  { value: 'coursework', label: 'Coursework' },
  { value: 'hackathon', label: 'Hackathon' },
  { value: 'startup', label: 'Startup' },
  { value: 'learning', label: 'Learning' },
  { value: 'open_source', label: 'Open Source' },
];

const DURATION_OPTIONS = [
  { value: '', label: 'Any Duration' },
  { value: 'less_than_1_month', label: '< 1 month' },
  { value: '1_to_3_months', label: '1-3 months' },
  { value: '3_to_6_months', label: '3-6 months' },
  { value: 'ongoing', label: 'Ongoing' },
];

export function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [duration, setDuration] = useState('');
  const [techStack, setTechStack] = useState('');

  const fetchProjects = async () => {
    setLoading(true);
    setError('');
    try {
      const filters: ProjectFilters = {};
      if (search) filters.search = search;
      if (category) filters.category = category;
      if (duration) filters.duration = duration;
      if (techStack) filters.tech_stack = techStack;

      const data = await projectsApi.getProjects(filters);
      setProjects(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchProjects();
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Browse Projects</h1>
          <Link
            to="/projects/new"
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
          >
            Post a Project
          </Link>
        </div>

        <form onSubmit={handleSearch} className="bg-white p-4 rounded-lg shadow-sm mb-6">
          <div className="grid md:grid-cols-6 gap-4">
            <div className="md:col-span-2">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search projects..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              {CATEGORY_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <select
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              {DURATION_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <input
              type="text"
              value={techStack}
              onChange={(e) => setTechStack(e.target.value)}
              placeholder="Tech (comma sep.)"
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
            <button
              type="submit"
              className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
            >
              Search
            </button>
          </div>
        </form>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-12">
            <h3 className="text-lg font-medium text-gray-900 mb-2">No projects found</h3>
            <p className="text-gray-600">Try adjusting your filters or be the first to post a project!</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map(project => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
