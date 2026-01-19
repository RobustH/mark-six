<template>
  <div class="page-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>历史数据管理</span>
          <div class="actions">
            <el-select v-model="selectedYear" placeholder="选择年份" style="width: 120px" @change="loadData" clearable>
              <el-option label="全部年份" value="" />
              <el-option v-for="year in availableYears" :key="year" :label="year" :value="year" />
            </el-select>
            <el-button type="primary" @click="handleImport" :loading="importing">导入数据</el-button>
            <el-button type="success" @click="handleSync" :loading="syncing">在线更新</el-button>
            <el-button @click="loadData" :loading="loading">刷新数据</el-button>
          </div>
        </div>
      </template>

      <el-table v-if="tableData.length > 0" :data="paginatedData" border stripe style="width: 100%"
        height="calc(100vh - 250px)">
        <el-table-column prop="period" label="期号" align="center" />
        <el-table-column prop="date" label="开奖日期" align="center" />
        <el-table-column label="正码" align="center">
          <el-table-column label="正1" align="center">
            <template #default="scope">
              <div class="number-cell">
                <div class="color-circle" :class="scope.row.n1_color">
                  <span class="circle-number">{{ scope.row.n1 }}</span>
                </div>
                <span class="number-info">{{ scope.row.n1_zodiac }}/{{ scope.row.n1_odd ? '单' : '双' }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="正2" align="center">
            <template #default="scope">
              <div class="number-cell">
                <div class="color-circle" :class="scope.row.n2_color">
                  <span class="circle-number">{{ scope.row.n2 }}</span>
                </div>
                <span class="number-info">{{ scope.row.n2_zodiac }}/{{ scope.row.n2_odd ? '单' : '双' }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="正3" align="center">
            <template #default="scope">
              <div class="number-cell">
                <div class="color-circle" :class="scope.row.n3_color">
                  <span class="circle-number">{{ scope.row.n3 }}</span>
                </div>
                <span class="number-info">{{ scope.row.n3_zodiac }}/{{ scope.row.n3_odd ? '单' : '双' }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="正4" align="center">
            <template #default="scope">
              <div class="number-cell">
                <div class="color-circle" :class="scope.row.n4_color">
                  <span class="circle-number">{{ scope.row.n4 }}</span>
                </div>
                <span class="number-info">{{ scope.row.n4_zodiac }}/{{ scope.row.n4_odd ? '单' : '双' }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="正5" align="center">
            <template #default="scope">
              <div class="number-cell">
                <div class="color-circle" :class="scope.row.n5_color">
                  <span class="circle-number">{{ scope.row.n5 }}</span>
                </div>
                <span class="number-info">{{ scope.row.n5_zodiac }}/{{ scope.row.n5_odd ? '单' : '双' }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="正6" align="center">
            <template #default="scope">
              <div class="number-cell">
                <div class="color-circle" :class="scope.row.n6_color">
                  <span class="circle-number">{{ scope.row.n6 }}</span>
                </div>
                <span class="number-info">{{ scope.row.n6_zodiac }}/{{ scope.row.n6_odd ? '单' : '双' }}</span>
              </div>
            </template>
          </el-table-column>
        </el-table-column>
        <el-table-column label="特码" align="center">
          <template #default="scope">
            <div class="number-cell special-cell">
              <div class="color-circle" :class="scope.row.special_color">
                <span class="circle-number special-number">{{ scope.row.special }}</span>
              </div>
              <span class="number-info">{{ scope.row.special_zodiac }}/{{ scope.row.special_odd ? '单' : '双' }}</span>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-else description="暂无历史数据，请导入" />

      <div class="pagination-container" v-if="tableData.length > 0">
        <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :page-sizes="[20, 50, 100, 200]"
          layout="total, sizes, prev, pager, next, jumper" :total="tableData.length" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import { open } from '@tauri-apps/plugin-dialog'
import { ElMessage } from 'element-plus'

const tableData = ref<any[]>([])
const loading = ref(false)
const importing = ref(false)
const syncing = ref(false)
const currentPage = ref(1)
const pageSize = ref(50)
const selectedYear = ref('')
const availableYears = ref<string[]>([])

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return tableData.value.slice(start, end)
})

const loadYears = async () => {
  try {
    const years: string[] = await invoke('get_historical_years')
    availableYears.value = years
  } catch (error: any) {
    console.error('加载年份失败:', error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const data: any = await invoke('get_historical_data', { year: selectedYear.value })
    tableData.value = data
  } catch (error: any) {
    ElMessage.error('加载数据失败: ' + error)
  } finally {
    loading.value = false
  }
}

const handleImport = async () => {
  try {
    const selected = await open({
      multiple: false,
      filters: [{
        name: 'Excel',
        extensions: ['xlsx', 'xls']
      }]
    })

    if (selected && !Array.isArray(selected)) {
      importing.value = true
      const result: string = await invoke('import_excel', { filePath: selected })
      ElMessage.success(result)
      await loadYears()
      await loadData()
    }
  } catch (error: any) {
    ElMessage.error('导入失败: ' + error)
  } finally {
    importing.value = false
  }
}

const handleSync = async () => {
  syncing.value = true
  try {
    // 默认更新所有年份 (2000-至今)
    const result: string = await invoke('fetch_historical_data', { years: null })
    ElMessage.success(result)
    await loadYears()
    await loadData()
  } catch (error: any) {
    ElMessage.error('更新失败: ' + error)
  } finally {
    syncing.value = false
  }
}

onMounted(() => {
  loadYears()
  loadData()
})
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

.actions {
  display: flex;
  gap: 10px;
}

.number-cell {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}

.color-circle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 5px solid;
  flex-shrink: 0;
  background-color: white;
}

.color-circle.red {
  border-color: #f56c6c;
}

.color-circle.blue {
  border-color: #409eff;
}

.color-circle.green {
  border-color: #67c23a;
}

.circle-number {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.number-info {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
}

.special-cell .circle-number {
  font-weight: bold;
  color: #f56c6c;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
