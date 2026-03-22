# SARA-WS Flexibility Benchmark Summary

## Common Case Comparison

| Suite | Case | Shape | Latency Delta | Mapping Eff Delta | Output Slot Delta | Bytes/MAC Delta | SARA Config |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| bandwidth_sweep | bw_pointwise_like | 49x32x64 | +0.0% | +0.0% | +0.0% | +0.0% | 8x8 (cfg 0) |
| bandwidth_sweep | bw_small_batch_large_channel | 2x32x32 | +0.0% | +300.0% | +300.0% | +0.0% | 2x8 (cfg 4) |
| bandwidth_sweep | bw_tall_skinny | 32x8x3 | +0.0% | +100.0% | +100.0% | +0.0% | 8x4 (cfg 2) |
| layer_sweep | bottleneck_like | 16x64x24 | +0.0% | +0.0% | +0.0% | +0.0% | 8x8 (cfg 0) |
| layer_sweep | early_conv_like | 64x27x16 | +0.0% | +0.0% | +0.0% | +0.0% | 8x8 (cfg 0) |
| layer_sweep | late_stage_like | 4x64x128 | +0.0% | +100.0% | +100.0% | +0.0% | 4x8 (cfg 1) |
| layer_sweep | pointwise_like | 49x32x64 | +0.0% | +0.0% | +0.0% | +0.0% | 8x8 (cfg 0) |
| shape_sweep | irregular_small | 5x11x7 | +6.8% | +87.2% | +0.0% | +0.0% | 4x8 (cfg 1) |
| shape_sweep | small_batch_large_channel | 2x32x32 | +0.0% | +300.0% | +300.0% | +0.0% | 2x8 (cfg 4) |
| shape_sweep | square_exact | 8x8x8 | +0.0% | +0.0% | +0.0% | +0.0% | 8x8 (cfg 0) |
| shape_sweep | square_ragged | 15x10x13 | +0.0% | +0.0% | +0.0% | +0.0% | 8x8 (cfg 0) |
| shape_sweep | tall_skinny | 32x8x3 | +0.0% | +100.0% | +100.0% | +0.0% | 8x4 (cfg 2) |
| shape_sweep | wide_short | 3x8x32 | +0.0% | +100.0% | +100.0% | +0.0% | 4x8 (cfg 1) |

## Stability Summary

| Variant | Mean cycles/MAC | Worst cycles/MAC | Mean mapping eff | Min mapping eff | Mapping eff std | Mean bytes/MAC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| sara_ws | 1.1023 | 1.7109 | 0.0258 | 0.0122 | 0.0098 | 0.5999 |
| ws | 1.0929 | 1.7109 | 0.0179 | 0.0091 | 0.0091 | 0.5999 |

## Config Space Gain

| Shape | Auto cfg | Auto map eff | Best map cfg | Best map eff | Worst map cfg | Worst map eff | Best latency cfg | Auto vs best map | Auto vs best latency |
| --- | --- | ---: | --- | ---: | --- | ---: | --- | ---: | ---: |
| cfg_tall_3x16 (3x8x16) | 1 | 0.0183 | manual_2x2 | 0.0619 | manual_8x8 | 0.0091 | manual_8x8 | -70.4% | -1.2% |
| cfg_tiny_2x2 (2x8x2) | 6 | 0.0548 | manual_2x2 | 0.0548 | manual_8x8 | 0.0034 | manual_2x2 | +0.0% | +0.0% |
| cfg_tradeoff_5x7 (5x11x7) | 1 | 0.0215 | manual_2x2 | 0.0661 | manual_8x8 | 0.0116 | manual_8x8 | -67.5% | +7.7% |
| cfg_wide_16x3 (16x8x3) | 2 | 0.0189 | manual_2x2 | 0.0756 | manual_8x8 | 0.0093 | manual_8x8 | -75.0% | -1.2% |
