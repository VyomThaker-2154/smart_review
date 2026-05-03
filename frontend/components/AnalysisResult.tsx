"use client";

import { CheckCircle2, MessageCircle, Quote, Sparkles, Tag, ThumbsDown, ThumbsUp, HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface AnalysisResultProps {
  result: {
    text: string;
    sentiment: string;
    confidence: number;
    aspects: { aspect: string; sentiment: string }[];
    summary: string;
    suggested_reply: string;
    key_phrases: string[];
  };
}

export function AnalysisResult({ result }: AnalysisResultProps) {
  const getSentimentStyles = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case "positive": return "bg-positive/10 text-positive border-positive/20";
      case "negative": return "bg-negative/10 text-negative border-negative/20";
      case "neutral": return "bg-neutral/10 text-neutral border-neutral/20";
      case "mixed": return "bg-mixed/10 text-mixed border-mixed/20";
      default: return "bg-muted text-muted-foreground border-border";
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case "positive": return <ThumbsUp size={16} />;
      case "negative": return <ThumbsDown size={16} />;
      case "mixed": return <Sparkles size={16} />;
      default: return <HelpCircle size={16} />;
    }
  };

  return (
    <div className="space-y-6 animate-fade-in mt-8">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold flex items-center gap-2">
          Analysis Results
          <div className={cn(
            "text-[10px] uppercase tracking-widest font-black px-2 py-0.5 rounded-full border",
            getSentimentStyles(result.sentiment)
          )}>
            {result.sentiment}
          </div>
        </h3>
        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground bg-secondary px-3 py-1 rounded-full border border-border">
          <CheckCircle2 size={12} className="text-positive" />
          {Math.round(result.confidence * 100)}% Confidence
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Summary & Reply */}
        <div className="md:col-span-2 space-y-6">
          <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
            <div className="bg-secondary/50 px-6 py-3 border-b border-border flex items-center gap-2">
              <Sparkles size={16} className="text-primary" />
              <span className="text-sm font-bold">AI Executive Summary</span>
            </div>
            <div className="p-6">
              <p className="text-sm leading-relaxed italic text-foreground/80">
                "{result.summary}"
              </p>
            </div>
          </div>

          <div className="bg-primary/5 border border-primary/20 rounded-2xl overflow-hidden shadow-sm">
            <div className="bg-primary/10 px-6 py-3 border-b border-primary/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageCircle size={16} className="text-primary" />
                <span className="text-sm font-bold text-primary">Suggested Reply</span>
              </div>
              <button className="text-[10px] font-bold uppercase tracking-widest text-primary hover:underline">Copy</button>
            </div>
            <div className="p-6 bg-white dark:bg-card">
              <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">
                {result.suggested_reply}
              </p>
            </div>
          </div>
        </div>

        {/* Right Column: Aspects & Phrases */}
        <div className="space-y-6">
          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
            <h4 className="text-sm font-bold mb-4 flex items-center gap-2 uppercase tracking-wider">
              <Tag size={16} className="text-muted-foreground" />
              Key Phrases
            </h4>
            <div className="flex flex-wrap gap-2">
              {result.key_phrases.map((phrase, i) => (
                <span key={i} className="text-xs bg-secondary px-2.5 py-1 rounded-lg border border-border font-medium">
                  {phrase}
                </span>
              ))}
            </div>
          </div>

          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
            <h4 className="text-sm font-bold mb-4 flex items-center gap-2 uppercase tracking-wider">
              <Sparkles size={16} className="text-muted-foreground" />
              Aspect Analysis
            </h4>
            <div className="space-y-3">
              {result.aspects.map((aspect, i) => (
                <div key={i} className="flex items-center justify-between group">
                  <span className="text-xs font-medium text-muted-foreground capitalize">{aspect.aspect}</span>
                  <div className={cn(
                    "flex items-center gap-1.5 text-[10px] font-bold px-2 py-0.5 rounded-full border transition-all group-hover:scale-105",
                    getSentimentStyles(aspect.sentiment)
                  )}>
                    {getSentimentIcon(aspect.sentiment)}
                    <span className="uppercase tracking-tighter">{aspect.sentiment}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-secondary/20 rounded-2xl p-6 border border-border">
        <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-3 flex items-center gap-2">
          <Quote size={14} />
          Original Content
        </h4>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {result.text}
        </p>
      </div>
    </div>
  );
}
