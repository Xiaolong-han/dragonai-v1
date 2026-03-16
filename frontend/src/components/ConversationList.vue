<template>
  <div class="conversation-list">
    <div class="conversations">
      <!-- 置顶对话 -->
      <div v-if="pinnedConversations.length > 0" class="conversation-group">
        <div class="group-label">
          <el-icon><Star /></el-icon>
          <span>置顶</span>
        </div>
        <div
          v-for="conversation in pinnedConversations"
          :key="conversation.id"
          class="conversation-item"
          @click="handleSelectConversation(conversation.id)"
        >
          <div :class="['conversation-content', { active: currentConversationId === conversation.id }]">
            <el-icon class="chat-icon"><ChatDotRound /></el-icon>
            <span class="title-text">{{ conversation.title }}</span>
          </div>
          
          <div class="conversation-actions" @click.stop>
            <el-dropdown trigger="click" popper-class="dark-dropdown">
              <el-button class="more-btn" link @click.stop>
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handleUnpinConversation(conversation.id)">
                    <el-icon><Bottom /></el-icon>
                    <span>取消置顶</span>
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleEditConversation(conversation)">
                    <el-icon><Edit /></el-icon>
                    <span>重命名</span>
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="handleDeleteConversation(conversation.id)">
                    <el-icon><Delete /></el-icon>
                    <span class="delete-text">删除</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>

      <!-- 今天 -->
      <div v-if="todayConversations.length > 0" class="conversation-group">
        <div class="group-label">
          <span>今天</span>
        </div>
        <div
          v-for="conversation in todayConversations"
          :key="conversation.id"
          class="conversation-item"
          @click="handleSelectConversation(conversation.id)"
        >
          <div :class="['conversation-content', { active: currentConversationId === conversation.id }]">
            <el-icon class="chat-icon"><ChatDotRound /></el-icon>
            <span class="title-text">{{ conversation.title }}</span>
          </div>
          
          <div class="conversation-actions" @click.stop>
            <el-dropdown trigger="click" popper-class="dark-dropdown">
              <el-button class="more-btn" link @click.stop>
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handlePinConversation(conversation.id)">
                    <el-icon><Top /></el-icon>
                    <span>置顶</span>
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleEditConversation(conversation)">
                    <el-icon><Edit /></el-icon>
                    <span>重命名</span>
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="handleDeleteConversation(conversation.id)">
                    <el-icon><Delete /></el-icon>
                    <span class="delete-text">删除</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>

      <!-- 昨天 -->
      <div v-if="yesterdayConversations.length > 0" class="conversation-group">
        <div class="group-label">
          <span>昨天</span>
        </div>
        <div
          v-for="conversation in yesterdayConversations"
          :key="conversation.id"
          class="conversation-item"
          @click="handleSelectConversation(conversation.id)"
        >
          <div :class="['conversation-content', { active: currentConversationId === conversation.id }]">
            <el-icon class="chat-icon"><ChatDotRound /></el-icon>
            <span class="title-text">{{ conversation.title }}</span>
          </div>
          
          <div class="conversation-actions" @click.stop>
            <el-dropdown trigger="click">
              <el-button class="more-btn" link @click.stop>
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handlePinConversation(conversation.id)">
                    <el-icon><Top /></el-icon>
                    <span>置顶</span>
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleEditConversation(conversation)">
                    <el-icon><Edit /></el-icon>
                    <span>重命名</span>
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="handleDeleteConversation(conversation.id)">
                    <el-icon><Delete /></el-icon>
                    <span class="delete-text">删除</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>

      <!-- 最近7天 -->
      <div v-if="last7DaysConversations.length > 0" class="conversation-group">
        <div class="group-label">
          <span>最近7天</span>
        </div>
        <div
          v-for="conversation in last7DaysConversations"
          :key="conversation.id"
          class="conversation-item"
          @click="handleSelectConversation(conversation.id)"
        >
          <div :class="['conversation-content', { active: currentConversationId === conversation.id }]">
            <el-icon class="chat-icon"><ChatDotRound /></el-icon>
            <span class="title-text">{{ conversation.title }}</span>
          </div>
          
          <div class="conversation-actions" @click.stop>
            <el-dropdown trigger="click">
              <el-button class="more-btn" link @click.stop>
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handlePinConversation(conversation.id)">
                    <el-icon><Top /></el-icon>
                    <span>置顶</span>
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleEditConversation(conversation)">
                    <el-icon><Edit /></el-icon>
                    <span>重命名</span>
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="handleDeleteConversation(conversation.id)">
                    <el-icon><Delete /></el-icon>
                    <span class="delete-text">删除</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>

      <!-- 更早 -->
      <div v-if="olderConversations.length > 0" class="conversation-group">
        <div class="group-label">
          <span>更早</span>
        </div>
        <div
          v-for="conversation in olderConversations"
          :key="conversation.id"
          class="conversation-item"
          @click="handleSelectConversation(conversation.id)"
        >
          <div :class="['conversation-content', { active: currentConversationId === conversation.id }]">
            <el-icon class="chat-icon"><ChatDotRound /></el-icon>
            <span class="title-text">{{ conversation.title }}</span>
          </div>
          
          <div class="conversation-actions" @click.stop>
            <el-dropdown trigger="click">
              <el-button class="more-btn" link @click.stop>
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handlePinConversation(conversation.id)">
                    <el-icon><Top /></el-icon>
                    <span>置顶</span>
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleEditConversation(conversation)">
                    <el-icon><Edit /></el-icon>
                    <span>重命名</span>
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="handleDeleteConversation(conversation.id)">
                    <el-icon><Delete /></el-icon>
                    <span class="delete-text">删除</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="filteredConversations.length === 0" class="empty-state">
        <el-icon class="empty-icon"><ChatLineRound /></el-icon>
        <p>{{ searchQuery ? '没有找到匹配的对话' : '还没有对话' }}</p>
        <el-button v-if="!searchQuery" type="primary" text @click="handleNewConversation">
          开始新对话
        </el-button>
      </div>
    </div>

    <el-dialog v-model="editDialogVisible" title="重命名会话" width="400px">
      <el-input
        v-model="editTitle"
        placeholder="请输入新的会话标题"
        maxlength="200"
        show-word-limit
      />
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="deleteDialogVisible" title="确认删除" width="400px">
      <p>确定要删除这个会话吗？此操作不可恢复。</p>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="handleConfirmDelete">删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound, Edit, Delete, Top, Bottom, Star, ChatLineRound, MoreFilled } from '@element-plus/icons-vue'
