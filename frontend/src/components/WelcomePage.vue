<template>
  <div class="welcome-page">
    <!-- 背景效果 -->
    <div class="bg-effects">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <div class="welcome-content">
      <!-- 欢迎头部 -->
      <div class="welcome-header">
        <div class="logo-wrapper">
          <div class="logo">
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M24 4L6 14V34L24 44L42 34V14L24 4Z" stroke="currentColor" stroke-width="2" fill="none"/>
              <path d="M24 4V24M24 24L6 14M24 24L42 14" stroke="currentColor" stroke-width="2"/>
              <circle cx="24" cy="24" r="4" fill="currentColor"/>
            </svg>
          </div>
          <div class="status-dot"></div>
        </div>
        <h1 class="welcome-title">
          <span class="greeting">你好</span>，我是 DragonAI
        </h1>
        <p class="welcome-subtitle">有什么我可以帮你的？</p>
      </div>

      <!-- 能力展示 -->
      <div class="capabilities">
        <h3 class="section-title">我可以帮你</h3>
        <div class="capabilities-list">
          <div
            v-for="capability in capabilities"
            :key="capability.id"
            class="capability-tag"
          >
            <div class="capability-dot" :style="{ background: capability.color }"></div>
            <span class="capability-name">{{ capability.name }}</span>
          </div>
        </div>
      </div>

      <!-- 示例提示词 -->
      <div class="example-prompts">
        <h3 class="section-title">试试这样问我</h3>
        <div class="prompts-list">
          <div
            v-for="(prompt, index) in examplePrompts"
            :key="index"
            class="prompt-item"
            @click="handlePromptClick(prompt)"
          >
            <span class="prompt-text">{{ prompt }}</span>
            <svg class="prompt-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </div>
        </div>
      </div>

  
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ChatDotRound, Edit, Picture, Search, Document, Collection } from '@element-plus/icons-vue'
import { useConversationStore } from '@/stores/conversation'

const router = useRouter()
const conversationStore = useConversationStore()

const capabilities = [
  { id: 'chat', name: '智能对话', color: '#06b6d4' },
  { id: 'code', name: '代码编写', color: '#8b5cf6' },
  { id: 'image', name: '图像生成', color: '#f97316' },
  { id: 'search', name: '信息检索', color: '#10b981' },
  { id: 'doc', name: '文档分析', color: '#f59e0b' },
  { id: 'translate', name: '多语言翻译', color: '#ec4899' }
]

const examplePrompts = [
  '帮我写一段 Python 代码，实现快速排序算法',
  '解释一下量子计算的基本原理',
  '帮我生成一张未来城市的概念图',
  '总结一下人工智能的发展历程',
  '翻译这段英文：The quick brown fox jumps over the lazy dog'
]

const recentConversations = computed(() => {
  return conversationStore.sortedConversations.slice(0, 5)
})



const handlePromptClick = (prompt: string) => {
  // 跳转到 /chat 并带上 message 参数，让 Chat.vue 处理创建会话和发送消息
  router.push({
    path: '/chat',
    query: { message: encodeURIComponent(prompt) }
  })
}

const handleConversationClick = (id: number) => {
  conversationStore.selectConversation(id)
  router.push(`/chat/${id}`)
}

const createNewConversation = async (initialMessage?: string) => {
  try {
    const conversation = await conversationStore.createConversation({
      title: initialMessage ? initialMessage.slice(0, 20) + '...' : '新会话'
    })
    if (conversation && conversation.id) {
      router.push(`/chat/${conversation.id}`)
    }
  } catch (error) {
    console.error('创建会话失败:', error)
  }
}

const formatTime = (date: string | Date) => {
  const d = new Date(date)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    const hours = Math.floor(diff / (1000 * 60 * 60))
    if (hours === 0) {
      const minutes = Math.floor(diff / (1000 * 60))
      return minutes === 0 ? '刚刚' : `${minutes}分钟前`
    }
    return `${hours}小时前`
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }
}
</script>

<style scoped>
.welcome-page {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  position: relative;
  overflow-y: auto;
  background: var(--bg-secondary);
}

/* 背景效果 */
.bg-effects {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.15;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: #06b6d4;
  top: -200px;
  right: -100px;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: #8b5cf6;
  bottom: -150px;
  left: -100px;
  animation-delay: -7s;
}

.orb-3 {
  width: 300px;
  height: 300px;
  background: #f97316;
  top: 50%;
  left: 30%;
  animation-delay: -14s;
  opacity: 0.08;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(30px, -30px) scale(1.1); }
  50% { transform: translate(-20px, 20px) scale(0.9); }
  75% { transform: translate(20px, 10px) scale(1.05); }
}

/* 内容区域 */
.welcome-content {
  position: relative;
  z-index: 1;
  max-width: 800px;
  width: 100%;
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 欢迎头部 */
.welcome-header {
  text-align: center;
  margin-bottom: 48px;
}

.logo-wrapper {
  position: relative;
  display: inline-block;
  margin-bottom: 24px;
}

.logo {
  width: 80px;
  height: 80px;
  color: var(--primary-color, #06b6d4);
  animation: pulse 3s ease-in-out infinite;
}

.logo svg {
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 0 30px rgba(6, 182, 212, 0.3));
}

.status-dot {
  position: absolute;
  bottom: 4px;
  right: 4px;
  width: 16px;
  height: 16px;
  background: #10b981;
  border-radius: 50%;
  border: 3px solid var(--bg-secondary);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.8; }
}

.welcome-title {
  font-size: 36px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 12px;
  letter-spacing: -0.5px;
}

.greeting {
  background: linear-gradient(135deg, var(--primary-color, #06b6d4) 0%, #22d3ee 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-subtitle {
  font-size: 18px;
  color: var(--text-secondary);
  margin: 0;
}

/* 分区标题 */
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 16px;
}

/* 能力展示 */
.capabilities {
  margin-bottom: 40px;
}

.capabilities-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.capability-tag {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  transition: all 0.2s ease;
}

.capability-tag:hover {
  border-color: var(--primary-color);
  background: var(--bg-tertiary);
  transform: translateY(-1px);
}

.capability-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 8px currentColor;
}

.capability-name {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
}

/* 示例提示词 */
.example-prompts {
  margin-bottom: 40px;
}

.prompts-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.prompt-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.prompt-item:hover {
  background: var(--bg-tertiary);
  border-color: var(--primary-color);
  padding-left: 24px;
}

.prompt-text {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.5;
}

.prompt-arrow {
  width: 16px;
  height: 16px;
  color: var(--text-tertiary);
  opacity: 0;
  transform: translateX(-8px);
  transition: all 0.2s ease;
}

.prompt-item:hover .prompt-arrow {
  opacity: 1;
  transform: translateX(0);
  color: var(--primary-color);
}

/* 最近对话 */
.recent-conversations {
  margin-bottom: 40px;
}

.conversations-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.conversation-item:hover {
  background: var(--bg-tertiary);
  border-color: var(--primary-color);
}

.conversation-icon {
  width: 36px;
  height: 36px;
  background: rgba(6, 182, 212, 0.1);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-color);
  font-size: 18px;
}

.conversation-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.conversation-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conversation-time {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 响应式 */
@media (max-width: 640px) {
  .welcome-title {
    font-size: 28px;
  }

  .welcome-subtitle {
    font-size: 16px;
  }

  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .action-card {
    padding: 20px 12px;
  }

  .action-icon {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }
}

@media (max-width: 480px) {
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .action-card {
    padding: 16px 8px;
  }

  .action-name {
    font-size: 12px;
  }
}
</style>
