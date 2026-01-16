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
          path: '/strategy',
          name: 'strategy',
          component: () => import('../views/StrategyEditor.vue'),
          meta: { title: '策略与规则' }
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
