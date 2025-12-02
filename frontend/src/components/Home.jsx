import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const Home = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-indigo-600">DQTimes</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg transition"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white rounded-lg shadow-xl p-8">
          <h2 className="text-3xl font-bold text-gray-800 mb-4">
            Welcome to DQTimes! 🎉
          </h2>
          <p className="text-gray-600 mb-6">
            You are successfully logged in and authenticated. This is a protected route.
          </p>

          {/* User Info Card */}
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-semibold text-indigo-900 mb-3">Your Account</h3>
            <div className="space-y-2 text-sm">
              <p>
                <span className="font-medium text-gray-700">Email:</span>{' '}
                <span className="text-gray-600">{user?.email}</span>
              </p>
              <p>
                <span className="font-medium text-gray-700">Account ID:</span>{' '}
                <span className="text-gray-600">{user?.id}</span>
              </p>
              <p>
                <span className="font-medium text-gray-700">Status:</span>{' '}
                <span className={user?.is_active ? 'text-green-600' : 'text-red-600'}>
                  {user?.is_active ? 'Active' : 'Inactive'}
                </span>
              </p>
              <p>
                <span className="font-medium text-gray-700">Member Since:</span>{' '}
                <span className="text-gray-600">
                  {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                </span>
              </p>
            </div>
          </div>

          {/* Features Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="border border-gray-200 rounded-lg p-6">
              <h4 className="text-lg font-semibold text-gray-800 mb-2">📊 Time Series Forecasting</h4>
              <p className="text-gray-600 text-sm">
                Use CUDA-accelerated algorithms to predict future values based on historical data.
              </p>
            </div>
            <div className="border border-gray-200 rounded-lg p-6">
              <h4 className="text-lg font-semibold text-gray-800 mb-2">🔒 Secure Authentication</h4>
              <p className="text-gray-600 text-sm">
                Your session is protected with JWT tokens stored securely in localStorage.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
