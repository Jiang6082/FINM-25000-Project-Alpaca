# L4 组项目 — 视频录制流程（全程不用说话）

> 作业要求视频 10–15 分钟，讲清：架构、UI 演示、纸面交易实盘运行、策略/数据/执行/风控说明、反思。
> 你不开口的替代方案：所有"解说词"都由命令清单里的 `Write-Host` 用**彩色大字打印在屏幕正中**，每块停留几秒即可。
> 开头和结尾的免责声明（step 5 / step 18）是作业硬性要求的那句 "This is paper trading only — no real money is used."，红底白字打印。

> 所有要粘贴的命令都在 **`DEMO_COMMANDS.md`**（同目录），step 编号一一对应，直接复制粘贴。

密钥：`.env` 已从 L3 复制并验证（Connected: True，账户 ACTIVE，当前 Equity ≈ $1,000,000，无持仓）。
时间：**必须美股盘中 = 北京时间 21:30 → 次日 04:00（周一至周五）**，市价单才会秒成交。

---

## PART 0 — 录制前准备（现在就能做，不用开录）

1. **（可选）重置账户到 $100,000**：配置里 `initial_capital = 100000`，画面上账户也是 $100k 会更一致。
   https://app.alpaca.markets/ → 左上角切到 **Paper Trading** → 账户设置（⚙️）→ **Reset** → 填 `100000`。
   重置会清空持仓和历史订单，画面干净。不重置也不影响演示（下单金额由风控上限决定，与账户总额无关）。
2. **跑一遍只读检查**：命令清单 **step 1–4**。期望看到 `9 passed` 和 `Connected to Alpaca PAPER. Market open: True`。
   然后跑 **step 4b** 清掉之前测试留下的模拟数据日志（录像时 step 12 和 step 16 的输出才只含真实 Alpaca 数据）。
   - 若 step 3 激活报"禁止运行脚本"，先跑 step 2（每个新终端都要 step 2 + step 3）。
   - `Market open: False` 说明不在盘中，等开盘再录。
3. 把浏览器开两个标签页备用：`http://localhost:8501`（UI，step 13 启动后才有）和 `https://app.alpaca.markets/`（Alpaca 后台，确认左上角 **Paper** 标识）。
4. 终端字体调大（右键标题栏 → 属性 → 字体），录屏时 Write-Host 的字才看得清。

---

## PART 1 — 正式录制（盘中，Win+G 开始录屏，从 step 5 开始）

| 顺序 | 干什么 | 命令 | 屏幕上应出现 | 时长 |
|---|---|---|---|---|
| 1 | 免责声明（开场） | step 5 | 红底大字 "THIS IS PAPER TRADING ONLY…" | 5s |
| 2 | 项目简介 | step 6 | 青色文字块：系统组成 | 15s |
| 3 | 架构总览 | step 7 | 青色文字块：模块流程 data→strategy→risk→execution | 30s |
| 4 | 测试通过 | step 8 | `9 passed` | 30s |
| 5 | 策略解说 | step 9 | 青色文字块：均线突破规则 + 直觉 | 30s |
| 6 | 真实数据回测 | step 10 | 拉取 Alpaca 历史数据 → 打印 8 项指标 | 60s |
| 7 | 看两张图 | step 11 | equity_curve / drawdown | 30s |
| 8 | 数据管线 | step 12 | 青色解说 + `Logged market data to ...` + CSV 前 6 行 | 60s |
| 9 | UI 清单 + 启动 | step 13 | 青色"看点清单"，新窗口起 Streamlit，浏览器自动打开 | 30s |
| 10 | **浏览器：UI 巡览** | — | 状态行（Connected / Market Open）、账户面板、侧栏风控参数 | 60s |
| 11 | **浏览器：UI 里跑回测** | — | 点 *Run Backtest*：指标表、净值、回撤、信号、订单 | 60s |
| 12 | **浏览器：dry-run** | — | 切 *Paper trading* 模式，Dry-run 勾着，点 *Run one cycle now* | 45s |
| 13 | 风控解说（回终端） | step 14 | 青色文字块：限额、止损止盈、订单状态轮询 | 25s |
| 14 | 建仓（视情况） | step 15 | `SUBMITTED: accepted ...` → `FINAL: ... status='filled'` | 60s |
| 15 | **浏览器：实盘周期** | — | 刷新页面→AAPL 在持仓面板；**取消勾选 Dry-run**（出现黄色警告），点 *Run one cycle now* → 表格里 SELL status=filled | 90s |
| 16 | **浏览器：Alpaca 后台** | — | app.alpaca.markets：**Paper** 标识、BUY+SELL 都 filled、持仓归零 | 45s |
| 17 | **浏览器：循环开关** | — | 点 *Start strategy loop* → 显示 RUNNING → 点 *Stop strategy loop*（演示启停控制） | 30s |
| 18 | 事件日志（回终端） | step 16 | system.log 最后 15 行：数据、信号、订单、成交 | 30s |
| 19 | 反思 | step 17 | 青色文字块：局限、改进、收获 | 35s |
| 20 | 免责声明（收尾） | step 18 | 红底大字再放一次 | 5s |

