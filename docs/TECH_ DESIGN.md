📘 Tech Design Document: Mark Six Quant Platform (v2.3)ProjectMark Six Backtest PlatformVersionv2.3 (Matches PRD)Tech StackFrontend: Tauri v2, Vue 3, TypeScript, Pinia, Element Plus/Naive UIBackend (Sidecar): Python 3.10+, Pandas, NumPy, PyArrow (Feather)Charts: EChartsArchitectureLocal Desktop App with IPC-bridged Computation Engine1. 🏗️ 系统架构深度设计 (System Architecture)1.1 核心设计模式：Sidecar (边车模式)应用采用 UI 与计算分离 的架构。Rust (Tauri Main Process): 负责窗口管理、文件系统读写权限控制、以及作为 Python 进程的守护者（Spawner）。Python (Subprocess): 一个无状态的计算服务。它不直接访问 UI，只通过 stdin/stdout 接收 JSON 指令并返回计算结果。Why? Pandas 的向量化计算能力无法被 JS 替代，且 Python 生态拥有最完善的量化库。1.2 数据流向图 (Data Flow)代码段sequenceDiagram
    participant User as 👤 User
    participant Vue as 🟢 Vue Frontend
    participant Rust as 🦀 Tauri Core
    participant Py as 🐍 Python Engine
    participant DB as 💾 Feather File

    %% 场景：回测
    User->>Vue: 点击 "开始回测"
    Vue->>Vue: 组装策略 JSON
    Vue->>Rust: Invoke `run_backtest(strategy_json)`
    Rust->>Py: 转发 JSON 指令 (via Stdin)
    
    rect rgb(240, 240, 240)
        Note over Py: 1. 加载 Feather 数据
        Py->>DB: Read binary
        Note over Py: 2. 预计算属性 (Enrich)
        Note over Py: 3. 向量化计算指标 (Vectorized Stats)
        Note over Py: 4. SHIFT(1) 防未来函数处理
        Note over Py: 5. 逐行资金模拟 (Loop)
    end
    
    Py->>Rust: 返回 Result JSON (via Stdout)
    Rust->>Vue: Resolve Promise
    Vue->>User: 渲染 ECharts 资金曲线
2. 🗄️ 数据存储层设计 (Storage Layer)2.1 文件结构Plaintext/app_data
  /data
    history.feather      # 核心数据，二进制列式存储 (Apache Arrow)
  /config
    strategies.json      # 用户保存的策略集合
    odds_profiles.json   # 赔率表
    settings.json        # 全局配置 (如：生肖年份映射表)
2.2 Schema: history.feather仅存储原始不可变数据。为了节省 IO 和存储，生肖、波色等属性在 Python 读取时动态生成。ColumnTypeCommentperiodstring期号 (Index, e.g., "2024005") - Unique Keydatedatetime64[ns]开奖日期yearuint16年份 (用于生肖映射)n1...n6uint8正码 1-6specialuint8特码 (重点分析对象)2.3 动态生肖映射配置 (settings.json)JSON{
  "zodiac_mapping": {
    "2024": { "zodiac": "dragon", "start_date": "2024-02-10" }, 
    "2025": { "zodiac": "snake", "start_date": "2025-01-29" }
  },
  "zodiac_order": ["rat", "ox", "tiger", "rabbit", "dragon", "snake", "horse", "goat", "monkey", "rooster", "dog", "pig"]
}
逻辑说明：生肖不仅仅看年份，还要看是否过了春节。PRD v2.3 要求支持跨年回测，因此必须严格根据 date 判断生肖。3. 🐍 Python 计算引擎详设 (The Brain)此部分是开发的核心。需创建一个 Python 项目结构，最终通过 PyInstaller 打包。3.1 核心类设计A. 数据加载与清洗 (DataLoader)职责：读取 Feather -> 扩展衍生列 (Enrichment)。Python# pseudo_code/data_loader.py
import pandas as pd

def enrich_data(df: pd.DataFrame) -> pd.DataFrame:
    # 1. 属性字典 (Map)
    RED_WAVE = {1, 2, 7, 8, ...}
    BLUE_WAVE = {3, 4, 9, 10, ...}
    
    # 2. 向量化计算波色 (Vectorized Operation)
    # 比 .apply() 快 100 倍
    df['sp_color'] = 'green' # default
    df.loc[df['special'].isin(RED_WAVE), 'sp_color'] = 'red'
    df.loc[df['special'].isin(BLUE_WAVE), 'sp_color'] = 'blue'
    
    # 3. 向量化计算生肖 (难点)
    # 方案：先通过 merge left join 年份表，或者基于 date区间 赋值
    # 假设 2024年 1号是龙，则 number % 12 的余数与生肖有固定偏移关系
    # 具体算法：ZodiacIndex = (ReferenceZodiacIndex + (Number - 1)) % 12 (逆推需注意方向)
    df['sp_zodiac'] = calculate_zodiac_vectorized(df['year'], df['special'])
    
    return df
B. 统计指标计算器 (StatEngine)职责：实现 PRD 6.2 的 "遗漏" 和 "热度" 计算。关键算法：不能使用 Python for 循环计算遗漏，必须使用 Pandas/NumPy 向量化操作。Python# pseudo_code/stat_engine.py

