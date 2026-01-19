<template>
  <div class="replay-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="left">
            <span>策略回放/手动回测 (Replay Mode)</span>
            <el-select 
              v-model="selectedStrategyId" 
              placeholder="选择要模拟的策略" 
              clearable 
              style="width: 200px; margin-left: 15px;"
              @change="handleStrategyChange"
            >
              <el-option
                v-for="s in strategiesStore.strategies"
                :key="s.id"
                :label="s.name"
                :value="s.id"
              />
            </el-select>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              @change="handleDateRangeChange"
              style="margin-left: 15px; width: 300px;"
            />
          </div>
          <div class="control-group">
           <span class="label">数据源:</span>
           <el-select v-model="selectedDataSource" placeholder="选择数据年份" style="width: 150px" @change="handleDataSourceChange">
             <el-option label="全部历史" value="all" />
             <el-option v-for="year in availableYears" :key="year" :label="year + '年'" :value="year" />
           </el-select>
        </div>
        
        <div class="control-group">
             <el-button-group>
               <el-button icon="ArrowLeft" @click="prevPeriod" :disabled="loading">上一期</el-button>
               <el-button type="primary" :icon="isPlaying ? 'VideoPause' : 'VideoPlay'" @click="togglePlay">
                 {{ isPlaying ? '暂停' : '自动回放' }}
               </el-button>
               <el-button icon="ArrowRight" @click="nextPeriod" :disabled="loading">下一期 (Next)</el-button>
               <el-button icon="List" @click="showHistory = true">历史订单</el-button>
             </el-button-group>
             <el-select v-model="playSpeed" style="width: 100px; margin-left: 10px;">
               <el-option label="1.0s" :value="1000" />
               <el-option label="0.5s" :value="500" />
               <el-option label="0.2s" :value="200" />
             </el-select>
          </div>
        </div>
      </template>
      
      <div v-loading="loading" class="replay-content">
        <!-- Signal Indicator -->
        <div v-if="currentState && currentState.signal" class="signal-alert">
           <el-alert
             :title="`策略信号触发: 投注 ${currentState.signal.target}`"
             :type="currentState.signal.is_hit ? 'success' : 'warning'"
             :description="currentState.signal.is_hit ? '✅ 本期中奖 (HIT!)' : '❌ 本期未中 (MISS)'"
             show-icon
             :closable="false"
           />
        </div>

        <!-- Strategy Execution Details -->
        <el-card v-if="currentStrategyConfig && currentState && currentState.signal_evaluation" class="strategy-details-card">
            <template #header>
                <div class="card-header">
                    <span>策略执行详情 (Strategy Execution)</span>
                </div>
            </template>
            
            <div class="strategy-section">
                <h4>1. 入场条件评估</h4>
                <div v-for="(cond, idx) in currentState.signal_evaluation.conditions" :key="idx" class="condition-item">
                    <el-tag :type="cond.passed ? 'success' : 'danger'" size="small">
                        {{ cond.passed ? '通过' : '未通过' }}
                    </el-tag>
                    <span class="cond-desc">{{ cond.desc }}</span>
                    <span class="cond-val">
                        (期望 {{ cond.operator }} {{ cond.threshold }}, 实际: {{ cond.actual }})
                    </span>
                </div>
                <div class="signal-summary">
                    <strong>最终判定: </strong>
                    <el-tag :type="currentState.signal_evaluation.triggered ? 'success' : 'info'">
                        {{ currentState.signal_evaluation.triggered ? '触发信号' : '未触发' }}
                    </el-tag>
                </div>
            </div>

            <div class="strategy-section" v-if="currentState.signal">
                <h4>2. 当前下注状态</h4>
                <el-descriptions :column="2" border size="small">
                    <el-descriptions-item label="下注目标">{{ currentState.signal.target }}</el-descriptions-item>
                    <el-descriptions-item label="下注结果">
                        <span :style="{ color: currentState.signal.is_hit ? 'green' : 'red', fontWeight: 'bold' }">
                            {{ currentState.signal.is_hit ? '赢 (Win)' : '输 (Loss)' }}
                        </span>
                    </el-descriptions-item>
                </el-descriptions>
            </div>
        </el-card>

        <!-- Accumulated Analysis -->
        <el-card v-if="currentState && currentState.accumulated_stats" class="analysis-card" style="margin-top: 15px;">
            <template #header>
                <div class="card-header">
                    <span>累计回测数据 (Cumulative Analysis)</span>
                </div>
            </template>
            <el-row :gutter="20">
                <el-col :span="6">
                   <div class="stat-box">
                       <div class="label">当前本金 (Capital)</div>
                       <div class="val" :class="{ profit: currentState.accumulated_stats.profit > 0, loss: currentState.accumulated_stats.profit < 0 }">
                           {{ currentState.accumulated_stats.capital }}
                       </div>
                   </div>
                </el-col>
                <el-col :span="6">
                   <div class="stat-box">
                       <div class="label">累计盈亏 (Profit)</div>
                       <div class="val" :class="{ profit: currentState.accumulated_stats.profit > 0, loss: currentState.accumulated_stats.profit < 0 }">
                           {{ currentState.accumulated_stats.profit > 0 ? '+' : ''}}{{ currentState.accumulated_stats.profit }}
                       </div>
                   </div>
                </el-col>
                <el-col :span="6">
                   <div class="stat-box">
                       <div class="label">胜率 (Win Rate)</div>
                       <div class="val">{{ (currentState.accumulated_stats.win_rate * 100).toFixed(1) }}%</div>
                   </div>
                </el-col>
                 <el-col :span="6">
                   <div class="stat-box">
                       <div class="label">总交易数 (Trades)</div>
                       <div class="val">{{ currentState.accumulated_stats.total_trades }}</div>
                   </div>
                </el-col>
            </el-row>
        </el-card>

        <!-- Detailed Betting Status -->
        <el-card v-if="currentState && currentState.betting_status" class="betting-status-card" style="margin-top: 15px;">
            <template #header>
                <div class="card-header">
                    <span>下注详细情况 (Betting Details)</span>
                </div>
            </template>
            
            <el-descriptions :column="2" border>
                <el-descriptions-item label="下注结果 (Bet Result)">
                    <template v-if="currentState.betting_status.last_result">
                        <el-tag :type="currentState.betting_status.last_result.is_hit ? 'success' : 'danger'">
                            {{ currentState.betting_status.last_result.is_hit ? '赢 Win' : '输 Loss' }}
                        </el-tag>
                        <span style="margin-left: 10px;">
                            (期数: {{ currentState.betting_status.last_result.period }}, 
                             投: {{ currentState.betting_status.last_result.amount }}, 
                             {{ currentState.betting_status.last_result.profit > 0 ? '+' : '' }}{{ currentState.betting_status.last_result.profit }})
                        </span>
                    </template>
                    <span v-else class="text-gray">无下注</span>
                </el-descriptions-item>
                
                <el-descriptions-item label="下期下注 (Next Bet)">
                    <template v-if="currentState.betting_status.next_bet">
                        <strong style="color: #409EFF; font-size: 1.1em;">
                            {{ currentState.betting_status.next_bet.target }}
                        </strong>
                        <el-tag effect="plain" style="margin-left: 10px;">
                            期数: {{ currentState.betting_status.next_bet.period || '---' }}
                        </el-tag>
                        <el-tag effect="plain" style="margin-left: 5px;">
                            金额: {{ currentState.betting_status.next_bet.amount }}
                        </el-tag>
                        <el-tag type="warning" size="small" style="margin-left: 5px;" v-if="currentState.betting_status.next_bet.step > 0">
                            追号 Lv{{ currentState.betting_status.next_bet.step }}
                        </el-tag>
                    </template>
                    <span v-else class="text-gray">观望中 (Wait)</span>
                </el-descriptions-item>
            </el-descriptions>
        </el-card>

        <!-- Current Period Info -->
        <div v-if="currentState" class="period-info">
           <h2>第 {{ currentState.period }} 期</h2>
           <p>开奖日期: {{ currentState.result.date }}</p>
           
           <div class="balls">
             <div v-for="n in currentState.result.numbers" :key="n" class="ball normal-ball">
               {{ n }}
             </div>
             <div class="ball special-ball">
               {{ currentState.result.special }}
             </div>
           </div>
           
           <div class="attributes">
             <el-tag>{{ getZodiacName(currentState.result.zodiac) }}</el-tag>
             <el-tag :type="getColorType(currentState.result.color)">{{ getColorName(currentState.result.color) }}</el-tag>
           </div>
        </div>
        
        <el-divider />
        
        <!-- Stats Panel -->
        <div v-if="currentState" class="stats-panel">
          <el-row :gutter="20">
            <el-col :span="12">
               <h3>当前遗漏 (Omission)</h3>
               <el-descriptions :column="2" border size="small">
                 <el-descriptions-item label="红波">{{ currentState.stats.omission.color_0 }}</el-descriptions-item>
                 <el-descriptions-item label="蓝波">{{ currentState.stats.omission.color_1 }}</el-descriptions-item>
                 <el-descriptions-item label="绿波">{{ currentState.stats.omission.color_2 }}</el-descriptions-item>
               </el-descriptions>
               
               <div style="margin-top: 10px;">
                 <el-descriptions :column="2" border size="small">
                   <el-descriptions-item label="大">{{ currentState.stats.omission.size_1 }}</el-descriptions-item>
                   <el-descriptions-item label="小">{{ currentState.stats.omission.size_0 }}</el-descriptions-item>
                   <el-descriptions-item label="单">{{ currentState.stats.omission.parity_1 }}</el-descriptions-item>
                   <el-descriptions-item label="双">{{ currentState.stats.omission.parity_0 }}</el-descriptions-item>
                 </el-descriptions>
               </div>
               
               <div style="margin-top: 10px;">
                 <strong>特码尾数遗漏:</strong>
                 <div class="zodiac-grid" style="grid-template-columns: repeat(5, 1fr);">
                   <div v-for="t in 10" :key="t-1" class="stat-item">
                     <span class="label">{{ t-1 }}尾</span>
                     <span class="value" :class="{ high: currentState.stats.omission['tail_'+(t-1)] > 10 }">
                       {{ currentState.stats.omission['tail_'+(t-1)] }}
                     </span>
                   </div>
                 </div>
               </div>

               <div style="margin-top: 10px;">
                 <strong>生肖遗漏:</strong>
                 <div class="zodiac-grid">
                   <div v-for="z in 12" :key="z-1" class="stat-item">
                     <span class="label">{{ getZodiacName(z-1) }}</span>
                     <span class="value" :class="{ high: currentState.stats.omission['zodiac_'+(z-1)] > 10 }">
                       {{ currentState.stats.omission['zodiac_'+(z-1)] }}
                     </span>
                   </div>
                 </div>
               </div>
            </el-col>
            <el-col :span="12">
               <h3>近期热度 (Frequency 100)</h3>
               <el-descriptions :column="2" border size="small">
                 <el-descriptions-item label="红波">{{ currentState.stats.freq_100.color_0 }}</el-descriptions-item>
                 <el-descriptions-item label="蓝波">{{ currentState.stats.freq_100.color_1 }}</el-descriptions-item>
                 <el-descriptions-item label="绿波">{{ currentState.stats.freq_100.color_2 }}</el-descriptions-item>
               </el-descriptions>
               
               <div style="margin-top: 10px;">
                 <el-descriptions :column="2" border size="small">
                   <el-descriptions-item label="大">{{ currentState.stats.freq_100.size_1 }}</el-descriptions-item>
                   <el-descriptions-item label="小">{{ currentState.stats.freq_100.size_0 }}</el-descriptions-item>
                   <el-descriptions-item label="单">{{ currentState.stats.freq_100.parity_1 }}</el-descriptions-item>
                   <el-descriptions-item label="双">{{ currentState.stats.freq_100.parity_0 }}</el-descriptions-item>
                 </el-descriptions>
               </div>
               
               <div style="margin-top: 10px;">
                 <strong>特码尾数热度:</strong>
                 <div class="zodiac-grid" style="grid-template-columns: repeat(5, 1fr);">
                   <div v-for="t in 10" :key="t-1" class="stat-item">
                     <span class="label">{{ t-1 }}尾</span>
                     <span class="value" :class="{ high: currentState.stats.freq_100['tail_'+(t-1)] > 15 }">
                       {{ currentState.stats.freq_100['tail_'+(t-1)] }}
                     </span>
                   </div>
                 </div>
               </div>

               <div style="margin-top: 10px;">
                 <strong>生肖热度:</strong>
                 <div class="zodiac-grid">
                   <div v-for="z in 12" :key="z-1" class="stat-item">
                     <span class="label">{{ getZodiacName(z-1) }}</span>
                     <span class="value" :class="{ high: currentState.stats.freq_100['zodiac_'+(z-1)] > 12 }">
                       {{ currentState.stats.freq_100['zodiac_'+(z-1)] }}
                     </span>
                   </div>
                 </div>
               </div>
            </el-col>
          </el-row>
        </div>
        
        <el-empty v-else description="请点击下一期开始回放" />
      </div>
    </el-card>

    <el-drawer v-model="showHistory" title="历史订单记录 (Recent 100)" size="40%">
      <el-table :data="currentState?.history_orders || []" style="width: 100%" stripe border height="calc(100vh - 100px)">
        <el-table-column prop="period" label="期数" width="100" />
        <el-table-column prop="target" label="下注目标" width="120" />
        <el-table-column prop="amount" label="金额" width="100" />
        <el-table-column label="结果" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.is_hit ? 'success' : 'danger'">
              {{ scope.row.is_hit ? '赢' : '输' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="盈亏" align="right">
          <template #default="scope">
             <span :style="{ color: scope.row.profit > 0 ? 'green' : 'red', fontWeight: 'bold' }">
               {{ scope.row.profit > 0 ? '+' : '' }}{{ scope.row.profit }}
             </span>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { invoke } from '@tauri-apps/api/core';
import { ElMessage } from 'element-plus';
import { useStrategiesStore } from '../stores/strategies';
import { useEntryRulesStore } from '../stores/entryRules';
import { useMoneyRulesStore } from '../stores/moneyRules';
import { useOddsRulesStore } from '../stores/oddsRules';

interface ConditionResult {
    desc: string;
    passed: boolean;
    operator: string;
    threshold: number;
    actual: number;
}

interface SignalEvaluation {
    triggered: boolean;
    conditions: ConditionResult[];
}

interface TradeResult {
    is_hit: boolean;
    profit: number;
    amount: number;
}

interface BetInfo {
    target: string;
    amount: number;
    step: number;
}

interface BettingStatus {
    last_result: TradeResult | null;
    next_bet: BetInfo | null;
}

interface AccumulatedStats {
    capital: number;
    profit: number;
    win_rate: number;
    total_trades: number;
}

interface ReplayState {
    period: string;
    result: any;
    stats: any;
    signal: any; // Legacy simple signal
    signal_evaluation?: SignalEvaluation;
    accumulated_stats?: AccumulatedStats;
    betting_status?: BettingStatus;
    history_orders?: any[];
}

const strategiesStore = useStrategiesStore();
const entryRulesStore = useEntryRulesStore();
const moneyRulesStore = useMoneyRulesStore();
const oddsRulesStore = useOddsRulesStore();

const loading = ref(false);
const currentState = ref<ReplayState | null>(null);
const currentPeriod = ref(2023000);
const isPlaying = ref(false);
const playSpeed = ref(1000);
const selectedStrategyId = ref('');
const showHistory = ref(false);
let timer: any = null;

const ZODIAC_NAMES = ['鼠', '牛', '虎', '兔', '龙', '蛇', '马', '羊', '猴', '鸡', '狗', '猪'];
const getZodiacName = (idx: number) => ZODIAC_NAMES[idx] || idx;

const getColorName = (c: number) => ['红波', '蓝波', '绿波'][c];
const getColorType = (c: number) => ['danger', 'primary', 'success'][c];

// 计算要发送给后端的完整配置
const currentStrategyConfig = computed(() => {
    if (!selectedStrategyId.value) return null;
    const strategy = strategiesStore.strategies.find(s => s.id === selectedStrategyId.value);
    if (!strategy) return null;
    
    const entry = entryRulesStore.getRuleById(strategy.entryRuleId);
    const money = moneyRulesStore.getRuleById(strategy.moneyRuleId);
    const odds = strategy.oddsProfileId ? oddsRulesStore.getProfileById(strategy.oddsProfileId) : null;
    
    if (!entry || !money) return null;
    return { entry, money, odds };
});

import { callPython } from '../utils/python';

const fetchState = async (period: string | number) => {
  loading.value = true;
  try {
    const params: any = { period: String(period) };
    if (currentStrategyConfig.value) {
        params.strategy_config = JSON.parse(JSON.stringify(currentStrategyConfig.value));
    }
    
    // 使用 callPython 替代 invoke，因为它是异步 sidecar
    const res = await callPython('get_replay_state', params);
    if (res && res.status === 'ok') {
      currentState.value = res.data;
      console.log("Current State:", currentState.value); // DEBUG
      currentPeriod.value = parseInt(res.data.period);
    } else {
      console.error(res);
      if (isPlaying.value) togglePlay();
    }
  } catch (e: any) {
    console.error("Fetch State 错误:", e);
    ElMessage.error(e.message || "请求超时");
    if (isPlaying.value) togglePlay();
  } finally {
    loading.value = false;
  }
};



const allPeriods = ref<string[]>([]);
const allDates = ref<string[]>([]);
const activePeriods = ref<string[]>([]);
const dateRange = ref<any>(null);
const currentIndex = ref(-1);

const selectedDataSource = ref('all');
const availableYears = ref<string[]>([]);

const initData = async () => {
    loading.value = true;
    try {
        await Promise.all([
            strategiesStore.init(),
            entryRulesStore.init(),
            moneyRulesStore.init(),
            oddsRulesStore.init()
        ]);
        
        // 0. 加载可用年份
        try {
            const years: string[] = await invoke('get_historical_years');
            availableYears.value = years;
        } catch(e) { console.error("加载年份失败", e); }

        // 1. 先加载数据 (让后端自动寻找 all.feather)
        await callPython('load_data', { file_path: "" });

        // 2. 获取数据统计
        const res = await callPython('get_data_stats');
        if (res.status === 'ok' && res.data && res.data.count > 0) {
            allPeriods.value = res.data.periods;
            allDates.value = res.data.dates || [];
            activePeriods.value = [...allPeriods.value];
            
            if (activePeriods.value.length > 0) {
                 currentIndex.value = 0;
                 fetchState(activePeriods.value[0]);
                 
                 // 设置默认时间范围 (最近一年?) 或者不设置显示全部
                 // if (allDates.value.length > 0) {
                 //    dateRange.value = [allDates.value[allDates.value.length-1], allDates.value[0]].sort();
                 // }
            }
        }
    } catch (e: any) {
        console.error("初始化数据失败", e);
        ElMessage.error("初始化数据失败: " + (e.message || "Unknown error"));
    } finally {
        loading.value = false;
    }
};

const handleDataSourceChange = async () => {
    loading.value = true;
    try {
        // 重置状态
        currentIndex.value = -1;
        currentState.value = null;
        dateRange.value = null;
        
        // 加载新数据源
        await callPython('load_data', { file_path: selectedDataSource.value });
        
        // 刷新统计
        const res = await callPython('get_data_stats');
        if (res.status === 'ok' && res.data) {
            allPeriods.value = res.data.periods || [];
            allDates.value = res.data.dates || [];
            activePeriods.value = [...allPeriods.value];
            
            if (activePeriods.value.length > 0) {
                 currentIndex.value = 0;
                 fetchState(activePeriods.value[0]);
            }
            ElMessage.success("数据源切换成功");
        }
    } catch (e: any) {
        ElMessage.error("切换数据源失败: " + e.message);
    } finally {
        loading.value = false;
    }
};

const handleDateRangeChange = () => {
    if (!dateRange.value) {
        activePeriods.value = [...allPeriods.value];
    } else {
        const [start, end] = dateRange.value;
        activePeriods.value = allPeriods.value.filter((_, i) => {
            const date = allDates.value[i];
            return date >= start && date <= end;
        });
    }
    
    if (activePeriods.value.length > 0) {
        currentIndex.value = 0; // 重置到筛选后的第一期
        fetchState(activePeriods.value[0]);
    } else {
        currentIndex.value = -1;
        currentState.value = null;
        ElMessage.warning("该时间段内无数据");
    }
};

const handleStrategyChange = () => {
    if (currentIndex.value !== -1 && activePeriods.value.length > 0) {
        fetchState(activePeriods.value[currentIndex.value]);
    }
};

const nextPeriod = () => {
  if (currentIndex.value < activePeriods.value.length - 1) {
      currentIndex.value++;
      fetchState(activePeriods.value[currentIndex.value]);
  } else {
      ElMessage.info("已是最后一期");
      if (isPlaying.value) togglePlay();
  }
};

const prevPeriod = () => {
  if (currentIndex.value > 0) {
      currentIndex.value--;
      fetchState(activePeriods.value[currentIndex.value]);
  } else {
      ElMessage.info("已是第一期");
  }
};

onMounted(() => {
    initData();
});

const togglePlay = () => {
  isPlaying.value = !isPlaying.value;
  if (isPlaying.value) {
    if (currentIndex.value >= activePeriods.value.length - 1) {
        // Restart if at end?
        currentIndex.value = 0; // or just stop? Let's restart or continue
    }
    timer = setInterval(nextPeriod, playSpeed.value);
  } else {
    clearInterval(timer);
  }
};

onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-header .left { display: flex; align-items: center; }
.signal-alert { margin-bottom: 20px; }
.period-info { text-align: center; }
.balls { display: flex; justify-content: center; gap: 10px; margin: 20px 0; }
.ball { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; }
.normal-ball { background-color: #409EFF; }
.special-ball { background-color: #F56C6C; box-shadow: 0 0 10px rgba(245, 108, 108, 0.5); transform: scale(1.1); }
.zodiac-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; }
.stat-item { display: flex; flex-direction: column; align-items: center; padding: 5px; border: 1px solid #eee; border-radius: 4px; }
.value { font-weight: bold; }
.value.high { color: red; }
.stat-box { text-align: center; }
.stat-box .label { font-size: 12px; color: #909399; margin-bottom: 5px; }
.stat-box .val { font-size: 20px; font-weight: bold; }
.stat-box .val.profit { color: #67C23A; }
.stat-box .val.loss { color: #F56C6C; }
.text-gray { color: #909399; font-style: italic; }

</style>
