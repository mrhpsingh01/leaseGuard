"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { Header } from "../components/Header";
import { ScenarioBar, ScenarioType } from "../components/ScenarioBar";
import { PDFViewer } from "../components/PDFViewer";
import { RiskScorecard } from "../components/RiskScorecard";
import { RiskCardList } from "../components/RiskCardList";
import { DepositShieldTab } from "../components/DepositShieldTab";
import { DemandLetterModal } from "../components/DemandLetterModal";
import { EngineeringDrawer } from "../components/EngineeringDrawer";
import {
  ApiError,
  downloadDemandLetterPdf,
  evaluateDispute,
  fetchSampleScenario,
  streamLeaseAudit,
} from "../lib/api";
import {
  AuditProgress,
  DisputeEvaluationResponse,
  DisputeScenario,
  FlaggedLeaseRisk,
  LeaseAuditResponse,
} from "../lib/types";
import { AlertTriangle, Loader2, RefreshCw, ShieldAlert, ShieldCheck, X } from "lucide-react";

type Status = "idle" | "streaming" | "done" | "error";

interface BannerState {
  message: string;
  retry: (() => void) | null;
}

export default function Home() {
  const [activeScenario, setActiveScenario] = useState<ScenarioType>("LEASE_SCAN");
  const [activeTab, setActiveTab] = useState<"AUDIT" | "DEPOSIT_SHIELD">("AUDIT");

  const [status, setStatus] = useState<Status>("idle");
  const [progress, setProgress] = useState<AuditProgress[]>([]);
  const [liveRisks, setLiveRisks] = useState<FlaggedLeaseRisk[]>([]);
  const [auditData, setAuditData] = useState<LeaseAuditResponse | null>(null);
  const [selectedClauseId, setSelectedClauseId] = useState<string | null>(null);

  const [scenario, setScenario] = useState<DisputeScenario | null>(null);
  const [disputeData, setDisputeData] = useState<DisputeEvaluationResponse | null>(null);
  const [disputeLoading, setDisputeLoading] = useState(false);

  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isDemandModalOpen, setIsDemandModalOpen] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [banner, setBanner] = useState<BannerState | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const showError = useCallback((err: unknown, retry: (() => void) | null) => {
    const message = err instanceof Error ? err.message : "Something went wrong.";
    const retryable = err instanceof ApiError ? err.retryable : true;
    setBanner({ message, retry: retryable ? retry : null });
  }, []);

  /** Run the live SSE audit pipeline on the sample lease (no file) or an uploaded PDF. */
  const runAudit = useCallback(
    async (file?: File) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setStatus("streaming");
      setBanner(null);
      setProgress([]);
      setLiveRisks([]);
      setAuditData(null);
      setSelectedClauseId(null);
      try {
        const result = await streamLeaseAudit(
          {
            onProgress: (p) => setProgress((prev) => [...prev, p]),
            onClause: (r) => setLiveRisks((prev) => [...prev, r]),
          },
          file,
          controller.signal
        );
        if (controller.signal.aborted) return;
        setAuditData(result);
        setLiveRisks(result.flagged_risks);
        setStatus("done");
      } catch (err) {
        if (controller.signal.aborted) return;
        setStatus("error");
        showError(err, () => runAudit(file));
      }
    },
    [showError]
  );

  const loadDispute = useCallback(async () => {
    setDisputeLoading(true);
    setBanner(null);
    try {
      const sc = scenario ?? (await fetchSampleScenario());
      const evaluation = await evaluateDispute(sc);
      setScenario(sc);
      setDisputeData(evaluation);
    } catch (err) {
      showError(err, () => loadDispute());
    } finally {
      setDisputeLoading(false);
    }
  }, [scenario, showError]);

  // Zero-login landing: the sample lease audit starts streaming immediately.
  useEffect(() => {
    runAudit();
    return () => abortRef.current?.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSelectScenario = (next: ScenarioType) => {
    setActiveScenario(next);
    if (next === "LEASE_SCAN") {
      setActiveTab("AUDIT");
      runAudit();
    } else if (next === "DEPOSIT_DISPUTE") {
      setActiveTab("DEPOSIT_SHIELD");
      if (!disputeData) loadDispute();
    } else {
      setActiveTab("AUDIT");
      fileInputRef.current?.click();
    }
  };

  const handleFileChosen = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setActiveScenario("UPLOAD_CUSTOM");
    setActiveTab("AUDIT");
    runAudit(file);
  };

  const handleDownloadDemandLetter = async () => {
    if (!scenario) return;
    setIsDownloadingPdf(true);
    setBanner(null);
    try {
      const blob = await downloadDemandLetterPdf(scenario);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "LeaseGuard_Security_Deposit_Demand_Letter_OCGA_44-7-35.pdf";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => window.URL.revokeObjectURL(url), 10_000);
    } catch (err) {
      showError(err, () => handleDownloadDemandLetter());
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const risks = auditData?.flagged_risks ?? liveRisks;
  const selectedRisk = risks.find((r) => r.clause_id === selectedClauseId);
  const lastProgress = progress[progress.length - 1];

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-slate-950 font-sans">
      <Header isDrawerOpen={isDrawerOpen} onToggleDrawer={() => setIsDrawerOpen(!isDrawerOpen)} />

      <ScenarioBar activeScenario={activeScenario} onSelectScenario={handleSelectScenario} />

      <input
        ref={fileInputRef}
        type="file"
        accept="application/pdf,.pdf"
        className="hidden"
        data-testid="lease-upload"
        onChange={handleFileChosen}
      />

      {banner && (
        <div
          role="alert"
          data-testid="error-banner"
          className="bg-red-950 border-b border-red-800 text-red-100 px-4 sm:px-6 py-2.5 flex items-center gap-3 text-xs"
        >
          <AlertTriangle className="h-4 w-4 text-red-400 flex-shrink-0" />
          <span className="flex-1">{banner.message}</span>
          {banner.retry && (
            <button
              onClick={banner.retry}
              className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-red-700 hover:bg-red-600 text-white font-semibold"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Retry
            </button>
          )}
          <button onClick={() => setBanner(null)} aria-label="Dismiss" className="p-1 text-red-300 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <main className="flex-1 flex flex-col md:flex-row overflow-hidden" data-testid="workspace">
        <section className="w-full md:w-1/2 lg:w-7/12 h-1/2 md:h-full relative overflow-hidden flex flex-col">
          <PDFViewer
            pages={auditData?.pages ?? []}
            filename={auditData?.filename}
            flaggedRisks={risks}
            selectedClauseId={selectedClauseId}
            isLoading={status === "streaming"}
            loadingMessage={lastProgress?.message}
            onSelectClause={(id) => {
              setSelectedClauseId(id);
              setActiveTab("AUDIT");
            }}
            onLoadSample={() => handleSelectScenario("LEASE_SCAN")}
            onUpload={() => fileInputRef.current?.click()}
          />
        </section>

        <section className="w-full md:w-1/2 lg:w-5/12 h-1/2 md:h-full flex flex-col bg-slate-950 border-t md:border-t-0 border-slate-800 overflow-hidden">
          {auditData && <RiskScorecard auditData={auditData} />}
          {!auditData && (
            <div className="bg-slate-900 border-b border-slate-800 p-4 sm:p-5 text-xs text-slate-300 flex items-center gap-3" data-testid="stream-status">
              {status === "streaming" ? (
                <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />
              ) : (
                <ShieldAlert className="h-5 w-5 text-slate-500" />
              )}
              <div>
                <div className="font-semibold text-white">
                  {status === "streaming" ? "Auditing lease…" : "No lease loaded"}
                </div>
                <div className="text-slate-400">
                  {lastProgress?.message ?? "Load the sample lease or upload your own PDF."}
                </div>
              </div>
            </div>
          )}

          <div className="bg-slate-900/90 border-b border-slate-800 px-4 sm:px-5 flex items-center gap-4 text-xs font-semibold">
            <button
              onClick={() => setActiveTab("AUDIT")}
              className={`py-3 flex items-center gap-2 border-b-2 transition-all ${
                activeTab === "AUDIT" ? "border-red-500 text-white font-bold" : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <ShieldAlert className="h-4 w-4 text-red-500" />
              <span>Statutory Risks ({risks.length})</span>
            </button>

            <button
              onClick={() => {
                setActiveTab("DEPOSIT_SHIELD");
                setActiveScenario("DEPOSIT_DISPUTE");
                if (!disputeData) loadDispute();
              }}
              className={`py-3 flex items-center gap-2 border-b-2 transition-all ${
                activeTab === "DEPOSIT_SHIELD" ? "border-amber-500 text-white font-bold" : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <ShieldCheck className="h-4 w-4 text-amber-500" />
              <span>Deposit Shield &amp; Demand Letter</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800/80 font-mono">3x Treble</span>
            </button>
          </div>

          <div className="flex-1 overflow-y-auto" data-testid="right-pane">
            {activeTab === "AUDIT" ? (
              <RiskCardList
                flaggedRisks={risks}
                selectedClauseId={selectedClauseId}
                onSelectClause={(id) => setSelectedClauseId(id)}
                isStreaming={status === "streaming"}
              />
            ) : disputeData && scenario ? (
              <DepositShieldTab
                disputeData={disputeData}
                onOpenDemandLetter={() => setIsDemandModalOpen(true)}
                onDownloadPdf={handleDownloadDemandLetter}
                isDownloading={isDownloadingPdf}
              />
            ) : (
              <div className="p-6 text-xs text-slate-400 flex items-center gap-2">
                {disputeLoading && <Loader2 className="h-4 w-4 animate-spin text-amber-400" />}
                {disputeLoading ? "Evaluating statutory deadlines…" : "Dispute evaluation unavailable."}
              </div>
            )}
          </div>
        </section>
      </main>

      {disputeData && scenario && (
        <DemandLetterModal
          isOpen={isDemandModalOpen}
          onClose={() => setIsDemandModalOpen(false)}
          onDownloadPdf={handleDownloadDemandLetter}
          isDownloading={isDownloadingPdf}
          scenario={scenario}
          evaluation={disputeData}
        />
      )}

      {auditData && (
        <EngineeringDrawer
          isOpen={isDrawerOpen}
          onClose={() => setIsDrawerOpen(false)}
          telemetry={auditData.telemetry}
          selectedRisk={selectedRisk}
          fullAuditData={auditData}
        />
      )}
      {!auditData && isDrawerOpen && (
        <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-slate-950 border-l border-slate-800 p-6 text-xs text-slate-300" data-testid="telemetry-pending">
          <button onClick={() => setIsDrawerOpen(false)} className="float-right p-1 text-slate-400 hover:text-white" aria-label="Close inspector">
            <X className="h-4 w-4" />
          </button>
          Pipeline telemetry appears once an audit completes.
        </div>
      )}
    </div>
  );
}
