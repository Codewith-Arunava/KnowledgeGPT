import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { authApi } from '@/api';
import { useAuthStore } from '@/stores/authStore';
import { Brain, Mail, Lock, User, Eye, EyeOff, ArrowRight, Loader2 } from 'lucide-react';
import type { AxiosError } from 'axios';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');

  const registerMutation = useMutation({
    mutationFn: () => authApi.register({ name, email, password }),
    onSuccess: ({ data }) => {
      setAuth(data.user, data.access_token, data.refresh_token);
      navigate('/dashboard');
    },
    onError: (err: AxiosError<{ detail: string }>) => {
      setError(err.response?.data?.detail || 'Registration failed');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    registerMutation.mutate();
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-[hsl(var(--background))]">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-[hsl(var(--accent)/0.15)] rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-[hsl(var(--primary)/0.1)] rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md p-6 animate-fade-in">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl gradient-primary flex items-center justify-center shadow-2xl mb-4">
            <Brain size={28} className="text-white" />
          </div>
          <h1 className="text-3xl font-bold gradient-text mb-1">KnowledgeGPT</h1>
          <p className="text-[hsl(var(--text-muted))] text-sm">Multi-Agent RAG Platform</p>
        </div>

        <div className="glass rounded-2xl p-8 shadow-2xl">
          <h2 className="text-xl font-semibold text-[hsl(var(--text))] mb-1">Create account</h2>
          <p className="text-[hsl(var(--text-muted))] text-sm mb-6">Start building your knowledge base</p>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-[hsl(var(--error)/0.1)] border border-[hsl(var(--error)/0.3)] text-[hsl(var(--error))] text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-medium text-[hsl(var(--text-muted))] uppercase tracking-wide mb-1.5 block">Full Name</label>
              <div className="relative">
                <User size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[hsl(var(--text-muted))]" />
                <input
                  id="reg-name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  placeholder="John Doe"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[hsl(var(--surface-elevated))] border border-[hsl(var(--border))] text-[hsl(var(--text))] text-sm placeholder:text-[hsl(var(--text-muted))] focus:outline-none focus:border-[hsl(var(--primary))] transition-all"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-[hsl(var(--text-muted))] uppercase tracking-wide mb-1.5 block">Email</label>
              <div className="relative">
                <Mail size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[hsl(var(--text-muted))]" />
                <input
                  id="reg-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="you@example.com"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[hsl(var(--surface-elevated))] border border-[hsl(var(--border))] text-[hsl(var(--text))] text-sm placeholder:text-[hsl(var(--text-muted))] focus:outline-none focus:border-[hsl(var(--primary))] transition-all"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-[hsl(var(--text-muted))] uppercase tracking-wide mb-1.5 block">Password</label>
              <div className="relative">
                <Lock size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[hsl(var(--text-muted))]" />
                <input
                  id="reg-password"
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  placeholder="Min. 8 characters"
                  className="w-full pl-10 pr-10 py-2.5 rounded-xl bg-[hsl(var(--surface-elevated))] border border-[hsl(var(--border))] text-[hsl(var(--text))] text-sm placeholder:text-[hsl(var(--text-muted))] focus:outline-none focus:border-[hsl(var(--primary))] transition-all"
                />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[hsl(var(--text-muted))]">
                  {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            <button
              id="reg-submit"
              type="submit"
              disabled={registerMutation.isPending}
              className="w-full py-2.5 rounded-xl gradient-primary text-white font-semibold text-sm flex items-center justify-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-50 shadow-lg"
            >
              {registerMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : <><span>Create Account</span><ArrowRight size={16} /></>}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-[hsl(var(--text-muted))]">
            Already have an account?{' '}
            <Link to="/login" className="text-[hsl(var(--primary))] hover:underline font-medium">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
