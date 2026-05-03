"use client";

import { useState } from "react";
import { 
  Settings, 
  Cpu, 
  Database, 
  Globe, 
  Shield, 
  Bell, 
  Save,
  CheckCircle2
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
  const [model, setModel] = useState("llama-3.3-70b-versatile");
  const [isSaved, setIsSaved] = useState(false);

  const models = [
    { id: "llama-3.3-70b-versatile", name: "Llama 3.3 70B (Versatile)", speed: "Fast", accuracy: "High" },
    { id: "llama-3.1-8b-instant", name: "Llama 3.1 8B (Instant)", speed: "Real-time", accuracy: "Standard" },
    { id: "mixtral-8x7b-32768", name: "Mixtral 8x7B", speed: "Moderate", accuracy: "Very High" },
  ];

  const handleSave = () => {
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
      <div className="flex items-end justify-between">
        <div>
          <div className="flex items-center gap-2 text-primary mb-2">
            <Settings size={16} />
            <span className="text-[10px] font-bold uppercase tracking-widest">Preferences</span>
          </div>
          <h1 className="text-3xl font-black">System Settings</h1>
          <p className="text-sm text-muted-foreground">Configure AI models, scraping limits, and API behavior.</p>
        </div>
        <button 
          onClick={handleSave}
          className="flex items-center gap-2 bg-primary text-primary-foreground px-6 py-2.5 rounded-xl font-bold hover:opacity-90 transition-all shadow-lg shadow-primary/20"
        >
          {isSaved ? <CheckCircle2 size={18} /> : <Save size={18} />}
          {isSaved ? "Saved" : "Save Changes"}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-1 space-y-1">
          {[
            { icon: Cpu, label: "AI Engine", active: true },
            { icon: Database, label: "Data Storage", active: false },
            { icon: Globe, label: "Scraper Config", active: false },
            { icon: Shield, label: "Security", active: false },
            { icon: Bell, label: "Notifications", active: false },
          ].map((nav, i) => (
            <button 
              key={i}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-sm font-medium",
                nav.active ? "bg-card border border-border shadow-sm text-foreground" : "text-muted-foreground hover:bg-secondary/50"
              )}
            >
              <nav.icon size={18} />
              {nav.label}
            </button>
          ))}
        </div>

        <div className="md:col-span-2 space-y-6">
          <div className="bg-card border border-border rounded-2xl p-6 space-y-6">
            <div className="space-y-4">
              <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Model Selection</h3>
              <div className="grid gap-3">
                {models.map((m) => (
                  <label 
                    key={m.id}
                    className={cn(
                      "flex items-center justify-between p-4 rounded-xl border-2 transition-all cursor-pointer",
                      model === m.id ? "border-primary bg-primary/5" : "border-border hover:bg-secondary/30"
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <input 
                        type="radio" 
                        name="model" 
                        checked={model === m.id}
                        onChange={() => setModel(m.id)}
                        className="w-4 h-4 accent-primary" 
                      />
                      <div>
                        <p className="text-sm font-bold">{m.name}</p>
                        <p className="text-[10px] text-muted-foreground">Speed: {m.speed} • Accuracy: {m.accuracy}</p>
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div className="space-y-4 pt-4 border-t border-border">
              <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Scraper Sensitivity</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Auto-retry on failure</span>
                  <div className="w-10 h-5 bg-primary rounded-full relative">
                    <div className="absolute right-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow-sm" />
                  </div>
                </div>
                <div className="flex items-center justify-between text-muted-foreground">
                   <span className="text-sm font-medium">Max parallel instances</span>
                   <span className="text-sm font-bold">4</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
