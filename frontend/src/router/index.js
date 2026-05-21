import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '工作台' },
      },
      {
        path: 'books',
        name: 'BookList',
        component: () => import('../views/BookList.vue'),
        meta: { title: '图书管理' },
      },
      {
        path: 'books/:id',
        name: 'BookDetail',
        component: () => import('../views/BookDetail.vue'),
        meta: { title: '图书详情' },
      },
      {
        path: 'ocr',
        name: 'OcrWorkspace',
        component: () => import('../views/OcrWorkspace.vue'),
        meta: { title: 'OCR识别' },
      },
      {
        path: 'search',
        name: 'Search',
        component: () => import('../views/Search.vue'),
        meta: { title: '全文检索' },
      },
      {
        path: 'export',
        name: 'Export',
        component: () => import('../views/Export.vue'),
        meta: { title: '导出管理' },
      },
      {
        path: 'recycle',
        name: 'RecycleBin',
        component: () => import('../views/RecycleBin.vue'),
        meta: { title: '回收站' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../views/Settings.vue'),
        meta: { title: '系统设置' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || 'BookGuard'} - 珍贵图书数字化保护系统`
  const token = localStorage.getItem('token')
  if (!to.meta.public && !token) {
    next('/login')
  } else if (to.meta.public && token && to.path === '/login') {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
