<template>
  <div class="page-container">
    <div class="welcome-section">
      <h1>珍贵图书数字化保护系统</h1>
      <p class="subtitle">基于 UmiOCR 手写文字识别技术，为珍贵古籍文献提供全方位数字化保护方案</p>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-number">{{ stats?.total_books || 0 }}</div>
          <div class="stat-label">馆藏图书</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-number">{{ stats?.total_pages || 0 }}</div>
          <div class="stat-label">总页数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-number">{{ stats?.recognized_pages || 0 }}</div>
          <div class="stat-label">已识别页数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-number">{{ (stats?.avg_confidence * 100 || 0).toFixed(1) }}%</div>
          <div class="stat-label">平均置信度</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 24px;">
      <el-col :span="16">
        <el-card class="card-shadow">
          <template #header>
            <div class="card-header">
              <span>最近图书</span>
              <el-button type="primary" text @click="$router.push('/books')">
                查看全部 <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </template>
          <el-table :data="recentBooks" stripe style="width: 100%">
            <el-table-column prop="title" label="书名" min-width="200" />
            <el-table-column prop="author" label="作者" width="120" />
            <el-table-column prop="category" label="分类" width="100" />
            <el-table-column prop="total_pages" label="页数" width="80" align="center" />
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="置信度" width="100" align="center">
              <template #default="{ row }">
                <span v-if="row.avg_confidence > 0">{{ (row.avg_confidence * 100).toFixed(1) }}%</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="card-shadow">
          <template #header><span>分类统计</span></template>
          <div v-if="categoryStats.length > 0">
            <div v-for="cat in categoryStats" :key="cat.category" class="category-item">
              <span class="category-name">{{ cat.category || '未分类' }}</span>
              <el-progress
                :percentage="cat.percentage"
                :stroke-width="16"
                :color="'#8B4513'"
                :format="() => cat.count + '本'"
              />
            </div>
          </div>
          <el-empty v-else description="暂无数据" :image-size="60" />
        </el-card>

        <el-card class="card-shadow" style="margin-top: 16px;">
          <template #header><span>OCR 服务状态</span></template>
          <div class="ocr-status">
            <el-icon :size="48" :color="ocrAvailable ? '#67C23A' : '#F56C6C'">
              <Connection />
            </el-icon>
            <div>
              <p :style="{ color: ocrAvailable ? '#67C23A' : '#F56C6C', fontWeight: 'bold' }">
                {{ ocrAvailable ? '服务正常运行' : '服务未连接' }}
              </p>
              <p style="color: #999; font-size: 13px;">UmiOCR HTTP API</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { bookApi, ocrApi } from '../api'

const stats = ref({})
const recentBooks = ref([])
const categoryStats = ref([])
const ocrAvailable = ref(false)

const statusType = (status) => {
  const map = { pending: 'info', scanning: 'warning', recognizing: '', reviewing: 'success', completed: 'success', archived: 'info' }
  return map[status] || 'info'
}

const statusLabel = (status) => {
  const map = { pending: '待处理', scanning: '扫描中', recognizing: '识别中', reviewing: '校对中', completed: '已完成', archived: '已归档' }
  return map[status] || status
}

onMounted(async () => {
  try {
    const [s, books, cats, ocr] = await Promise.all([
      bookApi.getStats(),
      bookApi.list({ limit: 5 }),
      bookApi.getCategories(),
      ocrApi.getStatus(),
    ])
    stats.value = s
    recentBooks.value = books.items
    ocrAvailable.value = ocr.available

    const total = cats.reduce((sum, c) => sum + c.count, 0)
    categoryStats.value = cats.map(c => ({
      ...c,
      percentage: total > 0 ? Math.round(c.count / total * 100) : 0,
    }))
  } catch (e) {
    console.error(e)
  }
})
</script>

<style scoped>
.welcome-section {
  text-align: center;
  padding: 30px 0 20px;
}

.welcome-section h1 {
  font-size: 28px;
  color: #5D3A1A;
  margin-bottom: 8px;
}

.subtitle {
  color: #999;
  font-size: 15px;
}

.stats-row {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.category-item {
  margin-bottom: 16px;
}

.category-name {
  font-size: 14px;
  margin-bottom: 6px;
  display: block;
}

.ocr-status {
  display: flex;
  align-items: center;
  gap: 16px;
}
</style>
