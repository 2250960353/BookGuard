<template>
  <div class="page-container" v-loading="loading">
    <div class="page-header">
      <el-button text @click="$router.push('/books')"><el-icon><ArrowLeft /></el-icon> 返回列表</el-button>
    </div>

    <el-row :gutter="20" v-if="book">
      <el-col :span="16">
        <el-card class="card-shadow">
          <template #header>
            <div class="card-header">
              <h3>{{ book.title }}</h3>
              <div>
                <el-tag :type="statusType(book.status)">{{ statusLabel(book.status) }}</el-tag>
                <el-button type="primary" size="small" @click="showOcrDialog = true" style="margin-left: 8px;" v-if="hasUnprocessedPages && !isViewer">
                  <el-icon><Scan /></el-icon> 开始识别
                </el-button>
                <el-button type="success" size="small" @click="handleCompleteBook" style="margin-left: 8px;" v-if="book.status === 'reviewing' && !isViewer" :loading="completing">
                  <el-icon><CircleCheck /></el-icon> 全部校对完成
                </el-button>
                <el-button size="small" @click="showEditDialog = true" style="margin-left: 8px;" v-if="!isViewer">
                  <el-icon><EditPen /></el-icon> 编辑信息
                </el-button>
              </div>
            </div>
          </template>

          <el-descriptions :column="2" border>
            <el-descriptions-item label="作者">{{ book.author || '未知' }}</el-descriptions-item>
            <el-descriptions-item label="朝代">{{ book.dynasty || '未知' }}</el-descriptions-item>
            <el-descriptions-item label="分类">{{ book.category || '未分类' }}</el-descriptions-item>
            <el-descriptions-item label="语言">{{ book.language }}</el-descriptions-item>
            <el-descriptions-item label="手写体">
              <el-tag :type="book.is_handwritten ? 'warning' : 'info'" size="small">
                {{ book.is_handwritten ? '手写' : '印刷' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="总页数">{{ book.total_pages }}</el-descriptions-item>
            <el-descriptions-item label="已识别">{{ book.recognized_pages }} 页</el-descriptions-item>
            <el-descriptions-item label="平均置信度">
              {{ book.avg_confidence > 0 ? (book.avg_confidence * 100).toFixed(1) + '%' : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="描述" :span="2">{{ book.description || '无' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card class="card-shadow" style="margin-top: 16px;">
          <template #header>
            <div class="card-header">
              <span>页面列表
                <el-tag size="small" type="success" style="margin-left: 8px;" v-if="reviewedCount > 0">
                  已校对 {{ reviewedCount }}/{{ pages.length }}
                </el-tag>
              </span>
              <el-upload
                v-if="!isViewer"
                :action="`/api/books/${bookId}/pages`"
                name="file"
                multiple
                :show-file-list="false"
                :on-success="handleUploadSuccess"
                :on-error="handleUploadError"
                :on-progress="handleUploadProgress"
                accept="image/*"
              >
                <el-button type="primary" size="small" :loading="uploading">
                  <el-icon><Upload /></el-icon> {{ uploading ? '导入中...' : '导入图片' }}
                </el-button>
              </el-upload>
            </div>
          </template>

          <div class="pages-grid" v-if="pages.length > 0">
            <div
              v-for="page in pages"
              :key="page.id"
              class="page-item"
              :class="{ active: selectedPage?.id === page.id, reviewed: page.is_reviewed }"
              @click="selectPage(page)"
            >
              <el-popconfirm v-if="!isViewer" title="确定删除此页面？" confirm-button-text="确定" cancel-button-text="取消" @confirm="handleDeletePage(page)" @click.stop>
                <template #reference>
                  <div class="page-delete-btn"><el-icon><Close /></el-icon></div>
                </template>
              </el-popconfirm>
              <div class="page-thumb" @click.stop="showImagePreview(page)">
                <img v-if="page.image_path" :src="bookApi.getPageThumbnail(bookId, page.id)" alt="" @error="onImgError" />
                <el-icon v-else :size="32" :color="page.is_reviewed ? '#67C23A' : '#8B4513'"><Document /></el-icon>
              </div>
              <div class="page-info">
                <span class="page-num">第 {{ page.page_number }} 页</span>
                <div class="page-tags">
                  <el-tag :type="pageStatusType(page.status)" size="small">{{ pageStatusLabel(page.status) }}</el-tag>
                  <el-tag :type="page.is_reviewed ? 'success' : 'info'" size="small" effect="plain" @click.stop="!isViewer && toggleReview(page)" :style="!isViewer ? 'cursor:pointer' : ''">
                    {{ page.is_reviewed ? '已校对' : '未校对' }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无页面，请导入图片" />
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="card-shadow" v-if="selectedPage">
          <template #header>
            <div class="card-header">
              <span>第 {{ selectedPage.page_number }} 页 - OCR结果</span>
              <el-tag :type="selectedPage.confidence > 0.8 ? 'success' : selectedPage.confidence > 0.5 ? 'warning' : 'danger'" size="small">
                置信度: {{ (selectedPage.confidence * 100).toFixed(1) }}%
              </el-tag>
            </div>
          </template>
          <div class="page-image-preview" v-if="selectedPage.image_path">
            <img :src="bookApi.getPageImage(bookId, selectedPage.id)" alt="页面原图" @error="onPreviewImgError" />
          </div>
          <el-input
            v-model="editableText"
            type="textarea"
            :rows="12"
            placeholder="OCR识别文本将显示在这里，可手动编辑校正"
            :disabled="isViewer"
          />
          <div style="margin-top: 12px; text-align: right;" v-if="!isViewer">
            <el-button size="small" :type="selectedPage?.is_reviewed ? 'success' : 'info'" @click="toggleReview(selectedPage)" plain>
              <el-icon><CircleCheck /></el-icon> {{ selectedPage?.is_reviewed ? '已校对' : '标记校对' }}
            </el-button>
            <el-button type="primary" size="small" @click="savePageText" :loading="saving">保存修改</el-button>
          </div>
        </el-card>
        <el-empty v-else description="请选择页面查看OCR结果" />

        <el-card class="card-shadow" style="margin-top: 16px;">
          <template #header><span>OCR任务</span></template>
          <div v-if="tasks.length > 0">
            <div v-for="task in tasks" :key="task.id" class="task-item">
              <div class="task-info">
                <span>{{ task.ocr_language }} - {{ task.ocr_engine }}</span>
                <el-tag :type="taskStatusType(task.status)" size="small">{{ taskStatusLabel(task.status) }}</el-tag>
              </div>
              <el-progress v-if="task.status === 'running'" :percentage="Math.round(task.progress * 100)" :stroke-width="8" />
            </div>
          </div>
          <el-empty v-else description="暂无任务" :image-size="40" />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showOcrDialog" title="启动OCR识别" width="450px">
      <el-form label-width="100px">
        <el-form-item label="识别语言">
          <el-select v-model="ocrForm.language">
            <el-option label="简体中文" value="简体中文" />
            <el-option label="繁體中文" value="繁體中文" />
            <el-option label="日本語" value="日本語" />
            <el-option label="English" value="English" />
          </el-select>
        </el-form-item>
        <el-form-item label="排版解析">
          <el-select v-model="ocrForm.parser">
            <el-option label="多栏-按自然段换行" value="multi_para" />
            <el-option label="多栏-总是换行" value="multi_line" />
            <el-option label="单栏-按自然段换行" value="single_para" />
            <el-option label="单栏-总是换行" value="single_line" />
            <el-option label="单栏-保留缩进" value="single_code" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showOcrDialog = false">取消</el-button>
        <el-button type="primary" @click="startOcr" :loading="startingOcr">开始识别</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showEditDialog" title="编辑图书信息" width="550px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="书名"><el-input v-model="editForm.title" /></el-form-item>
        <el-form-item label="作者"><el-input v-model="editForm.author" /></el-form-item>
        <el-form-item label="朝代"><el-input v-model="editForm.dynasty" /></el-form-item>
        <el-form-item label="分类"><el-input v-model="editForm.category" /></el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="语言">
              <el-select v-model="editForm.language">
                <el-option label="简体中文" value="简体中文" />
                <el-option label="繁體中文" value="繁體中文" />
                <el-option label="English" value="English" />
                <el-option label="日本語" value="日本語" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手写体">
              <el-switch v-model="editForm.is_handwritten" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="描述"><el-input v-model="editForm.description" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveBookInfo" :loading="savingBook">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showImageDialog" :title="'第 ' + previewPage?.page_number + ' 页'" width="700px">
      <div class="image-preview-full">
        <img :src="previewUrl" alt="页面原图" v-if="previewUrl" />
        <el-empty v-else description="图片加载失败" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { bookApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const bookId = computed(() => route.params.id)
const currentUser = computed(() => {
  try { return JSON.parse(localStorage.getItem('user') || '{}') } catch { return {} }
})
const isViewer = computed(() => currentUser.value.role === 'viewer')
const book = ref(null)
const pages = ref([])
const selectedPage = ref(null)
const editableText = ref('')
const tasks = ref([])
const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const showOcrDialog = ref(false)
const startingOcr = ref(false)
const completing = ref(false)
const showEditDialog = ref(false)
const savingBook = ref(false)
const showImageDialog = ref(false)
const previewPage = ref(null)
const previewUrl = ref('')

const ocrForm = ref({ language: '简体中文', parser: 'multi_para' })
const editForm = ref({})

const reviewedCount = computed(() => pages.value.filter(p => p.is_reviewed).length)

const hasUnprocessedPages = computed(() => {
  if (!book.value || pages.value.length === 0) return false
  return book.value.total_pages > book.value.recognized_pages ||
    pages.value.some(p => p.status === 'pending' || p.status === 'failed')
})

const statusType = (s) => ({ pending: 'info', scanning: 'warning', recognizing: '', reviewing: 'success', completed: 'success', archived: 'info' }[s] || 'info')
const statusLabel = (s) => ({ pending: '待处理', scanning: '扫描中', recognizing: '识别中', reviewing: '校对中', completed: '已完成', archived: '已归档' }[s] || s)
const pageStatusType = (s) => ({ pending: 'info', processing: 'warning', completed: 'success', failed: 'danger' }[s] || 'info')
const pageStatusLabel = (s) => ({ pending: '待处理', processing: '识别中', completed: '已完成', failed: '失败' }[s] || s)
const taskStatusType = (s) => ({ pending: 'info', running: 'warning', completed: 'success', failed: 'danger' }[s] || 'info')
const taskStatusLabel = (s) => ({ pending: '等待中', running: '运行中', completed: '已完成', failed: '失败' }[s] || s)

async function fetchData() {
  loading.value = true
  try {
    const [b, p, t] = await Promise.all([
      bookApi.get(bookId.value),
      bookApi.getPages(bookId.value, { limit: 200 }),
      bookApi.getTasks(bookId.value),
    ])
    book.value = b
    pages.value = p.items
    tasks.value = t
  } finally {
    loading.value = false
  }
}

function selectPage(page) {
  selectedPage.value = page
  editableText.value = page.ocr_text || ''
}

function onImgError(e) {
  e.target.style.display = 'none'
}

function onPreviewImgError(e) {
  e.target.alt = '图片加载失败'
}

function showImagePreview(page) {
  previewPage.value = page
  previewUrl.value = page.image_path ? bookApi.getPageImage(bookId.value, page.id) : ''
  showImageDialog.value = true
}

async function savePageText() {
  saving.value = true
  try {
    await bookApi.updatePageText(bookId.value, selectedPage.value.id, { ocr_text: editableText.value })
    ElMessage.success('保存成功')
    selectedPage.value.ocr_text = editableText.value
  } finally {
    saving.value = false
  }
}

async function saveBookInfo() {
  savingBook.value = true
  try {
    await bookApi.update(bookId.value, editForm.value)
    ElMessage.success('图书信息已更新')
    showEditDialog.value = false
    fetchData()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    savingBook.value = false
  }
}

async function toggleReview(page) {
  try {
    const res = await bookApi.togglePageReview(bookId.value, page.id)
    page.is_reviewed = res.reviewed
    if (selectedPage.value?.id === page.id) {
      selectedPage.value.is_reviewed = res.reviewed
    }
    if (res.reviewed) {
      ElMessage.success('已标记为校对完成')
    } else {
      ElMessage.warning('已取消校对标记')
      if (res.book_reverted) {
        ElMessage.info('图书状态已回退为"校对中"')
        fetchData()
      }
    }
  } catch {
    ElMessage.error('操作失败')
  }
}

async function handleDeletePage(page) {
  try {
    await bookApi.deletePage(bookId.value, page.id)
    if (selectedPage.value?.id === page.id) {
      selectedPage.value = null
      editableText.value = ''
    }
    pages.value = pages.value.filter(p => p.id !== page.id)
    ElMessage.success(`第 ${page.page_number} 页已删除`)
    fetchData()
  } catch {
    ElMessage.error('删除失败')
  }
}

async function handleCompleteBook() {
  const total = pages.value.length
  const reviewed = reviewedCount.value
  const unreviewed = total - reviewed

  if (unreviewed > 0) {
    try {
      await ElMessageBox.confirm(
        `还有 ${unreviewed} 页未校对，是否仍标记为已完成？`,
        '校对未完成',
        { confirmButtonText: '继续', cancelButtonText: '取消', type: 'warning' }
      )
      const markAll = await ElMessageBox.confirm(
        '是否将所有页面标记为已校对？',
        '批量标记',
        { confirmButtonText: '全部标记', cancelButtonText: '仅完成图书', type: 'info' }
      ).then(() => true).catch(() => false)
      if (markAll) {
        for (const page of pages.value) {
          if (!page.is_reviewed) {
            page.is_reviewed = true
            await bookApi.togglePageReview(bookId.value, page.id)
          }
        }
      }
    } catch (e) {
      if (e === 'cancel') return
    }
  } else {
    try {
      await ElMessageBox.confirm(
        '确认所有页面都已校对完毕？完成后图书状态将变为"已完成"',
        '确认完成',
        { confirmButtonText: '确认', cancelButtonText: '取消', type: 'info' }
      )
    } catch {
      return
    }
  }

  completing.value = true
  try {
    await bookApi.completeBook(bookId.value)
    ElMessage.success('图书已标记为完成')
    fetchData()
  } catch {
    ElMessage.error('操作失败')
  } finally {
    completing.value = false
  }
}

async function startOcr() {
  startingOcr.value = true
  try {
    await bookApi.startOcr(bookId.value, { ocr_language: ocrForm.value.language, tbpu_parser: ocrForm.value.parser })
    ElMessage.success('OCR任务已启动')
    showOcrDialog.value = false
    await fetchData()
    startPolling()
  } finally {
    startingOcr.value = false
  }
}

function handleUploadSuccess(response) {
  uploading.value = false
  if (response.imported > 0) {
    ElMessage.success('图片导入成功')
    fetchData()
  } else {
    ElMessage.warning('图片导入失败，请检查文件格式')
  }
}

function handleUploadError(error) {
  uploading.value = false
  ElMessage.error('图片导入失败')
}

function handleUploadProgress() {
  uploading.value = true
}

watch(showEditDialog, (val) => {
  if (val && book.value) {
    editForm.value = {
      title: book.value.title,
      author: book.value.author,
      dynasty: book.value.dynasty,
      category: book.value.category,
      language: book.value.language,
      is_handwritten: book.value.is_handwritten,
      description: book.value.description,
    }
  }
})

onMounted(fetchData)

let pollTimer = null

function startPolling() {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const [b, p, t] = await Promise.all([
        bookApi.get(bookId.value),
        bookApi.getPages(bookId.value, { limit: 200 }),
        bookApi.getTasks(bookId.value),
      ])
      book.value = b
      pages.value = p.items
      tasks.value = t
      if (selectedPage.value) {
        const updated = p.items.find(pg => pg.id === selectedPage.value.id)
        if (updated) {
          selectedPage.value = updated
          if (!document.activeElement || document.activeElement.tagName !== 'TEXTAREA') {
            editableText.value = updated.ocr_text || ''
          }
        }
      }
      const hasRunning = t.some(task => task.status === 'running' || task.status === 'pending')
      if (!hasRunning) {
        stopPolling()
      }
    } catch {
      stopPolling()
    }
  }, 1000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

watch(tasks, (val) => {
  const hasRunning = val.some(t => t.status === 'running' || t.status === 'pending')
  if (hasRunning && !pollTimer) {
    startPolling()
  }
}, { deep: true })

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.page-header { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-header h3 { margin: 0; color: #5D3A1A; }

.pages-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 12px;
}

.page-item {
  cursor: pointer;
  padding: 12px;
  border: 2px solid transparent;
  border-radius: 8px;
  background: #FFF8F0;
  text-align: center;
  transition: all 0.2s;
  position: relative;
}

.page-delete-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #F56C6C;
  color: white;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.2s;
  cursor: pointer;
}

.page-item:hover .page-delete-btn {
  opacity: 1;
}

.page-item:hover { border-color: #D2691E; }
.page-item.active { border-color: #8B4513; background: #F5E6D3; }
.page-item.reviewed { background: #F0F9EB; border-color: #E1F3D8; }
.page-item.reviewed.active { border-color: #67C23A; background: #E1F3D8; }

.page-thumb {
  height: 90px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F5F0E8;
  border-radius: 4px;
  margin-bottom: 8px;
  overflow: hidden;
  cursor: zoom-in;
}
.page-thumb img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 2px;
}

.page-image-preview {
  text-align: center;
  margin-bottom: 12px;
  background: #FAFAFA;
  border-radius: 6px;
  padding: 6px;
}
.page-image-preview img {
  max-height: 180px;
  max-width: 100%;
  border-radius: 4px;
  object-fit: contain;
}

.image-preview-full {
  text-align: center;
}
.image-preview-full img {
  max-width: 100%;
  max-height: 600px;
  object-fit: contain;
  border-radius: 4px;
}

.page-info { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.page-num { font-size: 13px; color: #666; }
.page-tags { display: flex; gap: 4px; flex-wrap: wrap; justify-content: center; }

.task-item { margin-bottom: 12px; padding: 8px; background: #FFF8F0; border-radius: 6px; }
.task-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 13px; }
</style>
