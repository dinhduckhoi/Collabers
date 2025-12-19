import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export function LandingPage() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Find Your Project Partner.
            <br />
            <span className="text-indigo-600">Build Something Together.</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Connect with fellow students for hackathons, coursework, startup ideas, and personal projects.
          </p>
          <div className="flex justify-center space-x-4">
            {user ? (
              <>
                <Link
                  to="/projects"
                  className="bg-indigo-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-indigo-700 transition"
                >
                  Browse Projects
                </Link>
                <Link
                  to="/projects/new"
                  className="bg-white text-indigo-600 px-8 py-3 rounded-lg font-medium border border-indigo-600 hover:bg-indigo-50 transition"
                >
                  Post a Project
                </Link>
              </>
            ) : (
              <>
                <Link
                  to="/register"
                  className="bg-indigo-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-indigo-700 transition"
                >
                  Get Started
                </Link>
                <Link
                  to="/login"
                  className="bg-white text-indigo-600 px-8 py-3 rounded-lg font-medium border border-indigo-600 hover:bg-indigo-50 transition"
                >
                  Login
                </Link>
              </>
            )}
          </div>
        </div>

        <div className="mt-24 grid md:grid-cols-3 gap-8">
          <div className="bg-white p-8 rounded-xl shadow-sm">
            <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-2">Find Projects</h3>
            <p className="text-gray-600">
              Browse projects that match your skills and interests. Filter by tech stack, role, and commitment level.
            </p>
          </div>
          <div className="bg-white p-8 rounded-xl shadow-sm">
            <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-2">Build Your Team</h3>
            <p className="text-gray-600">
              Post your project idea and find skilled collaborators. Review applications and build your dream team.
            </p>
          </div>
          <div className="bg-white p-8 rounded-xl shadow-sm">
            <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-2">Collaborate</h3>
            <p className="text-gray-600">
              Once accepted, team chat unlocks. Coordinate, share ideas, and build something amazing together.
            </p>
          </div>
        </div>

        <div className="mt-24">
          <h2 className="text-3xl font-bold text-center mb-12">Perfect For</h2>
          <div className="grid md:grid-cols-5 gap-4">
            {['Hackathons', 'Coursework', 'Startups', 'Learning Projects', 'Open Source'].map((item) => (
              <div key={item} className="bg-white p-4 rounded-lg text-center shadow-sm">
                <span className="font-medium text-gray-800">{item}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
