<template>
  <div class="page-container">
    <div class="page-header">
      <h2 style="color: #5D3A1A;">🗑️ 回收站</h2>
      <el-tag type="info" size="large">已删除的内容将在此保留，可随时恢复或永久清除</el-tag>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- Tab 1: 已删除的图书 -->
      <el-tab-pane label="已删除图书" name="books">
        <el-card class="card-shadow" style="margin-bottom: 16px;">
          <el-row :gutter="16" align="middle">
            <el-col :span="8">
              <el-input v-model="bookKeyword" placeholder="搜索已删除图书..." clearable @clear="fetchBooks" @keyup.enter="fetchBooks">
                <template #prefix><el-icon><Search /></el-icon></template>
              </el-input>
            </el-col>
            <el-col :span="4">
              <el-button @click="fetchBooks"><el-icon><Refresh /></el-icon> 刷新</el-button>
            </el-col>
          </el-row>
        </el-card>

        <el-empty v-if="!booksLoading && books.length === 0" description="暂无已删除的图书" :image-size="100">
          <template #image><el-icon :size="60" color="#C0C4CC"><Notebook /></el-icon></template>
        </el-empty>

        <el-table v-else :data="books" stripe v-loading="booksLoading" style="width: 100%;">
          <el-table-column label="图书信息" min-width="260">
            <template #default="{ row }">
              <div class="book-cell">
                <el-icon :size="26" color="#909399"><Notebook /></el-icon>
                <div class="book-detail">
                  <span class="book-title">{{ row.title }}</span>
                  <span class="book-meta">{{ row.author || '未知作者' }} {{ row.dynasty ? '· ' + row.dynasty : '' }} · 共 {{ row.total_pages }} 页</span>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="category" label="分类" width="90" />
          <el-table-column label="原状态" width="90" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="删除时间" width="170" align="center">
            <template #default="{ row }">{{ formatTime(row.deleted_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="180" align="center" fixed="right" v-if="!isViewer">
            <template #default="{ row }">
              <el-button type="success" size="small" @click="handleRestoreBook(row)" plain><el-icon><RefreshRight /></el-icon> 恢复</el-button>
              <el-popconfirm title="确定要永久删除此图书？所有页面和数据将无法恢复！" confirm-button-text="确定删除" cancel-button-text="取消" @confirm="handlePermanentDeleteBook(row)">
                <template #reference>
                  <el-button type="danger" size="small"><el-icon><Delete /></el-icon> 永久删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-wrapper" v-if="bookTotal > bookPageSize">
          <el-pagination v-model:current-page="bookPage" :page-size="bookPageSize" :total="bookTotal" layout="total, prev, pager, next" @current-change="fetchBooks" />
        </div>
      </el-tab-pane>

      <!-- Tab 2: 已删除的页面（属于未删除的图书） -->
      <el-tab-pane name="pages">
        <template #label>
          已删除页面<el-badge v-if="pageTotal > 0" :value="pageTotal" :max="99" style="margin-left: 6px;" />
        </template>

        <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px;">
          此处显示的是从正常图书中单独删除的页面。如果整本书被删除，其页面会随书一起恢复。
        </el-alert>

        <el-input v-model="pageKeyword" placeholder="搜索已删除的页面（按图书名）..." clearable @clear="fetchPages" @keyup.enter="fetchPages" style="margin-bottom: 12px;">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>

        <el-empty v-if="!pagesLoading && pages.length === 0" description="暂无已删除的页面" :image-size="100">
          <template #image><el-icon :size="60" color="#C0C4CC"><Document /></el-icon></template>
        </el-empty>

        <el-table v-else :data="pages" stripe v-loading="pagesLoading" style="width: 100%;">
          <el-table-column label="页面信息" min-width="280">
            <template #default="{ row }">
              <div class="page-cell">
                <el-icon :size="24" color="#909399"><Document /></el-icon>
                <div class="page-detail">
                  <span class="page-title">第 {{ row.page_number }} 页</span>
                  <span class="page-meta">所属图书：<strong>{{ row.book_title }}</strong>{{ row.ocr_text ? ' · 有识别文本' : '' }}</span>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="原状态" width="90" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === 'completed' ? 'success' : 'info'">{{ pageStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="删除时间" width="170" align="center">
            <template #default="{ row }">{{ formatTime(row.deleted_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="200" align="center" fixed="right" v-if="!isViewer">
            <template #default="{ row }">
              <el-button type="success" size="small" @click="handleRestorePage(row)" plain><el-icon><RefreshRight /></el-icon> 恢复</el-button>
              <el-popconfirm title="确定要永久删除此页面？数据将无法恢复！" confirm-button-text="确定删除" cancel-button-text="取消" @confirm="handlePermanentDeletePage(row)">
                <template #reference>
                  <el-button type="danger" size="small"><el-icon><Delete /></el-icon> 永久删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-wrapper" v-if="pageTotal > pagePageSize">
          <el-pagination v-model:current-page="pagePage" :page-size="pagePageSize" :total="pageTotal" layout="total, prev, pager, next" @current-change="fetchPages" />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { recycleApi } from '../api'
