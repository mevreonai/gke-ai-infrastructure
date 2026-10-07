# KEY DISCOVERIES V6 VALIDATION REPORT
**Target HTML (Dual Tabs):** `MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST.html`
**Target HTML (Clean Top-10):** `MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST_NO_KEYFINDS.html`
**Status:** PASS (18/18 tests passed)

| # | Test Name | Status | Detail |
|---|---|---|---|
| 1 | `P0_Stable_IDs_1_to_10` | ✅ PASS | 10 full-depth discovery pages in exact canonical sequence 1..10 |
| 2 | `P0_Trust_Strip_Wording` | ✅ PASS | Contains Application 119/126, Profile 14/22, and Strict Sign-Off Incomplete |
| 3 | `P0_Measured_Transports` | ✅ PASS | Contains Native 173.58 Gb/s, 100G 56.84 Gb/s, 20G 16.48 Gb/s |
| 4 | `P0_Map_Scope_Column` | ✅ PASS | Finding map table includes dedicated Scope column |
| 5 | `P0_Coverage_Rails_On_Cards` | ✅ PASS | Found 12/10 coverage rails on Signal cards |
| 6 | `P0_Finding1_Fabric_Data` | ✅ PASS | Canonical 20G values enforced; stale literals 2.926, 18.860, 2.510, 15.650 completely eliminated |
| 7 | `P0_Finding2_Concurrency_Data` | ✅ PASS | Validated 0.3415->0.3467 tok/s, 231.268s TTFT, 267.411ms TPOT, 134.428s queue |
| 8 | `P0_Finding3_Complexity_Wording` | ✅ PASS | Uses 'empirical p≈1.99'; removed quadratic prefill expansion claims |
| 9 | `P0_Finding4_Prefix_Reuse` | ✅ PASS | Validated cold vs repeat-hit speedup (36.0x @ 1M) |
| 10 | `P0_Finding5_Admission_Data` | ✅ PASS | Validated 3.3586 vs 0.1846 req/s admission throughput |
| 11 | `P0_Finding6_Parallelism_Frontier` | ✅ PASS | Contains TP8/PP2 @ 664.24 GPU-s / 41.515s measured point; TP8/PP4 never rendered |
| 12 | `P0_Finding7_TP_Decode_TPOT` | ✅ PASS | Validated TP4/TP8 PyTorch AllReduce breakdown 251.53ms vs 583.87ms |
| 13 | `P0_Finding8_Runtime_Knobs` | ✅ PASS | Fixed 233.364s typo; chunk -27.1% verified; maxseq flat |
| 14 | `P0_Finding9_Busy_GPU` | ✅ PASS | Neutral activity labels applied; Erroneous High / Fast & Efficient removed |
| 15 | `P0_Finding10_KV_vs_VRAM` | ✅ PASS | Peak GPU Memory Telemetry used; Global KV check and 93% saturated removed |
| 16 | `P0_UX_Action_Labels` | ✅ PASS | Signal uses 'View Detailed Finding ↓'; Engineer uses 'Inspect Evidence →'; Forensic Modal View removed |
| 17 | `P0_With_KeyFinds_Nav_Integrity` | ✅ PASS | Version 1 keeps 'Key Finds' tab active alongside 'Key Discoveries' |
| 18 | `P0_No_KeyFinds_Nav_Isolation` | ✅ PASS | Version 2 removes/hides legacy Key Finds tab; Key Discoveries is single top-level Top-10 |
