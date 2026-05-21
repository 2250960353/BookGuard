<template>
  <div class="page-container">
    <h2 style="color: #5D3A1A; margin-bottom: 20px;">导出管理</h2>

    <el-card class="card-shadow">
      <template #header><span>导出图书</span></template>
      <el-form label-width="100px">
        <el-form-item label="选择图书">
          <el-select v-model="bookId" placeholder="请选择图书" filterable style="width: 100%;" @change="onBookChange">
            <el-option v-for="item in books" :key="item.id" :label="item.title + ' (' + (item.total_pages || 0) + '页)'" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="导出格式">
          <el-select v-model="format" placeholder="选择格式" style="width: 200px;">
            <el-option label="纯文本 (TXT)" value="txt" />
            <el-option label="结构化 (JSON)" value="json" />
            <el-option label="Markdown (MD)" value="md" />
            <el-option label="图文包 (ZIP)" value="zip" />
          </el-select>
        </el-form-item>
        <el-form-item label="包含图片">
          <el-switch v-model="includeImages" />
        </el-form-item>
        <el-form-item label="页码范围">
          <div style="display: flex; align-items: center; gap: 8px;">
            <el-input-number v-model="pageStart" :min="1" :max="maxPage" controls-position="right" style="width: 130px;" />
            <span>至</span>
            <el-input-number v-model="pageEnd" :min="1" :max="maxPage" controls-position="right" style="width: 130px;" />
            <el-button size="small" @click="selectAll">全选</el-button>
          </div>
          <div style="color: #999; font-size: 12px; margin-top: 4px;">
            第 {{ pageStart }} - 第 {{ pageEnd }} 页 / 共 {{ totalPage }} 页
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="doExport" :loading="exporting" :disabled="!bookId">开始导出</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="card-shadow" style="margin-top: 16px;">
      <template #header><span>格式说明</span></template>
      <ul style="padding-left: 18px; color: #666; line-height: 1.8;">
        <li><strong>TXT 纯文本</strong> — 包含书名、作者等元信息及每页OCR文本，适合阅读和引用</li>
        <li><strong>JSON 结构化</strong> — 包含完整元数据和分页OCR结果，适合程序处理和数据交换</li>
        <li><strong>MD Markdown</strong> — 格式化文档，保留标题层级和分页结构，适合在线展示</li>
        <li><strong>ZIP 图文包</strong> — 包含原图和对应OCR文本，适合长期归档保存</li>
      </ul>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { bookApi, exportApi } from '../api'
import { ElMessage } from 'element-plus'

const books = ref([])
const bookId = ref(null)
const format = ref('txt')
const includeImages = ref(false)
const exporting = ref(false)
const totalPage = ref(0)

const pageStart = ref(1)
const pageEnd = ref(1)
const maxPage = computed(() => Math.max(totalPage.value, 1))

function onBookChange(id) {
  const b = books.value.find(x => x.id === id)
  if (b) {
    totalPage.value = b.total_pages || 0
    pageStart.value = 1
    pageEnd.value = Math.max(b.total_pages || 1, 1)
  }
}

function selectAll() {
  pageStart.value = 1
  pageEnd.value = maxPage.value
}

async function doExport() {
  if (!bookId.value) {
    ElMessage.warning('请选择图书')
    return
  }
  exporting.value = true
  try {
    const res = await exportApi.exportBook({
      book_id: bookId.value,
      export_format: format.value,
      include_images: includeImages.value,
      page_range: [pageStart.value, pageEnd.value],
    })
    ElMessage.success('导出成功')
    const a = document.createElement('a')
    a.href = exportApi.downloadUrl(res.filename)
    a.download = res.filename
    a.click()
  } catch (e) {
    console.error(e)
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(async () => {
  try {
    const res = await bookApi.list({ limit: 100 })
    books.value = res.items || []
  } catch (e) {
    console.error(e)
  }
})
</script>
