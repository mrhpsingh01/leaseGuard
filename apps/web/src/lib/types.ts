export interface BoundingBox {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface PageLayoutInfo {
  page_number: number;
  width: number;
  height: number;
  image_base64?: string;
}

export interface RetrievalScore {
  rule_id: string;
  statute_section: string;
  bm25_score: number;
  vector_score: number;
  rrf_score: number;
  bm25_rank?: number;
  vector_rank?: number;
}

export interface FlaggedLeaseRisk {
  clause_id: string;
  page_number: number;
  bounding_box: [number, number, number, number];
  verbatim_lease_quote: string;
  statute_citation: string;
  rule_id: string;
  severity: "HIGH" | "MEDIUM" | "LOW";
  plain_english_explanation: string;
  negotiation_counter_clause: string;
  retrieval_telemetry?: RetrievalScore;
  excess_amount?: number;
}

export interface PIIRedactionSummary {
  total_redacted: number;
  entity_counts: Record<string, number>;
  redaction_latency_ms: number;
  redacted_tokens: string[];
}

export interface PipelineTelemetry {
  pdf_parse_ms: number;
  pii_redaction_ms: number;
  rule_eval_ms: number;
  retrieval_ms: number;
  total_ms: number;
  pii_summary: PIIRedactionSummary;
  chunks_indexed: number;
  statutes_evaluated: number;
  storage_mode: string;
  clauses_scanned: number;
}

export interface LeaseAuditResponse {
  lease_id: string;
  filename: string;
  property_address: string;
  tenant_name_masked: string;
  monthly_rent?: number;
  security_deposit?: number;
  deposit_cap_allowed?: number;
  deposit_excess?: number;
  overall_risk_score: number;
  unenforceable_clauses_count: number;
  flagged_risks: FlaggedLeaseRisk[];
  pages: PageLayoutInfo[];
  telemetry: PipelineTelemetry;
}

export interface ConditionEvidenceItem {
  item_id: string;
  area: string;
  item_title: string;
  withheld_amount: number;
  wear_tear_classification: "ORDINARY_WEAR_TEAR" | "TENANT_DAMAGE";
  statutory_assessment: string;
  move_in_description: string;
  move_out_description: string;
  move_in_photo_url?: string;
  move_out_photo_url?: string;
}

export interface DisputeEvaluationResponse {
  dispute_id: string;
  inspection_business_days_elapsed: number;
  inspection_timely: boolean;
  inspection_statute_citation: string;
  return_calendar_days_elapsed: number;
  return_timely: boolean;
  return_statute_citation: string;
  forfeiture_triggered: boolean;
  forfeiture_reason: string;
  treble_damages_eligible: boolean;
  treble_damages_amount: number;
  total_potential_recovery: number;
  summary_verdict: string;
  move_out_date: string;
  inspection_list_date: string | null;
  deposit_returned_date: string | null;
  current_date: string;
  total_withheld: number;
  items_evaluated: ConditionEvidenceItem[];
}

export interface DisputeScenario {
  tenant_name: string;
  landlord_name: string;
  property_address: string;
  move_out_date: string;
  inspection_list_date: string | null;
  deposit_returned_date: string | null;
  current_date: string;
  monthly_rent: number;
  deposit_paid: number;
  total_withheld: number;
}

export interface AuditProgress {
  stage: string;
  message: string;
  elapsed_ms?: number;
}