import { ElMessage } from 'element-plus'

const currentUser = computed(() => {
  try { return JSON.parse(localStorage.getItem('user') || '{}') } catch { return {} }
})
const isViewer = computed(() => currentUser.value.role === 'viewer')
const activeTab = ref('books')

const books = ref([])
const bookTotal = ref(0)
const bookPage = ref(1)
const bookPageSize = ref(10)
const bookKeyword = ref('')
const booksLoading = ref(false)

const pages = ref([])
const pageTotal = ref(0)
const pagePage = ref(1)
const pagePageSize = ref(10)
const pagesLoading = ref(false)
const pageKeyword = ref('')

const statusType = (s) => ({ pending: 'info', scanning: 'warning', recognizing: '', reviewing: 'success', completed: 'success', archived: 'info' }[s] || 'info')
const statusLabel = (s) => ({ pending: '待处理', scanning: '扫描中', recognizing: '识别中', reviewing: '校对中', completed: '已完成', archived: '已归档' }[s] || s)
const pageStatusLabel = (s) => ({ pending: '待处理', processing: '识别中', completed: '已完成', failed: '失败' }[s] || s)

function formatTime(timeStr) {
  if (!timeStr) return '-'
  const d = new Date(timeStr)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function fetchBooks() {
  booksLoading.value = true
  try {
    const params = { skip: (bookPage.value - 1) * bookPageSize.value, limit: bookPageSize.value }
    if (bookKeyword.value) params.keyword = bookKeyword.value
    const res = await recycleApi.list(params)
    books.value = res.items
    bookTotal.value = res.total
  } finally {
    booksLoading.value = false
  }
}

async function fetchPages() {
  pagesLoading.value = true
  try {
    const params = { skip: (pagePage.value - 1) * pagePageSize.value, limit: pagePageSize.value }
    if (pageKeyword.value) params.keyword = pageKeyword.value
    const res = await recycleApi.listPages(params)
    pages.value = res.items
    pageTotal.value = res.total
  } finally {
    pagesLoading.value = false
  }
}

watch(activeTab, (val) => {
  if (val === 'pages') fetchPages()
})

async function handleRestoreBook(book) {
  try {
    await recycleApi.restore(book.id)
    ElMessage.success(`"${book.title}" 已恢复到图书列表`)
    fetchBooks()
  } catch {
    ElMessage.error('恢复失败')
  }
}

async function handlePermanentDeleteBook(book) {
  try {
    await recycleApi.permanentDelete(book.id)
    ElMessage.success(`"${book.title}" 已永久删除`)
    fetchBooks()
  } catch {
    ElMessage.error('删除失败')
  }
}

async function handleRestorePage(page) {
  try {
    await recycleApi.restorePage(page.id)
    ElMessage.success(`第 ${page.page_number} 页已恢复`)
    fetchPages()
  } catch {
    ElMessage.error('恢复失败，可能所属图书已被删除')
  }
}

async function handlePermanentDeletePage(page) {
  try {
    await recycleApi.permanentDeletePage(page.id)
    ElMessage.success('页面已永久删除')
    fetchPages()
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchBooks()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h2 { color: #5D3A1A; }

.book-cell, .page-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.book-detail, .page-detail {
  display: flex;
  flex-direction: column;
}
.book-title, .page-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}
.book-meta, .page-meta {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}
.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
