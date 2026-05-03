"use client";

import { useEffect, useState } from "react";
import { analysisApi } from "@/lib/api";
import { cn, formatDate } from "@/lib/utils";
import { 
  History, 
  Search, 
  ExternalLink, 
  FileText, 
  CheckCircle2, 
  MoreHorizontal,
  ChevronLeft,
  ChevronRight,
  Filter
} from "lucide-react";
import Link from "next/link";

export default function HistoryPage() {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    fetchHistory();
  }, [page]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await analysisApi.getHistory(page);
      setHistory(data.records);
      setTotalPages(data.pages);
    } catch (err) {
      console.error("Failed to fetch history", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      <div className="flex items-end justify-between">
        <div>
          <div className="flex items-center gap-2 text-primary mb-2">
            <History size={16} />
            <span className="text-[10px] font-bold uppercase tracking-widest">Logs & Records</span>
          </div>
          <h1 className="text-3xl font-black">Analysis History</h1>
          <p className="text-sm text-muted-foreground">View and manage all previous batch and single review analyses.</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input 
              type="text" 
              placeholder="Search history..." 
              className="pl-10 pr-4 py-2 bg-card border border-border rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-primary w-64"
            />
          </div>
          <button className="p-2 bg-card border border-border rounded-xl hover:bg-secondary transition-colors text-muted-foreground">
            <Filter size={18} />
          </button>
        </div>
      </div>

      <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-secondary/50 border-b border-border">
                <th className="px-6 py-4 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Analysis Type</th>
                <th className="px-6 py-4 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Details</th>
                <th className="px-6 py-4 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Date</th>
                <th className="px-6 py-4 text-[10px] font-bold text-muted-foreground uppercase tracking-widest text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="px-6 py-6"><div className="h-4 w-24 bg-secondary rounded"></div></td>
                    <td className="px-6 py-6"><div className="h-4 w-48 bg-secondary rounded"></div></td>
                    <td className="px-6 py-6"><div className="h-4 w-32 bg-secondary rounded"></div></td>
                    <td className="px-6 py-6"><div className="h-4 w-8 bg-secondary rounded ml-auto"></div></td>
                  </tr>
                ))
              ) : history.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-muted-foreground text-sm">
                    No history records found.
                  </td>
                </tr>
              ) : (
                history.map((record) => (
                  <tr key={record.batch_id || record.id} className="hover:bg-secondary/20 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className={cn(
                          "w-10 h-10 rounded-xl flex items-center justify-center",
                          record.batch_id ? "bg-primary/10 text-primary" : "bg-mixed/10 text-mixed"
                        )}>
                          {record.batch_id ? <FileText size={18} /> : <CheckCircle2 size={18} />}
                        </div>
                        <div>
                          <p className="text-sm font-bold">{record.batch_id ? "Bulk Analysis" : "Single Analysis"}</p>
                          <p className="text-[10px] text-muted-foreground font-mono">ID: {record.batch_id?.slice(0, 8) || record.id?.slice(0, 8)}...</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-sm text-foreground/80 line-clamp-1 max-w-xs">
                        {record.text || `${record.total_reviews} reviews analyzed in this batch`}
                      </p>
                    </td>
                    <td className="px-6 py-4 text-xs font-medium text-muted-foreground">
                      {formatDate(record.created_at)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {record.batch_id ? (
                        <Link 
                          href={`/dashboard?batchId=${record.batch_id}`}
                          className="inline-flex items-center gap-1.5 text-xs font-bold text-primary hover:underline"
                        >
                          View Results <ExternalLink size={12} />
                        </Link>
                      ) : (
                        <button className="text-muted-foreground hover:text-foreground">
                          <MoreHorizontal size={18} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-6 py-4 border-t border-border flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Showing Page <span className="font-bold text-foreground">{page}</span> of <span className="font-bold text-foreground">{totalPages}</span>
          </p>
          <div className="flex items-center gap-2">
            <button 
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
              className="p-1.5 rounded-lg border border-border hover:bg-secondary disabled:opacity-30 disabled:hover:bg-transparent transition-all"
            >
              <ChevronLeft size={18} />
            </button>
            <button 
              disabled={page === totalPages}
              onClick={() => setPage(p => p + 1)}
              className="p-1.5 rounded-lg border border-border hover:bg-secondary disabled:opacity-30 disabled:hover:bg-transparent transition-all"
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
