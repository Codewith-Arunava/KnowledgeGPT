import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/api';
import type { AnalyticsSummary } from '@/types';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, ComposedChart, Line
} from 'recharts';
import { BarChart3, Zap, Clock, Coins, Users, FileText } from 'lucide-react';

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

export default function AnalyticsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics-full'],
    queryFn: () => analyticsApi.get(30).then((r) => r.data as AnalyticsSummary),
  });

  if (isLoading || !data) {
    return (
      <div className="p-8 space-y-4">
        {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-52 rounded-2xl" />)}
      </div>
    );
  }

  const summaryCards = [
    { label: 'Total Tokens Used', value: data.total_tokens_used.toLocaleString(), icon: Zap, color: 'var(--primary)' },
    { label: 'Avg Response Time', value: `${data.avg_response_time_ms.toFixed(0)}ms`, icon: Clock, color: 'var(--secondary)' },
    { label: 'Estimated API Cost', value: `$${data.estimated_cost_usd.toFixed(4)}`, icon: Coins, color: 'var(--success)' },
    { label: 'Total Documents', value: data.total_documents.toString(), icon: FileText, color: 'var(--accent)' },
  ];

  return (
    <div className="p-8 space-y-6 animate-fade-in">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <BarChart3 size={20} className="text-[hsl(var(--primary))]" />
          <h1 className="text-2xl font-bold text-[hsl(var(--text))]">Analytics</h1>
        </div>
        <p className="text-[hsl(var(--text-muted))] text-sm">Platform usage and performance metrics — last 30 days</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {summaryCards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="glass rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <Icon size={16} style={{ color: `hsl(${color})` }} />
              <span className="text-xs text-[hsl(var(--text-muted))]">{label}</span>
            </div>
            <p className="text-2xl font-bold text-[hsl(var(--text))]">{value}</p>
          </div>
        ))}
      </div>

      {/* Composed Chart: Queries + Response Time */}
      <div className="glass rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 size={15} className="text-[hsl(var(--primary))]" />
          <h2 className="text-sm font-semibold text-[hsl(var(--text))]">Queries vs Response Time</h2>
        </div>
        <ResponsiveContainer width="100%" height={250}>
          <ComposedChart data={data.daily_stats}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.4} />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'hsl(var(--text-muted))' }} tickFormatter={(v) => v.slice(5)} />
            <YAxis yAxisId="left" tick={{ fontSize: 10, fill: 'hsl(var(--text-muted))' }} />
            <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10, fill: 'hsl(var(--text-muted))' }} />
            <Tooltip content={<CustomTooltip />} />
            <Bar yAxisId="left" dataKey="queries" name="Queries" fill="hsl(262 83% 68%)" radius={[4, 4, 0, 0]} fillOpacity={0.8} />
            <Line yAxisId="right" type="monotone" dataKey="avg_response_time_ms" name="Response Time (ms)" stroke="hsl(316 70% 60%)" strokeWidth={2} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Token Usage */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Zap size={15} className="text-[hsl(var(--secondary))]" />
            <h2 className="text-sm font-semibold text-[hsl(var(--text))]">Token Usage Over Time</h2>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={data.daily_stats}>
              <defs>
                <linearGradient id="gradTokens" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(197 71% 58%)" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="hsl(197 71% 58%)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.4} />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'hsl(var(--text-muted))' }} tickFormatter={(v) => v.slice(5)} />
              <YAxis tick={{ fontSize: 10, fill: 'hsl(var(--text-muted))' }} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="tokens_used" name="Tokens" stroke="hsl(197 71% 58%)" fill="url(#gradTokens)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Model Usage Bar Chart */}
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Users size={15} className="text-[hsl(var(--primary))]" />
            <h2 className="text-sm font-semibold text-[hsl(var(--text))]">Model Usage Distribution</h2>
          </div>
          {Object.keys(data.model_usage).length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={Object.entries(data.model_usage).map(([name, count]) => ({ name, count }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.4} />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: 'hsl(var(--text-muted))' }} />
                <YAxis tick={{ fontSize: 10, fill: 'hsl(var(--text-muted))' }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" name="Queries" fill="hsl(262 83% 68%)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-[hsl(var(--text-muted))] text-sm">
              No queries yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
