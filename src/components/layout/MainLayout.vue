<template>
  <el-container class="layout-container">
    <el-aside width="240px">
      <div class="logo">
        <h2 class="app-title">Mark Six Quant</h2>
        <div class="version">v2.3</div>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="el-menu-vertical"
        background-color="#1d1e1f"
        text-color="#cfd3dc"
        active-text-color="#409eff"
        router
      >
        <el-menu-item index="/data">
          <el-icon><DataLine /></el-icon>
          <span>历史数据管理</span>
        </el-menu-item>
        <el-menu-item index="/statistics">
          <el-icon><TrendCharts /></el-icon>
          <span>历史开奖统计</span>
        </el-menu-item>
        <el-sub-menu index="/strategy">
          <template #title>
            <el-icon><Cpu /></el-icon>
            <span>策略与规则</span>
          </template>
          <el-menu-item index="/strategy/workshop">策略工坊</el-menu-item>
          <el-sub-menu index="/strategy/rules">
            <template #title>规则配置</template>
            <el-menu-item index="/strategy/rules/entry">下注条件</el-menu-item>
            <el-menu-item index="/strategy/rules/money">资金管理</el-menu-item>
          </el-sub-menu>
        </el-sub-menu>
        <el-menu-item index="/backtest">
          <el-icon><VideoPlay /></el-icon>
          <span>回测控制台</span>
        </el-menu-item>
        <el-sub-menu index="/config-group">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统配置</span>
          </template>
          <el-menu-item index="/config">基础赔率规则</el-menu-item>
          <el-menu-item index="/zodiac">年份生肖映射</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header height="60px" class="header">
        <div class="header-left">
          <h3 class="page-title">{{ currentRouteName }}</h3>
        </div>
        <div class="header-right">
          <el-tag type="info" effect="dark" round>Environment: Dev</el-tag>
        </div>
      </el-header>
      
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { DataLine, TrendCharts, Setting, VideoPlay, Cpu } from '@element-plus/icons-vue'

const route = useRoute()

const activeMenu = computed(() => route.path)
const currentRouteName = computed(() => route.meta.title || '')
</script>

<style scoped lang="scss">
.layout-container {
  height: 100vh;
  background-color: #141414;
}

.el-aside {
  background-color: #1d1e1f;
  border-right: 1px solid #2c2d2e;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid #2c2d2e;
  
  .app-title {
    color: #fff;
    font-size: 16px;
    margin: 0;
    font-weight: 600;
  }
  
  .version {
    font-size: 12px;
    color: #909399;
    padding: 2px 6px;
    background: #303133;
    border-radius: 4px;
  }
}

.el-menu-vertical {
  border-right: none;
  flex: 1;
}

.header {
  background-color: #1d1e1f;
  border-bottom: 1px solid #2c2d2e;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.page-title {
  margin: 0;
  color: #E5EAF3;
  font-weight: 500;
  font-size: 16px;
}

.main-content {
  padding: 24px;
  background-color: #141414;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
