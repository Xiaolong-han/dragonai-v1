<template>
  <div class="empty-chat-state">
    <div class="empty-content">
      <!-- 图标 -->
      <div class="empty-icon-wrapper">
        <svg class="empty-icon" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- 外圈 -->
          <circle cx="60" cy="60" r="50" stroke="var(--primary-color)" stroke-width="1.5" opacity="0.2"/>
          <circle cx="60" cy="60" r="40" stroke="var(--primary-color)" stroke-width="1" opacity="0.15"/>
          <!-- 聊天气泡 -->
          <path d="M40 45C40 41.6863 42.6863 39 46 39H74C77.3137 39 80 41.6863 80 45V65C80 68.3137 77.3137 71 74 71H55L45 79V71H46C42.6863 71 40 68.3137 40 65V45Z" 
                fill="var(--bg-primary)" 
                stroke="var(--primary-color)" 
                stroke-width="2"/>
          <!-- 消息线条 -->
          <line x1="50" y1="52" x2="70" y2="52" stroke="var(--text-tertiary)" stroke-width="2" stroke-linecap="round" opacity="0.5"/>
          <line x1="50" y1="60" x2="62" y2="60" stroke="var(--text-tertiary)" stroke-width="2" stroke-linecap="round" opacity="0.3"/>
          <!-- 装饰点 -->
          <circle cx="35" cy="55" r="3" fill="var(--primary-color)" opacity="0.4"/>
          <circle cx="85" cy="50" r="2" fill="var(--success-color)" opacity="0.4"/>
          <circle cx="80" cy="75" r="2.5" fill="var(--warning-color)" opacity="0.4"/>
        </svg>
      </div>
      
      <!-- 标题 -->
      <h3 class="empty-title">开始新的对话</h3>
      
      <!-- 描述 -->
      <p class="empty-desc">我可以帮你解答问题、编写代码、生成图像、翻译文本等</p>
      
      <!-- 示例提示词 -->
      <div class="example-prompts">
        <div 
          v-for="(prompt, index) in examplePrompts" 
          :key="index"
          class="prompt-card"
          @click="handlePromptClick(prompt.fullText)"
        >
          <div class="prompt-icon">
            <el-icon :size="18">
              <component :is="prompt.icon" />
            </el-icon>
          </div>
          <div class="prompt-text">{{ prompt.displayText }}</div>
          <div class="prompt-arrow">
            <el-icon><ArrowRight /></el-icon>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Cpu, ChatDotRound, Picture, Document, ArrowRight } from '@element-plus/icons-vue'

const examplePrompts = [
  {
    icon: 'Cpu',
    displayText: '帮我写一段 Python 快速排序算法',
    fullText: '帮我写一段 Python 代码，实现快速排序算法，并添加详细注释说明原理'
  },
  {
    icon: 'ChatDotRound',
    displayText: '解释一下量子计算的基本原理',
    fullText: '用通俗易懂的语言解释一下量子计算的基本原理，以及它与经典计算的区别'
  },
  {
    icon: 'Picture',
    displayText: '生成一张未来城市的概念图',
    fullText: '帮我生成一张未来城市的概念图，要有高科技感，包含飞行汽车和绿色建筑'
  },
  {
    icon: 'Document',
    displayText: '翻译这段英文并解释语法',
    fullText: '翻译这段英文：The quick brown fox jumps over the lazy dog，并解释其中的语法结构'
  }
]

const emit = defineEmits<{
  selectPrompt: [prompt: string]
}>()

function handlePromptClick(prompt: string) {
  emit('selectPrompt', prompt)
}
</script>

<style scoped>
.empty-chat-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  min-height: 0;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  max-width: 560px;
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.empty-icon-wrapper {
  width: 120px;
  height: 120px;
  margin-bottom: 24px;
  position: relative;
}

.empty-icon-wrapper::before {
  content: '';
  position: absolute;
  inset: -10px;
  background: radial-gradient(circle, var(--primary-light-bg) 0%, transparent 70%);
  border-radius: 50%;
  opacity: 0.5;
}

.empty-icon {
  width: 100%;
  height: 100%;
  position: relative;
  z-index: 1;
}

.empty-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.empty-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 32px;
  line-height: 1.6;
}

/* 示例提示词卡片 */
.example-prompts {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  width: 100%;
}

.prompt-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.prompt-card:hover {
  border-color: var(--primary-color);
  background: var(--primary-light-bg);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.prompt-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-light-bg);
  border-radius: 8px;
  color: var(--primary-color);
  flex-shrink: 0;
}

.prompt-card:hover .prompt-icon {
  background: var(--primary-color);
  color: white;
}

.prompt-text {
  flex: 1;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.prompt-card:hover .prompt-text {
  color: var(--text-primary);
}

.prompt-arrow {
  color: var(--text-tertiary);
  opacity: 0;
  transition: all 0.2s ease;
}

.prompt-card:hover .prompt-arrow {
  opacity: 1;
  color: var(--primary-color);
  transform: translateX(2px);
}

/* 响应式 */
@media (max-width: 640px) {
  .example-prompts {
    grid-template-columns: 1fr;
  }
}
</style>
