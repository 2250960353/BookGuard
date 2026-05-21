<template>
  <div class="page-container">
    <h2 style="color: #5D3A1A; margin-bottom: 20px;">系统设置</h2>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- Tab 1: 系统配置 -->
      <el-tab-pane label="系统配置" name="config">
        <el-row :gutter="20" style="margin-top: 16px;">
          <el-col :span="12">
            <el-card class="card-shadow">
              <template #header><span>OCR 服务配置</span></template>
              <el-form label-width="120px">
                <el-form-item label="UmiOCR 地址">
                  <el-input v-model="ocrUrl" placeholder="http://127.0.0.1:1224" :disabled="isViewer" />
                </el-form-item>
                <el-form-item v-if="!isViewer">
                  <el-button type="primary" @click="testConnection" :loading="testing"><el-icon><Connection /></el-icon> 测试连接</el-button>
                </el-form-item>
                <el-form-item label="连接状态">
                  <el-tag :type="connected ? 'success' : 'danger'" effect="dark">{{ connected ? '已连接' : '未连接' }}</el-tag>
                </el-form-item>
              </el-form>
            </el-card>

            <el-card class="card-shadow" style="margin-top: 16px;">
              <template #header><span>系统信息</span></template>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="系统名称">BookGuard 珍贵图书数字化保护系统</el-descriptions-item>
                <el-descriptions-item label="版本号">1.0.0</el-descriptions-item>
                <el-descriptions-item label="OCR引擎">UmiOCR (RapidOCR / PaddleOCR)</el-descriptions-item>
                <el-descriptions-item label="后端框架">FastAPI + SQLAlchemy</el-descriptions-item>
                <el-descriptions-item label="前端框架">Vue3 + Element Plus</el-descriptions-item>
                <el-descriptions-item label="数据库">SQLite</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>

          <el-col :span="12">
            <el-card class="card-shadow">
              <template #header><div class="card-header"><span>📊 数据统计</span><el-button type="primary" size="small" @click="refreshStats" :loading="statsLoading"><el-icon><Refresh /></el-icon> 刷新</el-button></div></template>
              <div v-if="stats" class="stats-panel">
                <el-row :gutter="12" class="stat-cards">
                  <el-col :span="8"><div class="stat-card stat-primary"><div class="stat-number">{{ stats.total_books }}</div><div class="stat-label">图书总数</div></div></el-col>
                  <el-col :span="8"><div class="stat-card stat-warning"><div class="stat-number">{{ stats.total_pages }}</div><div class="stat-label">总页数</div></div></el-col>
                  <el-col :span="8"><div class="stat-card stat-success"><div class="stat-number">{{ stats.recognized_pages }}</div><div class="stat-label">已识别</div></div></el-col>
                </el-row>
                <el-row :gutter="12" style="margin-top: 12px;">
                  <el-col :span="12"><div class="stat-mini"><span class="mini-label">平均置信度</span><span class="mini-value">{{ stats.avg_confidence > 0 ? (stats.avg_confidence * 100).toFixed(1) : 0 }}%</span></div></el-col>
                  <el-col :span="12"><div class="stat-mini"><span class="mini-label">识别率</span><span class="mini-value">{{ stats.total_pages > 0 ? (stats.recognized_pages / stats.total_pages * 100).toFixed(1) : 0 }}%</span></div></el-col>
                </el-row>
                <el-divider content-position="left">图书状态分布</el-divider>
                <div class="status-bars">
                  <div v-for="(count, status) in stats.books_by_status" :key="status" class="status-bar-row">
                    <span class="status-name">{{ statusLabel(status) }}</span>
                    <el-progress :percentage="stats.total_books > 0 ? Math.round(count / stats.total_books * 100) : 0" :stroke-width="10" :color="statusColor(status)" :format="() => count + ' 本'" />
                  </div>
                </div>
                <el-divider content-position="left">分类分布</el-divider>
                <div class="category-tags">
                  <el-tag v-for="(count, category) in stats.books_by_category" :key="category" size="small" effect="plain" round class="cat-tag">{{ category || '未分类' }} ({{ count }})</el-tag>
                </div>
              </div>
              <el-empty v-else description="点击刷新按钮加载统计数据" :image-size="60" />
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- Tab 2: 用户管理 -->
      <el-tab-pane name="users">
        <template #label>
          👥 用户管理
          <el-badge v-if="currentUser.role === 'admin'" :value="users.length" :max="99" style="margin-left: 6px;" />
        </template>
        <div v-if="currentUser.role === 'admin'" style="margin-top: 16px;">
          <el-card class="card-shadow">
            <template #header>
              <div class="card-header">
                <span>用户列表</span>
                <el-button type="primary" size="small" @click="showAddDialog = true"><el-icon><Plus /></el-icon> 新增用户</el-button>
              </div>
            </template>
            <el-table :data="users" stripe v-loading="loadingUsers" style="width: 100%;">
              <el-table-column prop="username" label="用户名" width="120" />
              <el-table-column prop="real_name" label="姓名" width="120" />
              <el-table-column label="角色" width="120" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.role === 'admin' ? 'danger' : row.role === 'operator' ? 'warning' : 'info'" size="small">
                    {{ roleLabel(row.role) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="90" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.is_active ? 'success' : 'info'" size="small" effect="dark">{{ row.is_active ? '正常' : '已禁用' }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="最后登录" width="170" align="center">
                <template #default="{ row }">{{ row.last_login ? formatTime(row.last_login) : '从未登录' }}</template>
              </el-table-column>
              <el-table-column label="操作" width="140" align="center" fixed="right">
                <template #default="{ row }">
                  <el-popconfirm :title="(row.is_active ? '禁用' : '启用') + '该用户？'" confirm-button-text="确定" cancel-button-text="取消" @confirm="handleToggle(row)" v-if="row.role !== 'admin'">
                    <template #reference>
                      <el-button size="small" :type="row.is_active ? 'warning' : 'success'">{{ row.is_active ? '禁用' : '启用' }}</el-button>
                    </template>
                  </el-popconfirm>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
        <el-empty v-else description="仅管理员可管理用户" :image-size="80" style="margin-top: 40px;" />
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="showAddDialog" title="新增用户" width="420px">
      <el-form :model="newUser" label-width="70px">
        <el-form-item label="用户名"><el-input v-model="newUser.username" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="newUser.password" type="password" show-password /></el-form-item>
        <el-form-item label="姓名"><el-input v-model="newUser.real_name" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="newUser.role" style="width: 100%;">
            <el-option label="操作员" value="operator" />
            <el-option label="只读用户" value="viewer" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateUser" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ocrApi, bookApi, authApi } from '../api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const activeTab = ref('config')
const currentUser = computed(() => {
  try { return JSON.parse(localStorage.getItem('user') || '{}') } catch { return {} }
})
const isViewer = computed(() => currentUser.value.role === 'viewer')

const ocrUrl = ref('http://127.0.0.1:1224')
const testing = ref(false)
const connected = ref(false)
const stats = ref(null)
const statsLoading = ref(false)

const statusLabel = (s) => ({ pending: '待处理', scanning: '扫描中', recognizing: '识别中', reviewing: '校对中', completed: '已完成', archived: '已归档' }[s] || s)
const statusColor = (s) => ({ pending: '#909399', scanning: '#E6A23C', recognizing: '#409EFF', reviewing: '#67C23A', completed: '#67C23A', archived: '#909399' }[s] || '#909399')

async function testConnection() {
  testing.value = true
  try {
    const res = await ocrApi.getStatus()
    connected.value = res.available
    ElMessage.success(res.available ? 'UmiOCR 服务连接成功' : 'UmiOCR 服务不可用')
  } catch {
    connected.value = false
    ElMessage.error('连接失败')
  } finally {
    testing.value = false
  }
}

async function refreshStats() {
  statsLoading.value = true
  try {
    stats.value = await bookApi.getStats()
    ElMessage.success('统计信息已更新')
  } catch {
    ElMessage.error('获取统计失败')
  } finally {
    statsLoading.value = false
  }
}

// 用户管理
const users = ref([])
const loadingUsers = ref(false)
const showAddDialog = ref(false)
const creating = ref(false)
const newUser = ref({ username: '', password: '', real_name: '', role: 'operator' })

const roleLabel = (r) => ({ admin: '系统管理员', operator: '操作员', viewer: '只读用户' }[r] || r)

function formatTime(timeStr) {
  if (!timeStr) return '-'
  const d = new Date(timeStr)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function fetchUsers() {
  loadingUsers.value = true
  try {
    users.value = await authApi.listUsers()
  } catch {
    ElMessage.error('获取用户列表失败')
  } finally {
    loadingUsers.value = false
  }
}

async function handleToggle(user) {
  try {
    const res = await authApi.toggleUser(user.id)
    user.is_active = res.is_active
    ElMessage.success(user.is_active ? '已启用' : '已禁用')
  } catch {
    ElMessage.error('操作失败')
  }
}

async function handleCreateUser() {
  if (!newUser.value.username || !newUser.value.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  creating.value = true
  try {
    await authApi.register(newUser.value)
    ElMessage.success(`用户 "${newUser.value.username}" 创建成功`)
    showAddDialog.value = false
    newUser.value = { username: '', password: '', real_name: '', role: 'operator' }
    fetchUsers()
  } catch (e) {
    const msg = e.response?.data?.detail || '创建失败'
    ElMessage.error(msg)
  } finally {
    creating.value = false
  }
}

watch(() => route.query.tab, (val) => {
  if (val === 'users') {
    activeTab.value = 'users'
    fetchUsers()
  }
}, { immediate: true })

watch(activeTab, (val) => {
  if (val === 'users') {
    fetchUsers()
  }
})

onMounted(async () => {
  refreshStats()
  try {
    const res = await ocrApi.getStatus()
    connected.value = res.available
  } catch {
    connected.value = false
  }
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }

.stat-cards { margin-bottom: 8px; }
.stat-card { text-align: center; padding: 16px 8px; border-radius: 10px; background: #FAFAFA; }
.stat-primary { border-left: 4px solid #409EFF; }
.stat-warning { border-left: 4px solid #E6A23C; }
.stat-success { border-left: 4px solid #67C23A; }
.stat-number { font-size: 28px; font-weight: bold; color: #333; line-height: 1.2; }
.stat-label { font-size: 13px; color: #999; margin-top: 4px; }
.stat-mini { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #FAFAFA; border-radius: 6px; }
.mini-label { font-size: 13px; color: #666; }
.mini-value { font-weight: bold; color: #5D3A1A; font-size: 15px; }
.status-bars { padding: 0 4px; }
.status-bar-row { margin-bottom: 10px; }
.status-name { display: inline-block; width: 56px; font-size: 13px; color: #666; vertical-align: middle; }
.category-tags { padding: 0 4px; }
.cat-tag { margin: 2px 4px 2px 0; }
</style>
