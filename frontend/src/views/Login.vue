<template>
  <div class="login-page">
    <!-- 动态背景 -->
    <div class="bg-effects">
      <div class="grid-pattern"></div>
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
      <div class="glow-orb orb-3"></div>
    </div>

    <!-- 主内容区 -->
    <div class="login-content">
      <!-- 品牌区域 -->
      <div class="brand-section">
        <div class="logo">
          <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M24 4L6 14V34L24 44L42 34V14L24 4Z" stroke="currentColor" stroke-width="2" fill="none"/>
            <path d="M24 4V24M24 24L6 14M24 24L42 14" stroke="currentColor" stroke-width="2"/>
            <circle cx="24" cy="24" r="4" fill="currentColor"/>
          </svg>
        </div>
        <h1 class="brand-title">DragonAI</h1>
        <p class="brand-subtitle">智能助手，重新定义工作效率</p>
      </div>

      <!-- 登录卡片 -->
      <div class="login-card-wrapper">
        <div class="login-card">
          <div class="card-header">
            <h2>欢迎回来</h2>
            <p>登录您的账户以继续</p>
          </div>

          <form @submit.prevent="handleLogin" class="login-form">
            <div class="form-group">
              <label for="username">用户名</label>
              <div class="input-wrapper">
                <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
                <input
                  id="username"
                  v-model="loginForm.username"
                  type="text"
                  placeholder="请输入用户名"
                  required
                  @focus="activeField = 'username'"
                  @blur="activeField = ''"
                />
              </div>
            </div>

            <div class="form-group">
              <label for="password">
                密码
                <a href="#" class="forgot-link">忘记密码？</a>
              </label>
              <div class="input-wrapper">
                <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
                <input
                  id="password"
                  v-model="loginForm.password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="请输入密码"
                  required
                  @focus="activeField = 'password'"
                  @blur="activeField = ''"
                />
                <button
                  type="button"
                  class="toggle-password"
                  @click="showPassword = !showPassword"
                >
                  <svg v-if="showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                  </svg>
                </button>
              </div>
            </div>

            <button
              type="submit"
              class="submit-btn"
              :class="{ loading: authStore.loading }"
              :disabled="authStore.loading"
            >
              <span class="btn-text">{{ authStore.loading ? '登录中...' : '登录' }}</span>
              <span class="btn-shine"></span>
            </button>
          </form>

          <div class="card-footer">
            <p>还没有账号？<router-link to="/register" class="register-link">立即注册</router-link></p>
          </div>
        </div>
      </div>
    </div>

    <!-- 装饰性元素 -->
    <div class="decoration-lines">
      <div class="line line-1"></div>
      <div class="line line-2"></div>
      <div class="line line-3"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const activeField = ref('')
const showPassword = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请填写完整的登录信息')
    return
  }

  try {
    await authStore.login(loginForm)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    ElMessage.error('登录失败，请检查用户名和密码')
  }
}
</script>

