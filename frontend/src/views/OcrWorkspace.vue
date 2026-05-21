<template>
  <div class="page-container">
    <h2 style="color: #5D3A1A; margin-bottom: 20px;">OCR 识别工作台</h2>

    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="card-shadow">
          <template #header><span>OCR 服务状态</span></template>
          <div class="ocr-status-panel">
            <el-icon :size="64" :color="ocrAvailable ? '#67C23A' : '#F56C6C'">
              <Monitor />
            </el-icon>
            <div class="ocr-status-info">
              <h3 :style="{ color: ocrAvailable ? '#67C23A' : '#F56C6C' }">
                {{ ocrAvailable ? 'UmiOCR 服务正常' : 'UmiOCR 服务未连接' }}
              </h3>
              <p>地址: {{ ocrUrl }}</p>
              <el-button type="primary" size="small" @click="checkStatus" style="margin-top: 8px;">
                <el-icon><Refresh /></el-icon> 重新检测
              </el-button>
            </div>
          </div>
        </el-card>

        <el-card class="card-shadow" style="margin-top: 16px;">
          <template #header><span>OCR 配置</span></template>
          <el-form label-width="80px" size="small">
            <el-form-item label="识别语言">
              <el-select v-model="ocrConfig.language">
                <el-option v-for="lang in ocrOptions.languages.length > 0 ? ocrOptions.languages : defaultLanguages" :key="lang.value || lang" :label="lang.label || lang" :value="lang.value || lang" />
              </el-select>
            </el-form-item>
            <el-form-item label="排版解析">
              <el-select v-model="ocrConfig.parser">
                <el-option v-for="p in ocrOptions.parsers.length > 0 ? ocrOptions.parsers : defaultParsers" :key="p.value || p" :label="p.label || p" :value="p.value || p" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card class="card-shadow">
          <template #header>
            <div class="card-header">
              <span>快速识别</span>
              <el-upload
                action=""
                :auto-upload="false"
                :on-change="handleFileChange"
                accept="image/*"
                :show-file-list="false"
              >
                <el-button type="primary" size="small"><el-icon><Upload /></el-icon> 选择图片</el-button>
              </el-upload>
            </div>
          </template>

          <div v-if="previewUrl" class="quick-ocr">
            <el-row :gutter="16">
              <el-col :span="12">
                <div class="preview-image">
                  <img :src="previewUrl" alt="预览" />
                </div>
              </el-col>
              <el-col :span="12">
                <div class="ocr-result">
                  <h4>识别结果</h4>
                  <div v-if="ocrLoading" style="text-align: center; padding: 40px;">
                    <el-icon :size="32" class="is-loading"><Loading /></el-icon>
                    <p>正在识别中...</p>
                  </div>
                  <div v-else-if="ocrResult" class="result-text">
                    <el-input v-model="ocrResult" type="textarea" :rows="12" />
                    <div style="margin-top: 8px;">
                      <el-button size="small" type="primary" @click="copyResult">复制文本</el-button>
                    </div>
                  </div>
                  <el-empty v-else description="选择图片后点击识别" :image-size="60" />
                </div>
              </el-col>
            </el-row>
          </div>
          <el-empty v-else description="请选择一张图片进行OCR识别" :image-size="80" />
        </el-card>

        <el-card class="card-shadow" style="margin-top: 16px;">
          <template #header><span>待处理图书</span></template>
          <el-table :data="pendingBooks" stripe>
            <el-table-column prop="title" label="书名" />
            <el-table-column prop="total_pages" label="页数" width="80" align="center" />
            <el-table-column label="操作" width="120" align="center" v-if="!isViewer">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="startBookOcr(row)">开始识别</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ocrApi, bookApi } from '../api'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const currentUser = computed(() => {
  try { return JSON.parse(localStorage.getItem('user') || '{}') } catch { return {} }
})
const isViewer = computed(() => currentUser.value.role === 'viewer')
const ocrAvailable = ref(false)
const ocrUrl = ref('')
const ocrConfig = ref({ language: '简体中文', parser: 'multi_para' })
const ocrOptions = ref({ languages: [], parsers: [] })

const defaultLanguages = [
  { label: '简体中文', value: '简体中文' },
  { label: '繁體中文', value: '繁體中文' },
  { label: '日本語', value: '日本語' },
  { label: 'English', value: 'English' },
]
const defaultParsers = [
  { label: '多栏-自然段换行', value: 'multi_para' },
  { label: '多栏-总是换行', value: 'multi_line' },
  { label: '单栏-自然段换行', value: 'single_para' },
  { label: '单栏-保留缩进', value: 'single_code' },
]
const previewUrl = ref('')
const ocrResult = ref('')
const ocrLoading = ref(false)
const pendingBooks = ref([])
let selectedFile = null

async function checkStatus() {
  try {
    const [statusRes, optsRes] = await Promise.all([
      ocrApi.getStatus(),
      ocrApi.getOptions(),
    ])
    ocrAvailable.value = statusRes.available
    ocrUrl.value = statusRes.url
    if (optsRes && optsRes.ocr) {
      if (optsRes.ocr.languages) ocrOptions.value.languages = optsRes.ocr.languages
      if (optsRes.ocr.parsers) ocrOptions.value.parsers = optsRes.ocr.parsers
    }
  } catch {
    ocrAvailable.value = false
  }
}

function handleFileChange(file) {
  selectedFile = file.raw
  previewUrl.value = URL.createObjectURL(file.raw)
  ocrResult.value = ''
  doOcr(file.raw)
}

async function doOcr(file) {
  if (!ocrAvailable.value) {
    ElMessage.warning('UmiOCR 服务未连接，请先启动 UmiOCR')
    return
  }
  ocrLoading.value = true
  try {
    const reader = new FileReader()
    reader.onload = async (e) => {
      const base64 = e.target.result.split(',')[1]
      const res = await axios.post('/api/ocr', {
        base64,
        options: {
          'ocr.language': ocrConfig.value.language,
          'tbpu.parser': ocrConfig.value.parser,
          'data.format': 'text',
        },
      })
      if (res.data.code === 100) {
        ocrResult.value = res.data.data
      } else {
        ElMessage.error('识别失败: ' + res.data.data)
      }
      ocrLoading.value = false
    }
    reader.readAsDataURL(file)
  } catch (e) {
    ElMessage.error('识别异常')
    ocrLoading.value = false
  }
}

function copyResult() {
  navigator.clipboard.writeText(ocrResult.value)
  ElMessage.success('已复制到剪贴板')
}

async function startBookOcr(book) {
  try {
    await bookApi.startOcr(book.id, { ocr_language: ocrConfig.value.language, tbpu_parser: ocrConfig.value.parser })
    ElMessage.success(`已启动 ${book.title} 的OCR识别`)
    fetchPendingBooks()
  } catch (e) {
    ElMessage.error('启动失败')
  }
}

async function fetchPendingBooks() {
  const res = await bookApi.list({ status: 'scanning', limit: 10 })
  pendingBooks.value = res.items
}

onMounted(async () => {
  await checkStatus()
  await fetchPendingBooks()
})
</script>

<style scoped>
.ocr-status-panel { display: flex; align-items: center; gap: 20px; }
.ocr-status-info h3 { margin: 0 0 4px; }
.ocr-status-info p { color: #999; font-size: 13px; margin: 0; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.preview-image { background: #F5F0E8; border-radius: 8px; padding: 12px; text-align: center; }
.preview-image img { max-width: 100%; max-height: 400px; border-radius: 4px; }
.ocr-result h4 { margin: 0 0 12px; color: #5D3A1A; }
.result-text { }
</style>
