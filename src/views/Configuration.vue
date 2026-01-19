<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>💰 赔率配置管理</span>
          <el-button type="primary" @click="openDialog()">
            <el-icon><Plus /></el-icon>
            新增赔率
          </el-button>
        </div>
      </template>

      <!-- 赔率列表 -->
      <el-table :data="oddsStore.profiles" stripe style="width: 100%">
        <el-table-column prop="name" label="名称" width="150" />
        <el-table-column prop="playType" label="玩法类型" width="140">
          <template #default="{ row }">
            <el-tag :type="getPlayTypeTagType(row.playType as PlayType)">
              {{ playTypeLabels[row.playType as PlayType] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="odds" label="赔率" width="100">
          <template #default="{ row }">
            <span class="odds-value">{{ row.odds.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="rebate" label="返水" width="80">
          <template #default="{ row }">
            {{ row.rebate != null ? (row.rebate * 100).toFixed(1) + '%' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="100" />
        <el-table-column label="生效区间" width="200">
          <template #default="{ row }">
            <span v-if="row.validFrom || row.validTo">
              {{ row.validFrom || '∞' }} ~ {{ row.validTo || '∞' }}
            </span>
            <span v-else class="text-muted">永久有效</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <el-empty v-if="oddsStore.profiles.length === 0" description="暂无赔率配置，请点击上方按钮新增" />
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEditing ? '编辑赔率配置' : '新增赔率配置'" width="500px">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="formData.name" placeholder="如：特码单双-标准赔率" />
        </el-form-item>
        
        <el-form-item label="玩法类型" prop="playType">
          <el-select v-model="formData.playType" placeholder="请选择玩法类型" style="width: 100%">
            <el-option
              v-for="(label, key) in playTypeLabels"
              :key="key"
              :label="label"
              :value="key"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="固定赔率" prop="odds">
          <el-input-number v-model="formData.odds" :min="1" :max="100" :precision="2" :step="0.1" style="width: 100%" />
        </el-form-item>

        <el-form-item label="返水比例">
          <el-input-number v-model="formData.rebate" :min="0" :max="0.2" :precision="3" :step="0.001" style="width: 100%">
            <template #append>%</template>
          </el-input-number>
          <div class="form-tip">可选，如 0.01 表示 1% 返水</div>
        </el-form-item>

        <el-form-item label="封顶收益">
          <el-input-number v-model="formData.maxPayout" :min="0" :precision="0" style="width: 100%" />
          <div class="form-tip">可选，最大单注收益上限</div>
        </el-form-item>

        <el-form-item label="版本号" prop="version">
          <el-input v-model="formData.version" placeholder="如：v1.0" />
        </el-form-item>

        <el-form-item label="生效区间">
          <el-date-picker
            v-model="formData.validRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
          <div class="form-tip">可选，不填则永久有效</div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import { useOddsRulesStore } from '../stores/oddsRules';
import type { OddsProfile, PlayType } from '../types/strategy';

const oddsStore = useOddsRulesStore();

// 玩法类型标签映射
const playTypeLabels: Record<PlayType, string> = {
  special_number: '特码号码',
  special_color: '特码波色',
  special_zodiac: '特码生肖',
  special_parity: '特码单双',
  special_size: '特码大小',
};

// 获取玩法类型对应的 tag 样式
const getPlayTypeTagType = (playType: PlayType) => {
  const types: Record<PlayType, string> = {
    special_number: 'danger',
    special_color: 'success',
    special_zodiac: 'warning',
    special_parity: 'info',
    special_size: '',
  };
  return types[playType] || '';
};

// 对话框状态
const dialogVisible = ref(false);
const isEditing = ref(false);
const editingId = ref<string | null>(null);
const formRef = ref<FormInstance>();

// 表单数据
const formData = reactive({
  name: '',
  playType: '' as PlayType | '',
  odds: 1.98,
  rebate: undefined as number | undefined,
  maxPayout: undefined as number | undefined,
  version: 'v1.0',
  validRange: null as [string, string] | null,
});

// 表单验证规则
const formRules: FormRules = {
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  playType: [{ required: true, message: '请选择玩法类型', trigger: 'change' }],
  odds: [{ required: true, message: '请输入赔率', trigger: 'blur' }],
  version: [{ required: true, message: '请输入版本号', trigger: 'blur' }],
};

// 打开对话框
const openDialog = (profile?: OddsProfile) => {
  if (profile) {
    isEditing.value = true;
    editingId.value = profile.id;
    formData.name = profile.name;
    formData.playType = profile.playType;
    formData.odds = profile.odds;
    formData.rebate = profile.rebate;
    formData.maxPayout = profile.maxPayout;
    formData.version = profile.version;
    formData.validRange = profile.validFrom && profile.validTo
      ? [profile.validFrom, profile.validTo]
      : null;
  } else {
    isEditing.value = false;
    editingId.value = null;
    formData.name = '';
    formData.playType = '';
    formData.odds = 1.98;
    formData.rebate = undefined;
    formData.maxPayout = undefined;
    formData.version = 'v1.0';
    formData.validRange = null;
  }
  dialogVisible.value = true;
};

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    const profileData = {
      name: formData.name,
      playType: formData.playType as PlayType,
      odds: formData.odds,
      rebate: formData.rebate,
      maxPayout: formData.maxPayout,
      version: formData.version,
      validFrom: formData.validRange?.[0],
      validTo: formData.validRange?.[1],
    };

    try {
      if (isEditing.value && editingId.value) {
        await oddsStore.updateProfile(editingId.value, profileData);
        ElMessage.success('赔率配置已更新');
      } else {
        await oddsStore.addProfile(profileData);
        ElMessage.success('赔率配置已添加');
      }
      dialogVisible.value = false;
    } catch (e) {
      ElMessage.error('操作失败: ' + (e as Error).message);
    }
  });
};

// 删除配置
const handleDelete = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定要删除此赔率配置吗？', '确认删除', {
      type: 'warning',
    });
    await oddsStore.deleteProfile(id);
    ElMessage.success('已删除');
  } catch {
    // 用户取消
  }
};

// 初始化
onMounted(async () => {
  await oddsStore.init();
});
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

.odds-value {
  font-weight: bold;
  color: var(--el-color-primary);
  font-size: 1.1em;
}

.text-muted {
  color: var(--el-text-color-secondary);
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
</style>
