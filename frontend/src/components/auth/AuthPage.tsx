import { useState } from 'react';
import { useAuthStore } from '@/stores/authStore';

type Mode = 'login' | 'register';

export function AuthPage() {
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const login = useAuthStore((s) => s.login);
  const register = useAuthStore((s) => s.register);
  const isLoading = useAuthStore((s) => s.isLoading);
  const error = useAuthStore((s) => s.error);
  const clearError = useAuthStore((s) => s.clearError);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (mode === 'login') {
      login(email, password);
    } else {
      register(email, password);
    }
  };

  const toggleMode = () => {
    clearError();
    setMode(mode === 'login' ? 'register' : 'login');
  };

  return (
    <div className="h-screen w-screen flex items-center justify-center" style={{ backgroundColor: '#0f0f0f' }}>
      <div className="w-full max-w-sm">
        {/* Branding */}
        <div className="text-center mb-8">
          <h1
            className="text-2xl font-bold tracking-widest"
            style={{ fontFamily: "'JetBrains Mono', monospace", color: '#e2e8f0' }}
          >
            POLYTRADE
          </h1>
          <p className="text-xs mt-1" style={{ color: '#64748b' }}>
            Autonomous Trading Terminal
          </p>
        </div>

        {/* Auth Panel */}
        <div
          className="p-6 border"
          style={{
            backgroundColor: '#1a1a2e',
            borderColor: '#1e293b',
            borderRadius: '2px',
          }}
        >
          {/* Mode Toggle */}
          <div className="flex mb-6" style={{ borderBottom: '1px solid #1e293b' }}>
            <button
              type="button"
              onClick={() => { clearError(); setMode('login'); }}
              className="flex-1 pb-2 text-xs font-medium tracking-wide transition-colors"
              style={{
                color: mode === 'login' ? '#3b82f6' : '#64748b',
                borderBottom: mode === 'login' ? '2px solid #3b82f6' : '2px solid transparent',
              }}
            >
              LOGIN
            </button>
            <button
              type="button"
              onClick={() => { clearError(); setMode('register'); }}
              className="flex-1 pb-2 text-xs font-medium tracking-wide transition-colors"
              style={{
                color: mode === 'register' ? '#3b82f6' : '#64748b',
                borderBottom: mode === 'register' ? '2px solid #3b82f6' : '2px solid transparent',
              }}
            >
              REGISTER
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email */}
            <div>
              <label className="block text-xxs font-medium mb-1" style={{ color: '#94a3b8' }}>
                EMAIL
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                placeholder="trader@example.com"
                className="w-full px-3 py-2 text-sm outline-none transition-colors"
                style={{
                  backgroundColor: '#0f0f0f',
                  color: '#e2e8f0',
                  border: '1px solid #1e293b',
                  borderRadius: '2px',
                  fontFamily: "'Inter', system-ui, sans-serif",
                }}
                onFocus={(e) => { e.currentTarget.style.borderColor = '#3b82f6'; }}
                onBlur={(e) => { e.currentTarget.style.borderColor = '#1e293b'; }}
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-xxs font-medium mb-1" style={{ color: '#94a3b8' }}>
                PASSWORD
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                placeholder="Enter password"
                className="w-full px-3 py-2 text-sm outline-none transition-colors"
                style={{
                  backgroundColor: '#0f0f0f',
                  color: '#e2e8f0',
                  border: '1px solid #1e293b',
                  borderRadius: '2px',
                  fontFamily: "'Inter', system-ui, sans-serif",
                }}
                onFocus={(e) => { e.currentTarget.style.borderColor = '#3b82f6'; }}
                onBlur={(e) => { e.currentTarget.style.borderColor = '#1e293b'; }}
              />
            </div>

            {/* Error */}
            {error && (
              <div
                className="px-3 py-2 text-xs"
                style={{
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#ef4444',
                  borderRadius: '2px',
                }}
              >
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2 text-xs font-semibold tracking-wide transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              style={{
                backgroundColor: '#3b82f6',
                color: '#ffffff',
                border: '1px solid #3b82f6',
                borderRadius: '2px',
              }}
            >
              {isLoading
                ? 'CONNECTING...'
                : mode === 'login'
                  ? 'LOGIN'
                  : 'CREATE ACCOUNT'}
            </button>
          </form>

          {/* Toggle link */}
          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={toggleMode}
              className="text-xxs transition-colors"
              style={{ color: '#64748b' }}
              onMouseEnter={(e) => { e.currentTarget.style.color = '#3b82f6'; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = '#64748b'; }}
            >
              {mode === 'login'
                ? 'No account? Register'
                : 'Already have an account? Login'}
            </button>
          </div>
        </div>

        {/* Version */}
        <div className="text-center mt-4">
          <span className="text-xxs" style={{ color: '#64748b', fontFamily: "'JetBrains Mono', monospace" }}>
            v0.1.0
          </span>
        </div>
      </div>
    </div>
  );
}