import { useConversationStore } from '@/stores/conversation'

interface Props {
  searchQuery?: string
}

const props = withDefaults(defineProps<Props>(), {
  searchQuery: ''
})

const router = useRouter()
const conversationStore = useConversationStore()

const sortedConversations = computed(() => conversationStore.sortedConversations)
const currentConversationId = computed(() => conversationStore.currentConversationId)
const { fetchConversations, pinConversation, unpinConversation, selectConversation, updateConversation, deleteConversation, createConversation } = conversationStore

const editDialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const editingId = ref<number | null>(null)
const editTitle = ref('')
const deletingId = ref<number | null>(null)

// 过滤对话
const filteredConversations = computed(() => {
  if (!props.searchQuery.trim()) {
    return sortedConversations.value
  }
  const query = props.searchQuery.toLowerCase()
  return sortedConversations.value.filter(conv => 
    conv.title.toLowerCase().includes(query)
  )
})

// 按时间分组
const pinnedConversations = computed(() => 
  filteredConversations.value.filter(c => c.is_pinned)
)

const todayConversations = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return filteredConversations.value.filter(c => {
    if (c.is_pinned) return false
    const date = new Date(c.updated_at)
    date.setHours(0, 0, 0, 0)
    return date.getTime() === today.getTime()
  })
})

const yesterdayConversations = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
  return filteredConversations.value.filter(c => {
    if (c.is_pinned) return false
    const date = new Date(c.updated_at)
    date.setHours(0, 0, 0, 0)
    return date.getTime() === yesterday.getTime()
  })
})

const last7DaysConversations = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
  const last7Days = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
  return filteredConversations.value.filter(c => {
    if (c.is_pinned) return false
    const date = new Date(c.updated_at)
    date.setHours(0, 0, 0, 0)
    return date.getTime() < yesterday.getTime() && date.getTime() >= last7Days.getTime()
  })
})

