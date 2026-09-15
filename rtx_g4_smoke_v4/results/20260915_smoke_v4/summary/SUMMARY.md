# RTX G4 smoke-test summary

Results root: `/home/ayu23/rtx_g4_smoke/results/20260915_smoke_v4`

## NCCL exact points

| Kind | TP | Network provenance | Cap Gb/s | Size | Time (us) | algbw GB/s | busbw GB/s |
|---|---:|---|---:|---:|---:|---:|---:|
| ALLREDUCE | 4 |  |  | 8 | 18.880 | 0.000 | 0.000 |
| ALLREDUCE | 4 |  |  | 8 | 20.270 | 0.000 | 0.000 |
| ALLREDUCE | 4 |  |  | 16K | 20.170 | 0.810 | 1.220 |
| ALLREDUCE | 4 |  |  | 16K | 17.930 | 0.910 | 1.370 |
| ALLREDUCE | 4 |  |  | 128K | 20.730 | 6.320 | 9.490 |
| ALLREDUCE | 4 |  |  | 128K | 21.210 | 6.180 | 9.270 |
| ALLREDUCE | 4 |  |  | 512K | 47.810 | 10.970 | 16.450 |
| ALLREDUCE | 4 |  |  | 512K | 47.470 | 11.050 | 16.570 |
| ALLREDUCE | 4 |  |  | 64M | 2599.870 | 25.810 | 38.720 |
| ALLREDUCE | 4 |  |  | 64M | 2598.530 | 25.830 | 38.740 |
| ALLREDUCE | 4 |  |  | 128M | 5164.900 | 25.990 | 38.980 |
| ALLREDUCE | 4 |  |  | 128M | 5163.100 | 26.000 | 38.990 |
| ALLREDUCE | 4 |  |  | 256M | 10258.200 | 26.170 | 39.250 |
| ALLREDUCE | 4 |  |  | 256M | 10210.800 | 26.290 | 39.430 |
| ALLREDUCE | 8 |  |  | 8 | 39.110 | 0.000 | 0.000 |
| ALLREDUCE | 8 |  |  | 8 | 38.250 | 0.000 | 0.000 |
| ALLREDUCE | 8 |  |  | 16K | 38.240 | 0.430 | 0.750 |
| ALLREDUCE | 8 |  |  | 16K | 37.520 | 0.440 | 0.760 |
| ALLREDUCE | 8 |  |  | 128K | 38.930 | 3.370 | 5.890 |
| ALLREDUCE | 8 |  |  | 128K | 39.100 | 3.350 | 5.870 |
| ALLREDUCE | 8 |  |  | 512K | 61.390 | 8.540 | 14.950 |
| ALLREDUCE | 8 |  |  | 512K | 60.150 | 8.720 | 15.250 |
| ALLREDUCE | 8 |  |  | 64M | 2961.970 | 22.660 | 39.650 |
| ALLREDUCE | 8 |  |  | 64M | 2964.520 | 22.640 | 39.620 |
| ALLREDUCE | 8 |  |  | 128M | 5891.010 | 22.780 | 39.870 |
| ALLREDUCE | 8 |  |  | 128M | 5890.500 | 22.790 | 39.870 |
| ALLREDUCE | 8 |  |  | 256M | 11688.200 | 22.970 | 40.190 |
| ALLREDUCE | 8 |  |  | 256M | 11721.900 | 22.900 | 40.080 |
| SENDRECV |  | GCP_CAPPED_100G | 100.0 | 16K | -1.000 | 5.520 | 2.970 |
| SENDRECV |  | GCP_CAPPED_100G | 100.0 | 128K | -1.000 | 6.610 | 19.840 |
| SENDRECV |  | GCP_CAPPED_100G | 100.0 | 512K | -1.000 | 7.050 | 74.380 |
| SENDRECV |  | GCP_CAPPED_100G | 100.0 | 64M | -1.000 | 49.150 | 1365.500 |
| SENDRECV |  | GCP_CAPPED_100G | 100.0 | 128M | -1.000 | 189.570 | 708.030 |
| SENDRECV |  | GCP_CAPPED_100G | 100.0 | 256M | -1.000 | 374.840 | 716.140 |
| SENDRECV |  | GCP_CAPPED_10G | 10.0 | 16K | -1.000 | 5.280 | 3.100 |
| SENDRECV |  | GCP_CAPPED_10G | 10.0 | 128K | -1.000 | 6.550 | 20.000 |
| SENDRECV |  | GCP_CAPPED_10G | 10.0 | 512K | -1.000 | 6.910 | 75.830 |
| SENDRECV |  | GCP_CAPPED_10G | 10.0 | 64M | -1.000 | 49.600 | 1353.000 |
| SENDRECV |  | GCP_CAPPED_10G | 10.0 | 128M | -1.000 | 190.040 | 706.250 |
| SENDRECV |  | GCP_CAPPED_10G | 10.0 | 256M | -1.000 | 374.390 | 717.000 |
| SENDRECV |  | GCP_CAPPED_20G | 20.0 | 16K | -1.000 | 5.310 | 3.090 |
| SENDRECV |  | GCP_CAPPED_20G | 20.0 | 128K | -1.000 | 6.770 | 19.370 |
| SENDRECV |  | GCP_CAPPED_20G | 20.0 | 512K | -1.000 | 6.970 | 75.200 |
| SENDRECV |  | GCP_CAPPED_20G | 20.0 | 64M | -1.000 | 49.370 | 1359.300 |
| SENDRECV |  | GCP_CAPPED_20G | 20.0 | 128M | -1.000 | 189.800 | 707.150 |
| SENDRECV |  | GCP_CAPPED_20G | 20.0 | 256M | -1.000 | 374.670 | 716.460 |
| SENDRECV |  | GCP_CAPPED_50G | 50.0 | 16K | -1.000 | 5.470 | 3.000 |
| SENDRECV |  | GCP_CAPPED_50G | 50.0 | 128K | -1.000 | 6.710 | 19.530 |
| SENDRECV |  | GCP_CAPPED_50G | 50.0 | 512K | -1.000 | 6.990 | 75.040 |
| SENDRECV |  | GCP_CAPPED_50G | 50.0 | 64M | -1.000 | 49.100 | 1366.900 |
| SENDRECV |  | GCP_CAPPED_50G | 50.0 | 128M | -1.000 | 189.570 | 708.020 |
| SENDRECV |  | GCP_CAPPED_50G | 50.0 | 256M | -1.000 | 375.200 | 715.440 |
| SENDRECV |  | GCP_NATIVE | 0.0 | 16K | -1.000 | 5.340 | 3.070 |
| SENDRECV |  | GCP_NATIVE | 0.0 | 128K | -1.000 | 6.270 | 20.920 |
| SENDRECV |  | GCP_NATIVE | 0.0 | 512K | -1.000 | 7.010 | 74.790 |
| SENDRECV |  | GCP_NATIVE | 0.0 | 64M | -1.000 | 49.050 | 1368.200 |
| SENDRECV |  | GCP_NATIVE | 0.0 | 128M | -1.000 | 189.210 | 709.370 |
| SENDRECV |  | GCP_NATIVE | 0.0 | 256M | -1.000 | 374.570 | 716.640 |

## iperf3

| Network provenance | Gb/s | GB/s |
|---|---:|---:|
| GCP_CAPPED_100G | 58.75 | 7.34 |
| GCP_CAPPED_10G | 9.02 | 1.13 |
| GCP_CAPPED_20G | 16.80 | 2.10 |
| GCP_CAPPED_50G | 33.77 | 4.22 |
| GCP_NATIVE | 173.58 | 21.70 |

## Other raw metrics

- NVBandwidth numeric bandwidth/latency fields parsed: **70**
- BabelStream rows parsed: **30**
- CUTLASS rows parsed from machine-readable profiler CSV: **{len(cutlass)}**

> Check `nccl_points.csv`, `iperf.csv`, `nvbandwidth_metrics.csv`, `babelstream.csv`, `cutlass.csv`, and `summary.json` for machine-readable data.

