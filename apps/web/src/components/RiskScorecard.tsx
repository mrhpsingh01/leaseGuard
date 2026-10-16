"use client";

import React from "react";
import { AlertCircle, DollarSign, ShieldCheck, UserCheck, Scale } from "lucide-react";
import { LeaseAuditResponse } from "../lib/types";

interface RiskScorecardProps {
  auditData: LeaseAuditResponse;
}

export const RiskScorecard: React.FC<RiskScorecardProps> = ({ auditData }) => {
  const isHighRisk = auditData.overall_risk_score >= 70;
  const count = auditData.flagged_risks.length;
  const cap = auditData.deposit_cap_allowed;
  const grounded = count === 0 ? 100 : Math.round((auditData.flagged_risks.filter((r) => r.statute_citation && r.verbatim_lease_quote).length / count) * 100);

  return (
    <div className="bg-slate-900 border-b border-slate-800 p-4 sm:p-5" data-testid="risk-scorecard">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        {/* Score Gauge */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center">
            <div
              className={`h-16 w-16 rounded-full flex flex-col items-center justify-center border-4 ${
                isHighRisk
                  ? "border-red-500 bg-red-950/40 text-red-400 shadow-lg shadow-red-900/30"
                  : "border-emerald-500 bg-emerald-950/40 text-emerald-400"
              }`}
            >
              <span className="text-xl font-black font-mono leading-none">
                {auditData.overall_risk_score}
              </span>
              <span className="text-[9px] font-semibold uppercase tracking-wider text-slate-400 mt-0.5">
                /100
              </span>
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-sm sm:text-base text-white tracking-tight">
                {count === 0 ? "NO STATUTORY VIOLATIONS DETECTED" : isHighRisk ? "CRITICAL RISK: UNENFORCEABLE LEASE TRAPS DETECTED" : "RISKS DETECTED: REVIEW BEFORE SIGNING"}
              </span>
              {count > 0 && (
                <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-red-900/80 text-red-200 border border-red-700">
                  Action Required
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {count} {count === 1 ? "clause conflicts" : "clauses conflict"} with Georgia HB 404 &amp; O.C.G.A. Title 44, Chapter 7 in {auditData.filename}.
            </p>
          </div>
        </div>

        {/* Quick Summary Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 w-full sm:w-auto text-xs">
          {/* Metric 1: Deposit Excess */}
          <div className="bg-slate-950/90 border border-red-900/60 rounded-lg p-2.5 flex flex-col justify-between">
            <span className="text-[10px] text-slate-400 uppercase font-medium flex items-center gap-1">
              <DollarSign className="h-3 w-3 text-red-400" />
              Illegal Excess
            </span>
            <span className="font-mono font-bold text-red-400 text-sm mt-1">
              +${(auditData.deposit_excess ?? 0).toFixed(2)}
            </span>
            <span className="text-[9px] text-slate-500">{cap ? `Cap: 2x Rent ($${cap.toLocaleString("en-US", { minimumFractionDigits: 2 })})` : "Deposit cap not evaluated"}</span>
          </div>

          {/* Metric 2: Void Clauses */}
          <div className="bg-slate-950/90 border border-amber-900/60 rounded-lg p-2.5 flex flex-col justify-between">
            <span className="text-[10px] text-slate-400 uppercase font-medium flex items-center gap-1">
              <AlertCircle className="h-3 w-3 text-amber-400" />
              Void Clauses
            </span>
            <span className="font-mono font-bold text-amber-400 text-sm mt-1">
              {auditData.unenforceable_clauses_count} Clauses
            </span>
            <span className="text-[9px] text-slate-500">Void under Georgia law</span>
          </div>

          {/* Metric 3: PII Masked */}
          <div className="bg-slate-950/90 border border-blue-900/60 rounded-lg p-2.5 flex flex-col justify-between">
            <span className="text-[10px] text-slate-400 uppercase font-medium flex items-center gap-1">
              <UserCheck className="h-3 w-3 text-blue-400" />
              Local PII Masked
            </span>
            <span className="font-mono font-bold text-blue-400 text-sm mt-1">
              {auditData.telemetry.pii_summary.total_redacted} Entities
            </span>
            <span className="text-[9px] text-slate-500">Zero Cloud Leak</span>
          </div>

          {/* Metric 4: Statutory Grounding */}
          <div className="bg-slate-950/90 border border-emerald-900/60 rounded-lg p-2.5 flex flex-col justify-between">
            <span className="text-[10px] text-slate-400 uppercase font-medium flex items-center gap-1">
              <Scale className="h-3 w-3 text-emerald-400" />
              Statutory Grounding
            </span>
            <span className="font-mono font-bold text-emerald-400 text-sm mt-1">
              {grounded}%
            </span>
            <span className="text-[9px] text-slate-500">HB 404 &amp; OCGA</span>
          </div>
        </div>
      </div>
    </div>
  );
};
