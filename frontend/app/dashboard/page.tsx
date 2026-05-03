"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { analysisApi } from "@/lib/api";
import { DashboardCharts } from "@/components/DashboardCharts";
import { 
  Users, 
  MessageSquare, 
  TrendingUp, 
  AlertCircle, 
  ArrowUpRight, 
  ArrowDownRight,
  Loader2,
  Sparkles,
  Search
} from "lucide-react";
import { cn } from "@/lib/utils";

function DashboardContent() {
  const searchParams = useSearchParams();
  const batchId = searchParams.get("batchId");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (batchId) {
      fetchDashboardData(batchId);
    } else {
      setLoading(false);
    }
  }, [batchId]);

  const fetchDashboardData = async (id: string) => {
    setLoading(true);
    try {
      const summary = await analysisApi.getSummary(id);
      setData(summary);
    } catch (err: any) {
      setError("Failed to load dashboard data. Ensure the batch ID is valid.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
        <Loader2 className="w-10 h-10 text-primary animate-spin" />
        <p className="text-muted-foreground font-medium animate-pulse">Processing Analysis Results...</p>
      </div>
    );
  }

  if (!batchId) {
    return (
      <div className="max-w-2xl mx-auto mt-20 text-center space-y-6">
        <div className="w-20 h-20 bg-secondary rounded-3xl flex items-center justify-center mx-auto text-muted-foreground">
          <Search size={40} />
        </div>
        <h2 className="text-2xl font-bold">No Analysis Selected</h2>
        <p className="text-muted-foreground">
          Upload a CSV or paste reviews on the main page to see the dynamic dashboard insights.
        </p>
        <button 
          onClick={() => window.location.href = "/"}
          className="bg-primary text-primary-foreground px-6 py-2.5 rounded-xl font-bold hover:opacity-90 transition-all shadow-lg shadow-primary/20"
        >
          Go to Analyze
        </button>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-negative/10 border border-negative/20 p-8 rounded-2xl text-center">
        <AlertCircle className="mx-auto text-negative mb-4" size={48} />
        <p className="text-negative font-bold text-lg">{error || "Something went wrong"}</p>
      </div>
    );
  }

  // Transform data for charts
  const sentimentData = [
    { name: 'Positive', value: data.sentiment_distribution.positive, color: 'var(--color-positive)' },
    { name: 'Negative', value: data.sentiment_distribution.negative, color: 'var(--color-negative)' },
    { name: 'Neutral', value: data.sentiment_distribution.neutral, color: 'var(--color-neutral)' },
    { name: 'Mixed', value: data.sentiment_distribution.mixed, color: 'var(--color-mixed)' },
  ].filter(d => d.value > 0);

  const aspectData = data.frequent_aspects.map((a: any) => ({
    aspect: a.aspect,
    positive: a.positive_count,
    negative: a.negative_count,
    neutral: a.count - a.positive_count - a.negative_count
  }));

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-primary mb-2">
            <TrendingUp size={16} />
            <span className="text-[10px] font-bold uppercase tracking-widest">Live Dashboard</span>
          </div>
          <h1 className="text-3xl font-black">Batch Analytics</h1>
          <p className="text-sm text-muted-foreground">Batch ID: <span className="font-mono">{batchId}</span></p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => window.location.href = "/"}
            className="text-xs font-bold bg-primary text-primary-foreground px-4 py-2 rounded-xl shadow-lg shadow-primary/20 hover:opacity-90 transition-all mr-2"
          >
            New Analysis
          </button>
          <div className="bg-card border border-border px-4 py-2 rounded-xl flex items-center gap-2">
            <span className="text-[10px] font-bold text-muted-foreground uppercase">Status</span>
            <div className="w-2 h-2 rounded-full bg-positive animate-pulse"></div>
            <span className="text-xs font-bold uppercase tracking-tight">Complete</span>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: "Total Reviews", value: data.total_reviews, icon: MessageSquare, color: "text-primary", bg: "bg-primary/10" },
          { label: "Positive Ratio", value: `${Math.round(data.sentiment_percentages.positive || 0)}%`, icon: ArrowUpRight, color: "text-positive", bg: "bg-positive/10" },
          { label: "Critical Issues", value: data.sentiment_distribution.negative, icon: AlertCircle, color: "text-negative", bg: "bg-negative/10" },
          { label: "Active Aspects", value: data.frequent_aspects.length, icon: Users, color: "text-mixed", bg: "bg-mixed/10" },
        ].map((stat, i) => (
          <div key={i} className="bg-card border border-border p-6 rounded-2xl shadow-sm hover:shadow-md transition-all">
            <div className="flex items-center justify-between mb-4">
              <div className={cn("p-2.5 rounded-xl", stat.bg, stat.color)}>
                <stat.icon size={20} />
              </div>
              <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">{stat.label}</span>
            </div>
            <p className="text-2xl font-black tracking-tight">{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Executive Summary Card */}
        <div className="lg:col-span-2 bg-primary/5 border border-primary/20 rounded-3xl p-8 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:scale-110 transition-transform duration-500">
            <Sparkles size={120} />
          </div>
          <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
            <Sparkles className="text-primary" size={20} />
            AI Executive Summary
          </h3>
          <p className="text-sm leading-relaxed text-foreground/80 relative z-10 max-w-2xl italic">
            "{data.executive_summary}"
          </p>
        </div>

        {/* Complaints/Praise Mini List */}
        <div className="bg-card border border-border rounded-3xl p-6 shadow-sm">
          <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground mb-6">Top Praise</h3>
          <div className="space-y-3">
            {data.top_praise.slice(0, 4).map((item: string, i: number) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-positive"></div>
                <p className="text-xs font-medium">{item}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <DashboardCharts sentimentData={sentimentData} aspectData={aspectData} />
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <DashboardContent />
    </Suspense>
  );
}
