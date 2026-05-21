<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup>
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
</script>

<style>
:root {
  --primary-color: #8B4513;
  --secondary-color: #D2691E;
  --bg-color: #F5F0E8;
  --card-bg: #FFFDF7;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
  background-color: var(--bg-color);
  color: #333;
}

.el-menu--horizontal {
  border-bottom: none !important;
}

.page-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.card-shadow {
  box-shadow: 0 2px 12px rgba(139, 69, 19, 0.08);
  border-radius: 8px;
}

.stat-card {
  text-align: center;
  padding: 20px;
  border-radius: 8px;
  background: var(--card-bg);
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: var(--primary-color);
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 8px;
}
</style>
