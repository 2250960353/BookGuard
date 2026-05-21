<template>
  <div class="page-container">
    <h2 style="color: #5D3A1A; margin-bottom: 20px;">全文检索</h2>

    <el-card class="card-shadow">
      <el-row :gutter="16" align="middle">
        <el-col :span="10">
          <el-input v-model="keyword" placeholder="输入关键词搜索图书内容..." size="large" clearable @keyup.enter="doSearch">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterCategory" placeholder="分类筛选" clearable size="large" filterable allow-create>
            <el-option v-for="cat in categories" :key="cat.category" :label="cat.category || '未分类'" :value="cat.category" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" size="large" @click="doSearch" :loading="searching" style="width: 100%;">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <div v-if="results.length > 0" style="margin-top: 20px;">
      <p style="color: #999; margin-bottom: 16px;">找到 {{ results.length }} 条结果</p>
      <el-card v-for="item in results" :key="item.page_id" class="result-card card-shadow" @click="goToBook(item.book_id)">
        <div class="result-item">
          <div class="result-meta">
            <span class="result-book">{{ item.book_title }}</span>
            <el-tag size="small">第 {{ item.page_number }} 页</el-tag>
            <el-tag type="success" size="small" v-if="item.confidence > 0">置信度: {{ (item.confidence * 100).toFixed(1) }}%</el-tag>
          </div>
          <div class="result-highlight" v-html="item.highlight"></div>
        </div>
      </el-card>
    </div>

    <el-empty v-else-if="searched" description="未找到相关内容" />
    <el-empty v-else description="输入关键词开始搜索" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ocrApi, bookApi } from '../api'

const router = useRouter()
const keyword = ref('')
const filterCategory = ref('')
const categories = ref([])
const results = ref([])
const searching = ref(false)
const searched = ref(false)

async function doSearch() {
  if (!keyword.value.trim()) return
  searching.value = true
  searched.value = true
  try {
    results.value = await ocrApi.search({
      keyword: keyword.value,
      category: filterCategory.value || undefined,
    })
  } finally {
    searching.value = false
  }
}

function goToBook(bookId) {
  router.push(`/books/${bookId}`)
}

onMounted(async () => {
  categories.value = await bookApi.getCategories()
})
</script>

<style scoped>
.result-card { margin-bottom: 12px; cursor: pointer; transition: transform 0.2s; }
.result-card:hover { transform: translateX(4px); }
.result-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.result-book { font-weight: bold; color: #5D3A1A; }
.result-highlight { color: #666; font-size: 14px; line-height: 1.6; }
</style>