<style scoped>
/* 页面基础 */
.login-page {
  min-height: 100vh;
  background: var(--bg-secondary, #f7f8fa);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 深色主题支持 */
.login-page[data-theme="dark"] {
  background: #0a0a0f;
}

/* 背景效果 */
.bg-effects {
  position: fixed;
  inset: 0;
  pointer-events: none;
}

.grid-pattern {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(45, 125, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(45, 125, 255, 0.05) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(ellipse at center, black 40%, transparent 80%);
}

/* 深色主题下的网格 */
.login-page[data-theme="dark"] .grid-pattern {
  background-image:
    linear-gradient(rgba(6, 182, 212, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(6, 182, 212, 0.03) 1px, transparent 1px);
}

.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 400px;
  height: 400px;
  background: #2d7dff;
  top: -100px;
  right: -100px;
  animation-delay: 0s;
  opacity: 0.15;
}

.orb-2 {
  width: 300px;
  height: 300px;
  background: #5a9cff;
  bottom: -50px;
  left: -50px;
  animation-delay: -7s;
  opacity: 0.12;
}

.orb-3 {
  width: 250px;
  height: 250px;
  background: #16c784;
  top: 50%;
  left: 30%;
  animation-delay: -14s;
  opacity: 0.1;
}

/* 深色主题下的光球 */
.login-page[data-theme="dark"] .orb-1 {
  background: #06b6d4;
  opacity: 0.4;
}

.login-page[data-theme="dark"] .orb-2 {
  background: #8b5cf6;
  opacity: 0.4;
}

.login-page[data-theme="dark"] .orb-3 {
  background: #f97316;
  opacity: 0.2;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(30px, -30px) scale(1.1); }
  50% { transform: translate(-20px, 20px) scale(0.9); }
  75% { transform: translate(20px, 10px) scale(1.05); }
}

/* 主内容 */
.login-content {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
  padding: 40px 20px;
  width: 100%;
  max-width: 420px;
  animation: fadeInUp 0.8s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 品牌区域 */
.brand-section {
  text-align: center;
}

.logo {
  width: 64px;
  height: 64px;
  margin: 0 auto 20px;
  color: var(--primary-color, #2d7dff);
  animation: pulse 3s ease-in-out infinite;
}

.logo svg {
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 0 20px rgba(45, 125, 255, 0.3));
}

/* 深色主题下的Logo */
.login-page[data-theme="dark"] .logo {
  color: #06b6d4;
}

.login-page[data-theme="dark"] .logo svg {
  filter: drop-shadow(0 0 20px rgba(6, 182, 212, 0.5));
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.brand-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary, #1f2329);
  margin: 0 0 8px;
  letter-spacing: -0.5px;
  background: linear-gradient(135deg, var(--text-primary, #1f2329) 0%, var(--primary-color, #2d7dff) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-subtitle {
  font-size: 14px;
  color: var(--text-secondary, #646a73);
  margin: 0;
}

/* 深色主题下的品牌文字 */
.login-page[data-theme="dark"] .brand-title {
  color: #fff;
  background: linear-gradient(135deg, #fff 0%, #06b6d4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-page[data-theme="dark"] .brand-subtitle {
  color: rgba(255, 255, 255, 0.5);
}

/* 登录卡片 */
.login-card-wrapper {
  width: 100%;
}

.login-card {
  background: var(--bg-primary, #ffffff);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-color, #e8e8e8);
  border-radius: 24px;
  padding: 40px;
  box-shadow:
    0 0 0 1px rgba(45, 125, 255, 0.08),
    0 20px 60px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

/* 深色主题下的卡片 */
.login-page[data-theme="dark"] .login-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow:
    0 0 0 1px rgba(6, 182, 212, 0.1),
    0 20px 60px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.card-header {
  text-align: center;
  margin-bottom: 32px;
}

.card-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary, #1f2329);
  margin: 0 0 8px;
}

.card-header p {
  font-size: 14px;
  color: var(--text-secondary, #646a73);
  margin: 0;
}

/* 深色主题下的卡片头部 */
.login-page[data-theme="dark"] .card-header h2 {
  color: #fff;
}

.login-page[data-theme="dark"] .card-header p {
  color: rgba(255, 255, 255, 0.4);
}

/* 表单样式 */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary, #646a73);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.forgot-link {
  font-size: 12px;
  color: var(--primary-color, #2d7dff);
  text-decoration: none;
  transition: color 0.2s;
}

.forgot-link:hover {
  color: var(--primary-light, #5a9cff);
}

/* 深色主题下的表单标签 */
.login-page[data-theme="dark"] .form-group label {
  color: rgba(255, 255, 255, 0.7);
}

.login-page[data-theme="dark"] .forgot-link {
  color: #06b6d4;
}

.login-page[data-theme="dark"] .forgot-link:hover {
  color: #22d3ee;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 16px;
  width: 18px;
  height: 18px;
  color: var(--text-tertiary, #8f959e);
  transition: color 0.2s;
  pointer-events: none;
}

.input-wrapper:focus-within .input-icon {
  color: var(--primary-color, #2d7dff);
}

.input-wrapper input {
  width: 100%;
  height: 48px;
  padding: 0 44px;
  background: var(--bg-secondary, #f7f8fa);
  border: 1px solid var(--border-color, #e8e8e8);
  border-radius: 12px;
  font-size: 14px;
  color: var(--text-primary, #1f2329);
  transition: all 0.2s;
  outline: none;
}

.input-wrapper input::placeholder {
  color: var(--text-tertiary, #8f959e);
}

.input-wrapper input:focus {
  background: var(--bg-primary, #ffffff);
  border-color: var(--primary-color, #2d7dff);
  box-shadow: 0 0 0 3px rgba(45, 125, 255, 0.1);
}

/* 深色主题下的输入框 */
.login-page[data-theme="dark"] .input-icon {
  color: rgba(255, 255, 255, 0.3);
}

.login-page[data-theme="dark"] .input-wrapper:focus-within .input-icon {
  color: #06b6d4;
}

.login-page[data-theme="dark"] .input-wrapper input {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
}

.login-page[data-theme="dark"] .input-wrapper input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.login-page[data-theme="dark"] .input-wrapper input:focus {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(6, 182, 212, 0.5);
  box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1);
}

.toggle-password {
  position: absolute;
  right: 16px;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  color: var(--text-tertiary, #8f959e);
  transition: color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toggle-password:hover {
  color: var(--text-secondary, #646a73);
}

/* 深色主题下的密码切换按钮 */
.login-page[data-theme="dark"] .toggle-password {
  color: rgba(255, 255, 255, 0.3);
}

.login-page[data-theme="dark"] .toggle-password:hover {
  color: rgba(255, 255, 255, 0.6);
}

.toggle-password svg {
  width: 18px;
  height: 18px;
}

/* 提交按钮 */
.submit-btn {
  position: relative;
  height: 48px;
  margin-top: 8px;
  background: linear-gradient(135deg, var(--primary-color, #2d7dff) 0%, var(--primary-dark, #1a5fcc) 100%);
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s;
  box-shadow:
    0 4px 20px rgba(45, 125, 255, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow:
    0 8px 30px rgba(45, 125, 255, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

/* 深色主题下的提交按钮 */
.login-page[data-theme="dark"] .submit-btn {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  box-shadow:
    0 4px 20px rgba(6, 182, 212, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.login-page[data-theme="dark"] .submit-btn:hover:not(:disabled) {
  box-shadow:
    0 8px 30px rgba(6, 182, 212, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-shine {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent
  );
  transition: left 0.5s;
}

.submit-btn:hover:not(:disabled) .btn-shine {
  left: 100%;
}

/* 卡片底部 */
.card-footer {
  margin-top: 24px;
  text-align: center;
}

.card-footer p {
  font-size: 14px;
  color: var(--text-secondary, #646a73);
  margin: 0;
}

.register-link {
  color: var(--primary-color, #2d7dff);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.register-link:hover {
  color: var(--primary-light, #5a9cff);
}

/* 深色主题下的卡片底部 */
.login-page[data-theme="dark"] .card-footer p {
  color: rgba(255, 255, 255, 0.4);
}

.login-page[data-theme="dark"] .register-link {
  color: #06b6d4;
}

.login-page[data-theme="dark"] .register-link:hover {
  color: #22d3ee;
}

/* 装饰线条 */
.decoration-lines {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.line {
  position: absolute;
  background: linear-gradient(90deg, transparent, rgba(45, 125, 255, 0.1), transparent);
  height: 1px;
}

/* 深色主题下的装饰线条 */
.login-page[data-theme="dark"] .line {
  background: linear-gradient(90deg, transparent, rgba(6, 182, 212, 0.1), transparent);
}

.line-1 {
  top: 30%;
  left: 0;
  right: 0;
  animation: slideLine 8s ease-in-out infinite;
}

.line-2 {
  top: 60%;
  left: 0;
  right: 0;
  animation: slideLine 10s ease-in-out infinite reverse;
}

.line-3 {
  top: 45%;
  left: 0;
  right: 0;
  animation: slideLine 12s ease-in-out infinite;
}

@keyframes slideLine {
  0%, 100% { transform: translateX(-100%); opacity: 0; }
  50% { transform: translateX(100%); opacity: 1; }
}

/* 响应式 */
@media (max-width: 480px) {
  .login-card {
    padding: 32px 24px;
  }

  .brand-title {
    font-size: 28px;
  }

  .card-header h2 {
    font-size: 20px;
  }
}
</style>
