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
          </div>
          <div class="controls">
             <el-button-group>
               <el-button icon="ArrowLeft" @click="prevPeriod" :disabled="loading">上一期</el-button>
               <el-button type="primary" :icon="isPlaying ? 'VideoPause' : 'VideoPlay'" @click="togglePlay">
                 {{ isPlaying ? '暂停' : '自动回放' }}
               </el-button>
               <el-button icon="ArrowRight" @click="nextPeriod" :disabled="loading">下一期 (Next)</el-button>
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
               <el-descriptions :column="2" border>
                 <el-descriptions-item label="红波遗漏">{{ currentState.stats.omission.color_0 }}</el-descriptions-item>
                 <el-descriptions-item label="蓝波遗漏">{{ currentState.stats.omission.color_1 }}</el-descriptions-item>
                 <el-descriptions-item label="绿波遗漏">{{ currentState.stats.omission.color_2 }}</el-descriptions-item>
               </el-descriptions>
               
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
               <el-descriptions :column="2" border>
                 <el-descriptions-item label="红波热度">{{ currentState.stats.freq_100.color_0 }}</el-descriptions-item>
                 <el-descriptions-item label="蓝波热度">{{ currentState.stats.freq_100.color_1 }}</el-descriptions-item>
                 <el-descriptions-item label="绿波热度">{{ currentState.stats.freq_100.color_2 }}</el-descriptions-item>
               </el-descriptions>
            </el-col>
          </el-row>
        </div>
        
        <el-empty v-else description="请点击下一期开始回放" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { invoke } from '@tauri-apps/api/core';
import { ElMessage } from 'element-plus';
import { useStrategiesStore } from '../stores/strategies';
import { useEntryRulesStore } from '../stores/entryRules';
import { useMoneyRulesStore } from '../stores/moneyRules';

const strategiesStore = useStrategiesStore();
const entryRulesStore = useEntryRulesStore();
const moneyRulesStore = useMoneyRulesStore();

const loading = ref(false);
const currentState = ref<any>(null);
const currentPeriod = ref(2023000);
const isPlaying = ref(false);
const playSpeed = ref(1000);
const selectedStrategyId = ref('');
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
    
    if (!entry || !money) return null;
    return { entry, money };
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
const currentIndex = ref(-1);

const initData = async () => {
    loading.value = true;
    try {
        await Promise.all([
            strategiesStore.init(),
            entryRulesStore.init(),
            moneyRulesStore.init()
        ]);
        
        // 使用 callPython
        const res = await callPython('get_data_stats');
        if (res.status === 'ok' && res.data && res.data.count > 0) {
            allPeriods.value = res.data.periods;
            if (currentIndex.value === -1) {
                currentIndex.value = 0;
                fetchState(allPeriods.value[0]);
            }
        }
    } catch (e: any) {
        console.error("初始化数据失败", e);
        ElMessage.error("初始化数据失败: " + (e.message || "Unknown error"));
    } finally {
        loading.value = false;
    }
};

const handleStrategyChange = () => {
    if (currentIndex.value !== -1) {
        fetchState(allPeriods.value[currentIndex.value]);
    }
};

const nextPeriod = () => {
  if (currentIndex.value < allPeriods.value.length - 1) {
      currentIndex.value++;
      fetchState(allPeriods.value[currentIndex.value]);
  } else {
      ElMessage.info("已是最后一期");
      if (isPlaying.value) togglePlay();
  }
};

const prevPeriod = () => {
  if (currentIndex.value > 0) {
      currentIndex.value--;
      fetchState(allPeriods.value[currentIndex.value]);
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
    if (currentIndex.value >= allPeriods.value.length - 1) {
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

</style>
