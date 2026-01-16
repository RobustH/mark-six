<template>
  <div class="money-management-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>资金管理策略 (Money Management)</span>
          <el-button type="primary" size="small" @click="openDrawer()">新建策略</el-button>
        </div>
      </template>

      <!-- Strategy List -->
      <div class="content">
        <el-table :data="moneyRulesStore.rules" style="width: 100%" v-if="moneyRulesStore.rules.length > 0">
          <el-table-column prop="name" label="策略名称" width="200" />
          <el-table-column prop="mode" label="模式" width="120">
            <template #default="scope">
              <el-tag :type="getModeType(scope.row.mode)">{{ formatMode(scope.row.mode) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="参数详情">
            <template #default="scope">
               <span v-if="scope.row.mode === 'fixed'">
                 基础注额: {{ scope.row.params.baseBet }}
               </span>
               <span v-else-if="scope.row.mode === 'martingale'">
                 起步: {{ scope.row.params.baseBet }} | 倍投: [{{ scope.row.params.multipliers?.join(', ') }}]
               </span>
            </template>
          </el-table-column>
          <el-table-column fixed="right" label="操作" width="150">
            <template #default="scope">
              <el-button link type="primary" size="small" @click="openDrawer(scope.row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="handleDelete(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无策略，请新建 (No strategies found, please create one)" />
      </div>
    </el-card>

    <!-- Editor Drawer -->
    <el-drawer
      v-model="drawerVisible"
      :title="isEditMode ? '编辑资金策略' : '新建资金策略'"
      size="40%"
    >
      <el-form :model="currentRule" label-width="120px">
        <el-form-item label="策略名称" required>
          <el-input v-model="currentRule.name" placeholder="例如：平注10元 或 经典倍投" />
        </el-form-item>
        
        <el-form-item label="管理模式" required>
          <el-radio-group v-model="currentRule.mode" @change="handleModeChange">
            <el-radio-button label="fixed">平注 (Fixed)</el-radio-button>
            <el-radio-button label="martingale">马丁格尔 (Martingale)</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-divider>参数配置 (Parameters)</el-divider>

        <el-form-item label="基础注额" required>
           <el-input-number v-model="currentRule.params.baseBet" :min="1" label="Base Bet" />
           <div class="form-tip">每次下注的起始金额</div>
        </el-form-item>

        <!-- Martingale Specifics -->
        <template v-if="currentRule.mode === 'martingale'">
           <el-form-item label="倍投序列">
             <el-input v-model="multipliersInput" placeholder="1, 2, 4, 8, 16..." @blur="parseMultipliers" />
             <div class="form-tip">输了之后下一次的倍数，用逗号分隔 (例如: 1, 2, 4, 8)</div>
           </el-form-item>
        </template>

        <el-divider>风控 (Risk Control)</el-divider>
        <el-form-item label="止盈金额">
           <el-input-number v-model="currentRule.params.takeProfit" :min="0" placeholder="不设限" />
        </el-form-item>
        <el-form-item label="止损金额">
           <el-input-number v-model="currentRule.params.stopLoss" :min="0" placeholder="不设限" />
        </el-form-item>

      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="drawerVisible = false">取消</el-button>
          <el-button type="primary" @click="saveRule">保存</el-button>
        </span>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useMoneyRulesStore } from '../stores/moneyRules';
import type { MoneyRuleConfig, MoneyMode } from '../types/strategy';
import { ElMessage, ElMessageBox } from 'element-plus';

const moneyRulesStore = useMoneyRulesStore();
const drawerVisible = ref(false);
const isEditMode = ref(false);
const multipliersInput = ref('1, 2, 4, 8, 16');

const defaultRule: Omit<MoneyRuleConfig, 'id' | 'createTime' | 'updateTime'> = {
  name: '',
  mode: 'fixed',
  params: {
    baseBet: 10,
    multipliers: [],
    maxBet: undefined,
    stopLoss: undefined,
    takeProfit: undefined
  }
};

const currentRule = ref<Omit<MoneyRuleConfig, 'id' | 'createTime' | 'updateTime'> & { id?: string }>({ ...defaultRule });

// Watcher to sync multipliersInput when editing
watch(() => currentRule.value.params.multipliers, (newVal) => {
  if (newVal && newVal.length > 0) {
    multipliersInput.value = newVal.join(', ');
  } else {
    multipliersInput.value = '1, 2, 4, 8, 16'; // default hint
  }
}, { immediate: true });

const openDrawer = (rule?: MoneyRuleConfig) => {
  if (rule) {
    isEditMode.value = true;
    currentRule.value = JSON.parse(JSON.stringify(rule));
    if (currentRule.value.params.multipliers) {
       multipliersInput.value = currentRule.value.params.multipliers.join(', ');
    }
  } else {
    isEditMode.value = false;
    currentRule.value = {
      name: '',
      mode: 'fixed',
      params: {
        baseBet: 10,
        multipliers: [1, 2, 4, 8, 16] // Default sequence logic
      }
    };
    multipliersInput.value = '1, 2, 4, 8, 16';
  }
  drawerVisible.value = true;
};

const formatMode = (mode: MoneyMode) => {
  const maps: Record<MoneyMode, string> = {
    fixed: '平注 (Fixed)',
    martingale: '马丁格尔 (Martingale)',
    paroli: '帕罗利 (Paroli)'
  };
  return maps[mode] || mode;
};

const getModeType = (mode: MoneyMode) => {
  if (mode === 'fixed') return 'success';
  if (mode === 'martingale') return 'warning';
  return 'info';
};

const parseMultipliers = () => {
  if (!multipliersInput.value) {
    currentRule.value.params.multipliers = [];
    return;
  }
  const parts = multipliersInput.value.split(/[,，]/).map(s => s.trim()).filter(s => s);
  const numbers = parts.map(Number).filter(n => !isNaN(n));
  currentRule.value.params.multipliers = numbers;
};

const handleModeChange = (val: MoneyMode) => {
   // Reset default logic when switching
   if (val === 'martingale' && (!currentRule.value.params.multipliers || currentRule.value.params.multipliers.length === 0)) {
       currentRule.value.params.multipliers = [1, 2, 4, 8, 16];
       multipliersInput.value = '1, 2, 4, 8, 16';
   }
};

const saveRule = () => {
  if (!currentRule.value.name) {
    ElMessage.error('请输入策略名称');
    return;
  }
  
  if (currentRule.value.mode === 'martingale') {
     parseMultipliers(); // Ensure latest
     if (!currentRule.value.params.multipliers || currentRule.value.params.multipliers.length === 0) {
        ElMessage.warning('马丁格尔模式需要配置倍投序列');
        return;
     }
  }

  if (isEditMode.value && currentRule.value.id) {
    moneyRulesStore.updateRule(currentRule.value.id, currentRule.value);
    ElMessage.success('更新成功');
  } else {
    moneyRulesStore.addRule(currentRule.value);
    ElMessage.success('创建成功');
  }
  drawerVisible.value = false;
};

const handleDelete = (id: string) => {
  ElMessageBox.confirm('确定要删除该策略吗？', '警告', {
    type: 'warning'
  }).then(() => {
    moneyRulesStore.deleteRule(id);
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
.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.2;
  margin-top: 4px;
}
</style>
