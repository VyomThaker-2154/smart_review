"use client";

import { useState } from "react";
import { ReviewInput } from "@/components/ReviewInput";
import { AnalysisResult } from "@/components/AnalysisResult";
import { useRouter } from "next/navigation";
import { TrendingUp, Sparkles, ShieldCheck } from "lucide-react";

import { LoadingOverlay } from "@/components/LoadingOverlay";

export default function Home() {
  const [analysis, setAnalysis] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const router = useRouter();

  const handleBatchUpload = (batchId: string) => {
    setIsProcessing(true);
    // Give it a moment to show the nice loader before redirecting
    setTimeout(() => {
      router.push(`/dashboard?batchId=${batchId}`);
    }, 800);
  };

  return (
    <div className="max-w-5xl mx-auto pb-20">
      <LoadingOverlay isLoading={isProcessing} />
      <div className="mb-12">
        <div className="flex items-center gap-2 text-primary mb-3">
          <Sparkles size={20} className="animate-pulse" />
          <span className="text-sm font-bold uppercase tracking-[0.2em]">Next Gen Analysis</span>
        </div>
        <h1 className="text-4xl font-black tracking-tight text-foreground sm:text-5xl mb-4">
          Understand every <span className="text-primary">customer.</span>
        </h1>
        <p className="text-lg text-muted-foreground max-w-2xl leading-relaxed">
          Leverage enterprise-grade AI to analyze customer sentiment, extract key insights, and automate professional replies in seconds.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-12">
          <ReviewInput 
            onAnalysisComplete={setAnalysis} 
            onBatchUpload={handleBatchUpload} 
            onLoading={setIsProcessing}
          />
        </div>
      </div>

      {analysis && <AnalysisResult result={analysis} />}

      {!analysis && (
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            { 
              icon: TrendingUp, 
              title: "Sentiment Tracking", 
              desc: "Deep analysis of emotional tone across multiple dimensions." 
            },
            { 
              icon: Sparkles, 
              title: "AI Summaries", 
              desc: "Get the gist of thousands of reviews in a single paragraph." 
            },
            { 
              icon: ShieldCheck, 
              title: "Brand Voice", 
              desc: "Automated replies that perfectly match your professional tone." 
            }
          ].map((feature, i) => (
            <div key={i} className="group p-6 rounded-2xl border border-border bg-card hover:border-primary/50 transition-all duration-300 hover:shadow-xl hover:shadow-primary/5">
              <div className="w-12 h-12 rounded-xl bg-secondary flex items-center justify-center text-primary mb-4 group-hover:scale-110 transition-transform">
                <feature.icon size={24} />
              </div>
              <h3 className="font-bold text-lg mb-2">{feature.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{feature.desc}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
