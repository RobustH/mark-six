<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <span>6.2 历史开奖统计</span>
            <el-tag type="info" size="small" class="ml-2">Statistics</el-tag>
          </div>
          <div class="header-actions">
            <el-select v-model="selectedYear" placeholder="年份" style="width: 110px" @change="fetchStatistics">
              <el-option label="全部年份" value="" />
              <el-option v-for="year in years" :key="year" :label="year + '年'" :value="year" />
            </el-select>
            <el-select v-model="selectedLimit" placeholder="期数范围" style="width: 120px" @change="fetchStatistics">
              <el-option v-for="opt in periodOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
            </el-select>
            <el-button type="primary" :icon="Refresh" circle @click="fetchStatistics" :loading="loading" />
          </div>
        </div>
      </template>

      <div v-loading="loading">
        <el-tabs v-model="activeTab" class="stats-tabs">
          <!-- 特码统计 -->
          <el-tab-pane label="特码统计" name="special">
            <el-tabs v-model="specialSubTab" type="card">
              <el-tab-pane label="号码" name="number">
                <stats-table :data="statsData.special_number" />
              </el-tab-pane>
              <el-tab-pane label="生肖" name="zodiac">
                <stats-table :data="statsData.special_zodiac" />
              </el-tab-pane>
              <el-tab-pane label="波色" name="color">
                <stats-table :data="statsData.special_color" />
              </el-tab-pane>
              <el-tab-pane label="单双" name="odd">
                <stats-table :data="statsData.special_odd" />
              </el-tab-pane>
              <el-tab-pane label="大小" name="size">
                <stats-table :data="statsData.special_size" />
              </el-tab-pane>
              <el-tab-pane label="尾数" name="tail">
                <stats-table :data="statsData.special_tail" />
              </el-tab-pane>
            </el-tabs>
          </el-tab-pane>

          <!-- 正码统计 -->
          <el-tab-pane label="正码统计" name="normal">
            <el-alert title="正码统计说明" type="info" description="统计1-49号在正码位置(n1-n6)出现的各项指标" show-icon :closable="false"
              class="mb-4" />
            <stats-table :data="statsData.normal_number" />
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { invoke } from '@tauri-apps/api/core';
import { Refresh } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const loading = ref(false);
const years = ref<string[]>([]);
const selectedYear = ref("");
const selectedLimit = ref<number | null>(null);
const activeTab = ref("special");
const specialSubTab = ref("number");

const periodOptions = [
  { label: '全部期数', value: 0 },
  { label: '近50期', value: 50 },
  { label: '近100期', value: 100 },
  { label: '近200期', value: 200 },
  { label: '近500期', value: 500 },
];

const statsData = reactive({
  special_number: [],
  special_zodiac: [],
  special_color: [],
  special_odd: [],
  special_size: [],
  special_tail: [],
  normal_number: []
});

const fetchYears = async () => {
  try {
    const res = await invoke<string[]>('get_historical_years');
    years.value = res;
  } catch (err) {
    console.error("Failed to fetch years", err);
  }
};

const fetchStatistics = async () => {
  loading.value = true;
  try {
    const limit = selectedLimit.value === 0 ? null : selectedLimit.value;
    const res = await invoke<any>('get_statistics', {
      year: selectedYear.value || null,
      limit: limit
    });
    statsData.special_number = res.special_number;
    statsData.special_zodiac = res.special_zodiac;
    statsData.special_color = res.special_color;
    statsData.special_odd = res.special_odd;
    statsData.special_size = res.special_size;
    statsData.special_tail = res.special_tail;
    statsData.normal_number = res.normal_number;
  } catch (err: any) {
    ElMessage.error("获取统计数据失败: " + err);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchYears();
  fetchStatistics();
});
</script>

<script lang="ts">
import { defineComponent, h, resolveComponent } from 'vue';

const StatsTable = defineComponent({
  props: ['data'],
  setup(props) {
    return () => {
      const ElTable = resolveComponent('el-table');
      const ElTableColumn = resolveComponent('el-table-column');
      // Set default sort orders to ensure descending is prioritized and visible
      const sortOrders = ['descending', 'ascending', null];

      return h(ElTable, {
        data: props.data || [],
        stripe: true,
        border: true,
        style: { width: '100%' },
        'default-sort': { prop: 'current_omission', order: 'descending' }
      }, () => [
        h(ElTableColumn, { prop: 'label', label: '属性', width: '120', sortable: true, fixed: true }),
        h(ElTableColumn, {
          prop: 'current_omission',
          label: '当前遗漏',
          sortable: true,
          width: '120',
          'sort-orders': sortOrders
        }),
        h(ElTableColumn, {
          prop: 'max_omission',
          label: '历史最大遗漏',
          sortable: true,
          width: '150',
          'sort-orders': sortOrders
        }),
        h(ElTableColumn, {
          prop: 'frequency',
          label: '热度(次数)',
          sortable: true,
          width: '120',
          'sort-orders': sortOrders
        }),
        h(ElTableColumn, {
          prop: 'avg_omission',
          label: '平均遗漏',
          sortable: true,
          formatter: (row: any) => row.avg_omission?.toFixed(2),
          'sort-orders': sortOrders
        }),
      ]);
    }
  }
});

export default {
  components: { StatsTable }
}
</script>

<style scoped>
.page-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.stats-tabs {
  margin-top: 10px;
}

.ml-2 {
  margin-left: 8px;
}

.mb-4 {
  margin-bottom: 16px;
}
</style>