def calc_omission_matrix(series: pd.Series, target_value) -> pd.Series:
    """
    计算某列中 target_value 的【当前遗漏值】序列。
    例如数据: [Red, Blue, Red, Red] (Target: Red)
    命中向量: [1, 0, 1, 1]
    遗漏向量: [0, 1, 0, 0] (距离上一次出现的间隔)
    注意：这是"当前"状态。回测需要 Shift。
    """
    # 1. 构造布尔命中序列
    is_hit = (series == target_value)
    
    # 2. 构造分组 ID (每次命中重置 Group)
    # cumsum() 在命中时增加，使得两个命中之间的非命中行处于同一个 group
    groups = is_hit.cumsum()
    
    # 3. 利用 cumcount 计算每组内的累积计数 (即遗漏值)
    # 注意：需处理边界情况，Pandas 的 groupby cumcount 从 0 开始
    omission = series.groupby(groups).cumcount()
    
    # 修正：如果是命中行，omission 应为 0。非命中行逐步 +1
    # 上述逻辑在命中行是 0，下一行是 1，正确。
    return omission
C. 回测执行器 (Backtester)职责：严格的时间序列模拟。🌟 核心原则：防未来函数 (Anti-Future Leakage)在处理第 T 期时，我们只能“看到” T-1 期的统计结果。执行步骤：全量预计算 (Pre-calculation):加载所有历史数据。针对策略关注的指标（例如："红波遗漏"），调用 StatEngine 计算出整列 current_omission。时间位移 (Shift):df['signal_omission'] = df['current_omission'].shift(1)解释：第 T 行的 signal_omission 列，存储的是第 T-1 期结束时的遗漏值。这才是下注时能拿到的真实数据。切片 (Slicing):backtest_df = df[(df.date >= start) & (df.date <= end)]循环迭代 (Iteration):因为资金管理（Martingale等）是路径依赖的（下注额取决于上一把输赢），这里必须使用 Python 循环。由于指标已预计算，循环内部仅做简单的 if/else 和加减法，速度极快（10000期 < 0.5秒）。Python# pseudo_code/backtester.py

def run(strategy, df):
    # ... Pre-calc logic ...
    
    wallet = strategy.initial_capital
    records = []
    
    # 这里的 row 包含已经 shift 过的统计数据
    for idx, row in backtest_df.iterrows():
        signal_val = row['signal_omission'] # T-1 期的遗漏
        
        # 1. 策略判定 (Entry Rule)
        should_bet = strategy.check_rule(signal_val)
        
        bet_amount = 0
        profit = 0
        hit = False
        
        if should_bet:
            bet_amount = money_manager.get_next_bet()
            
            # 2. 结算 (使用当期真实开奖结果)
            actual_result = row['sp_color']
            if actual_result == strategy.target_value:
                profit = bet_amount * odds - bet_amount
                hit = True
                money_manager.reset()
            else:
                profit = -bet_amount
                money_manager.progress() # 倍投升级
                
        wallet += profit
        
        # 3. 记录日志 (用于前端绘图)
        records.append({
            "period": row['period'],
            "wallet": wallet,
            "bet": bet_amount,
            "omission_ref": signal_val # 用于验证策略是否严格执行
        })
        
    return records
4. 🔗 接口定义 (IPC Schema)Tauri 前端通过 tauri::command 调用，实际转发给 Python。4.1 Command: get_historical_stats用于 PRD 6.2 统计模块的展示。Request:JSON{
  "cmd": "get_stats",
  "params": {
    "range": 100, // 近100期
    "dimension": "zodiac", // 统计维度：生肖
    "target": "special"   // 统计对象：特码
  }
}
Response:JSON{
  "status": "ok",
  "data": [
    { "label": "龙", "cur_omission": 5, "max_omission": 34, "freq": 12 },
    { "label": "马", "cur_omission": 0, "max_omission": 40, "freq": 8 }
  ]
}
4.2 Command: run_backtest_simulation用于核心回测。Request:JSON{
  "cmd": "run_backtest",
  "payload": {
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_cash": 10000,
    "strategy": {
      "trigger": { "type": "omission", "val": 10, "target": "red_wave" },
      "money_mgmt": { "mode": "martingale", "sequence": [10, 20, 40, 80] }
    }
  }
}
5. 💻 前端实现细节 (Vue 3)5.1 Store 设计 (Pinia)useDataStore:status: 'loading' | 'ready' | 'error'lastPeriod: string (最新一期期号)actions: importExcel(), refreshStats()useBacktestStore:config: 当前配置对象results: 回测结果数组 (大数组，注意性能)kpi: { winRate, maxDrawdown, ev }5.2 性能优化：大表格渲染回测结果可能包含数千行。必须使用：el-table-v2 (Element Plus 的虚拟滚动表格) 或 vue-virtual-scroller。ECharts 优化: 开启 sampling: 'lttb' (Downsampling)，避免渲染过密的数据点导致卡顿。6. 📅 开发步骤清单 (Implementation Plan)Environment Setup:初始化 Tauri v2 + Vue 3 项目。创建 /python 目录，建立虚拟环境，安装 pandas, pyarrow。Step 1: Data Pipeline (Python):实现 data_loader.py: Excel -> DataFrame -> Feather。实现 enrich_data: 完成 生肖/波色 映射逻辑。Unit Test: 验证 2024年期号的生肖是否正确。Step 2: Stats Engine (Python):实现向量化遗漏计算。编写 main.py 处理 stdin 输入并调用计算函数。Tauri 侧实现 Sidecar 调用测试。Step 3: UI - Data & Stats:完成数据导入页面。完成 PRD 6.2 的统计表格展示 (冷热/遗漏)。Step 4: Backtest Engine (Core):实现 Python 侧的 Shift 逻辑和资金循环。实现 JSON 策略解析器。Step 5: Visualization:对接 ECharts，展示资金曲线。添加风控提示 (根据 PRD 6.11)。