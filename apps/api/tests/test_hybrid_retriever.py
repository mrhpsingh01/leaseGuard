"""
Tests for Hybrid Statutory Retriever (BM25 + Dense Cosine Vector + RRF)
"""

from apps.api.services.hybrid_retriever import HybridRetrieverService

def test_hybrid_retriever_all_statutes():
    retriever = HybridRetrieverService()
    assert len(retriever.statutes) == 5

    # Test 1: Deposit Cap
    results = retriever.retrieve("security deposit exceeds two months rent 44-7-30.1 cap", top_k=1)
    assert len(results) == 1
    statute, score = results[0]
    assert statute["rule_id"] == "GA-HB404-DEPOSIT-CAP"
    assert score.bm25_score > 0
    assert score.vector_score > 0
    assert score.rrf_score > 0

    # Test 2: Habitability / AC shutoff
    results = retriever.retrieve("landlord shut off air conditioning cooling maintenance HVAC", top_k=1)
    statute, score = results[0]
    assert statute["rule_id"] == "GA-HB404-HABITABILITY"

    # Test 3: Right to Cure / Eviction Notice
    results = retriever.retrieve("three-day notice right to cure grace period eviction dispossessory", top_k=1)
    statute, score = results[0]
    assert statute["rule_id"] == "GA-HB404-CURE-PERIOD"

    # Test 4: Move-Out Inspection
    results = retriever.retrieve("move-out inspection comprehensive damage list three business days", top_k=1)
    statute, score = results[0]
    assert statute["rule_id"] == "GA-OCGA-44-7-33-INSPECTION"

    # Test 5: Deposit Return & Treble Damages
    results = retriever.retrieve("thirty days deposit refund treble damages three times withheld 44-7-34", top_k=1)
    statute, score = results[0]
    assert statute["rule_id"] == "GA-OCGA-44-7-34-RETURN"
