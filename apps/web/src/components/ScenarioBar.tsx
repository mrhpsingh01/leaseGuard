"use client";

import React from "react";
import { FileText, ShieldCheck, UploadCloud, CheckCircle2 } from "lucide-react";

export type ScenarioType = "LEASE_SCAN" | "DEPOSIT_DISPUTE" | "UPLOAD_CUSTOM";

interface ScenarioBarProps {
  activeScenario: ScenarioType;
  onSelectScenario: (scenario: ScenarioType) => void;
}

export const ScenarioBar: React.FC<ScenarioBarProps> = ({
  activeScenario,
  onSelectScenario,
}) => {
  return (
    <div data-testid="scenario-bar" className="bg-slate-950 border-b border-slate-800/80 px-4 sm:px-6 py-2.5 flex items-center justify-between flex-wrap gap-2 text-xs">
      <div className="flex items-center gap-1 sm:gap-2 flex-wrap">
        <span className="text-slate-400 font-medium mr-1 hidden sm:inline">1-Click Scenarios:</span>
        
        {/* Preset 1 */}
        <button
          onClick={() => onSelectScenario("LEASE_SCAN")}
          aria-label="Preset 1: Athens Off-Campus Student Lease"
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-semibold transition-all ${
            activeScenario === "LEASE_SCAN"
              ? "bg-red-600/90 text-white shadow-sm shadow-red-900/50 border border-red-500"
              : "bg-slate-800 text-slate-300 hover:bg-slate-750 hover:text-white border border-slate-700/80"
          }`}
        >
          <FileText className="h-3.5 w-3.5" />
          <span>Preset 1: Athens Off-Campus Student Lease</span>
          <span className="px-1.5 py-0.2 rounded text-[10px] bg-red-900/70 text-red-200 border border-red-700/50">
            5 Violations
          </span>
        </button>

        {/* Preset 2 */}
        <button
          onClick={() => onSelectScenario("DEPOSIT_DISPUTE")}
          aria-label="Preset 2: Move-Out Security Deposit Dispute"
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-semibold transition-all ${
            activeScenario === "DEPOSIT_DISPUTE"
              ? "bg-amber-600/90 text-white shadow-sm shadow-amber-900/50 border border-amber-500"
              : "bg-slate-800 text-slate-300 hover:bg-slate-750 hover:text-white border border-slate-700/80"
          }`}
        >
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>Preset 2: Move-Out Security Deposit Dispute</span>
          <span className="px-1.5 py-0.2 rounded text-[10px] bg-amber-900/70 text-amber-200 border border-amber-700/50">
            Forfeiture + Treble
          </span>
        </button>

        {/* Preset 3 */}
        <button
          onClick={() => onSelectScenario("UPLOAD_CUSTOM")}
          aria-label="Preset 3: Custom PDF Dropzone"
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-semibold transition-all ${
            activeScenario === "UPLOAD_CUSTOM"
              ? "bg-blue-600/90 text-white shadow-sm shadow-blue-900/50 border border-blue-500"
              : "bg-slate-800 text-slate-300 hover:bg-slate-750 hover:text-white border border-slate-700/80"
          }`}
        >
          <UploadCloud className="h-3.5 w-3.5" />
          <span>Preset 3: Custom PDF Dropzone</span>
        </button>
      </div>

      <div className="flex items-center gap-2 text-slate-400">
        <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
          <CheckCircle2 className="h-3 w-3" />
          Georgia Safe at Home Act (HB 404) Compliant
        </span>
      </div>
    </div>
  );
};
