import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../components/layout/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: [
        {
          path: '',
          redirect: '/statistics'
        },
        {
          path: '/data',
          name: 'data',
          component: () => import('../views/DataManagement.vue'),
          meta: { title: '历史数据管理' }
        },
        {
          path: '/statistics',
          name: 'statistics',
          component: () => import('../views/Statistics.vue'),
          meta: { title: '历史开奖统计' }
        },
        {
          path: '/config',
          name: 'config',
          component: () => import('../views/Configuration.vue'),
          meta: { title: '基础配置 (玩法/赔率)' }
        },
        {
          path: '/strategy/workshop',
          name: 'StrategyWorkshop',
          component: () => import('../views/StrategyWorkshop.vue'),
          meta: { title: '策略工坊 (Strategy Workshop)' }
        },
        {
          path: '/strategy/rules/entry',
          name: 'EntryRules',
          component: () => import('../views/EntryRules.vue'),
          meta: { title: '下注条件 (Entry Rules)' }
        },
        {
          path: '/strategy/rules/money',
          name: 'moneyRules',
          component: () => import('../views/MoneyManagement.vue'),
          meta: { title: '资金管理', keepAlive: true }
        },
        {
          path: '/strategy/replay',
          name: 'strategyReplay',
          component: () => import('../views/StrategyReplay.vue'),
          meta: { title: '策略回放' }
        },
        {
          path: '/backtest',
          name: 'backtest',
          component: () => import('../views/BacktestConsole.vue'),
          meta: { title: '回测控制台' }
        },
        {
          path: '/zodiac',
          name: 'zodiac',
          component: () => import('../views/ZodiacMapping.vue'),
          meta: { title: '生肖规则配置' }
        }
      ]
    }
  ]
})

export default router
