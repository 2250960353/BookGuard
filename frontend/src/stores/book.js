import { defineStore } from 'pinia'
import { ref } from 'vue'
import { bookApi, ocrApi } from '../api'

export const useBookStore = defineStore('book', () => {
  const books = ref([])
  const currentBook = ref(null)
  const total = ref(0)
  const stats = ref(null)
  const ocrStatus = ref({ available: false })
  const loading = ref(false)

  async function fetchBooks(params = {}) {
    loading.value = true
    try {
      const res = await bookApi.list(params)
      books.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  async function fetchBook(id) {
    loading.value = true
    try {
      currentBook.value = await bookApi.get(id)
    } finally {
      loading.value = false
    }
  }

  async function createBook(data) {
    const book = await bookApi.create(data)
    return book
  }

  async function updateBook(id, data) {
    const book = await bookApi.update(id, data)
    return book
  }

  async function deleteBook(id) {
    await bookApi.delete(id)
  }

  async function fetchStats() {
    stats.value = await bookApi.getStats()
  }

  async function checkOcrStatus() {
    ocrStatus.value = await ocrApi.getStatus()
  }

  return {
    books, currentBook, total, stats, ocrStatus, loading,
    fetchBooks, fetchBook, createBook, updateBook, deleteBook, fetchStats, checkOcrStatus,
  }
})
