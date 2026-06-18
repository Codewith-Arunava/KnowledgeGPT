import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/api';
import type { AnalyticsSummary } from '@/types';
import {
  Database, FileText, MessageSquare, Search, TrendingUp, Shield,
  Coins, Clock, Zap, BarChart2
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, Legend
} from 'recharts';
import { useAuthStore } from '@/stores/authStore';

const STAT_CARDS = (data: AnalyticsSummary) => [
  { label: 'Knowledge Bases', value: data.total_knowledge_bases, icon: Database, color: 'var(--primary)', bg: 'hsl(var(--primary)/0.1)' },
  { label: 'Documents', value: data.total_documents, icon: FileText, color: 'var(--secondary)', bg: 'hsl(var(--secondary)/0.1)' },
  { label: 'Conversations', value: data.total_conversations, icon: MessageSquare, color: 'var(--accent)', bg: 'hsl(var(--accent)/0.1)' },
  { label: 'Total Queries', value: data.total_queries, icon: Search, color: 'var(--success)', bg: 'hsl(var(--success)/0.1)' },
  { label: 'Avg Retrieval Score', value: `${(data.avg_retrieval_score * 100).toFixed(1)}%`, icon: TrendingUp, color: 'var(--primary)', bg: 'hsl(var(--primary)/0.1)' },
  { label: 'Hallucination Score', value: `${(data.avg_hallucination_score * 100).toFixed(1)}%`, icon: Shield, color: 'var(--warning)', bg: 'hsl(var(--warning)/0.1)' },
  { label: 'Est. API Cost', value: `$${data.estimated_cost_usd.toFixed(4)}`, icon: Coins, color: 'var(--success)', bg: 'hsl(var(--success)/0.1)' },
  { label: 'Avg Response', value: `${data.avg_response_time_ms.toFixed(0)}ms`, icon: Clock, color: 'var(--secondary)', bg: 'hsl(var(--secondary)/0.1)' },
];

const COLORS = ['hsl(262 83% 68%)', 'hsl(197 71% 58%)', 'hsl(316 70% 60%)', 'hsl(142 71% 45%)'];

const CustomTooltip = ({ active, payload, label }: {
  active?: boolean;
  payload?: { name: string; value: number | string; color: string }[];
  label?: string;
}) => {
  if (active && payload?.length) {
    return (
      <div className="glass rounded-xl p-3 shadow-xl border border-[hsl(var(--border))]">
        <p className="text-xs text-[hsl(var(--text-muted))] mb-1">{label}</p>
        {payload.map((p, i: number) => (
          <p key={i} className="text-sm font-semibold" style={{ color: p.color }}>
            {p.name}: {typeof p.value === 'number' ? p.value.toLocaleString() : p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);

  const { data, isLoading } = useQuery({
    queryKey: ['analytics'],
    queryFn: () => analyticsApi.get(30).then((r) => r.data as AnalyticsSummary),
  });

  if (isLoading || !data) {
    return (
      <div className="p-8">
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="skeleton h-28 rounded-2xl" />
          ))}
        </div>
        <div className="grid grid-cols-2 gap-4">
          {[...Array(2)].map((_, i) => <div key={i} className="skeleton h-64 rounded-2xl" />)}
        </div>
      </div>
    );
  }

  const modelPieData = Object.entries(data.model_usage).map(([name, value]) => ({ name, value }));

  return (
    <div className="p-8 space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[hsl(var(--text))]">
          Welcome back, <span className="gradient-text">{user?.name?.split(' ')[0]}</span> 👋
        </h1>
        <p className="text-[hsl(var(--text-muted))] text-sm mt-1">Here's your RAG platform overview</p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {STAT_CARDS(data).map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className="glass rounded-2xl p-5 hover:glass-elevated transition-all duration-300 group cursor-default">
            <div className="flex items-start justify-between mb-3">
              <div className="p-2.5 rounded-xl" style={{ background: bg }}>
                <Icon size={18} style={{ color: `hsl(${color})` }} />
              </div>
              <Zap size={12} className="text-[hsl(var(--text-muted))] opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <p className="text-2xl font-bold text-[hsl(var(--text))] mb-1">{value}</p>
            <p className="text-xs text-[hsl(var(--text-muted))]">{label}</p>
          </div>
        ))}
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Daily Queries */}
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <BarChart2 size={16} className="text-[hsl(var(--primary))]" />
            <h2 className="text-sm font-semibold text-[hsl(var(--text))]">Daily Queries & Uploads</h2>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={data.daily_stats}>
              <defs>
                <linearGradient id="gradQueries" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(262 83% 68%)" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="hsl(262 83% 68%)" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradUploads" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(197 71% 58%)" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="hsl(197 71% 58%)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.4} />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'hsl(var(--text-muted))' }} tickFormatter={(v) => v.slice(5)} />
              <YAxis tick={{ fontSize: 10, fill: 'hsl(var(--text-muted))' }} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="queries" name="Queries" stroke="hsl(262 83% 68%)" fill="url(#gradQueries)" strokeWidth={2} />
              <Area type="monotone" dataKey="uploads" name="Uploads" stroke="hsl(197 71% 58%)" fill="url(#gradUploads)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Token Usage */}
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Coins size={16} className="text-[hsl(var(--secondary))]" />
            <h2 className="text-sm font-semibold text-[hsl(var(--text))]">Token Usage Trend</h2>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data.daily_stats}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.4} />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'hsl(var(--text-muted))' }} tickFormatter={(v) => v.slice(5)} />
              <YAxis tick={{ fontSize: 10, fill: 'hsl(var(--text-muted))' }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="tokens_used" name="Tokens" fill="hsl(197 71% 58%)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Response Time */}
        <div className="glass rounded-2xl p-6 xl:col-span-2">
          <div className="flex items-center gap-2 mb-4">
            <Clock size={16} className="text-[hsl(var(--accent))]" />
            <h2 className="text-sm font-semibold text-[hsl(var(--text))]">Response Time Trend (ms)</h2>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={data.daily_stats}>
              <defs>
                <linearGradient id="gradTime" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(316 70% 60%)" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="hsl(316 70% 60%)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.4} />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'hsl(var(--text-muted))' }} tickFormatter={(v) => v.slice(5)} />
              <YAxis tick={{ fontSize: 10, fill: 'hsl(var(--text-muted))' }} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="avg_response_time_ms" name="Response Time" stroke="hsl(316 70% 60%)" fill="url(#gradTime)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Model Usage Pie */}
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <BarChart2 size={16} className="text-[hsl(var(--primary))]" />
            <h2 className="text-sm font-semibold text-[hsl(var(--text))]">Model Usage</h2>
          </div>
          {modelPieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie data={modelPieData} cx="50%" cy="50%" innerRadius={40} outerRadius={70} dataKey="value">
                  {modelPieData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Legend formatter={(v) => <span className="text-xs text-[hsl(var(--text-muted))]">{v}</span>} />
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-40 flex items-center justify-center text-[hsl(var(--text-muted))] text-sm">
              No data yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