const olderConversations = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const last7Days = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
  return filteredConversations.value.filter(c => {
    if (c.is_pinned) return false
    const date = new Date(c.updated_at)
    date.setHours(0, 0, 0, 0)
    return date.getTime() < last7Days.getTime()
  })
})

onMounted(() => {
  fetchConversations()
})

function handleSelectConversation(id: number) {
  selectConversation(id)
  router.push(`/chat/${id}`)
}

async function handlePinConversation(id: number) {
  try {
    await pinConversation(id)
    ElMessage.success('会话已置顶')
  } catch (error) {
    ElMessage.error('置顶失败')
  }
}

async function handleUnpinConversation(id: number) {
  try {
    await unpinConversation(id)
    ElMessage.success('已取消置顶')
  } catch (error) {
    ElMessage.error('取消置顶失败')
  }
}

function handleEditConversation(conversation: any) {
  editingId.value = conversation.id
  editTitle.value = conversation.title
  editDialogVisible.value = true
}

async function handleSaveEdit() {
  if (!editingId.value || !editTitle.value.trim()) return
  
  try {
    await updateConversation(editingId.value, { title: editTitle.value.trim() })
    ElMessage.success('会话重命名成功')
    editDialogVisible.value = false
  } catch (error) {
    ElMessage.error('重命名失败')
  }
}

function handleDeleteConversation(id: number) {
  deletingId.value = id
  deleteDialogVisible.value = true
}

async function handleConfirmDelete() {
  if (!deletingId.value) return
  
  try {
    await deleteConversation(deletingId.value)
    ElMessage.success('会话删除成功')
    deleteDialogVisible.value = false
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

async function handleNewConversation() {
  try {
    const conversation = await createConversation({ title: '新会话' })
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
.conversation-list {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.conversations {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.conversations::-webkit-scrollbar {
  width: 4px;
}

.conversations::-webkit-scrollbar-track {
  background: transparent;
}

.conversations::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 2px;
}

.conversations::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}

/* 分组 */
.conversation-group {
  margin-bottom: 16px;
}

.group-label {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.group-label .el-icon {
  font-size: 12px;
}

/* 对话项 */
.conversation-item {
  display: flex;
  align-items: center;
  padding: 8px 10px;
  margin: 0 4px 2px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.conversation-item:hover {
  background: var(--bg-secondary);
}

.conversation-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
  padding: 4px 0;
}

.conversation-content.active {
  background: rgba(6, 182, 212, 0.1);
  border-radius: 6px;
  padding: 6px 10px;
  margin: -2px -4px;
  position: relative;
}

.conversation-content.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 16px;
  background: var(--primary-color);
  border-radius: 0 2px 2px 0;
}

.conversation-content.active .chat-icon {
  color: var(--primary-color);
}

.conversation-content.active .title-text {
  color: var(--text-primary);
  font-weight: 600;
}

.chat-icon {
  flex-shrink: 0;
  color: var(--text-tertiary);
  font-size: 16px;
}

.title-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  color: var(--text-primary);
}

.conversation-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.2s;
  padding-left: 4px;
}

.conversation-item:hover .conversation-actions {
  opacity: 1;
}

.more-btn {
  padding: 4px;
  color: var(--text-tertiary);
  font-size: 16px;
}

.more-btn:hover {
  color: var(--primary-color);
}

.delete-text {
  color: #ef4444;
}

/* 下拉菜单暗色主题 - 全局样式 */
:global(.dark-dropdown .el-dropdown-menu) {
  background: var(--bg-primary) !important;
  border: 1px solid var(--border-color) !important;
  box-shadow: var(--shadow-md) !important;
}

:global(.dark-dropdown .el-dropdown-menu__item) {
  color: var(--text-primary) !important;
}

:global(.dark-dropdown .el-dropdown-menu__item:hover) {
  background: var(--bg-secondary) !important;
}

:global(.dark-dropdown .el-dropdown-menu__item .el-icon) {
  color: var(--text-secondary) !important;
}

:global(.dark-dropdown .el-dropdown-menu__item.is-disabled) {
  color: var(--text-tertiary) !important;
}

:global(.dark-dropdown .el-dropdown-menu__item--divided) {
  border-top: 1px solid var(--border-color) !important;
}

:global(.dark-dropdown .el-dropdown-menu__item--divided:before) {
  background: var(--bg-primary) !important;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  color: var(--text-tertiary);
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state p {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 16px;
}
</style>
