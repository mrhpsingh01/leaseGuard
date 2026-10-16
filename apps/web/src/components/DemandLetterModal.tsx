"use client";

import React from "react";
import { X, FileDown, Scale, CheckCircle2 } from "lucide-react";
import { DisputeEvaluationResponse, DisputeScenario } from "../lib/types";

const money = (n: number) => n.toLocaleString("en-US", { style: "currency", currency: "USD" });

interface DemandLetterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDownloadPdf: () => void;
  isDownloading: boolean;
  scenario: DisputeScenario;
  evaluation: DisputeEvaluationResponse;
}

export const DemandLetterModal: React.FC<DemandLetterModalProps> = ({
  isOpen,
  onClose,
  onDownloadPdf,
  isDownloading,
  scenario,
  evaluation,
}) => {
  if (!isOpen) return null;
  const today = new Date().toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="bg-slate-950 px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30">
              <Scale className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm sm:text-base text-white">
                Statutory Security Deposit Demand Letter (PDF Preview)
              </h3>
              <p className="text-xs text-slate-400">
                O.C.G.A. §§ 44-7-33, 44-7-34, &amp; 44-7-35 Treble Damages Notice
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onDownloadPdf}
              disabled={isDownloading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white transition-all shadow"
            >
              <FileDown className="h-3.5 w-3.5" />
              <span>{isDownloading ? "Exporting..." : "Download PDF"}</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Formal Letter Document Body */}
        <div className="flex-1 overflow-y-auto p-6 sm:p-8 bg-slate-950 font-serif text-slate-800 flex justify-center">
          <div className="w-full max-w-2xl bg-white p-8 sm:p-10 rounded-sm shadow-xl text-xs sm:text-[13px] leading-relaxed space-y-4">
            <div className="border-b-2 border-slate-900 pb-3 text-center">
              <h2 className="font-bold text-sm tracking-wider uppercase">
                FORMAL STATUTORY DEMAND FOR RETURN OF SECURITY DEPOSIT
              </h2>
              <div className="text-[10px] uppercase font-sans text-slate-500 tracking-wider mt-0.5">
                Delivered via Certified Mail Return Receipt Requested &amp; Electronic Transmission
              </div>
            </div>

            <div className="font-sans text-[11px] space-y-1 text-slate-700">
              <div><strong>DATE:</strong> {today}</div>
              <div><strong>TO:</strong> {scenario.landlord_name}</div>
              <div><strong>TENANT:</strong> {scenario.tenant_name}</div>
              <div><strong>PREMISES:</strong> {scenario.property_address}</div>
            </div>

            <div className="p-2.5 bg-slate-100 rounded text-[11px] font-sans font-semibold text-slate-900 border border-slate-300">
              RE: DEMAND FOR RETURN OF WITHHELD SECURITY DEPOSIT ({money(evaluation.total_withheld)}) AND NOTICE OF STATUTORY TREBLE DAMAGES ({money(evaluation.treble_damages_amount)}) PURSUANT TO O.C.G.A. §§ 44-7-33, 44-7-34, AND 44-7-35
            </div>

            <p>Dear Management of {scenario.landlord_name}:</p>
            <p>
              Please accept this letter as formal demand on behalf of Tenant {scenario.tenant_name} for the return of the <strong>{money(evaluation.total_withheld)}</strong> withheld from the {money(scenario.deposit_paid)} security deposit following surrender of the premises on {evaluation.move_out_date}.
            </p>

            <div className="space-y-2.5 pl-4 border-l-2 border-red-500 font-sans text-[11.5px]">
              {!evaluation.inspection_timely && (
                <div>
                  <strong className="text-red-700">Forfeiture under O.C.G.A. § 44-7-33:</strong> the damage list is due within three (3) business days of surrender; Landlord delivered it after {evaluation.inspection_business_days_elapsed} business days.
                </div>
              )}
              {!evaluation.return_timely && (
                <div>
                  <strong className="text-red-700">Forfeiture under O.C.G.A. § 44-7-34:</strong> the deposit is due within thirty (30) calendar days; {evaluation.return_calendar_days_elapsed} calendar days have elapsed.
                </div>
              )}
              {evaluation.items_evaluated
                .filter((i) => i.wear_tear_classification === "ORDINARY_WEAR_TEAR")
                .map((i) => (
                  <div key={i.item_id}>
                    <strong className="text-red-700">Ordinary wear and tear ({money(i.withheld_amount)}):</strong> {i.item_title}. {i.statutory_assessment}
                  </div>
                ))}
            </div>

            {evaluation.treble_damages_eligible && (
              <>
                <p className="font-sans text-[11.5px] font-bold text-slate-900">NOTICE OF TREBLE DAMAGES CLAIM UNDER O.C.G.A. § 44-7-35:</p>
                <p>
                  Landlord is liable for <strong>THREE TIMES THE SUM IMPROPERLY WITHHELD ({money(evaluation.treble_damages_amount)})</strong>, plus reasonable attorney&apos;s fees and court costs. Tenant demands payment of <strong>{money(evaluation.total_withheld)}</strong> within ten (10) calendar days of delivery; otherwise Tenant will commence an action in the Magistrate Court of Athens-Clarke County, Georgia.
                </p>
              </>
            )}

            <div className="pt-4 font-sans text-[11px] space-y-1">
              <div>Respectfully submitted,</div>
              <div className="font-bold text-sm font-serif">/s/ {scenario.tenant_name}</div>
              <div>Tenant, {scenario.property_address}</div>
              <div className="text-slate-500 text-[10px] pt-2">
                Copy delivered to Athens-Clarke County Tenants Union
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="bg-slate-950 px-6 py-3 border-t border-slate-800 flex items-center justify-between">
          <span className="text-xs text-slate-400 flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            Generated from the deterministic O.C.G.A. § 44-7-33/34/35 engine
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
          >
            Close Preview
          </button>
        </div>
      </div>
    </div>
  );
};
