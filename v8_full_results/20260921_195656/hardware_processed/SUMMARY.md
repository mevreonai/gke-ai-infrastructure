# RTX G4 smoke-test summary

Results root: `/home/ayu23/v8_full_results/20260921_195656/hardware_raw`

## NCCL exact points

| Kind | TP | Network provenance | Cap Gb/s | Size | Time (us) | algbw GB/s | busbw GB/s |
|---|---:|---|---:|---:|---:|---:|---:|
| ALLREDUCE | 4 |  |  | 16K | 19.660 | 0.830 | 1.250 |
| ALLREDUCE | 4 |  |  | 16K | 19.040 | 0.860 | 1.290 |
| ALLREDUCE | 4 |  |  | 16K | 19.040 | 0.860 | 1.290 |
| ALLREDUCE | 4 |  |  | 128K | 28.640 | 4.580 | 6.870 |
| ALLREDUCE | 4 |  |  | 128K | 28.660 | 4.570 | 6.860 |
| ALLREDUCE | 4 |  |  | 128K | 28.660 | 4.570 | 6.860 |
| ALLREDUCE | 4 |  |  | 512K | 78.210 | 6.700 | 10.060 |
| ALLREDUCE | 4 |  |  | 512K | 78.510 | 6.680 | 10.020 |
| ALLREDUCE | 4 |  |  | 512K | 78.510 | 6.680 | 10.020 |
| ALLREDUCE | 4 |  |  | 64M | 3986.410 | 16.830 | 25.250 |
| ALLREDUCE | 4 |  |  | 64M | 3992.230 | 16.810 | 25.210 |
| ALLREDUCE | 4 |  |  | 64M | 3992.230 | 16.810 | 25.210 |
| ALLREDUCE | 4 |  |  | 128M | 7894.300 | 17.000 | 25.500 |
| ALLREDUCE | 4 |  |  | 128M | 7936.630 | 16.910 | 25.370 |
| ALLREDUCE | 4 |  |  | 128M | 7936.630 | 16.910 | 25.370 |
| ALLREDUCE | 4 |  |  | 256M | 15515.000 | 17.300 | 25.950 |
| ALLREDUCE | 4 |  |  | 256M | 15435.100 | 17.390 | 26.090 |
| ALLREDUCE | 4 |  |  | 256M | 15435.100 | 17.390 | 26.090 |
| ALLREDUCE | 8 |  |  | 16K | 37.030 | 0.440 | 0.770 |
| ALLREDUCE | 8 |  |  | 16384 | 37.200 | 0.440 | 0.770 |
| ALLREDUCE | 8 |  |  | 16384 | 37.970 | 0.430 | 0.760 |
| ALLREDUCE | 8 |  |  | 16384 | 38.770 | 0.420 | 0.740 |
| ALLREDUCE | 8 |  |  | 16K | 37.610 | 0.440 | 0.760 |
| ALLREDUCE | 8 |  |  | 16384 | 37.490 | 0.440 | 0.760 |
| ALLREDUCE | 8 |  |  | 16384 | 38.250 | 0.430 | 0.750 |
| ALLREDUCE | 8 |  |  | 16384 | 38.480 | 0.430 | 0.750 |
| ALLREDUCE | 8 |  |  | 16K | 37.610 | 0.440 | 0.760 |
| ALLREDUCE | 8 |  |  | 16384 | 37.490 | 0.440 | 0.760 |
| ALLREDUCE | 8 |  |  | 16384 | 38.250 | 0.430 | 0.750 |
| ALLREDUCE | 8 |  |  | 16384 | 38.480 | 0.430 | 0.750 |
| ALLREDUCE | 8 |  |  | 128K | 54.600 | 2.400 | 4.200 |
| ALLREDUCE | 8 |  |  | 128K | 55.520 | 2.360 | 4.130 |
| ALLREDUCE | 8 |  |  | 128K | 55.520 | 2.360 | 4.130 |
| ALLREDUCE | 8 |  |  | 512K | 168.720 | 3.110 | 5.440 |
| ALLREDUCE | 8 |  |  | 512K | 168.470 | 3.110 | 5.450 |
| ALLREDUCE | 8 |  |  | 512K | 168.470 | 3.110 | 5.450 |
| ALLREDUCE | 8 |  |  | 64M | 4682.370 | 14.330 | 25.080 |
| ALLREDUCE | 8 |  |  | 64M | 4881.190 | 13.750 | 24.060 |
| ALLREDUCE | 8 |  |  | 64M | 4881.190 | 13.750 | 24.060 |
| ALLREDUCE | 8 |  |  | 128M | 9173.410 | 14.630 | 25.600 |
| ALLREDUCE | 8 |  |  | 128M | 9608.520 | 13.970 | 24.450 |
| ALLREDUCE | 8 |  |  | 128M | 9608.520 | 13.970 | 24.450 |
| ALLREDUCE | 8 |  |  | 256M | 18760.500 | 14.310 | 25.040 |
| ALLREDUCE | 8 |  |  | 256M | 18831.200 | 14.250 | 24.950 |
| ALLREDUCE | 8 |  |  | 256M | 18831.200 | 14.250 | 24.950 |
| ALLREDUCE | 16 | GCP_CAPPED_100G | 100.0 | 16384 | 287.840 | 0.060 | 0.110 |
| ALLREDUCE | 2 | GCP_CAPPED_100G | 100.0 | 16384 | 236.740 | 0.070 | 0.070 |
| ALLREDUCE | 8 | GCP_CAPPED_100G | 100.0 | 16384 | 280.280 | 0.060 | 0.100 |
| ALLREDUCE | 16 | GCP_CAPPED_10G | 10.0 | 16384 | 319.450 | 0.050 | 0.100 |
| ALLREDUCE | 2 | GCP_CAPPED_10G | 10.0 | 16384 | 231.530 | 0.070 | 0.070 |
| ALLREDUCE | 8 | GCP_CAPPED_10G | 10.0 | 16384 | 300.910 | 0.050 | 0.100 |
| ALLREDUCE | 16 | GCP_CAPPED_20G | 20.0 | 16384 | 297.520 | 0.060 | 0.100 |
| ALLREDUCE | 2 | GCP_CAPPED_20G | 20.0 | 16384 | 231.100 | 0.070 | 0.070 |
| ALLREDUCE | 8 | GCP_CAPPED_20G | 20.0 | 16384 | 286.950 | 0.060 | 0.100 |
| ALLREDUCE | 16 | GCP_CAPPED_50G | 50.0 | 16384 | 296.840 | 0.060 | 0.100 |
| ALLREDUCE | 2 | GCP_CAPPED_50G | 50.0 | 16384 | 223.330 | 0.070 | 0.070 |
| ALLREDUCE | 8 | GCP_CAPPED_50G | 50.0 | 16384 | 277.850 | 0.060 | 0.100 |
| ALLREDUCE | 16 | GCP_NATIVE | 0.0 | 16384 | 290.340 | 0.060 | 0.110 |
| ALLREDUCE | 2 | GCP_NATIVE | 0.0 | 16384 | 226.660 | 0.070 | 0.070 |
| ALLREDUCE | 8 | GCP_NATIVE | 0.0 | 16384 | 279.860 | 0.060 | 0.100 |
| SENDRECV |  | GCP_CAPPED_100G | 100.0 | 16K | -1.000 | 174.650 | 0.090 |
| SENDRECV |  | GCP_CAPPED_100G | 100.0 | 128K | -1.000 | 217.540 | 0.600 |
| SENDRECV |  | GCP_CAPPED_100G | 100.0 | 512K | -1.000 | 338.750 | 1.550 |
| SENDRECV |  | GCP_CAPPED_100G | 100.0 | 64M | -1.000 | 12149.700 | 5.520 |
| SENDRECV |  | GCP_CAPPED_100G | 100.0 | 128M | -1.000 | 24864.600 | 5.400 |
| SENDRECV |  | GCP_CAPPED_100G | 100.0 | 256M | -1.000 | 48418.300 | 5.540 |
| SENDRECV |  | GCP_CAPPED_10G | 10.0 | 16K | -1.000 | 177.570 | 0.090 |
| SENDRECV |  | GCP_CAPPED_10G | 10.0 | 128K | -1.000 | 297.480 | 0.440 |
| SENDRECV |  | GCP_CAPPED_10G | 10.0 | 512K | -1.000 | 649.440 | 0.810 |
| SENDRECV |  | GCP_CAPPED_10G | 10.0 | 64M | -1.000 | 60335.800 | 1.110 |
| SENDRECV |  | GCP_CAPPED_10G | 10.0 | 128M | -1.000 | 120386.000 | 1.110 |
| SENDRECV |  | GCP_CAPPED_10G | 10.0 | 256M | -1.000 | 241218.000 | 1.110 |
| SENDRECV |  | GCP_CAPPED_20G | 20.0 | 16K | -1.000 | 169.760 | 0.100 |
| SENDRECV |  | GCP_CAPPED_20G | 20.0 | 128K | -1.000 | 222.800 | 0.590 |
| SENDRECV |  | GCP_CAPPED_20G | 20.0 | 512K | -1.000 | 426.540 | 1.230 |
| SENDRECV |  | GCP_CAPPED_20G | 20.0 | 64M | -1.000 | 32539.400 | 2.060 |
| SENDRECV |  | GCP_CAPPED_20G | 20.0 | 128M | -1.000 | 65459.800 | 2.050 |
| SENDRECV |  | GCP_CAPPED_20G | 20.0 | 256M | -1.000 | 131637.000 | 2.040 |
| SENDRECV |  | GCP_CAPPED_50G | 50.0 | 16K | -1.000 | 167.420 | 0.100 |
| SENDRECV |  | GCP_CAPPED_50G | 50.0 | 128K | -1.000 | 221.600 | 0.590 |
| SENDRECV |  | GCP_CAPPED_50G | 50.0 | 512K | -1.000 | 366.630 | 1.430 |
| SENDRECV |  | GCP_CAPPED_50G | 50.0 | 64M | -1.000 | 16262.800 | 4.130 |
| SENDRECV |  | GCP_CAPPED_50G | 50.0 | 128M | -1.000 | 32268.800 | 4.160 |
| SENDRECV |  | GCP_CAPPED_50G | 50.0 | 256M | -1.000 | 65597.500 | 4.090 |
| SENDRECV |  | GCP_NATIVE | 0.0 | 16K | -1.000 | 169.310 | 0.100 |
| SENDRECV |  | GCP_NATIVE | 0.0 | 128K | -1.000 | 200.810 | 0.650 |
| SENDRECV |  | GCP_NATIVE | 0.0 | 512K | -1.000 | 309.960 | 1.690 |
| SENDRECV |  | GCP_NATIVE | 0.0 | 64M | -1.000 | 9267.930 | 7.240 |
| SENDRECV |  | GCP_NATIVE | 0.0 | 128M | -1.000 | 19218.000 | 6.980 |
| SENDRECV |  | GCP_NATIVE | 0.0 | 256M | -1.000 | 37742.400 | 7.110 |

## iperf3

| Network provenance | Gb/s | GB/s |
|---|---:|---:|
| GCP_CAPPED_100G | 54.19 | 6.77 |
| GCP_CAPPED_100G_reverse | 55.82 | 6.98 |
| GCP_CAPPED_10G | 9.00 | 1.12 |
| GCP_CAPPED_10G_reverse | 9.01 | 1.13 |
| GCP_CAPPED_20G | 16.69 | 2.09 |
| GCP_CAPPED_20G_reverse | 16.79 | 2.10 |
| GCP_CAPPED_50G | 33.02 | 4.13 |
| GCP_CAPPED_50G_reverse | 34.19 | 4.27 |
| GCP_NATIVE | 173.60 | 21.70 |
| GCP_NATIVE_reverse | 173.59 | 21.70 |

## Other raw metrics

- NVBandwidth numeric bandwidth/latency fields parsed: **105**
- BabelStream rows parsed: **40**
- CUTLASS rows parsed from machine-readable profiler CSV: **{len(cutlass)}**

> Check `nccl_points.csv`, `iperf.csv`, `nvbandwidth_metrics.csv`, `babelstream.csv`, `cutlass.csv`, and `summary.json` for machine-readable data.

