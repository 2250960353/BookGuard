<template>
  <div class="login-page">
    <div class="login-bg"></div>
    <div class="login-card">
      <div class="login-header">
        <el-icon :size="40" color="#8B4513"><Reading /></el-icon>
        <h1>BookGuard</h1>
        <p>珍贵图书数字化保护系统</p>
      </div>
      <el-form :model="form" @keyup.enter="handleLogin" class="login-form">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" size="large" prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" size="large" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" @click="handleLogin" :loading="loading" style="width: 100%;">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        <span>默认管理员: admin / admin123</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '../api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const form = ref({ username: '', password: '' })

async function handleLogin() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await authApi.login(form.value)
    localStorage.setItem('token', res.token)
    localStorage.setItem('user', JSON.stringify(res.user))
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (e) {
    const msg = e.response?.data?.detail || '登录失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: #F5F0E8;
}

.login-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #5D3A1A 0%, #8B4513 40%, #D2691E 100%);
  opacity: 0.08;
}

.login-card {
  width: 400px;
  background: white;
  border-radius: 16px;
  padding: 40px 36px;
  box-shadow: 0 8px 40px rgba(93, 58, 26, 0.15);
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  margin: 12px 0 4px;
  font-size: 28px;
  color: #5D3A1A;
  letter-spacing: 2px;
}

.login-header p {
  color: #999;
  font-size: 14px;
  margin: 0;
}

.login-form {
  margin-top: 8px;
}

.login-footer {
  text-align: center;
  margin-top: 16px;
  color: #bbb;
  font-size: 12px;
}
</style>
