import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { authApi } from '@/api';
import {
  LayoutDashboard, Database, MessageSquare, BarChart3,
  FlaskConical, LogOut, Brain, ChevronRight, User
} from 'lucide-react';

const NAV_ITEMS = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/knowledge-bases', icon: Database, label: 'Knowledge Bases' },
  { to: '/chat', icon: MessageSquare, label: 'Chat' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/evaluation', icon: FlaskConical, label: 'Evaluation' },
];

export default function AppLayout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try { await authApi.logout(); } catch { /* stateless JWT — ignore logout API errors */ }
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* ─── Sidebar ─── */}
      <aside className="w-64 flex-shrink-0 flex flex-col glass border-r border-[hsl(var(--border)/0.5)]">
        {/* Logo */}
        <div className="p-6 border-b border-[hsl(var(--border)/0.5)]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl gradient-primary flex items-center justify-center shadow-lg">
              <Brain size={18} className="text-white" />
            </div>
            <div>
              <h1 className="font-bold text-[hsl(var(--text))] text-base leading-none">KnowledgeGPT</h1>
              <p className="text-[hsl(var(--text-muted))] text-xs mt-0.5">Multi-Agent RAG</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-1">
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group ${
                  isActive
                    ? 'bg-[hsl(var(--primary)/0.15)] text-[hsl(var(--primary))] border border-[hsl(var(--primary)/0.3)]'
                    : 'text-[hsl(var(--text-muted))] hover:text-[hsl(var(--text))] hover:bg-[hsl(var(--surface-elevated))]'
                }`
              }
            >
              <Icon size={16} className="flex-shrink-0" />
              <span className="flex-1">{label}</span>
              <ChevronRight size={12} className="opacity-0 group-hover:opacity-50 transition-opacity" />
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="p-3 border-t border-[hsl(var(--border)/0.5)]">
          <div className="flex items-center gap-3 px-3 py-2 rounded-xl glass-elevated">
            <div className="w-8 h-8 rounded-full gradient-primary flex items-center justify-center flex-shrink-0">
              <User size={14} className="text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-[hsl(var(--text))] truncate">{user?.name}</p>
              <p className="text-xs text-[hsl(var(--text-muted))] truncate">{user?.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 rounded-lg text-[hsl(var(--text-muted))] hover:text-[hsl(var(--error))] hover:bg-[hsl(var(--error)/0.1)] transition-all"
              title="Logout"
            >
              <LogOut size={14} />
            </button>
          </div>
        </div>
      </aside>

      {/* ─── Main ─── */}
      <main className="flex-1 overflow-auto bg-[hsl(var(--background))]">
        <Outlet />
      </main>
    </div>
  );
}
