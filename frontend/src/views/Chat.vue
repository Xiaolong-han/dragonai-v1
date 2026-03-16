<template>
  <div class="chat-page">
    <template v-if="currentConversationId">
      <ChatMessageList 
        :messages="chatStore.messages" 
        :loading="chatStore.loading" 
        :conversation-id="currentConversationId"
        @regenerate="handleRegenerate"
        @select-prompt="handleSelectPrompt"
      />
      <ChatInput
        :loading="isCurrentSending"
        :disabled="chatStore.loading"
        @send="handleSendMessage"
      />
    </template>
    <WelcomePage v-else />
  </div>
</template>

<script setup lang="ts">
import { watch, onMounted, computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useConversationStore } from '@/stores/conversation'
import { useChatStore } from '@/stores/chat'
import ChatMessageList from '@/components/ChatMessageList.vue'
import ChatInput from '@/components/ChatInput.vue'
import WelcomePage from '@/components/WelcomePage.vue'

interface Props {
  conversationId?: string
}

const props = defineProps<Props>()
const route = useRoute()
const router = useRouter()
const conversationStore = useConversationStore()
const chatStore = useChatStore()

const { currentConversationId } = storeToRefs(conversationStore)

// 标记是否已经处理了初始消息，防止重复发送
const initialMessageProcessed = ref(false)

const isCurrentSending = computed(() => {
  return currentConversationId.value ? chatStore.isSending(currentConversationId.value) : false
})

function getConversationIdFromRoute(): number | null {
  const id = props.conversationId || route.params.conversationId
  if (id) {
    const numId = parseInt(id as string, 10)
    return isNaN(numId) ? null : numId
  }
  return null
}

// 处理 URL 中的初始消息参数
async function handleInitialMessage() {
  const message = route.query.message as string
  if (!message || initialMessageProcessed.value) return

  initialMessageProcessed.value = true
  const decodedMessage = decodeURIComponent(message)

  try {
    // 创建新会话
    const conversation = await conversationStore.createConversation({
      title: decodedMessage.slice(0, 20) + '...'
    })

    if (conversation && conversation.id) {
      // 先清除 URL 参数，避免刷新时重复发送
      await router.replace({
        path: `/chat/${conversation.id}`,
        query: {}
      })

      // 设置当前会话
      conversationStore.selectConversation(conversation.id)
      chatStore.setCurrentConversation(conversation.id)

      // 发送消息
      await chatStore.sendMessage(conversation.id, decodedMessage)
    }
  } catch (error) {
    console.error('发送初始消息失败:', error)
  }
}

// 同步路由到状态
async function syncFromRoute() {
  const routeId = getConversationIdFromRoute()
  if (routeId) {
    if (routeId !== currentConversationId.value) {
      conversationStore.selectConversation(routeId)
    }
    if (routeId !== chatStore.currentConversationId) {
      chatStore.setCurrentConversation(routeId)
      await chatStore.fetchConversationHistory(routeId)
    }
  } else {
    conversationStore.currentConversationId = null
    chatStore.setCurrentConversation(null)

    // 检查是否有初始消息参数，有则创建会话并发送
    if (route.query.message && !initialMessageProcessed.value) {
      await handleInitialMessage()
    }
  }
}

// 监听路由变化
watch(
  () => route.params.conversationId,
  syncFromRoute,
  { immediate: true }
)

// 监听 query 参数变化（处理从 WelcomePage 点击提示词的情况）
watch(
  () => route.query.message,
  async (newMessage) => {
    if (newMessage && !initialMessageProcessed.value && !getConversationIdFromRoute()) {
      await handleInitialMessage()
    }
  }
)

// 监听当前会话ID变化（处理新建会话的情况）
watch(
  currentConversationId,
  async (newId) => {
    if (newId) {
      // 同步URL
      const currentRouteId = route.params.conversationId
      if (currentRouteId !== String(newId)) {
        router.replace(`/chat/${newId}`)
      }
      // 确保chatStore也同步
      if (newId !== chatStore.currentConversationId) {
        chatStore.setCurrentConversation(newId)
        await chatStore.fetchConversationHistory(newId)
      }
    }
  }
)

function handleSendMessage(content: string, files: any[], tool?: string, options?: any, settings?: { isExpert: boolean; enableThinking: boolean }) {
  if (!currentConversationId.value) return
  
  const imageUrls = files.filter((url): url is string => typeof url === 'string')
  
  if (tool) {
    chatStore.sendMessageWithTool(currentConversationId.value, content, tool, options, imageUrls, settings)
  } else {
    chatStore.sendMessage(currentConversationId.value, content, imageUrls, settings)
  }
}

function handleRegenerate(messageIndex: number) {
  if (!currentConversationId.value) return
  chatStore.regenerateMessage(currentConversationId.value, messageIndex)
}

function handleSelectPrompt(prompt: string) {
  if (!currentConversationId.value) return
  chatStore.sendMessage(currentConversationId.value, prompt)
}

onMounted(() => {
  syncFromRoute()
})
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-secondary);
  overflow: hidden;
}

.chat-page > *:first-child {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}
</style>
