<template>
  <div class="page-container">
    <div class="page-header">
      <h2>图书管理</h2>
      <el-button type="primary" @click="showCreateDialog = true" v-if="!isViewer">
        <el-icon><Plus /></el-icon> 新建图书
      </el-button>
    </div>

    <el-card class="card-shadow" style="margin-bottom: 16px;">
      <el-row :gutter="16" align="middle">
        <el-col :span="8">
          <el-input v-model="searchKeyword" placeholder="搜索图书名称..." clearable @clear="fetchBooks" @keyup.enter="fetchBooks">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterStatus" placeholder="状态筛选" clearable @change="fetchBooks">
            <el-option label="待处理" value="pending" />
            <el-option label="扫描中" value="scanning" />
            <el-option label="识别中" value="recognizing" />
            <el-option label="校对中" value="reviewing" />
            <el-option label="已完成" value="completed" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterCategory" placeholder="分类筛选" clearable filterable allow-create @change="fetchBooks">
            <el-option v-for="cat in categories" :key="cat.category" :label="cat.category || '未分类'" :value="cat.category" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button @click="fetchBooks"><el-icon><Refresh /></el-icon> 刷新</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-row :gutter="16">
      <el-col :span="8" v-for="book in books" :key="book.id">
        <el-card class="book-card card-shadow" @click="$router.push(`/books/${book.id}`)">
          <div class="book-delete-btn" @click.stop v-if="!isViewer">
            <el-popconfirm title="确定删除此图书？所有页面和数据将被清除" confirm-button-text="确定" cancel-button-text="取消" @confirm="handleDelete(book)">
              <template #reference>
                <el-button circle size="small" type="danger"><el-icon><Delete /></el-icon></el-button>
              </template>
            </el-popconfirm>
          </div>
          <div class="book-cover">
            <img v-if="book.total_pages > 0" :src="bookApi.getCoverUrl(book.id)" alt="" @error="onCoverError" class="cover-img" />
            <el-icon v-else :size="48" color="#8B4513"><Notebook /></el-icon>
          </div>
          <div class="book-info">
            <h3 class="book-title">{{ book.title }}</h3>
            <p class="book-meta">{{ book.author || '未知作者' }} {{ book.dynasty ? '· ' + book.dynasty : '' }}</p>
            <div class="book-tags">
              <el-tag size="small" v-if="book.category">{{ book.category }}</el-tag>
              <el-tag size="small" type="warning" v-if="book.is_handwritten">手写</el-tag>
              <el-tag :type="statusType(book.status)" size="small">{{ statusLabel(book.status) }}</el-tag>
            </div>
            <div class="book-progress">
              <el-progress
                :percentage="book.total_pages > 0 ? Math.round(book.recognized_pages / book.total_pages * 100) : 0"
                :stroke-width="6"
                :color="'#8B4513'"
                :format="() => `${book.recognized_pages}/${book.total_pages}页`"
              />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchBooks"
      />
    </div>

    <el-dialog v-model="showCreateDialog" title="新建图书" width="600px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="书名" required>
          <el-input v-model="createForm.title" placeholder="请输入书名" />
        </el-form-item>
        <el-form-item label="作者">
          <el-input v-model="createForm.author" placeholder="请输入作者" />
        </el-form-item>
        <el-form-item label="朝代">
          <el-input v-model="createForm.dynasty" placeholder="如：清、明、宋" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="createForm.category" placeholder="如：经部、史部、子部、集部" />
        </el-form-item>
        <el-form-item label="语言">
          <el-select v-model="createForm.language">
            <el-option label="简体中文" value="简体中文" />
            <el-option label="繁体中文" value="繁體中文" />
            <el-option label="日本語" value="日本語" />
            <el-option label="English" value="English" />
          </el-select>
        </el-form-item>
        <el-form-item label="手写体">
          <el-switch v-model="createForm.is_handwritten" active-text="是" inactive-text="否" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="图书描述信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { bookApi } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const currentUser = computed(() => {
  try { return JSON.parse(localStorage.getItem('user') || '{}') } catch { return {} }
})
const isViewer = computed(() => currentUser.value.role === 'viewer')
const books = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(9)
const searchKeyword = ref('')
const filterStatus = ref('')
const filterCategory = ref('')
const categories = ref([])
const showCreateDialog = ref(false)
const creating = ref(false)

const createForm = ref({
  title: '', author: '', dynasty: '', category: '',
  language: '简体中文', is_handwritten: false, description: '',
})

const statusType = (s) => ({ pending: 'info', scanning: 'warning', recognizing: '', reviewing: 'success', completed: 'success', archived: 'info' }[s] || 'info')
const statusLabel = (s) => ({ pending: '待处理', scanning: '扫描中', recognizing: '识别中', reviewing: '校对中', completed: '已完成', archived: '已归档' }[s] || s)

async function fetchBooks() {
  const params = { skip: (currentPage.value - 1) * pageSize.value, limit: pageSize.value }
  if (searchKeyword.value) params.keyword = searchKeyword.value
  if (filterStatus.value) params.status = filterStatus.value
  if (filterCategory.value) params.category = filterCategory.value
  const res = await bookApi.list(params)
  books.value = res.items
  total.value = res.total
}

async function handleCreate() {
  if (!createForm.value.title) { ElMessage.warning('请输入书名'); return }
  creating.value = true
  try {
    await bookApi.create(createForm.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    createForm.value = { title: '', author: '', dynasty: '', category: '', language: '简体中文', is_handwritten: false, description: '' }
    fetchBooks()
  } finally {
    creating.value = false
  }
}

async function handleDelete(book) {
  try {
    await bookApi.delete(book.id)
    ElMessage.success(`"${book.title}" 已删除`)
    fetchBooks()
  } catch {
    ElMessage.error('删除失败')
  }
}

function onCoverError(e) {
  e.target.style.display = 'none'
}

onMounted(async () => {
  await fetchBooks()
  categories.value = await bookApi.getCategories()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  color: #5D3A1A;
}

.book-card {
  cursor: pointer;
  margin-bottom: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
  position: relative;
}

.book-delete-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.book-card:hover .book-delete-btn {
  opacity: 1;
}

.book-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 20px rgba(139, 69, 19, 0.15);
}

.book-cover {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #FFF8F0 0%, #F5E6D3 100%);
  border-radius: 6px;
  margin-bottom: 12px;
  overflow: hidden;
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.book-title {
  font-size: 16px;
  color: #333;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.book-meta {
  font-size: 13px;
  color: #999;
  margin-bottom: 8px;
}

.book-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.book-progress {
  margin-top: 4px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
