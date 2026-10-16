"use client";

import React, { useState } from "react";
import { DisputeEvaluationResponse } from "../lib/types";
import {
  ShieldAlert,
  Clock,
  Calendar,
  AlertTriangle,
  FileDown,
  Scale,
  CheckCircle2,
  XCircle,
  Eye,
} from "lucide-react";

const fmtDate = (iso: string | null) =>
  iso ? new Date(`${iso}T00:00:00Z`).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" }) : "never";

interface DepositShieldTabProps {
  disputeData: DisputeEvaluationResponse;
  onOpenDemandLetter: () => void;
  onDownloadPdf: () => void;
  isDownloading: boolean;
}

export const DepositShieldTab: React.FC<DepositShieldTabProps> = ({
  disputeData,
  onOpenDemandLetter,
  onDownloadPdf,
  isDownloading,
}) => {
  const [activeItemIndex, setActiveItemIndex] = useState<number>(0);
  const activeItem = disputeData.items_evaluated[activeItemIndex] || disputeData.items_evaluated[0];
  const d = disputeData;
  const money = (n: number) => n.toLocaleString("en-US", { style: "currency", currency: "USD" });

  return (
    <div className="space-y-6 p-4 sm:p-5 overflow-y-auto max-h-full text-xs" data-testid="deposit-shield">
      {/* Statutory Forfeiture Banner */}
      <div className="bg-gradient-to-r from-red-950/80 via-slate-900 to-amber-950/60 border border-red-500/60 rounded-xl p-4 shadow-lg">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-red-600/20 text-red-400 border border-red-500/40">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-bold text-sm text-white">
                {d.forfeiture_triggered ? "STATUTORY FORFEITURE TRIGGERED (O.C.G.A. § 44-7-35)" : "STATUTORY DEADLINES MET"}
              </span>
              {d.forfeiture_triggered && (
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-red-900 text-red-200 border border-red-700">
                  Landlord Forfeits All Deductions
                </span>
              )}
            </div>
            <p className="text-slate-300 mt-1 leading-relaxed">
              {disputeData.summary_verdict}
            </p>
          </div>
        </div>

        {/* Financial Recovery Calculator */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4 pt-3 border-t border-slate-800">
          <div className="bg-slate-950/80 p-2.5 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-medium">Unlawfully Withheld</span>
            <div className="font-mono text-base font-bold text-amber-400 mt-0.5" data-testid="withheld-total">{money(d.total_withheld)}</div>
            <span className="text-[9px] text-slate-500">
              {d.items_evaluated.map((i) => `${i.item_title} (${money(i.withheld_amount)})`).join(" + ")}
            </span>
          </div>
          <div className="bg-slate-950/80 p-2.5 rounded-lg border border-red-900/60">
            <span className="text-[10px] text-red-400 uppercase font-medium">Statutory Multiplier</span>
            <div className="font-mono text-base font-bold text-red-400 mt-0.5" data-testid="treble-amount">
              {d.treble_damages_eligible ? `3x = ${money(d.treble_damages_amount)}` : "Not triggered"}
            </div>
            <span className="text-[9px] text-slate-500">Under O.C.G.A. § 44-7-35(c)</span>
          </div>
          <div className="bg-slate-950/80 p-2.5 rounded-lg border border-emerald-900/60">
            <span className="text-[10px] text-emerald-400 uppercase font-medium">Potential Total Recovery</span>
            <div className="font-mono text-base font-bold text-emerald-400 mt-0.5">
              {money(d.total_potential_recovery)}
            </div>
            <span className="text-[9px] text-emerald-500/80">+ Attorney Fees &amp; Costs</span>
          </div>
        </div>
      </div>

      {/* Statutory Timeline Tracker */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
        <h4 className="font-bold text-slate-200 uppercase tracking-wider text-[11px] flex items-center gap-2 mb-3">
          <Clock className="h-4 w-4 text-blue-400" />
          Georgia Statutory Deadlines &amp; Forfeiture Timeline
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Milestone 1: Move Out */}
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
            <div className="flex items-center justify-between text-slate-400 text-[10px] mb-1 font-mono">
              <span>DAY 0</span>
              <Calendar className="h-3 w-3" />
            </div>
            <div className="font-bold text-slate-200">Lease Surrender</div>
            <div className="text-slate-400 text-[11px] mt-0.5">{fmtDate(d.move_out_date)}</div>
            <div className="text-[10px] text-emerald-400 mt-1 flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3" />
              Premises surrendered
            </div>
          </div>

          {/* Milestone 2: 3-Business-Day Inspection */}
          <div className={`bg-slate-950 p-3 rounded-lg border ${d.inspection_timely ? "border-emerald-900/80" : "border-red-900/80"}`}>
            <div className="flex items-center justify-between text-red-400 text-[10px] mb-1 font-mono">
              <span>DAY 3 STATUTORY LIMIT</span>
              <XCircle className="h-3 w-3 text-red-400" />
            </div>
            <div className="font-bold text-red-300">Move-Out Damage List</div>
            <div className="text-slate-400 text-[11px] mt-0.5" data-testid="inspection-days">
              Compiled {fmtDate(d.inspection_list_date)} ({d.inspection_business_days_elapsed} business days)
            </div>
            <div className={`text-[10px] font-semibold mt-1 ${d.inspection_timely ? "text-emerald-400" : "text-red-400"}`}>
              {d.inspection_timely ? "Timely" : "VIOLATION: Exceeded 3 business days"} ({d.inspection_statute_citation})
            </div>
          </div>

          {/* Milestone 3: 30-Day Refund Deadline */}
          <div className={`bg-slate-950 p-3 rounded-lg border ${d.return_timely ? "border-emerald-900/80" : "border-red-900/80"}`}>
            <div className="flex items-center justify-between text-red-400 text-[10px] mb-1 font-mono">
              <span>DAY 30 STATUTORY LIMIT</span>
              <XCircle className="h-3 w-3 text-red-400" />
            </div>
            <div className="font-bold text-red-300">Deposit Return Window</div>
            <div className="text-slate-400 text-[11px] mt-0.5" data-testid="return-days">{d.return_calendar_days_elapsed} calendar days elapsed</div>
            <div className={`text-[10px] font-semibold mt-1 ${d.return_timely ? "text-emerald-400" : "text-red-400"}`}>
              {d.return_timely ? "Timely" : "VIOLATION: Unreturned past 30 days"} ({d.return_statute_citation})
            </div>
          </div>
        </div>
      </div>

      {/* Side-by-Side Visual Condition Comparator */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Eye className="h-4 w-4 text-emerald-400" />
            <span className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">
              Visual Condition Evidence Comparator
            </span>
          </div>

          {/* Item Selector Pills */}
          <div className="flex items-center gap-1.5">
            {disputeData.items_evaluated.map((item, idx) => (
              <button
                key={item.item_id}
                onClick={() => setActiveItemIndex(idx)}
                className={`px-2.5 py-1 rounded text-[10px] font-semibold transition-all ${
                  activeItemIndex === idx
                    ? "bg-blue-600 text-white shadow-sm"
                    : "bg-slate-800 text-slate-400 hover:text-white"
                }`}
              >
                {item.area} (${item.withheld_amount.toFixed(0)})
              </button>
            ))}
          </div>
        </div>

        {/* Side by side photos */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Move-In Baseline */}
          <div className="bg-slate-950 rounded-lg p-3 border border-slate-800">
            <div className="flex items-center justify-between text-[11px] font-semibold text-emerald-400 mb-2">
              <span>MOVE-IN BASELINE</span>
              <span className="text-[10px] text-slate-500">Initial Checklist</span>
            </div>
            <div className="aspect-[4/3] rounded overflow-hidden border border-slate-800 bg-slate-900 flex items-center justify-center">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={activeItem.move_in_photo_url || "/sample-photos/living_room_move_in.svg"}
                alt="Move-In Condition"
                className="w-full h-full object-cover"
              />
            </div>
            <p className="text-slate-400 text-[10.5px] mt-2 leading-relaxed">
              {activeItem.move_in_description}
            </p>
          </div>

          {/* Move-Out Claim */}
          <div className="bg-slate-950 rounded-lg p-3 border border-red-900/60">
            <div className="flex items-center justify-between text-[11px] font-semibold text-red-400 mb-2">
              <span>MOVE-OUT DEDUCTION CLAIM</span>
              <span className="font-mono text-amber-400 font-bold">${activeItem.withheld_amount.toFixed(2)} DOCKED</span>
            </div>
            <div className="aspect-[4/3] rounded overflow-hidden border border-slate-800 bg-slate-900 flex items-center justify-center">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={activeItem.move_out_photo_url || "/sample-photos/living_room_move_out.svg"}
                alt="Move-Out Condition"
                className="w-full h-full object-cover"
              />
            </div>
            <p className="text-slate-400 text-[10.5px] mt-2 leading-relaxed">
              {activeItem.move_out_description}
            </p>
          </div>
        </div>

        {/* Legal Assessment Callout */}
        <div className="mt-3 bg-amber-950/30 border border-amber-800/60 rounded-lg p-3">
          <div className="font-bold text-amber-400 text-[11px] flex items-center gap-1.5 mb-1">
            <Scale className="h-3.5 w-3.5" />
            Statutory Assessment: {activeItem.wear_tear_classification === "ORDINARY_WEAR_TEAR" ? "Non-Deductible Ordinary Wear and Tear" : "Tenant-Caused Damage"}
          </div>
          <p className="text-slate-300 text-[11px] leading-relaxed">
            {activeItem.statutory_assessment}
          </p>
        </div>
      </div>

      {/* Demand Letter Call-to-Action Bar */}
      <div className="bg-gradient-to-r from-blue-950 to-slate-900 border border-blue-800/60 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-lg">
        <div>
          <div className="font-bold text-sm text-white">Generate Athens-Clarke County Statutory Demand Letter</div>
          <p className="text-slate-400 text-[11px] mt-0.5">
            Cites O.C.G.A. § 44-7-33, § 44-7-34, and treble damages under § 44-7-35 with 10-day notice.
          </p>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <button
            onClick={onOpenDemandLetter}
            className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-lg font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 transition-all text-xs"
          >
            <Eye className="h-3.5 w-3.5" />
            <span>Preview Demand Letter</span>
          </button>
          
          <button
            onClick={onDownloadPdf}
            disabled={isDownloading}
            data-testid="export-demand-letter"
            className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg font-bold bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-900/40 transition-all text-xs"
          >
            <FileDown className="h-3.5 w-3.5" />
            <span>{isDownloading ? "Generating PDF..." : "Export Formal Demand Letter (PDF)"}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
