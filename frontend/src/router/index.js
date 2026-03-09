import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // 公開頁面
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresGuest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/Register.vue'),
      meta: { requiresGuest: true },
    },

    // 主要內容（需登入）
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: '/home',
        },
        {
          path: 'home',
          name: 'home',
          component: () => import('@/views/Home.vue'),
        },
        {
          path: 'farms',
          name: 'farms',
          component: () => import('@/views/Farms.vue'),
        },
        {
          path: 'farms/:id',
          name: 'farm-detail',
          component: () => import('@/views/FarmDetail.vue'),
        },
        {
          path: 'knowledge',
          name: 'knowledge',
          component: () => import('@/views/Knowledge.vue'),
        },
        {
          path: 'image-records',
          name: 'image-records',
          component: () => import('@/views/ImageRecords.vue'),
        },
      ],
    },

    // 404
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/404.vue'),
    },
  ],
})

// 路由守衛
router.beforeEach(async (to, from, next) => {
  try {
    const authStore = useAuthStore()

    // 初始化 auth store
    if (!authStore.user && authStore.token) {
      try {
        await authStore.initialize()
      } catch (error) {
        console.error('Failed to initialize auth:', error)
        authStore.logout()
      }
    }

    // 需要認證的路由
    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
      next({ name: 'login' })
      return
    }

    // 訪客限定的路由（已登入不能訪問）
    if (to.meta.requiresGuest && authStore.isAuthenticated) {
      next({ name: 'home' })
      return
    }

    next()
  } catch (error) {
    console.error('Router guard error:', error)
    next({ name: 'login' })
  }
})

export default router
