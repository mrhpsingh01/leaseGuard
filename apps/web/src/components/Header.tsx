"use client";

import React from "react";
import { ShieldAlert, Cpu, Sparkles, MapPin, ExternalLink } from "lucide-react";

interface HeaderProps {
  onToggleDrawer: () => void;
  isDrawerOpen: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onToggleDrawer, isDrawerOpen }) => {
  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-40 px-4 sm:px-6 py-3 flex items-center justify-between shadow-md">
      {/* Brand & Mission */}
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-red-600 via-rose-700 to-red-900 flex items-center justify-center shadow-lg shadow-red-900/40 border border-red-500/30">
          <ShieldAlert className="h-6 w-6 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-lg sm:text-xl tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">
              LeaseGuard
            </span>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-red-950/80 text-red-300 border border-red-800/60 font-semibold tracking-wider">
              Athens, GA
            </span>
            <span className="hidden md:inline-flex text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-blue-950 text-blue-300 border border-blue-800/60 font-medium">
              Zero Login
            </span>
          </div>
          <p className="text-xs text-slate-400 flex items-center gap-1.5 hidden sm:flex">
            <MapPin className="h-3 w-3 text-red-400" />
            Applied AI &amp; Georgia Statutory Lease Auditor for Athens Renters
          </p>
        </div>
      </div>

      {/* Actions & Hiring Manager Drawer Toggle */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleDrawer}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all duration-200 border shadow-sm ${
            isDrawerOpen
              ? "bg-blue-600 text-white border-blue-400 ring-2 ring-blue-500/40 shadow-blue-900/30"
              : "bg-slate-800 hover:bg-slate-750 text-slate-200 hover:text-white border-slate-700 hover:border-slate-600"
          }`}
          aria-label="Hiring Manager View: Inspect Live Pipeline"
          aria-pressed={isDrawerOpen}
          title="Open engineering pipeline trace, architecture diagram, and raw JSON telemetry"
        >
          <Cpu className={`h-4 w-4 ${isDrawerOpen ? "text-blue-200 animate-spin" : "text-blue-400"}`} />
          <span className="hidden sm:inline">Hiring Manager View:</span>
          <span>Inspect Live Pipeline</span>
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
        </button>
      </div>
    </header>
  );
};
