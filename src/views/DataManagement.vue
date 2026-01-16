<template>
  <div class="page-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>历史数据管理</span>
          <el-button type="primary">导入数据</el-button>
        </div>
      </template>
      <div class="placeholder-content">
        <el-empty description="数据管理功能开发中..." />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.page-container {
  height: 100%;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
