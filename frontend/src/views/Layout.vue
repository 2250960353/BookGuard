<template>
  <el-container class="layout-container">
    <el-header class="layout-header">
      <div class="header-left">
        <div class="logo" @click="$router.push('/')">
          <el-icon :size="28"><Reading /></el-icon>
          <span class="logo-text">BookGuard</span>
          <span class="logo-sub">珍贵图书数字化保护系统</span>
        </div>
      </div>
      <div class="header-right">
        <el-tag :type="ocrAvailable ? 'success' : 'danger'" effect="dark" size="small">
          <el-icon><Connection /></el-icon>
          OCR服务: {{ ocrAvailable ? '已连接' : '未连接' }}
        </el-tag>
        <el-dropdown @command="handleDropdown">
          <div class="user-btn">
            <el-icon :size="18"><User /></el-icon>
            <span class="user-name">{{ currentUser.real_name || currentUser.username }}</span>
            <el-icon :size="12" style="margin-left: 2px;"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="users" v-if="currentUser.role === 'admin'">
                <el-icon><UserFilled /></el-icon> 用户管理
              </el-dropdown-item>
              <el-dropdown-item command="settings"><el-icon><Setting /></el-icon> 系统设置</el-dropdown-item>
              <el-dropdown-item command="logout" divided><el-icon><SwitchButton /></el-icon> 退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>
    <el-container class="main-container">
      <el-aside width="220px" class="layout-aside">
        <el-menu
          :default-active="currentRoute"
          router
          class="side-menu"
        >
          <el-menu-item index="/dashboard">
            <el-icon><DataBoard /></el-icon>
            <span>工作台</span>
          </el-menu-item>
          <el-menu-item index="/books">
            <el-icon><Notebook /></el-icon>
            <span>图书管理</span>
          </el-menu-item>
          <el-menu-item index="/ocr">
            <el-icon><Postcard /></el-icon>
            <span>OCR识别</span>
          </el-menu-item>
          <el-menu-item index="/search">
            <el-icon><Search /></el-icon>
            <span>全文检索</span>
          </el-menu-item>
          <el-menu-item index="/export">
            <el-icon><Download /></el-icon>
            <span>导出管理</span>
          </el-menu-item>
          <el-menu-item index="/recycle">
            <el-icon><Delete /></el-icon>
            <span>回收站</span>
          </el-menu-item>
          <el-divider />
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ocrApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const currentRoute = computed(() => route.path)
const ocrAvailable = ref(false)

const currentUser = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}')
  } catch {
    return {}
  }
})

const roleLabel = (role) => ({ admin: '系统管理员', operator: '操作员', viewer: '只读用户' }[role] || role)

onMounted(async () => {
  try {
    const res = await ocrApi.getStatus()
    ocrAvailable.value = res.available
  } catch {
    ocrAvailable.value = false
  }
})

async function handleDropdown(command) {
  if (command === 'users') {
    router.push({ path: '/settings', query: { tab: 'users' } })
  } else if (command === 'settings') {
    router.push('/settings')
  } else if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '退出确认', {
        confirmButtonText: '确定退出',
        cancelButtonText: '取消',
        type: 'warning',
      })
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      ElMessage.success('已退出登录')
      router.push('/login')
    } catch {
      // 取消
    }
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #5D3A1A 0%, #8B4513 100%);
  color: white;
  padding: 0 24px;
  height: 60px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.logo-text {
  font-size: 22px;
  font-weight: bold;
  letter-spacing: 1px;
}

.logo-sub {
  font-size: 13px;
  opacity: 0.8;
  margin-left: 8px;
  padding-left: 12px;
  border-left: 1px solid rgba(255,255,255,0.3);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 10px;
  border-radius: 20px;
  background: rgba(255,255,255,0.15);
  transition: background 0.2s;
}
.user-btn:hover { background: rgba(255,255,255,0.25); }
.user-name { font-size: 13px; font-weight: 500; }

.main-container {
  height: calc(100vh - 60px);
}

.layout-aside {
  background: #FFFDF7;
  border-right: 1px solid #E8DFD0;
  overflow-y: auto;
}

.side-menu {
  border-right: none;
  background: transparent;
}

.side-menu .el-menu-item {
  height: 48px;
  line-height: 48px;
  margin: 4px 8px;
  border-radius: 6px;
}

.side-menu .el-menu-item.is-active {
  background: rgba(139, 69, 19, 0.1);
  color: #8B4513;
  font-weight: 600;
}

.layout-main {
  background: #F5F0E8;
  overflow-y: auto;
  padding: 24px;
}
</style>
