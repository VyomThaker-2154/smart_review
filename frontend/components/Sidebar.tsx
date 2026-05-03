"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  MessageSquareQuote, 
  History, 
  Settings, 
  ShieldCheck,
  ChevronRight,
  TrendingUp,
  Activity
} from "lucide-react";
import { cn } from "@/lib/utils";
import { analysisApi } from "@/lib/api";
import { useState, useEffect } from "react";

const menuItems = [
  { icon: MessageSquareQuote, label: "Analyze", href: "/" },
  { icon: History, label: "History", href: "/history" },
];

const secondaryItems = [
  { icon: Settings, label: "Settings", href: "/settings" },
];

export function Sidebar() {
  const pathname = usePathname();
  const [isApiOnline, setIsApiOnline] = useState<boolean | null>(null);

  useEffect(() => {
    analysisApi.getHealth()
      .then(() => setIsApiOnline(true))
      .catch(() => setIsApiOnline(false));
  }, []);

  return (
    <aside className="w-64 border-r border-border bg-card flex flex-col h-screen sticky top-0 transition-all duration-300">
      <div className="p-6 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-primary-foreground shadow-lg shadow-primary/20">
          <TrendingUp size={24} strokeWidth={2.5} />
        </div>
        <div>
          <h1 className="font-bold text-lg leading-tight tracking-tight">SmartReview</h1>
          <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold">AI Analytics</p>
        </div>
      </div>

      <nav className="flex-1 px-4 space-y-8 mt-4">
        <div className="space-y-1">
          <p className="px-3 text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-4">Main Menu</p>
          {menuItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "group flex items-center justify-between px-3 py-2.5 rounded-lg transition-all duration-200",
                  isActive 
                    ? "bg-primary text-primary-foreground shadow-md shadow-primary/10" 
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                )}
              >
                <div className="flex items-center gap-3">
                  <item.icon size={20} className={cn(isActive ? "text-primary-foreground" : "text-muted-foreground group-hover:text-foreground")} />
                  <span className="font-medium text-sm">{item.label}</span>
                </div>
                {isActive && <ChevronRight size={14} />}
              </Link>
            );
          })}
        </div>

        <div className="space-y-1">
          <p className="px-3 text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-4">System</p>
          {secondaryItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200",
                  isActive 
                    ? "bg-primary text-primary-foreground" 
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                )}
              >
                <item.icon size={20} />
                <span className="font-medium text-sm">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>

      <div className="p-4 border-t border-border space-y-4">
        <div className="flex items-center justify-between px-2">
          <div className="flex items-center gap-2">
            <Activity size={12} className={cn(isApiOnline ? "text-positive" : "text-negative")} />
            <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">API Status</span>
          </div>
          <span className={cn("text-[10px] font-bold uppercase", isApiOnline ? "text-positive" : "text-negative")}>
            {isApiOnline === null ? "Checking..." : isApiOnline ? "Online" : "Offline"}
          </span>
        </div>

        <div className="bg-secondary/50 rounded-xl p-4">
          <p className="text-xs font-semibold mb-1">Enterprise Plan</p>
          <div className="w-full bg-border rounded-full h-1.5 mb-2">
            <div className="bg-primary h-1.5 rounded-full w-[85%]"></div>
          </div>
          <p className="text-[10px] text-muted-foreground">8,542 / 10,000 reviews analyzed</p>
        </div>
      </div>
    </aside>
  );
}
