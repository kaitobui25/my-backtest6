# Exact Batch Backtester

Backtester nghiên cứu BTC Futures theo kiến trúc:

```text
MỘT EXACT EXECUTION LOOP
├── batch metrics mode  → chạy toàn bộ grid, không tạo Trade object
└── record mode         → chạy lại config cần soi, lưu từng trade
```

Hai mode gọi **cùng một hàm mô phỏng**. Không có Fast Engine gần đúng nên không
có trường hợp config tốt bị loại chỉ vì Fast/Exact lệch logic.

## Những gì đã khóa trong engine

- Signal ở nến `i` → entry tại `Open` nến `i+1`.
- Tối đa một vị thế, không pyramiding.
- Không scan setup trên nến đang có vị thế.
- Không mở lệnh mới trên chính nến vừa exit.
- Kiểm tra SL/TP ngay trên nến entry.
- SL và TP cùng hit → SL thắng.
- Gap qua SL → fill tại Open; gap qua TP → chỉ fill tại TP.
- Phí và slippage được trừ vào R.
- Vị thế còn mở cuối data → đóng tại Close cuối.
- Không dùng `fastmath`.
- Parallel theo config; timeline trong từng config vẫn tuần tự.

## Expectancy

Tiêu chí mặc định nằm trong `config/search.yaml`:

```yaml
selection:
  min_expectancy_r: 0.15
  strict_expectancy: true
```

Nghĩa là:

```text
expectancy_R > 0.15R/lệnh
```

Các cột kết quả giải thích rõ:

```text
gross_expectancy_R
= gross_win_rate × avg_gross_win_R
- gross_loss_rate × avg_gross_loss_R

expectancy_R
= gross_expectancy_R - avg_cost_R
= net_R_total / trades       ← nguồn chân lý
```

`win_rate`, `avg_win_R`, `avg_loss_R` là thống kê **sau chi phí**. Các cột có
prefix `gross_` dùng để nhìn edge trước phí/slippage, tránh trừ chi phí hai lần.

## Data Parquet

Chấp nhận một trong các cột thời gian:

```text
datetime / date / timestamp / time
```

Cột bắt buộc:

```text
open, high, low, close, volume
```

Timestamp được chuẩn hóa UTC. Data được sort và bỏ timestamp trùng. OHLC sai sẽ
bị chặn thay vì âm thầm chạy.

Đặt file vào:

```text
data/btcusdt_15m.parquet
```

hoặc sửa `data.file` trong YAML.

## Cài trên Windows

Yêu cầu Python 3.11 hoặc 3.12. Chạy:

```bat
setup.bat
```

Script sẽ tạo `.venv`, cài dependency, cài project editable và chạy test.

PowerShell đang chặn script unsigned thì dùng `run.bat`, không cần đổi Execution
Policy toàn máy.

## Chạy

TRAIN mặc định:

```bat
run.bat
```

VALIDATION:

```bat
run.bat --split validation
```

Hoặc PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1 -Split train
```

Final OOS bị khóa. Chỉ khi thực sự tới milestone cuối:

```bat
run.bat --split final_oos --unlock-final-oos
```

## Output

Mỗi run có ID dựa trên config, split, engine version và SHA-256 của dataset:

```text
results/<split>_<hash>/
├── manifest.json
├── run_config.yaml
├── batches/                         checkpoint/resume
├── all_results.parquet              mọi config đã chạy exact
├── passing_results.parquet          expectancy > ngưỡng + gate đã bật
├── near_threshold_results.parquet   sát ngưỡng, tránh bỏ quên
├── family_best_results.parquet      top mỗi strategy family
├── record_mode_metrics.parquet      parity với batch mode
├── trades/<config_id>.parquet       trade chi tiết
├── summary.json
└── summary.md
```

Checkpoint là file Parquet riêng từng batch và được ghi atomic. Restart sẽ bỏ
qua batch đã hoàn thành, không chạy trùng config.

## Strategy dễ thêm/bớt

Bật/tắt hoàn toàn trong YAML:

```yaml
- plugin: exactbt.strategies.liquidity_sweep:PLUGIN
  enabled: true
```

Project có sẵn **17 strategy family**, tất cả đang bật trong YAML:

- 2 strategy custom/stateful: Liquidity Sweep và Donchian + EMA + ATR.
- 4 mean-reversion.
- 3 momentum.
- 4 trend/breakout.
- 2 volatility.
- 2 volume-confirmed.

Grid mặc định hiện có **23.796 config exact**. Kiểm tra trước khi chạy:

```bat
count_configs.bat
```

15 strategy indicator dùng chung một adapter signal + ATR stop. Mỗi unique signal
combination chỉ được tính một lần rồi tái sử dụng cho các RR/SL/max-hold khác nhau.
Đây vẫn là exact execution, không phải Fast Engine gần đúng.

Xem [`docs/STRATEGY_LIBRARY.md`](docs/STRATEGY_LIBRARY.md) và
[`docs/ADDING_STRATEGY.md`](docs/ADDING_STRATEGY.md).

## Vì sao ít bỏ sót config tốt hơn

- Mọi combination được khai báo đều chạy exact; không random sample.
- Không có Fast top-N gate.
- Lưu toàn bộ results, không chỉ shortlist.
- Lưu riêng config sát ngưỡng.
- Luôn giữ top của từng strategy family.
- Record mode chỉ là phần soi trade; nó không quyết định config có được xét hay
  không.

Điểm vẫn phải hiểu đúng: code không thể khám phá một strategy family mà chưa ai
viết vào project, và grid quá thưa vẫn có thể bỏ qua vùng parameter tốt. Vì vậy
YAML hỗ trợ list và `{start, stop, step}` để quét grid rõ ràng, có kiểm soát.

## Test

```bat
.venv\Scripts\python.exe -m pytest -v
```

Các test khóa both-hit, gap, entry-bar exit, no same-bar re-entry, expectancy,
metrics/records parity, plugin loading, Liquidity Sweep state và toàn bộ thư viện
strategy indicator.
