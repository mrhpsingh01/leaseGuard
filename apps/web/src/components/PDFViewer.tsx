"use client";

import React, { useRef, useEffect, useState } from "react";
import { FlaggedLeaseRisk, PageLayoutInfo } from "../lib/types";
import { ZoomIn, ZoomOut, RotateCcw, AlertTriangle, FileText, Loader2, UploadCloud, ShieldCheck } from "lucide-react";

interface PDFViewerProps {
  pages: PageLayoutInfo[];
  filename?: string;
  flaggedRisks: FlaggedLeaseRisk[];
  selectedClauseId: string | null;
  isLoading: boolean;
  loadingMessage?: string;
  onSelectClause: (clauseId: string) => void;
  onLoadSample: () => void;
  onUpload: () => void;
}

/**
 * Renders the PyMuPDF-rasterised pages (server side, 150 DPI) as plain <img> elements and overlays
 * each flagged clause's exact PDF-point bounding box as an absolutely positioned div (percent units,
 * so overlays stay glued to the text at every zoom level). No canvas => nothing to hydrate-mismatch.
 */
export const PDFViewer: React.FC<PDFViewerProps> = ({
  pages,
  filename,
  flaggedRisks,
  selectedClauseId,
  isLoading,
  loadingMessage,
  onSelectClause,
  onLoadSample,
  onUpload,
}) => {
  const [zoomLevel, setZoomLevel] = useState<number>(100);
  const containerRef = useRef<HTMLDivElement>(null);
  const highlightRefs = useRef<{ [clauseId: string]: HTMLDivElement | null }>({});

  // Scroll the PDF container so the selected clause's highlight is in view.
  useEffect(() => {
    if (!selectedClauseId) return;
    const container = containerRef.current;
    const target = highlightRefs.current[selectedClauseId];
    if (!container || !target) return;
    const cRect = container.getBoundingClientRect();
    const tRect = target.getBoundingClientRect();
    const top = container.scrollTop + (tRect.top - cRect.top) - container.clientHeight / 3;
    container.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
  }, [selectedClauseId, pages, zoomLevel]);

  const scale = zoomLevel / 100;

  return (
    <div className="flex flex-col h-full bg-slate-900 border-r border-slate-800">
      <div className="bg-slate-950/80 px-4 py-2 border-b border-slate-800 flex items-center justify-between gap-2 flex-wrap text-xs text-slate-300">
        <div className="flex items-center gap-2 min-w-0">
          <FileText className="h-4 w-4 text-slate-400 flex-shrink-0" />
          <span className="font-semibold text-slate-200 truncate" data-testid="pdf-title">
            {filename ? `${filename} (${pages.length} ${pages.length === 1 ? "page" : "pages"})` : "No lease loaded"}
          </span>
          <span
            className="text-[10px] px-2 py-0.5 rounded bg-red-950 text-red-300 border border-red-800/60 font-mono whitespace-nowrap"
            data-testid="highlight-count"
          >
            {flaggedRisks.length} Statutory Coordinate Highlights
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={onLoadSample}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-700 hover:bg-emerald-600 text-white font-semibold"
          >
            <ShieldCheck className="h-3.5 w-3.5" />
            Load Sample Athens Student Lease (Zero Login)
          </button>
          <button
            onClick={onUpload}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
          >
            <UploadCloud className="h-3.5 w-3.5" />
            Upload PDF
          </button>
          <button
            onClick={() => setZoomLevel((z) => Math.max(60, z - 10))}
            className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors"
            title="Zoom Out"
            aria-label="Zoom out"
          >
            <ZoomOut className="h-3.5 w-3.5" />
          </button>
          <span className="font-mono text-[11px] w-12 text-center text-slate-400">{zoomLevel}%</span>
          <button
            onClick={() => setZoomLevel((z) => Math.min(150, z + 10))}
            className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors"
            title="Zoom In"
            aria-label="Zoom in"
          >
            <ZoomIn className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setZoomLevel(100)}
            className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors"
            title="Reset Zoom"
            aria-label="Reset zoom"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      <div
        ref={containerRef}
        data-testid="pdf-scroll-container"
        className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 bg-slate-950/50 flex flex-col items-center"
      >
        {pages.length === 0 && (
          <div className="m-auto text-center text-xs text-slate-400 flex flex-col items-center gap-3" data-testid="pdf-empty">
            {isLoading ? <Loader2 className="h-8 w-8 animate-spin text-blue-400" /> : <FileText className="h-8 w-8 text-slate-600" />}
            <div>{isLoading ? loadingMessage ?? "Parsing PDF with PyMuPDF…" : "Load the sample lease or upload a PDF to begin."}</div>
          </div>
        )}

        {pages.map((page) => {
          const pageRisks = flaggedRisks.filter((r) => r.page_number === page.page_number);
          const pageWidth = page.width;
          const pageHeight = page.height;

          return (
            <div
              key={page.page_number}
              data-testid={`pdf-page-${page.page_number}`}
              className="relative shadow-2xl rounded-sm flex-shrink-0"
              style={{ width: `${pageWidth * scale}px`, height: `${pageHeight * scale}px` }}
            >
              {page.image_base64 && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={page.image_base64}
                  alt={`Lease Page ${page.page_number}`}
                  className="w-full h-full object-contain bg-white rounded-sm select-none"
                  draggable={false}
                />
              )}

              <div className="absolute inset-0 pointer-events-none">
                {pageRisks.map((risk) => {
                  const [x0, y0, x1, y1] = risk.bounding_box;
                  const isSelected = selectedClauseId === risk.clause_id;
                  const isHigh = risk.severity === "HIGH";
                  return (
                    <div
                      key={risk.clause_id}
                      ref={(el) => {
                        highlightRefs.current[risk.clause_id] = el;
                      }}
                      data-testid={`highlight-${risk.clause_id}`}
                      data-highlight="true"
                      data-selected={isSelected ? "true" : "false"}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectClause(risk.clause_id);
                      }}
                      className={`absolute pointer-events-auto cursor-pointer rounded transition-all duration-300 group ${
                        isSelected
                          ? isHigh
                            ? "bg-red-500/35 border-2 border-red-500 ring-4 ring-red-500/40 z-30 shadow-lg shadow-red-500/30"
                            : "bg-amber-500/35 border-2 border-amber-500 ring-4 ring-amber-500/40 z-30 shadow-lg shadow-amber-500/30"
                          : isHigh
                          ? "bg-red-500/20 border border-red-500/80 hover:bg-red-500/30 z-20"
                          : "bg-amber-500/20 border border-amber-500/80 hover:bg-amber-500/30 z-20"
                      }`}
                      style={{
                        left: `${(x0 / pageWidth) * 100}%`,
                        top: `${(y0 / pageHeight) * 100}%`,
                        width: `${((x1 - x0) / pageWidth) * 100}%`,
                        height: `${((y1 - y0) / pageHeight) * 100}%`,
                      }}
                    >
                      <div
                        className={`absolute -top-6 left-0 px-2 py-0.5 rounded text-[10px] font-mono font-bold tracking-wider uppercase shadow-md flex items-center gap-1 whitespace-nowrap transition-opacity ${
                          isSelected
                            ? "opacity-100 bg-red-600 text-white border border-red-400"
                            : "opacity-0 group-hover:opacity-100 bg-slate-900 text-red-300 border border-red-700"
                        }`}
                      >
                        <AlertTriangle className="h-3 w-3" />
                        <span>
                          {risk.clause_id} • {risk.rule_id}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="absolute bottom-2 right-4 text-[10px] text-slate-500 font-mono select-none">
                Page {page.page_number} of {pages.length}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
