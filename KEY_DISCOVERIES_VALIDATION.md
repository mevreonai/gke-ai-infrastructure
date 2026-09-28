# KEY DISCOVERIES V6 VALIDATION REPORT
**Target HTML:** `MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_2amIST.html`
**Status:** FAIL (13/17 tests passed)

| # | Test Name | Status | Detail |
|---|---|---|---|
| 1 | `P0_Stable_IDs_1_to_10` | ✅ PASS | 10 cards and 10 pages in exact canonical sequence 1..10 |
| 2 | `P0_Trust_Strip_Wording` | ✅ PASS | Contains '119/126 COMPLETED E2E ROWS VALIDATED' & 'STRICT SUITE SIGN-OFF INCOMPLETE' |
| 3 | `P0_Measured_Transports` | ✅ PASS | Contains Native 173.58 Gb/s, 100G 56.84 Gb/s, 20G 16.48 Gb/s |
| 4 | `P0_Map_Scope_Column` | ✅ PASS | Finding map table includes dedicated Scope column |
| 5 | `P0_Coverage_Rails_On_Cards` | ✅ PASS | Found 10/10 coverage rails on Signal cards |
| 6 | `P0_Finding1_Fabric_Data` | ✅ PASS | Contains 256.889s, +276.69%, EV-078/EV-111 |
| 7 | `P0_Finding2_Concurrency_Data` | ✅ PASS | Validated 0.3415->0.3467 tok/s, 231.268s, 267.411ms, 134.428s queue; stale values eliminated |
| 8 | `P0_Finding3_Complexity_Wording` | ✅ PASS | Uses 'empirical p≈1.99'; removed 'exclusive bottleneck' |
| 9 | `P0_Finding4_Prefix_Reuse` | ❌ FAIL | Validated 94.2272s -> 2.6140s (36.0x); no '100% prefix hit' |
| 10 | `P0_Finding5_Admission_Data` | ✅ PASS | Validated 3.3586 vs 0.1846 req/s, 27.51K vs 24.19K tok/s, EV-116/EV-125 |
| 11 | `P0_Finding6_Parallelism_Frontier` | ❌ FAIL | Contains TP8/PP2 @ 664.24 GPU-s / 41.515s; never renders TP8/PP4 |
| 12 | `P0_Finding7_TP_Decode_TPOT` | ❌ FAIL | Validated 4.475/6.350ms, 10.267/12.102ms, PyTorch 251.529/583.866ms |
| 13 | `P0_Finding8_Runtime_Knobs` | ✅ PASS | Fixed 233.364s typo to 232.364s; non-binding wording present |
| 14 | `P0_Finding9_Busy_GPU` | ✅ PASS | Validated Util/TTFT pairs EV-082..EV-087; removed barrier stall claim |
| 15 | `P0_Finding10_KV_vs_VRAM` | ❌ FAIL | Validated TP8 87.27/87.51 GiB, 88.83 GiB peak; removed Global KV check & 93% saturated |
| 16 | `P0_UX_Action_Labels` | ✅ PASS | Found 30 'View Detailed Finding ↓' and 2 'Inspect Forensic Evidence →' |
| 17 | `P0_Other_Tabs_Preserved` | ✅ PASS | All 7 other tab sections verified intact and untouched |
