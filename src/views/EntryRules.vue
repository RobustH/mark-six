<template>
  <div class="entry-rules-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>下注触发条件 (Entry Rules)</span>
          <el-button type="primary" size="small" @click="openDrawer()">新建规则</el-button>
        </div>
      </template>
      <div class="content">
        <el-table :data="entryRulesStore.rules" style="width: 100%" v-if="entryRulesStore.rules.length > 0">
          <el-table-column prop="name" label="规则名称" width="200" />
          <el-table-column prop="logicOperator" label="逻辑关系" width="100">
            <template #default="scope">
              <el-tag>{{ scope.row.logicOperator }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="条件概览">
            <template #default="scope">
              <el-tag 
                v-for="cond in scope.row.conditions" 
                :key="cond.id" 
                type="info" 
                size="small" 
                style="margin-right: 5px; margin-bottom: 5px;"
              >
                {{ formatCondition(cond) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column fixed="right" label="操作" width="150">
            <template #default="scope">
              <el-button link type="primary" size="small" @click="openDrawer(scope.row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="handleDelete(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无规则，请新建 (No rules found, please create one)" />
      </div>
    </el-card>

    <!-- Rule Editor Drawer -->
    <el-drawer
      v-model="drawerVisible"
      :title="isEditMode ? '编辑规则 (Edit Rule)' : '新建规则 (New Rule)'"
      size="50%"
    >
      <el-form :model="currentRule" label-width="120px">
        <el-form-item label="规则名称" required>
          <el-input v-model="currentRule.name" placeholder="例如：特码红波遗漏追号" />
        </el-form-item>
        <el-form-item label="逻辑运算符" required>
          <el-radio-group v-model="currentRule.logicOperator">
            <el-radio-button label="AND">满足所有 (AND)</el-radio-button>
            <el-radio-button label="OR">满足任一 (OR)</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-divider>条件列表 (Conditions)</el-divider>

        <div v-for="(cond, index) in currentRule.conditions" :key="index" class="condition-row">
          <div class="condition-header">
            <span>条件 {{ index + 1 }}</span>
            <el-button type="danger" icon="Delete" circle size="small" @click="removeCondition(index)" />
          </div>
          
          <el-row :gutter="10">
            <el-col :span="6">
              <el-select v-model="cond.type" placeholder="类型" size="small">
                <el-option label="遗漏 (Omission)" value="omission" />
                <el-option label="窗口统计 (Window Stat)" value="window_stat" />
                <el-option label="连中/连挂 (Streak)" value="streak" />
              </el-select>
            </el-col>
            <el-col :span="6">
              <el-select v-model="cond.target" placeholder="目标" size="small">
                <el-option label="特码 (Special)" value="special" />
                <el-option label="正码 (Normal)" value="normal" />
              </el-select>
            </el-col>
            <el-col :span="6">
              <el-select v-model="cond.dimension" placeholder="维度" size="small">
                <el-option label="号码 (Number)" value="number" />
                <el-option label="生肖 (Zodiac)" value="zodiac" />
                <el-option label="波色 (Color)" value="color" />
                <el-option label="五行 (Wuxing)" value="wuxing" />
                <el-option label="大小 (Size)" value="size" />
                <el-option label="单双 (Parity)" value="parity" />
                <el-option label="尾数 (Tail)" value="tail" />
              </el-select>
            </el-col>
             <el-col :span="6" v-if="cond.type === 'window_stat'">
              <el-input v-model.number="cond.window" placeholder="窗口期数" size="small">
                 <template #prefix>最近</template>
              </el-input>
            </el-col>
          </el-row>

          <el-row :gutter="10" style="margin-top: 10px;">
             <el-col :span="8">
              <!-- Value Input based on Dimension -->
              <el-select v-if="cond.dimension === 'color'" v-model="cond.value" placeholder="选择波色" size="small">
                 <el-option label="红波" value="red" />
                 <el-option label="蓝波" value="blue" />
                 <el-option label="绿波" value="green" />
              </el-select>
              <el-select v-else-if="cond.dimension === 'parity'" v-model="cond.value" placeholder="选择单双" size="small">
                 <el-option label="单" value="odd" />
                 <el-option label="双" value="even" />
              </el-select>
              <el-select v-else-if="cond.dimension === 'size'" v-model="cond.value" placeholder="选择大小" size="small">
                 <el-option label="大" value="big" />
                 <el-option label="小" value="small" />
              </el-select>
              <el-select v-else-if="cond.dimension === 'wuxing'" v-model="cond.value" placeholder="选择五行" size="small">
                 <el-option v-for="w in ['金', '木', '水', '火', '土']" :key="w" :label="w" :value="w" />
              </el-select>
              <el-select v-else-if="cond.dimension === 'zodiac'" v-model="cond.value" placeholder="选择生肖" size="small">
                 <el-option v-for="z in ['鼠','牛','虎','兔','龙','蛇','马','羊','猴','鸡','狗','猪']" :key="z" :label="z" :value="z" />
              </el-select>
              <el-select v-else-if="cond.dimension === 'tail'" v-model="cond.value" placeholder="选择尾数" size="small">
                 <el-option v-for="t in 10" :key="t-1" :label="(t-1)+'尾'" :value="String(t-1)" />
              </el-select>
              <el-input v-else v-model="cond.value" placeholder="值 (例如: 10)" size="small" />
             </el-col>

            <el-col :span="6">
              <el-select v-model="cond.operator" placeholder="操作符" size="small">
                <el-option label=">=" value=">=" />
                <el-option label="<=" value="<=" />
                <el-option label="==" value="==" />
                <el-option label=">" value=">" />
                <el-option label="<" value="<" />
              </el-select>
            </el-col>
            <el-col :span="6">
              <el-input-number v-model="cond.threshold" placeholder="阈值" size="small" style="width: 100%" />
            </el-col>
          </el-row>
        </div>

        <el-button type="info" plain style="width: 100%; margin-top: 10px;" icon="Plus" @click="addCondition">
          添加条件
        </el-button>

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
import { ref, onMounted } from 'vue';
import { useEntryRulesStore } from '../stores/entryRules';
import type { EntryRuleConfig, Condition } from '../types/strategy';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Delete, Plus } from '@element-plus/icons-vue';

const entryRulesStore = useEntryRulesStore();

onMounted(() => {
    entryRulesStore.init();
});
const drawerVisible = ref(false);
const isEditMode = ref(false);

const defaultRule: Omit<EntryRuleConfig, 'id' | 'createTime' | 'updateTime'> = {
  name: '',
  logicOperator: 'AND',
  conditions: []
};

const currentRule = ref<Omit<EntryRuleConfig, 'id' | 'createTime' | 'updateTime'> & { id?: string }>({ ...defaultRule });

const openDrawer = (rule?: EntryRuleConfig) => {
  if (rule) {
    isEditMode.value = true;
    // Deep copy to facilitate reactivity
    currentRule.value = JSON.parse(JSON.stringify(rule));
  } else {
    isEditMode.value = false;
    currentRule.value = {
      name: '',
      logicOperator: 'AND',
      conditions: []
    };
    // Add one default condition for better UX
    addCondition();
  }
  drawerVisible.value = true;
};

const addCondition = () => {
  currentRule.value.conditions.push({
    id: Date.now().toString(),
    type: 'omission',
    target: 'special',
    dimension: 'color',
    value: 'red',
    operator: '>=',
    threshold: 5
  });
};

const removeCondition = (index: number) => {
  currentRule.value.conditions.splice(index, 1);
};

const saveRule = () => {
  if (!currentRule.value.name) {
    ElMessage.error('请输入规则名称 (Please enter rule name)');
    return;
  }
  if (currentRule.value.conditions.length === 0) {
     ElMessage.error('请至少添加一个条件 (Please add at least one condition)');
     return;
  }

  if (isEditMode.value && currentRule.value.id) {
    entryRulesStore.updateRule(currentRule.value.id, currentRule.value);
    ElMessage.success('更新成功 (Updated successfully)');
  } else {
    entryRulesStore.addRule(currentRule.value);
     ElMessage.success('创建成功 (Created successfully)');
  }
  drawerVisible.value = false;
};

const handleDelete = (id: string) => {
  ElMessageBox.confirm(
    '确定要删除该规则吗？(Are you sure to delete?)',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    entryRulesStore.deleteRule(id);
    ElMessage.success('删除成功 (Deleted successfully)');
  });
};

const formatCondition = (cond: Condition) => {
  // Simple formatter for list display
  let text = `${cond.type} | ${cond.target}.${cond.dimension}`;
  if (cond.type === 'window_stat') {
    text += `[${cond.window}期]`;
  }
  // 如果值是特殊英文，转换显示? 也可以直接显示value
  // 这里做一个简单的映射，提升可读性
  const map: any = { red:'红波', blue:'蓝波', green:'绿波', big:'大', small:'小', odd:'单', even:'双' };
  const displayVal = map[String(cond.value)] || cond.value;
  
  text += ` ${cond.operator} ${displayVal} (Th: ${cond.threshold})`;
  return text;
};
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.condition-row {
  border: 1px dashed #409eff;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 10px;
  background-color: #ecf5ff;
}
.condition-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  font-size: 12px;
  color: #606266;
}
/* Dark Mode Adaption for condition row if needed, element-plus style usually handles input bg */
</style>
