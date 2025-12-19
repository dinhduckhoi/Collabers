import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { authApi } from '../api/client';
import { useNavigate, useSearchParams } from 'react-router-dom';

export function VerifyEmailPage() {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [otp, setOtp] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [sendingEmail, setSendingEmail] = useState(false);
  const [devOtp, setDevOtp] = useState('');

  // Check for link verification status from redirect
  const status = searchParams.get('status');
  const linkMessage = searchParams.get('message');

  useEffect(() => {
    if (status === 'success') {
      setMessage('Email verified successfully! Redirecting...');
      refreshUser().then(() => navigate('/projects'));
    } else if (status === 'error' && linkMessage) {
      setError(decodeURIComponent(linkMessage));
    }
  }, [status, linkMessage, refreshUser, navigate]);

  useEffect(() => {
    if (user?.email_verified) {
      navigate('/projects');
    }
  }, [user, navigate]);

  const handleSendEmail = async () => {
    setSendingEmail(true);
    setError('');
    setMessage('');
    setDevOtp('');
    try {
      const result = await authApi.sendVerificationEmail();
      setMessage('Verification email sent! Check your inbox.');
      // In dev mode, show the OTP
      if (result.dev_otp) {
        setDevOtp(result.dev_otp);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send email');
    } finally {
      setSendingEmail(false);
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await authApi.verifyEmail(otp);
      setMessage('Email verified successfully!');
      await refreshUser();
      navigate('/projects');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-indigo-100 mb-4">
            <svg className="h-6 w-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h2 className="text-3xl font-bold text-gray-900">Verify Your Email</h2>
          <p className="mt-2 text-gray-600">
            Enter the 6-digit code sent to your email to verify your account.
          </p>
        </div>

        {message && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded text-sm">
            {message}
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Dev mode OTP display */}
        {devOtp && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm font-medium text-yellow-800 mb-1">Development Mode</p>
            <p className="text-sm text-yellow-700">
              OTP: <code className="bg-yellow-100 px-2 py-1 rounded font-mono text-lg">{devOtp}</code>
            </p>
          </div>
        )}

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <form onSubmit={handleVerify} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Verification Code
              </label>
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                className="w-full px-3 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-center text-2xl tracking-widest font-mono"
                placeholder="000000"
              />
              <p className="mt-1 text-xs text-gray-500 text-center">
                Enter the 6-digit code from your email
              </p>
            </div>
            <button
              type="submit"
              disabled={loading || otp.length !== 6}
              className="w-full py-2 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? 'Verifying...' : 'Verify Email'}
            </button>
          </form>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Didn't receive the code?</span>
            </div>
          </div>

          <button
            onClick={handleSendEmail}
            disabled={sendingEmail}
            className="w-full py-2 px-4 border border-indigo-600 text-indigo-600 rounded-md hover:bg-indigo-50 disabled:opacity-50"
          >
            {sendingEmail ? 'Sending...' : 'Resend Verification Email'}
          </button>
        </div>
      </div>
    </div>
  );
}
