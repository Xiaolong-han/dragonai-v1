<template>
  <div class="register-page">
    <!-- 动态背景 -->
    <div class="bg-effects">
      <div class="grid-pattern"></div>
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
      <div class="glow-orb orb-3"></div>
    </div>

    <!-- 主内容区 -->
    <div class="register-content">
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
        <p class="brand-subtitle">创建账户，开启智能之旅</p>
      </div>

      <!-- 注册卡片 -->
      <div class="register-card-wrapper">
        <div class="register-card">
          <div class="card-header">
            <h2>创建账户</h2>
            <p>填写以下信息完成注册</p>
          </div>

          <form @submit.prevent="handleRegister" class="register-form">
            <div class="form-group">
              <label for="username">用户名</label>
              <div class="input-wrapper">
                <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
                <input
                  id="username"
                  v-model="registerForm.username"
                  type="text"
                  placeholder="请输入用户名（3-20个字符）"
                  required
                  minlength="3"
                  maxlength="20"
                />
              </div>
              <span v-if="errors.username" class="error-text">{{ errors.username }}</span>
            </div>

            <div class="form-group">
              <label for="email">邮箱</label>
              <div class="input-wrapper">
                <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                  <polyline points="22,6 12,13 2,6"/>
                </svg>
                <input
                  id="email"
                  v-model="registerForm.email"
                  type="email"
                  placeholder="请输入邮箱地址"
                  required
                />
              </div>
              <span v-if="errors.email" class="error-text">{{ errors.email }}</span>
            </div>

            <div class="form-group">
              <label for="password">密码</label>
              <div class="input-wrapper">
                <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
                <input
                  id="password"
                  v-model="registerForm.password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="请输入密码（至少6位）"
                  required
                  minlength="6"
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
              <span v-if="errors.password" class="error-text">{{ errors.password }}</span>
            </div>

            <div class="form-group">
              <label for="confirmPassword">确认密码</label>
              <div class="input-wrapper">
                <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                  <path d="M9 16l2 2 4-4" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <input
                  id="confirmPassword"
                  v-model="registerForm.confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  placeholder="请再次输入密码"
                  required
                />
                <button
                  type="button"
                  class="toggle-password"
                  @click="showConfirmPassword = !showConfirmPassword"
                >
                  <svg v-if="showConfirmPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                  </svg>
                </button>
              </div>
              <span v-if="errors.confirmPassword" class="error-text">{{ errors.confirmPassword }}</span>
            </div>

            <button
              type="submit"
              class="submit-btn"
              :class="{ loading: authStore.loading }"
              :disabled="authStore.loading"
            >
              <span class="btn-text">{{ authStore.loading ? '注册中...' : '创建账户' }}</span>
              <span class="btn-shine"></span>
            </button>
          </form>

          <div class="card-footer">
            <p>已有账号？<router-link to="/login" class="login-link">立即登录</router-link></p>
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
const showPassword = ref(false)
const showConfirmPassword = ref(false)

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const errors = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validateForm = () => {
  let isValid = true
  errors.username = ''
  errors.email = ''
  errors.password = ''
  errors.confirmPassword = ''

  if (!registerForm.username) {
    errors.username = '请输入用户名'
    isValid = false
  } else if (registerForm.username.length < 3 || registerForm.username.length > 20) {
    errors.username = '用户名长度在 3 到 20 个字符'
    isValid = false
  }

  if (!registerForm.email) {
    errors.email = '请输入邮箱'
    isValid = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerForm.email)) {
    errors.email = '请输入正确的邮箱格式'
    isValid = false
  }

  if (!registerForm.password) {
    errors.password = '请输入密码'
    isValid = false
  } else if (registerForm.password.length < 6) {
    errors.password = '密码长度不能少于 6 位'
    isValid = false
  }

  if (!registerForm.confirmPassword) {
    errors.confirmPassword = '请再次输入密码'
    isValid = false
  } else if (registerForm.confirmPassword !== registerForm.password) {
    errors.confirmPassword = '两次输入密码不一致'
    isValid = false
  }

  return isValid
}

const handleRegister = async () => {
  if (!validateForm()) return

  try {
    const { confirmPassword, ...registerData } = registerForm
    await authStore.register(registerData)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '注册失败')
  }
}
</script>

<style scoped>
/* 页面基础 */
.register-page {
  min-height: 100vh;
  background: var(--bg-secondary, #f7f8fa);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 深色主题支持 */
.register-page[data-theme="dark"] {
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
.register-page[data-theme="dark"] .grid-pattern {
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
.register-page[data-theme="dark"] .orb-1 {
  background: #06b6d4;
  opacity: 0.4;
}

.register-page[data-theme="dark"] .orb-2 {
  background: #8b5cf6;
  opacity: 0.4;
}

.register-page[data-theme="dark"] .orb-3 {
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
.register-content {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
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
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
  color: #06b6d4;
  animation: pulse 3s ease-in-out infinite;
}

.logo svg {
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 0 20px rgba(6, 182, 212, 0.5));
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.brand-title {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 6px;
  letter-spacing: -0.5px;
  background: linear-gradient(135deg, #fff 0%, #06b6d4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

/* 注册卡片 */
.register-card-wrapper {
  width: 100%;
}

.register-card {
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  padding: 36px;
  box-shadow:
    0 0 0 1px rgba(6, 182, 212, 0.1),
    0 20px 60px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.card-header {
  text-align: center;
  margin-bottom: 28px;
}

.card-header h2 {
  font-size: 22px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 6px;
}

.card-header p {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  margin: 0;
}

/* 表单样式 */
.register-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 14px;
  width: 16px;
  height: 16px;
  color: rgba(255, 255, 255, 0.3);
  transition: color 0.2s;
  pointer-events: none;
}

.input-wrapper:focus-within .input-icon {
  color: #06b6d4;
}

.input-wrapper input {
  width: 100%;
  height: 44px;
  padding: 0 40px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  font-size: 13px;
  color: #fff;
  transition: all 0.2s;
  outline: none;
}

.input-wrapper input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.input-wrapper input:focus {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(6, 182, 212, 0.5);
  box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1);
}

.toggle-password {
  position: absolute;
  right: 14px;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.3);
  transition: color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toggle-password:hover {
  color: rgba(255, 255, 255, 0.6);
}

.toggle-password svg {
  width: 16px;
  height: 16px;
}

.error-text {
  font-size: 11px;
  color: #ef4444;
  margin-top: 2px;
}

/* 提交按钮 */
.submit-btn {
  position: relative;
  height: 44px;
  margin-top: 8px;
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s;
  box-shadow:
    0 4px 20px rgba(6, 182, 212, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
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
  margin-top: 20px;
  text-align: center;
}

.card-footer p {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  margin: 0;
}

.login-link {
  color: #06b6d4;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.login-link:hover {
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
  background: linear-gradient(90deg, transparent, rgba(6, 182, 212, 0.1), transparent);
  height: 1px;
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
  .register-card {
    padding: 28px 20px;
  }

  .brand-title {
    font-size: 24px;
  }

  .card-header h2 {
    font-size: 18px;
  }
}
</style>
