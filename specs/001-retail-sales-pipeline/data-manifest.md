# Synthetic Data Manifest — NexaRetail

**Feature:** 001-retail-sales-pipeline  
**Version:** 1.0.0  
**Status:** Approved distribution and fixture contract; generation not implemented  
**Input sales rows:** 100,000  
**Generator seed:** 20271024 (planned technical setting)  
**Generator version:** 0.1.0 (planned)

## Approved mutually exclusive distribution

| Final disposition | Input rows | Description |
| --- | ---: | --- |
| Accepted unique | 94,618 | Valid rows with unique business keys |
| Exact duplicate | 3,006 | Extra identical copies of 3,006 distinct accepted sales |
| Invalid | 1,176 | Rows with one intentional validation defect |
| Conflicting | 1,200 | 600 disjoint two-row groups sharing keys but with different valid payloads |
| **Total** | **100,000** | **94,618 + 3,006 + 1,176 + 1,200** |

**Approved by project owner:** the four category counts and total above. All other details below are technical design choices subject to validation.

Expected unique fact rows after initial load: **94,618**. Reprocessing the identical batch in the same database must insert **0** new sales and retain **94,618** fact rows, with unchanged revenue.

## Proposed invalid-row reason distribution (sums to 1,176)

| Primary reason code | Rows |
| --- | ---: |
| MISSING_REQUIRED | 176 |
| INVALID_DATE | 200 |
| INVALID_MONEY | 200 |
| INVALID_QUANTITY | 150 |
| TOTAL_MISMATCH | 150 |
| UNKNOWN_BRANCH | 150 |
| UNKNOWN_PRODUCT | 150 |
| **Total** | **1,176** |

`INVALID_TYPE` is covered by focused test fixtures but has zero occurrences in this baseline. The proposed reason split is not separately approved; adjust before implementation if desired without changing the 1,176 invalid-row total.

## Deterministic generator contract

- Generate exactly 5 valid branches (`F001`–`F005`) and 200 valid products (`P0001`–`P0200`).
- Create 94,618 valid unique sales, each with a distinct `(branch_id, sale_id)`.
- Append 3,006 exact duplicates of distinct accepted sales; count only the additional copies as duplicates.
- Append 1,176 invalid rows with distinct keys outside all accepted and conflict groups; each has one designated defect.
- Append 600 disjoint conflict keys, each appearing in exactly two different otherwise-valid normalized records; classify **both** rows as conflicting, so 1,200 conflicting input rows and zero accepted rows from those groups.
- Shuffle deterministically with a fixed PRNG seed and a versioned algorithm; record runtime and SHA-256 output hashes.
- Record source filename and CSV row number for every row. Every row has exactly one disposition.
- Generate monetary values using two-decimal decimal strings. Valid records must satisfy `quantity × unit_price = total_amount`.
- Compute exact expected revenue from the 94,618 accepted unique sales and publish expected per-branch totals in the generated run summary. Never invent an uncalculated revenue total.
- Do not commit full generated sales CSVs; publish sanitized reports through GitHub Actions artifacts.

## Required reconciliation assertions

```text
100000 = 94618 accepted + 3006 duplicate + 1176 invalid + 1200 conflict
1200 conflict rows = 600 conflict groups * 2 rows
94618 initial fact_sale rows
94618 fact_sale rows after exact same-batch replay
0 newly inserted rows on replay
sum(branch unique sale counts) = 94618
sum(branch revenue) = sum(accepted unique sale total_amount)
```

## Evidence boundary

These are approved expected quantities, **not observed pipeline results**. T002's quantity decision is recorded; T002 remains pending until generation and automated checks verify the distribution. Any deviation must update the manifest, specification, plan, and tests together.
