"use client";

import React, { useState } from "react";
import { FlaggedLeaseRisk } from "../lib/types";
import {
  AlertTriangle,
  Scale,
  Copy,
  Check,
  ChevronRight,
  ExternalLink,
  ShieldAlert,
} from "lucide-react";

interface RiskCardListProps {
  flaggedRisks: FlaggedLeaseRisk[];
  selectedClauseId: string | null;
  onSelectClause: (clauseId: string) => void;
  isStreaming?: boolean;
}

export const RiskCardList: React.FC<RiskCardListProps> = ({
  flaggedRisks,
  selectedClauseId,
  onSelectClause,
  isStreaming = false,
}) => {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = async (clauseId: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Clipboard API unavailable (insecure context / denied): fall back to a hidden textarea.
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    setCopiedId(clauseId);
    setTimeout(() => {
      setCopiedId(null);
    }, 2000);
  };

  return (
    <div className="space-y-4 p-4 sm:p-5 overflow-y-auto max-h-full" data-testid="risk-list">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <ShieldAlert className="h-4 w-4 text-red-500" />
          Flagged Georgia Statutory Violations ({flaggedRisks.length})
        </h3>
        <span className="text-[11px] text-slate-500">
          Click any card to locate on PDF canvas
        </span>
      </div>

      {flaggedRisks.length === 0 && (
        <div className="text-xs text-slate-400 border border-slate-800 rounded-xl p-4 bg-slate-900/60">
          {isStreaming ? "Streaming clause analysis…" : "No statutory violations were detected in this lease."}
        </div>
      )}

      {flaggedRisks.map((risk) => {
        const isSelected = selectedClauseId === risk.clause_id;
        const isCopied = copiedId === risk.clause_id;

        return (
          <div
            key={risk.clause_id}
            data-testid="risk-card"
            data-clause-id={risk.clause_id}
            data-selected={isSelected ? "true" : "false"}
            onClick={() => onSelectClause(risk.clause_id)}
            className={`border rounded-xl p-4 transition-all duration-200 cursor-pointer text-xs ${
              isSelected
                ? "bg-slate-900 border-red-500 ring-2 ring-red-500/30 shadow-xl shadow-red-950/40"
                : "bg-slate-900/60 hover:bg-slate-900 border-slate-800 hover:border-slate-700 shadow-md"
            }`}
          >
            {/* Header: Severity, Clause ID, Page Number */}
            <div className="flex items-center justify-between mb-2.5">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-red-950 text-red-300 border border-red-800 flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3 text-red-400" />
                  {risk.severity} RISK
                </span>
                <span className="font-mono text-slate-400 text-[11px] font-semibold">
                  {risk.clause_id}
                </span>
              </div>
              <span className="text-slate-500 text-[11px] font-medium">
                Page {risk.page_number}
              </span>
            </div>

            {/* Verbatim Lease Quote */}
            <div className="bg-slate-950/80 rounded-lg p-2.5 border-l-2 border-red-500 border-y border-r border-slate-800/80 mb-3">
              <div className="text-[10px] uppercase font-mono text-slate-500 mb-1">
                Verbatim Lease Language:
              </div>
              <p className="text-slate-200 italic font-mono text-[11px] leading-relaxed">
                &ldquo;{risk.verbatim_lease_quote}&rdquo;
              </p>
            </div>

            {/* Statutory Grounding Citation */}
            <div className="flex items-center gap-1.5 text-blue-400 mb-2">
              <Scale className="h-3.5 w-3.5 flex-shrink-0" />
              <span className="font-semibold text-[11px]">
                {risk.statute_citation}
              </span>
            </div>

            {/* Plain English Legal Assessment */}
            <p className="text-slate-300 leading-relaxed mb-3 text-[11px]">
              {risk.plain_english_explanation}
            </p>

            {/* Tenant Counter-Clause Box */}
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-3">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] uppercase font-bold text-emerald-400 flex items-center gap-1">
                  Ready-to-Use Tenant Counter-Clause:
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCopy(risk.clause_id, risk.negotiation_counter_clause);
                  }}
                  className={`flex items-center gap-1 px-2.5 py-1 rounded text-[10px] font-bold transition-all ${
                    isCopied
                      ? "bg-emerald-600 text-white"
                      : "bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700"
                  }`}
                  title="Copy replacement text to clipboard"
                  aria-label="Copy Tenant Counter-Clause"
                >
                  {isCopied ? (
                    <>
                      <Check className="h-3 w-3" />
                      <span>Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3" />
                      <span>Copy Tenant Counter-Clause</span>
                    </>
                  )}
                </button>
              </div>
              <p className="text-slate-400 font-mono text-[10.5px] leading-normal select-all">
                {risk.negotiation_counter_clause}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
};
