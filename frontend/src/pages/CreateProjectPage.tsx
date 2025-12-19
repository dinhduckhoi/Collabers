import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { projectsApi } from '../api/client';
import { useAuth } from '../hooks/useAuth';

const CATEGORY_OPTIONS = [
  { value: 'coursework', label: 'Coursework' },
  { value: 'hackathon', label: 'Hackathon' },
  { value: 'startup', label: 'Startup' },
  { value: 'learning', label: 'Learning' },
  { value: 'open_source', label: 'Open Source' },
];

const DURATION_OPTIONS = [
  { value: 'less_than_1_month', label: '< 1 month' },
  { value: '1_to_3_months', label: '1-3 months' },
  { value: '3_to_6_months', label: '3-6 months' },
  { value: 'ongoing', label: 'Ongoing' },
];

const COMMITMENT_OPTIONS = [
  '< 5 hrs/week',
  '5-10 hrs/week',
  '10-20 hrs/week',
  '20+ hrs/week',
];

const ROLE_OPTIONS = [
  'Frontend', 'Backend', 'Full-stack', 'Mobile', 'ML/AI', 'Data', 'DevOps',
  'Designer', 'PM', 'Writer', 'Other'
];

export function CreateProjectPage() {
  const { user, profile } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [detailedDescription, setDetailedDescription] = useState('');
  const [category, setCategory] = useState('');
  const [techStack, setTechStack] = useState('');
  const [desiredRoles, setDesiredRoles] = useState<string[]>([]);
  const [commitmentHours, setCommitmentHours] = useState('');
  const [duration, setDuration] = useState('');
  const [teamSizeNeeded, setTeamSizeNeeded] = useState('1');
  const [visibility, setVisibility] = useState('public');

  const toggleRole = (role: string) => {
    if (desiredRoles.includes(role)) {
      setDesiredRoles(desiredRoles.filter(r => r !== role));
    } else {
      setDesiredRoles([...desiredRoles, role]);
    }
  };

  const handleSubmit = async (e: React.FormEvent, asDraft: boolean = false) => {
    e.preventDefault();
    setError('');

    if (!title.trim()) {
      setError('Title is required');
      return;
    }
    if (!description.trim()) {
      setError('Description is required');
      return;
    }
    if (!category) {
      setError('Category is required');
      return;
    }
    if (desiredRoles.length === 0) {
      setError('Please select at least one role');
      return;
    }
    if (!commitmentHours) {
      setError('Commitment hours is required');
      return;
    }
    if (!duration) {
      setError('Duration is required');
      return;
    }

    setLoading(true);

    try {
      const project = await projectsApi.createProject({
        title,
        description,
        detailed_description: detailedDescription || undefined,
        category,
        tech_stack: techStack.split(',').map(t => t.trim()).filter(t => t),
        roles_needed: desiredRoles,
        commitment_hours: commitmentHours,
        duration,
        team_size: parseInt(teamSizeNeeded),
        visibility,
        status: asDraft ? 'draft' : 'open',
      });

      navigate(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  if (!user?.email_verified) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Email Verification Required</h2>
          <p className="text-gray-600 mb-4">Please verify your email to post projects.</p>
          <a href="/verify-email" className="text-indigo-600 hover:underline">Verify Email</a>
        </div>
      </div>
    );
  }

  if (!profile || !profile.full_name || profile.skills.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Complete Your Profile</h2>
          <p className="text-gray-600 mb-4">
            Please add a display name and at least one skill to your profile before posting.
          </p>
          <a href="/profile" className="text-indigo-600 hover:underline">Edit Profile</a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-sm p-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">Post a New Project</h1>

          <form onSubmit={(e) => handleSubmit(e, false)} className="space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Project Title *
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={100}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="My Awesome Project"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Short Description * (max 500 chars)
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                maxLength={500}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="A brief description that appears in project listings"
              />
              <p className="text-sm text-gray-500 mt-1">{description.length}/500</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Detailed Description
              </label>
              <textarea
                value={detailedDescription}
                onChange={(e) => setDetailedDescription(e.target.value)}
                rows={6}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="More details about your project, goals, current progress..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category *
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">Select a category</option>
                {CATEGORY_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tech Stack (comma separated)
              </label>
              <input
                type="text"
                value={techStack}
                onChange={(e) => setTechStack(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="React, Node.js, PostgreSQL"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Roles Needed * (select at least one)
              </label>
              <div className="flex flex-wrap gap-2">
                {ROLE_OPTIONS.map(role => (
                  <button
                    key={role}
                    type="button"
                    onClick={() => toggleRole(role)}
                    className={`px-3 py-1 rounded-full text-sm ${
                      desiredRoles.includes(role)
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {role}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Commitment *
                </label>
                <select
                  value={commitmentHours}
                  onChange={(e) => setCommitmentHours(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="">Select...</option>
                  {COMMITMENT_OPTIONS.map(opt => (
                    <option key={opt} value={opt}>{opt}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Duration *
                </label>
                <select
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="">Select...</option>
                  {DURATION_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Team Size Needed
                </label>
                <input
                  type="number"
                  value={teamSizeNeeded}
                  onChange={(e) => setTeamSizeNeeded(e.target.value)}
                  min="1"
                  max="20"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Visibility
                </label>
                <select
                  value={visibility}
                  onChange={(e) => setVisibility(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="public">Public</option>
                  <option value="unlisted">Unlisted</option>
                </select>
              </div>
            </div>

            <div className="flex space-x-4">
              <button
                type="button"
                onClick={(e) => handleSubmit(e, true)}
                disabled={loading}
                className="flex-1 py-3 px-4 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                Save as Draft
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 py-3 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
              >
                {loading ? 'Publishing...' : 'Publish Project'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