以上合计约 **12–13 分钟**，落在 10–15 分钟要求区间内。每个青色文字块出来后**停住别动**，按表里的时长默数，给观看者阅读时间；不够 10 分钟就把 UI 巡览（顺序 10–12）放慢。

### step 15 的判断（重要）

- 顺序 12 的 dry-run 如果显示 **"No orders generated this cycle."**（今天验证过就是这个结果）→ **必须跑 step 15 建仓**，这样实盘周期才有东西可卖：策略发现 AAPL 无信号 → 生成 `reason=exit` 的 SELL → 成交。
- 如果 dry-run 表格里**已经列出订单**（哪天信号触发了）→ **跳过 step 15**，直接取消 Dry-run 跑实盘周期，画面显示 BUY filled，同样满足要求。

---

## PART 2 — 视频上传 + 提交（录完后）

1. **视频上传**：YouTube → 可见性选 **Unlisted**，复制链接。
2. **填 README**：step 19 打开 README，把 `VIDEO LINK: TODO` 那行换成你的链接。
3. **提交推送**：step 20–21。注意当前分支是 `fix/review-fixes`（上面已有一个修复 commit 未推送），step 21 会把整个分支推上去，然后去 GitHub 开 **Pull Request** 让 Charles review 合并——顺便补上作业要求的协作证据。
   - 如果 push 报 403/权限错误：说明你还不是仓库 collaborator，让 Charles 在 GitHub 仓库 Settings → Collaborators 里加你；或者 fork 后推到自己的 fork 再开跨仓库 PR。
4. `.env`、`.venv/`、`logs/`、`data/live/*.csv`、`artifacts/backtests/` 都在 `.gitignore` 里，不会泄漏密钥。`DEMO_COMMANDS.md` 和本文件是否提交都可以，不影响评分。

---

## 常见问题

- **UI 显示 Disconnected** → `.env` 不在项目根目录或密钥错误；确认 step 4 能打印 Connected 再启动 UI。UI 状态有 30 秒缓存，改完 `.env` 重启 Streamlit（关掉它的黑窗口重跑 step 13）。
- **订单一直 accepted 不成交** → 不在盘中；等开盘（北京 21:30–04:00）。
- **实盘周期显示 "No orders generated this cycle."** → 没持仓且无信号，先跑 step 15 建仓再来一次。
- **Streamlit 起来了但浏览器没开** → 手动访问 `http://localhost:8501`。
- **激活 venv 报错** → 每个新终端先跑 step 2 再 step 3；或把命令里的 `python` 换成 `.\.venv\Scripts\python.exe`。
- **想让演示更丰富** → 侧栏把 *Max open positions* 从 3 改成 2 再跑一次 dry-run，展示"风险参数可在 UI 调整"这个评分点。
