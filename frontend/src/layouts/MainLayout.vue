<template>
  <div class="main-layout">
    <aside class="sidebar">
      <div class="sidebar-top">
        <button class="new-chat-btn" @click="handleNewConversation">
          <el-icon><Plus /></el-icon>
          <span>新建对话</span>
        </button>
        
        <!-- 搜索框 -->
        <div class="search-box">
          <el-icon class="search-icon"><Search /></el-icon>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索对话..."
            class="search-input"
          />
          <el-icon v-if="searchQuery" class="clear-icon" @click="searchQuery = ''"><CircleClose /></el-icon>
        </div>
        
        <div class="conversation-list-wrapper">
          <ConversationList :search-query="searchQuery" />
        </div>
      </div>
      
      <div class="sidebar-bottom">
        <div class="user-info-section">
          <el-dropdown>
            <div class="user-info">
              <div class="user-avatar">
                <el-icon><User /></el-icon>
              </div>
              <span class="user-name">{{ authStore.user?.username }}</span>
              <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/profile')">
                  <el-icon><User /></el-icon>
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item @click="router.push('/settings')">
                  <el-icon><Setting /></el-icon>
                  设置
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </aside>
    
    <main class="main-content">
      <header class="main-header">
        <div class="header-content">
          <!-- 左侧：主题切换按钮 -->
          <div class="header-left">
            <ThemeSwitcher />
          </div>
          <!-- 中间：会话标题 -->
          <div v-if="showConversationTitle" class="conversation-header">
            <span class="conversation-title">{{ currentConversationTitle }}</span>
          </div>
          <slot v-else name="header-left"></slot>
          <!-- 右侧：空（保持布局平衡） -->
          <div class="header-right">
          </div>
        </div>
      </header>
      <div class="content-area">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Plus, User, SwitchButton, Search, CircleClose, ArrowDown, Edit, Delete, Top } from '@element-plus/icons-vue'
import ConversationList from '@/components/ConversationList.vue'
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'
import { useConversationStore } from '@/stores/conversation'

const authStore = useAuthStore()
const conversationStore = useConversationStore()
const router = useRouter()
const route = useRoute()

const searchQuery = ref('')

// 当前会话标题
const currentConversationTitle = computed(() => {
  const conversationId = route.params.conversationId
  if (!conversationId) return ''
  const conversation = conversationStore.conversations.find(
    c => c.id === Number(conversationId)
  )
  return conversation?.title || ''
})

// 是否显示会话标题
const showConversationTitle = computed(() => {
  return route.path.startsWith('/chat/') && currentConversationTitle.value
})

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await authStore.logout()
    router.push('/login')
  } catch {
  }
}

const handleNewConversation = async () => {
  try {
    const conversation = await conversationStore.createConversation({ title: '新会话' })
    if (conversation && conversation.id) {
      router.push(`/chat/${conversation.id}`)
    }
    ElMessage.success('会话创建成功')
  } catch (error) {
    ElMessage.error('创建会话失败')
  }
}
</script>

<style scoped>
.main-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--bg-secondary);
}

.sidebar {
  width: 280px;
  background: var(--bg-primary);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
  border-right: 1px solid var(--border-color);
}

.sidebar-top {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px;
}

.new-chat-btn {
  width: 100%;
  padding: 12px 16px;
  margin-bottom: 12px;
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-light) 100%);
  color: #ffffff;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition-normal);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(6, 182, 212, 0.25);
}

.new-chat-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(6, 182, 212, 0.35);
}

.new-chat-btn:active {
  transform: translateY(0);
}

/* 搜索框 */
.search-box {
  position: relative;
  margin-bottom: 12px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-tertiary);
  font-size: 16px;
}

.search-input {
  width: 100%;
  height: 40px;
  padding: 0 36px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 14px;
  color: var(--text-primary);
  transition: all var(--transition-fast);
  outline: none;
}

.search-input::placeholder {
  color: var(--text-tertiary);
}

.search-input:focus {
  border-color: var(--primary-color);
  background: var(--bg-primary);
  box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1);
}

.clear-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-tertiary);
  font-size: 16px;
  cursor: pointer;
  transition: color var(--transition-fast);
}

.clear-icon:hover {
  color: var(--text-secondary);
}

.conversation-list-wrapper {
  flex: 1;
  overflow: hidden;
}

.sidebar-bottom {
  flex-shrink: 0;
  padding: 12px 16px;
  border-top: 1px solid var(--border-color);
}

.user-info-section {
  width: 100%;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.user-info:hover {
  background: var(--bg-secondary);
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-color);
  font-size: 16px;
}

.user-name {
  flex: 1;
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-arrow {
  font-size: 12px;
  color: var(--text-tertiary);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-secondary);
}

.main-header {
  height: 56px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  padding: 0 24px;
  flex-shrink: 0;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  justify-content: flex-end;
}

.conversation-header {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
}

.conversation-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.content-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
</style>
