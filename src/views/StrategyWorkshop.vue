<template>
  <div class="strategy-workshop-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>策略工坊 (Strategy Workshop)</span>
          <div>
            <span v-if="currentDataFile" style="font-size: 12px; color: #909399; margin-right: 10px;">
              当前数据: {{ currentDataFile.split(/[\\/]/).pop() }}
            </span>
            <el-button type="primary" size="small" plain @click="handleSelectData">选择数据源</el-button>
            <el-button type="success" size="small" @click="$router.push('/strategy/replay')">手动回放模式</el-button>
            <el-button type="primary" size="small" @click="openDrawer()">新建策略</el-button>
          </div>
        </div>
      </template>

      <!-- Strategy List -->
      <div class="content">
        <el-table :data="strategiesStore.strategies" style="width: 100%" v-if="strategiesStore.strategies.length > 0">
          <el-table-column prop="name" label="策略名称" width="200" />
          <el-table-column label="组成规则">
            <template #default="scope">
              <el-tag type="info" style="margin-right: 5px;">Entry: {{ getEntryRuleName(scope.row.entryRuleId) }}</el-tag>
              <el-tag type="warning">Money: {{ getMoneyRuleName(scope.row.moneyRuleId) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column fixed="right" label="操作" width="200">
            <template #default="scope">
              <el-button link type="primary" size="small" @click="openDrawer(scope.row)">编辑</el-button>
              <el-button link type="primary" size="small">立即回测</el-button>
              <el-button link type="danger" size="small" @click="handleDelete(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无策略，请新建 (No strategies found, please create one)" />
      </div>
    </el-card>

    <!-- Strategy Editor Drawer -->
    <el-drawer
      v-model="drawerVisible"
      :title="isEditMode ? '编辑策略' : '组装新策略'"
      size="50%"
    >
      <el-form :model="currentStrategy" label-width="120px">
        <el-form-item label="策略名称" required>
          <el-input v-model="currentStrategy.name" placeholder="例如：红波追号+马丁格尔V1" />
        </el-form-item>
        
        <el-form-item label="策略描述">
          <el-input v-model="currentStrategy.description" type="textarea" />
        </el-form-item>

        <el-divider>规则组装 (Assembly)</el-divider>

        <el-form-item label="下注条件" required>
          <el-select v-model="currentStrategy.entryRuleId" placeholder="请选择下注触发条件" style="width: 100%">
             <el-option
               v-for="rule in entryRulesStore.rules"
               :key="rule.id"
               :label="rule.name"
               :value="rule.id"
             />
          </el-select>
          <div v-if="entryRulesStore.rules.length === 0" class="form-tip-error">
            暂无可用规则，请先去 <router-link to="/strategy/rules/entry">规则配置</router-link> 创建。
          </div>
        </el-form-item>

        <el-form-item label="资金管理" required>
          <el-select v-model="currentStrategy.moneyRuleId" placeholder="请选择资金注码策略" style="width: 100%">
             <el-option
               v-for="rule in moneyRulesStore.rules"
               :key="rule.id"
               :label="rule.name"
               :value="rule.id"
             />
          </el-select>
           <div v-if="moneyRulesStore.rules.length === 0" class="form-tip-error">
            暂无可用规则，请先去 <router-link to="/strategy/rules/money">规则配置</router-link> 创建。
          </div>
        </el-form-item>

      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="drawerVisible = false">取消</el-button>
          <el-button type="primary" @click="saveStrategy">保存策略</el-button>
        </span>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useStrategiesStore } from '../stores/strategies';
import { useEntryRulesStore } from '../stores/entryRules';
import { useMoneyRulesStore } from '../stores/moneyRules';
import type { StrategyConfig } from '../types/strategy';
import { ElMessage, ElMessageBox } from 'element-plus';
import { open } from '@tauri-apps/plugin-dialog';
import { invoke } from '@tauri-apps/api/core';

const strategiesStore = useStrategiesStore();
const entryRulesStore = useEntryRulesStore();
const moneyRulesStore = useMoneyRulesStore();

const drawerVisible = ref(false);
const isEditMode = ref(false);

const defaultStrategy: Omit<StrategyConfig, 'id' | 'createTime' | 'updateTime'> = {
  name: '',
  description: '',
  entryRuleId: '',
  moneyRuleId: ''
};

const currentStrategy = ref<Omit<StrategyConfig, 'id' | 'createTime' | 'updateTime'> & { id?: string }>({ ...defaultStrategy });

// Helper to display names in table
const getEntryRuleName = (id: string) => {
  const r = entryRulesStore.getRuleById(id);
  return r ? r.name : 'Unknown Rule';
};

const getMoneyRuleName = (id: string) => {
  const r = moneyRulesStore.getRuleById(id);
  return r ? r.name : 'Unknown Rule';
};

const openDrawer = (strategy?: StrategyConfig) => {
  if (strategy) {
    isEditMode.value = true;
    currentStrategy.value = JSON.parse(JSON.stringify(strategy));
  } else {
    isEditMode.value = false;
    currentStrategy.value = { ...defaultStrategy };
  }
  drawerVisible.value = true;
};

const saveStrategy = () => {
  if (!currentStrategy.value.name) {
    ElMessage.error('请输入策略名称');
    return;
  }
  if (!currentStrategy.value.entryRuleId) {
    ElMessage.error('请选择下注条件');
    return;
  }
  if (!currentStrategy.value.moneyRuleId) {
    ElMessage.error('请选择资金管理策略');
    return;
  }

  if (isEditMode.value && currentStrategy.value.id) {
    strategiesStore.updateStrategy(currentStrategy.value.id, currentStrategy.value);
    ElMessage.success('策略更新成功');
  } else {
    strategiesStore.addStrategy(currentStrategy.value);
    ElMessage.success('策略创建成功');
  }
  drawerVisible.value = false;
};

const currentDataFile = ref('');

const handleSelectData = async () => {
    try {
        const selected = await open({
            multiple: false,
            filters: [{
                name: 'Feather Data',
                extensions: ['feather', 'arrow']
            }]
        });
        
        if (selected) {
            // Check if selected is string or array (based on multiple)
            const path = Array.isArray(selected) ? selected[0] : selected;
            currentDataFile.value = path;
            
            // Invoke backend to load data
            const res: any = await invoke('load_data_source', { filePath: path });
            if (res.status === 'ok') {
                ElMessage.success('数据加载成功');
            } else {
                ElMessage.error('数据加载失败: ' + res.message);
            }
        }
    } catch (e) {
        console.error('Selection failed', e);
        ElMessage.error('选择文件失败');
    }
};

const handleDelete = (id: string) => {
  ElMessageBox.confirm('确定要删除该策略吗？', '警告', {
    type: 'warning'
  }).then(() => {
    strategiesStore.deleteStrategy(id);
    ElMessage.success('删除成功');
  });
};
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.form-tip-error {
  font-size: 12px;
  color: #f56c6c;
  line-height: 1.2;
  margin-top: 4px;
}
</style>
