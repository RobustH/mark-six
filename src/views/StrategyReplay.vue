<template>
  <div class="replay-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>策略回放/手动回测 (Replay Mode)</span>
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
import { ref, onMounted, onUnmounted } from 'vue';
import { invoke } from '@tauri-apps/api/core'; // Tauri v2
import { ElMessage } from 'element-plus';
// Note: standard tauri API might be different in v2 depending on setup.
// Using @tauri-apps/api/core is standard for V2.

const loading = ref(false);
const currentState = ref<any>(null);
const currentPeriod = ref(2023000); // Start point
const isPlaying = ref(false);
const playSpeed = ref(1000);
let timer: any = null;

const ZODIAC_NAMES = ['鼠', '牛', '虎', '兔', '龙', '蛇', '马', '羊', '猴', '鸡', '狗', '猪'];
const getZodiacName = (idx: number) => ZODIAC_NAMES[idx] || idx;

const getColorName = (c: number) => ['红波', '蓝波', '绿波'][c];
const getColorType = (c: number) => ['danger', 'primary', 'success'][c];

const fetchState = async (period: string | number) => {
  loading.value = true;
  try {
    const res: any = await invoke('get_replay_state', { period: String(period) });
    if (res && res.status === 'ok') {
      currentState.value = res.data;
      currentPeriod.value = parseInt(res.data.period);
    } else {
      console.error(res);
      // If error (e.g. period not found/end of data), stop playing
      if (isPlaying.value) togglePlay();
    }
  } catch (e) {
    console.error("IPC Error:", e);
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
        const res: any = await invoke('get_data_stats');
        if (res.status === 'ok' && res.data.count > 0) {
            allPeriods.value = res.data.periods;
            // Default to first period if current not set
            if (currentIndex.value === -1) {
                currentIndex.value = 0;
                fetchState(allPeriods.value[0]);
            }
        } else {
             ElMessage.warning("未加载数据或数据为空");
        }
    } catch (e) {
        console.error("Init failed", e);
    } finally {
        loading.value = false;
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
