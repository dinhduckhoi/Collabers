import { Link } from 'react-router-dom';
import { Project } from '../types';

interface ProjectCardProps {
  project: Project;
}

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

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Link
      to={`/projects/${project.id}`}
      className="block bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow p-6"
    >
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-semibold text-gray-900 line-clamp-1">{project.title}</h3>
        <span className={`px-2 py-1 text-xs rounded-full ${categoryColors[project.category] || 'bg-gray-100 text-gray-800'}`}>
          {project.category}
        </span>
      </div>
      <p className="text-gray-600 text-sm mb-4 line-clamp-2">{project.description}</p>
      <div className="flex flex-wrap gap-2 mb-4">
        {project.tech_stack?.slice(0, 4).map((tech) => (
          <span key={tech} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
            {tech}
          </span>
        ))}
        {project.tech_stack && project.tech_stack.length > 4 && (
          <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
            +{project.tech_stack.length - 4}
          </span>
        )}
      </div>
      <div className="flex items-center justify-between text-sm text-gray-500">
        <div className="flex items-center space-x-4">
          <span>{project.commitment_hours}</span>
          <span>{durationLabels[project.duration] || project.duration}</span>
        </div>
        <div className="flex items-center space-x-2">
          <span>{project.application_count || 0} applicants</span>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {project.creator?.profile && (
            <>
              <div className="w-6 h-6 bg-indigo-100 rounded-full flex items-center justify-center text-xs">
                {project.creator.profile.full_name?.[0]?.toUpperCase() || '?'}
              </div>
              <span className="text-sm text-gray-600">{project.creator.profile.full_name}</span>
            </>
          )}
        </div>
        <div className="text-xs text-gray-400">
          Looking for: {project.roles_needed?.slice(0, 2).join(', ')}
          {project.roles_needed && project.roles_needed.length > 2 && ` +${project.roles_needed.length - 2}`}
        </div>
      </div>
    </Link>
  );
}
