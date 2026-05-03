"use client";

import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Cell,
  PieChart,
  Pie
} from 'recharts';

interface DashboardChartsProps {
  sentimentData: { name: string; value: number; color: string }[];
  aspectData: { aspect: string; positive: number; negative: number; neutral: number }[];
}

export function DashboardCharts({ sentimentData, aspectData }: DashboardChartsProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
      {/* Sentiment Distribution Pie Chart */}
      <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-8">
          <h3 className="font-bold text-sm uppercase tracking-wider text-muted-foreground">Sentiment Distribution</h3>
          <div className="flex items-center gap-2">
            {sentimentData.map((d, i) => (
              <div key={i} className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }}></div>
                <span className="text-[10px] font-bold text-muted-foreground uppercase">{d.name}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={sentimentData}
                cx="50%"
                cy="50%"
                innerRadius={80}
                outerRadius={110}
                paddingAngle={8}
                dataKey="value"
              >
                {sentimentData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'var(--card)', 
                  borderColor: 'var(--border)',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: '600'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Aspect Sentiment Bar Chart */}
      <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
        <h3 className="font-bold text-sm uppercase tracking-wider text-muted-foreground mb-8">Top Aspects by Sentiment</h3>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={aspectData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="var(--border)" />
              <XAxis type="number" hide />
              <YAxis 
                dataKey="aspect" 
                type="category" 
                tick={{ fontSize: 11, fontWeight: 500, fill: 'var(--muted-foreground)' }} 
                width={80}
              />
              <Tooltip 
                cursor={{ fill: 'var(--secondary)', opacity: 0.4 }}
                contentStyle={{ 
                  backgroundColor: 'var(--card)', 
                  borderColor: 'var(--border)',
                  borderRadius: '12px',
                  fontSize: '12px'
                }}
              />
              <Bar dataKey="positive" stackId="a" fill="var(--color-positive)" radius={[0, 0, 0, 0]} barSize={20} />
              <Bar dataKey="negative" stackId="a" fill="var(--color-negative)" radius={[0, 4, 4, 0]} barSize={20} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
