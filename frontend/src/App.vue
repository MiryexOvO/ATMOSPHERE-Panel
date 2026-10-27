<script setup lang="ts">
import { onMounted, ref } from 'vue'

const loggedIn = ref(false)
const username = ref('admin')
const password = ref('')
const error = ref('')
const loading = ref(false)
const showPassword = ref(false)

async function checkSession() {
  const response = await fetch('/api/me', { credentials: 'include' })
  loggedIn.value = response.ok
}
async function login() {
  error.value = ''
  loading.value = true
  const response = await fetch('/api/login', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: username.value, password: password.value }) })
  const data = await response.json()
  loading.value = false
  if (!response.ok) { error.value = data.message || '登录失败'; return }
  loggedIn.value = true
  password.value = ''
}
async function logout() {
  await fetch('/api/logout', { method: 'POST', credentials: 'include' })
  loggedIn.value = false
}
onMounted(checkSession)
</script>

<template>
  <main class="shell">
    <div class="grain"></div>
    <header class="topbar">
      <div class="brand"><span class="brand-mark">▰</span><span>MC PANEL</span><small>SERVER OPERATIONS / 01</small></div>
      <div class="top-meta"><span>LOCAL INSTANCE</span><i></i><span>PORT 27777</span><i></i><span>SECURE CHANNEL</span></div>
    </header>

    <section v-if="!loggedIn" class="login-layout">
      <div class="intro">
        <div class="eyebrow">/ AUTHENTICATION REQUIRED</div>
        <h1>Control<br><em>the server.</em></h1>
        <p>一个克制、可靠的 Minecraft 服务端控制台。<br>请使用管理员凭据继续。</p>
        <div class="coordinates">[ 01.24.2026 / PANEL ONLINE ]</div>
      </div>
      <form class="auth-card" @submit.prevent="login">
        <div class="card-line"><span>ACCESS / LOGIN</span><span>01</span></div>
        <div class="field-label">管理员账号</div>
        <input v-model="username" autocomplete="username" placeholder="admin" />
        <div class="field-label">访问密码</div>
        <div class="password-wrap"><input v-model="password" :type="showPassword ? 'text' : 'password'" autocomplete="current-password" placeholder="••••••••••••" /><button type="button" @click="showPassword = !showPassword">{{ showPassword ? '隐藏' : '显示' }}</button></div>
        <div v-if="error" class="error">! {{ error }}</div>
        <button class="primary" :disabled="loading">{{ loading ? '验证中…' : '进入控制台' }} <span>→</span></button>
        <div class="hint">SESSION / HTTPONLY · SAME-SITE LAX<br>默认会话有效期 24 小时</div>
      </form>
    </section>

    <section v-else class="dashboard">
      <div class="dash-head"><div><div class="eyebrow">/ DASHBOARD / AUTHORIZED</div><h2>Good evening, <em>admin.</em></h2></div><button class="ghost" @click="logout">登出 →</button></div>
      <div class="status-grid"><article><span>INSTANCE STATUS</span><strong><b></b> READY</strong><small>等待部署首个实例</small></article><article><span>ACTIVE SERVERS</span><strong>00</strong><small>阶段 2 将在此显示实例</small></article><article><span>SESSION</span><strong>24<span class="unit">H</span></strong><small>安全会话已建立</small></article></div>
      <div class="empty"><div class="empty-code">[ 00 / 00 ]</div><h3>NO SERVER INSTANCES</h3><p>登录系统骨架已就绪。下一阶段将接入 JAR 上传与一键部署。</p><div class="progress"><i></i></div></div>
    </section>
    <footer><span>MC PANEL / BUILD 0.1.0</span><span>AUTH SERVICE ONLINE · <b>●</b></span></footer>
  </main>
</template>
