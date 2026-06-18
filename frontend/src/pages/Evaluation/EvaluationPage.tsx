import { useQuery } from '@tanstack/react-query';
import { evaluationApi } from '@/api';
import type { EvaluationReport } from '@/types';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar
} from 'recharts';
import { FlaskConical, TrendingUp, Shield, Award, Target, Brain, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

function ConfidenceRing({ value, label, color }: { value: number; label: string; color: string }) {
  const r = 30;
  const circ = 2 * Math.PI * r;
  const dash = (value / 100) * circ;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-20 h-20">
        <svg viewBox="0 0 80 80" className="w-full h-full -rotate-90">
          <circle cx="40" cy="40" r={r} stroke="hsl(var(--border))" strokeWidth="6" fill="none" />
          <circle
            cx="40" cy="40" r={r}
            stroke={color} strokeWidth="6" fill="none"
            strokeDasharray={`${dash} ${circ}`}
            strokeLinecap="round"
            style={{ transition: 'stroke-dasharray 1s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-sm font-bold text-[hsl(var(--text))]">{value.toFixed(0)}%</span>
        </div>
      </div>
      <p className="text-xs text-[hsl(var(--text-muted))] text-center">{label}</p>
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }: {
  active?: boolean;
  payload?: { name: string; value: number | string; color: string }[];
  label?: string;
}) => {
  if (active && payload?.length) {
    return (
      <div className="glass rounded-xl p-3 shadow-xl">
        <p className="text-xs text-[hsl(var(--text-muted))] mb-1">{label}</p>
        {payload.map((p, i: number) => (
          <p key={i} className="text-sm font-semibold" style={{ color: p.color }}>
            {p.name}: {p.value}%
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function EvaluationPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['evaluation'],
    queryFn: () => evaluationApi.get(30).then((r) => r.data as EvaluationReport),
  });

  if (isLoading || !data) {
    return (
      <div className="p-8 space-y-4">
        {[...Array(3)].map((_, i) => <div key={i} className="skeleton h-40 rounded-2xl" />)}
      </div>
    );
  }

  const { context_precision, retrieval_accuracy_trend, hallucination_breakdown, confidence_scores, total_evaluated_queries } = data;

  const totalHall = hallucination_breakdown.low + hallucination_breakdown.medium + hallucination_breakdown.high;
  const radarData = [
    { subject: 'Retrieval', A: confidence_scores.retrieval_confidence },
    { subject: 'Citation', A: confidence_scores.citation_confidence },
    { subject: 'Answer', A: confidence_scores.answer_confidence },
    { subject: 'Precision', A: context_precision.precision_pct },
  ];

  return (
    <div className="p-8 space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <FlaskConical size={20} className="text-[hsl(var(--primary))]" />
          <h1 className="text-2xl font-bold text-[hsl(var(--text))]">Evaluation Dashboard</h1>
        </div>
        <p className="text-[hsl(var(--text-muted))] text-sm">RAG pipeline quality metrics • {total_evaluated_queries} queries evaluated</p>
      </div>

      {/* Top row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Context Precision */}
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Target size={15} className="text-[hsl(var(--primary))]" />
            <h2 className="text-sm font-semibold text-[hsl(var(--text))]">Context Precision</h2>
          </div>
          <div className="text-4xl font-bold gradient-text mb-2">{context_precision.precision_pct.toFixed(1)}%</div>
          <p className="text-xs text-[hsl(var(--text-muted))] mb-4">
            {context_precision.relevant_chunks} relevant / {context_precision.total_retrieved} retrieved chunks
          </p>
          <div className="w-full h-2 bg-[hsl(var(--border))] rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-1000"
              style={{ width: `${context_precision.precision_pct}%`, background: 'hsl(var(--primary))' }}
            />
          </div>
        </div>

        {/* Confidence Scores */}
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Award size={15} className="text-[hsl(var(--secondary))]" />
            <h2 className="text-sm font-semibold text-[hsl(var(--text))]">Confidence Scores</h2>
          </div>
          <div className="flex justify-around">
            <ConfidenceRing value={confidence_scores.retrieval_confidence} label="Retrieval" color="hsl(262 83% 68%)" />
            <ConfidenceRing value={confidence_scores.citation_confidence} label="Citation" color="hsl(197 71% 58%)" />
            <ConfidenceRing value={confidence_scores.answer_confidence} label="Answer" color="hsl(142 71% 45%)" />
          </div>
        </div>

        {/* Hallucination Breakdown */}
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Shield size={15} className="text-[hsl(var(--warning))]" />
            <h2 className="text-sm font-semibold text-[hsl(var(--text))]">Hallucination Analysis</h2>
          </div>
          <div className="space-y-3">
            {[
              { label: 'Low Risk', count: hallucination_breakdown.low, color: 'hsl(var(--success))', icon: <CheckCircle size={13} />, pct: totalHall ? (hallucination_breakdown.low / totalHall * 100) : 0 },
              { label: 'Medium Risk', count: hallucination_breakdown.medium, color: 'hsl(var(--warning))', icon: <AlertTriangle size={13} />, pct: totalHall ? (hallucination_breakdown.medium / totalHall * 100) : 0 },
              { label: 'High Risk', count: hallucination_breakdown.high, color: 'hsl(var(--error))', icon: <XCircle size={13} />, pct: totalHall ? (hallucination_breakdown.high / totalHall * 100) : 0 },
            ].map(({ label, count, color, icon, pct }) => (
              <div key={label}>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-1.5" style={{ color }}>
                    {icon}<span className="text-xs font-medium">{label}</span>
                  </div>
                  <span className="text-xs text-[hsl(var(--text-muted))]">{count}</span>
                </div>
                <div className="w-full h-1.5 bg-[hsl(var(--border))] rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${pct}%`, background: color }} />
                </div>
              </div>
            ))}
            <p className="text-xs text-[hsl(var(--text-muted))] mt-2">
              Avg score: {(hallucination_breakdown.avg_score * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {/* Retrieval Accuracy Trend */}
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={15} className="text-[hsl(var(--primary))]" />
            <h2 className="text-sm font-semibold text-[hsl(var(--text))]">Retrieval Accuracy Trend</h2>
          </div>
          {retrieval_accuracy_trend.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={retrieval_accuracy_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" strokeOpacity={0.4} />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'hsl(var(--text-muted))' }} tickFormatter={(v) => v.slice(5)} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: 'hsl(var(--text-muted))' }} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="accuracy" name="Accuracy" stroke="hsl(262 83% 68%)" strokeWidth={2} dot={{ r: 3, fill: 'hsl(262 83% 68%)' }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center text-[hsl(var(--text-muted))] text-sm">
              Not enough data yet. Run some queries first.
            </div>
          )}
        </div>

        {/* Radar Chart */}
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Brain size={15} className="text-[hsl(var(--accent))]" />
            <h2 className="text-sm font-semibold text-[hsl(var(--text))]">Pipeline Quality Radar</h2>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="hsl(var(--border))" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11, fill: 'hsl(var(--text-muted))' }} />
              <Radar name="Score" dataKey="A" stroke="hsl(262 83% 68%)" fill="hsl(262 83% 68%)" fillOpacity={0.2} strokeWidth={2} />
              <Tooltip formatter={(v: number | string) => [`${Number(v).toFixed(1)}%`, 'Score']} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
