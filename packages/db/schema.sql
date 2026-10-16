-- LeaseGuard Database Schema
-- Supports PostgreSQL with pgvector extension

CREATE EXTENSION IF NOT EXISTS vector;

-- Georgia Landlord-Tenant Statutory Corpus Table
CREATE TABLE IF NOT EXISTS georgia_statutes (
    id SERIAL PRIMARY KEY,
    rule_id VARCHAR(64) UNIQUE NOT NULL,
    statute_title VARCHAR(255) NOT NULL,
    section VARCHAR(64) NOT NULL,
    category VARCHAR(64) NOT NULL,
    statutory_requirement TEXT NOT NULL,
    rule_summary TEXT NOT NULL,
    full_text TEXT NOT NULL,
    remedy TEXT NOT NULL,
    standard_counter_clause TEXT NOT NULL,
    severity VARCHAR(16) NOT NULL DEFAULT 'HIGH',
    embedding vector(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Leases table
CREATE TABLE IF NOT EXISTS leases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    property_address TEXT,
    tenant_name_masked VARCHAR(255),
    monthly_rent NUMERIC(10, 2),
    security_deposit NUMERIC(10, 2),
    page_count INT NOT NULL DEFAULT 1,
    overall_risk_score INT NOT NULL DEFAULT 0,
    pii_redacted_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Flagged Lease Clauses Table
CREATE TABLE IF NOT EXISTS lease_clauses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lease_id UUID REFERENCES leases(id) ON DELETE CASCADE,
    clause_id VARCHAR(64) NOT NULL,
    page_number INT NOT NULL,
    bounding_box JSONB NOT NULL, -- [x0, y0, x1, y1]
    verbatim_lease_quote TEXT NOT NULL,
    statute_citation VARCHAR(255) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    plain_english_explanation TEXT NOT NULL,
    negotiation_counter_clause TEXT NOT NULL,
    bm25_score NUMERIC(8, 4),
    vector_score NUMERIC(8, 4),
    rrf_score NUMERIC(8, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Deposit Disputes Table
CREATE TABLE IF NOT EXISTS deposit_disputes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lease_id UUID REFERENCES leases(id) ON DELETE SET NULL,
    property_address TEXT NOT NULL,
    move_out_date DATE NOT NULL,
    inspection_list_date DATE,
    deposit_returned_date DATE,
    deposit_paid NUMERIC(10, 2) NOT NULL,
    amount_withheld NUMERIC(10, 2) NOT NULL,
    inspection_days_elapsed INT,
    return_days_elapsed INT,
    inspection_timely BOOLEAN NOT NULL DEFAULT true,
    return_timely BOOLEAN NOT NULL DEFAULT true,
    forfeiture_triggered BOOLEAN NOT NULL DEFAULT false,
    treble_damages_eligible BOOLEAN NOT NULL DEFAULT false,
    potential_recovery NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Dispute Condition Photos & Evidence
CREATE TABLE IF NOT EXISTS dispute_evidence_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispute_id UUID REFERENCES deposit_disputes(id) ON DELETE CASCADE,
    item_title VARCHAR(128) NOT NULL,
    area VARCHAR(64) NOT NULL,
    withheld_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    wear_tear_classification VARCHAR(32) NOT NULL, -- 'ORDINARY_WEAR_TEAR' | 'DAMAGE'
    statutory_assessment TEXT NOT NULL,
    move_in_photo_path TEXT,
    move_out_photo_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
