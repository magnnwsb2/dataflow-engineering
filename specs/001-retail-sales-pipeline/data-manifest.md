# Synthetic Data Manifest — NexaRetail

**Feature:** 001-retail-sales-pipeline  
**Version:** 0.1.0  
**Status:** Proposed fixture contract; not yet generated or verified  
**Input sales rows:** 100,000  
**Generator seed:** 20271024  
**Generator version:** 0.1.0 (planned)

## Proposed distribution

| Exclusive disposition | Input rows | Definition |
| --- | ---: | --- |
| Accepted unique | 94,000 | Valid, unique business keys |
| Exact duplicate | 3,000 | Additional copies of 3,000 accepted rows |
| Invalid | 2,000 | Rows with one designated validation defect |
| Conflicting | 1,000 | 500 two-row groups, each pair shares a business key but has distinct valid normalized payloads |
| **Total** | **100,000** | **94,000 + 3,000 + 2,000 + 1,000** |

Expected unique loaded sales after the initial load: **94,000**. Expected inserted on exact same-batch replay: **0**; expected already-present accepted sales: **94,000**. Replaying the batch must not change revenue or row counts.

## Proposed invalid-row breakdown

| Reason code | Rows |
| --- | ---: |
| MISSING_REQUIRED | 300 |
| INVALID_DATE | 300 |
| INVALID_MONEY | 300 |
| INVALID_QUANTITY | 250 |
| TOTAL_MISMATCH | 300 |
| UNKNOWN_BRANCH | 250 |
| UNKNOWN_PRODUCT | 300 |
| **Total** | **2,000** |

`INVALID_TYPE` remains supported and covered in focused test fixtures; its count is zero in the 100k baseline. Each invalid row must contain exactly one intended defect to make expected classification deterministic.

## Deterministic generation contract

- Generate 5 valid branches (F001–F005) and 200 valid products (P0001–P0200).
- Create 94,000 valid unique sales with unique `(branch_id, sale_id)` keys.
- Add 3,000 identical normalized copies of distinct accepted sales.
- Add 2,000 invalid rows, with unique keys disjoint from accepted and conflict groups; assign one invalid reason per row.
- Add 500 disjoint conflicting keys, each represented by 2 structurally valid but different sales rows (1,000 rows total); neither version is accepted.
- Shuffle rows using a fixed seeded PRNG and stable algorithm; generator must record its version, Python runtime version, and output SHA-256 hashes.
- Each input row receives a source CSV row number; every row receives exactly one final disposition.
- Monetary values use Decimal-compatible two-decimal source strings; generated valid rows satisfy quantity × unit_price = total_amount.
- Compute exact expected revenue from the generated valid unique rows, not an invented hardcoded amount. Store that value and per-branch counts in the generated run manifest.
- Never commit full 100,000-row outputs; publish sanitized generation/quality summaries as Actions artifacts.

## Reconciliation checks

```text
100000 = 94000 accepted + 3000 duplicates + 2000 invalid + 1000 conflicting
conflicting groups = 500
fact_sale initial row count = 94000
fact_sale replay row count = 94000
sum(branch unique sales) = 94000
sum(branch revenue) = sum(accepted unique sale total_amount)
```

## Approval and evidence

This is a **proposed test contract**, not proof of successful generation. T002 is complete only after this distribution is approved and generator tests confirm it. If the generator reveals ambiguity or implementation conflicts, revise the spec/plan/manifest before claiming acceptance.
