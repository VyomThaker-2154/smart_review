"use client";

import { useState, useRef } from "react";
import { Upload, Send, FileText, X, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { analysisApi } from "@/lib/api";

interface ReviewInputProps {
  onAnalysisComplete: (result: any) => void;
  onBatchUpload: (batchId: string) => void;
  onLoading?: (loading: boolean) => void;
}

export function ReviewInput({ onAnalysisComplete, onBatchUpload, onLoading }: ReviewInputProps) {
  const [shopName, setShopName] = useState("");
  const [location, setLocation] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleAnalyze = async () => {
    if (!shopName.trim() || shopName.length < 2) {
      setError("Please enter a valid shop or company name.");
      return;
    }

    setIsLoading(true);
    onLoading?.(true);
    setError(null);
    try {
      const result = await analysisApi.scrapeAndAnalyze(shopName, location);
      onBatchUpload(result.batch_id);
      setShopName("");
      setLocation("");
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const message = typeof detail === "string" 
        ? detail 
        : Array.isArray(detail) 
          ? detail[0]?.msg || "Analysis failed" 
          : "Failed to scrape reviews. Is the backend running?";
      setError(message);
    } finally {
      setIsLoading(false);
      onLoading?.(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!file.name.endsWith(".csv")) {
      setError("Please upload a CSV file.");
      return;
    }

    setIsLoading(true);
    onLoading?.(true);
    setError(null);
    try {
      const result = await analysisApi.uploadCsv(file);
      onBatchUpload(result.batch_id);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const message = typeof detail === "string" 
        ? detail 
        : Array.isArray(detail) 
          ? detail[0]?.msg || "Invalid file format" 
          : "Failed to upload CSV.";
      setError(message);
    } finally {
      setIsLoading(false);
      onLoading?.(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileUpload(file);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
          <MessageSquareQuote className="text-primary" size={20} />
          New Search Analysis
        </h2>
        
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground ml-1">Shop / Company Name</label>
              <input
                className="w-full px-4 py-3 rounded-xl bg-secondary/30 border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all text-sm"
                placeholder="e.g. Starbucks, Cafe Coffee Day..."
                value={shopName}
                onChange={(e) => setShopName(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground ml-1">Location (Optional)</label>
              <input
                className="w-full px-4 py-3 rounded-xl bg-secondary/30 border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all text-sm"
                placeholder="e.g. Mumbai, New York..."
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="bg-primary/5 border border-primary/10 p-4 rounded-xl flex items-start gap-3">
             <AlertCircle size={16} className="text-primary mt-0.5" />
             <p className="text-[11px] text-foreground/70 leading-relaxed">
               We'll search Google Maps for this business, scrape the latest reviews, and generate a comprehensive sentiment dashboard automatically.
             </p>
          </div>

          <button
            onClick={handleAnalyze}
            disabled={isLoading || !shopName.trim()}
            className="w-full bg-primary text-primary-foreground py-3 rounded-xl font-bold flex items-center justify-center gap-2 hover:opacity-90 disabled:opacity-50 transition-all shadow-lg shadow-primary/20"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Send size={16} />
            )}
            Start Scraping & Analysis
          </button>

          <div className="relative flex items-center gap-4">
            <div className="flex-1 h-px bg-border"></div>
            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">OR</span>
            <div className="flex-1 h-px bg-border"></div>
          </div>

          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={onDrop}
            className={cn(
              "border-2 border-dashed rounded-xl p-8 transition-all flex flex-col items-center justify-center gap-3 cursor-pointer",
              isDragging ? "border-primary bg-primary/5" : "border-border hover:border-muted-foreground/30 hover:bg-secondary/20"
            )}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              className="hidden"
              ref={fileInputRef}
              accept=".csv"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFileUpload(file);
              }}
            />
            <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center text-primary">
              <Upload size={24} />
            </div>
            <div className="text-center">
              <p className="text-sm font-bold">Bulk Analysis (CSV)</p>
              <p className="text-xs text-muted-foreground mt-1">Drag and drop or click to upload</p>
            </div>
            <div className="flex items-center gap-4 mt-2">
               <div className="flex items-center gap-1 text-[10px] text-muted-foreground font-medium">
                 <FileText size={12} />
                 <span>reviews.csv</span>
               </div>
            </div>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-negative/10 border border-negative/20 text-negative flex items-center gap-2 text-sm animate-fade-in">
            <AlertCircle size={16} />
            <span className="font-medium">{error}</span>
            <button onClick={() => setError(null)} className="ml-auto opacity-70 hover:opacity-100">
              <X size={16} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

const MessageSquareQuote = ({ className, size }: { className?: string, size?: number }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width={size || 24} 
    height={size || 24} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    className={className}
  >
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    <path d="m8 9 2 2 4-4"/>
  </svg>
);
