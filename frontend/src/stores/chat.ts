
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

export interface ToolCall {
  id: string
  name: string
  status: 'pending' | 'success' | 'error'
  summary?: string
  links?: Array<{ title: string; url: string }>
  details?: string
}

export interface ChatMessage {
  id: number
  conversation_id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
  is_streaming?: boolean
  thinking_content?: string
  is_thinking_expanded?: boolean
  incomplete?: boolean
  tool_calls?: ToolCall[]
}

export interface ToolOptions {
  targetLang?: string
  sourceLang?: string
  model?: string
  size?: string
  n?: number
  language?: string
}

export interface ChatSettings {
  isExpert: boolean
  enableThinking: boolean
}

const TOOL_PREFIXES: Record<string, string> = {
  translation: '翻译',
  coding: '编程',
  image_generation: '生成图像',
  image_editing: '编辑图像'
}

export const useChatStore = defineStore('chat', () => {
  const messagesMap = ref<Record<number, ChatMessage[]>>({})
  const loadingMap = ref<Record<number, boolean>>({})
  const sendingMap = ref<Record<number, boolean>>({})
  const xhrMap = new Map<number, XMLHttpRequest>()
  const assistantMessageIdMap = new Map<number, number>()
  const currentConversationId = ref<number | null>(null)

  const messages = computed(() => {
    if (!currentConversationId.value) return []
    return messagesMap.value[currentConversationId.value] || []
  })

  const loading = computed(() => {
    if (!currentConversationId.value) return false
    return loadingMap.value[currentConversationId.value] || false
  })

  const sending = computed(() => {
    if (!currentConversationId.value) return false
    return sendingMap.value[currentConversationId.value] || false
  })

  function isSending(conversationId: number): boolean {
    return sendingMap.value[conversationId] || false
  }

  function setCurrentConversation(conversationId: number | null) {
    currentConversationId.value = conversationId
    if (conversationId && loadingMap.value[conversationId] === undefined) {
      loadingMap.value[conversationId] = false
    }
  }

  function getMessages(conversationId: number): ChatMessage[] {
    return messagesMap.value[conversationId] || []
  }

  function setMessages(conversationId: number, msgs: ChatMessage[]) {
    messagesMap.value[conversationId] = msgs
  }

  async function fetchConversationHistory(conversationId: number) {
    loadingMap.value[conversationId] = true
    try {
      const response = await request.get(`/api/v1/chat/conversations/${conversationId}/history`)
      const rawMessages = (response as any).messages || []
      console.log('[HISTORY] Raw messages for', conversationId, ':', rawMessages.length)
      
      const serverMessages = rawMessages.map((msg: any) => {
        const extraData = msg.extra_data || {}
        return {
          ...msg,
          thinking_content: extraData.thinking_content || undefined,
          is_thinking_expanded: false,
          incomplete: extraData.incomplete || false,
          tool_calls: extraData.tool_calls || []
        }
      })

      const existingMessages = messagesMap.value[conversationId] || []
      const streamingMsg = existingMessages.find(m => m.is_streaming)
      
      if (streamingMsg) {
        const serverIds = new Set(serverMessages.map((m: ChatMessage) => m.id))
        if (!serverIds.has(streamingMsg.id)) {
          const streamingMsgIndex = existingMessages.findIndex(m => m.id === streamingMsg.id)
          const userMsg = streamingMsgIndex > 0 ? existingMessages[streamingMsgIndex - 1] : null
          
          if (userMsg && userMsg.role === 'user' && !serverIds.has(userMsg.id)) {
            messagesMap.value[conversationId] = [...serverMessages, userMsg, streamingMsg]
          } else {
            messagesMap.value[conversationId] = [...serverMessages, streamingMsg]
          }
        } else {
          messagesMap.value[conversationId] = serverMessages
        }
      } else {
        messagesMap.value[conversationId] = serverMessages
      }
    } catch (error) {
      console.error('[HISTORY] Error fetching history for', conversationId, error)
      messagesMap.value[conversationId] = []
    } finally {
      loadingMap.value[conversationId] = false
    }
  }

  function sendMessage(
    conversationId: number, 
    content: string, 
    attachments?: string[],
    settings?: ChatSettings
  ) {
    _sendMessageInternal(conversationId, content, attachments, settings)
  }

  function sendMessageWithTool(
    conversationId: number,
    content: string,
    tool: string,
    options?: ToolOptions,
    attachments?: string[],
    settings?: ChatSettings
  ) {
    const prefix = TOOL_PREFIXES[tool] || ''
    let prefixedContent = content
    
    if (prefix) {
      if (tool === 'translation' && options?.targetLang) {
        const langMap: Record<string, string> = {
          'zh': '中文',
          'en': '英文',
          'ja': '日文',
          'ko': '韩文',
          'fr': '法文',
          'de': '德文',
          'es': '西班牙文',
          'ru': '俄文'
        }
        const targetLangName = langMap[options.targetLang] || options.targetLang
        prefixedContent = `翻译成${targetLangName}：${content}`
      } else {
        prefixedContent = `${prefix}：${content}`
      }
    }
    
    _sendMessageInternal(conversationId, prefixedContent, attachments, settings)
  }

  function _sendMessageInternal(
    conversationId: number,
    content: string,
    attachments: string[] | undefined,
    settings?: ChatSettings
  ) {
    sendingMap.value[conversationId] = true

    const existingMsgs = messagesMap.value[conversationId] || []

    const userMessage: ChatMessage = {
      id: Date.now(),
      conversation_id: conversationId,
      role: 'user',
      content: content,
      created_at: new Date().toISOString()
    }

    const assistantMessageId = Date.now() + 1
    assistantMessageIdMap.set(conversationId, assistantMessageId)
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      conversation_id: conversationId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      is_streaming: true,
      thinking_content: '',
      is_thinking_expanded: true,
      tool_calls: []
    }

    messagesMap.value[conversationId] = [...existingMsgs, userMessage, assistantMessage]

    const url = '/api/v1/chat/send'
    
    const body: any = {
      conversation_id: conversationId,
      content: content,
      is_expert: settings?.isExpert ?? false,
      enable_thinking: settings?.enableThinking ?? false,
      attachments: attachments || null
    }

    const xhr = new XMLHttpRequest()
    xhrMap.set(conversationId, xhr)
    let receivedLength = 0
    let isThinkingPhase = false
    
    xhr.open('POST', url, true)
    xhr.setRequestHeader('Content-Type', 'application/json')
    xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('token')}`)
    
    const updateMessage = (updates: Partial<ChatMessage>) => {
      const currentMsgs = messagesMap.value[conversationId]
      if (!currentMsgs) return
      
      const msgIndex = currentMsgs.findIndex((m) => m.id === assistantMessageId)
      if (msgIndex !== -1) {
        const currentMsg = currentMsgs[msgIndex]
        const newMsgs = [...currentMsgs]
        newMsgs[msgIndex] = {
          ...currentMsg,
          ...updates,
          is_streaming: true,
          is_thinking_expanded: isThinkingPhase ? true : currentMsg.is_thinking_expanded
        }
        messagesMap.value[conversationId] = newMsgs
      }
    }
    
    xhr.onprogress = () => {
      if (xhr.status === 401) {
        console.log('[SSE] 401 detected in onprogress')
        localStorage.removeItem('token')
        sendingMap.value[conversationId] = false
        window.location.href = '/login'
        return
      }
      
      const newData = xhr.responseText.substring(receivedLength)
      receivedLength = xhr.responseText.length
      
      const lines = newData.split('\n')
      let newContent = ''
      let newThinkingContent = ''
      
      lines.forEach((line, index) => {
        if (index === lines.length - 1 && !newData.endsWith('\n')) {
          receivedLength -= line.length
          return
        }
        
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') {
            return
          }
          try {
            const decoded = JSON.parse(data)
            
            if (typeof decoded === 'object' && decoded.type === 'thinking') {
              isThinkingPhase = true
              const thinkingContent = decoded.data?.content || decoded.content || ''
              newThinkingContent += thinkingContent
            } else if (typeof decoded === 'object' && decoded.type === 'thinking_end') {
              isThinkingPhase = false
            } else if (typeof decoded === 'object' && decoded.type === 'heartbeat') {
              // 忽略心跳消息
            } else if (typeof decoded === 'object' && decoded.type === 'content') {
              const contentStr = decoded.data?.content || decoded.content || ''
              newContent += contentStr
            } else if (typeof decoded === 'object' && decoded.type === 'tool_call') {
              // 工具调用开始 - 解析完整信息
              const currentMsgs = messagesMap.value[conversationId]
              const currentMsg = currentMsgs?.find((m) => m.id === assistantMessageId)
              const existingToolCalls = currentMsg?.tool_calls || []
              
              // 解析工具调用 - 包含 id
              const callData = JSON.parse(decoded.data?.content || '{}')
              const calls = callData.calls || []
              
              // 添加新的 pending 工具调用
              const newCalls: ToolCall[] = calls.map((call: any) => ({
                id: call.id || '',
                name: call.name || '',
                status: 'pending' as const
              }))
              
              updateMessage({
                tool_calls: [...existingToolCalls, ...newCalls]
              })
            } else if (typeof decoded === 'object' && decoded.type === 'tool_result') {
              // 工具调用结果 - 使用 tool_call_id 匹配更新
              try {
                const resultData = JSON.parse(decoded.data?.content || '{}')
                const toolCallId = resultData.tool_call_id
                const toolName = resultData.name || 'unknown'
                const summary = resultData.summary || '完成'
                const links = resultData.links || []
                const details = resultData.details || ''
                
                const currentMsgs = messagesMap.value[conversationId]
                const currentMsg = currentMsgs?.find((m) => m.id === assistantMessageId)
                const existingToolCalls = currentMsg?.tool_calls || []
                
                // 使用 tool_call_id 精确匹配
                const updatedToolCalls = [...existingToolCalls]
                const pendingIndex = updatedToolCalls.findIndex(
                  (t: ToolCall) => t.id === toolCallId && t.status === 'pending'
                )
                
                if (pendingIndex !== -1) {
                  // 更新现有的 pending 工具调用
                  updatedToolCalls[pendingIndex] = {
                    ...updatedToolCalls[pendingIndex],
                    status: 'success',
                    summary: summary,
                    links: links,
                    details: details
                  }
                } else {
                  // 如果没有找到匹配的，添加一个新的
                  updatedToolCalls.push({
                    id: toolCallId || '',
                    name: toolName,
                    status: 'success',
                    summary: summary,
                    links: links,
                    details: details
                  })
                }
                
                updateMessage({
                  tool_calls: updatedToolCalls
                })
              } catch (e) {
                console.error('[SSE] Failed to parse tool_result:', e)
              }
            } else if (typeof decoded === 'object' && decoded.type === 'error') {
              const errorMsg = decoded.data?.content || decoded.data?.message || '发生错误'
              newContent += `\n\n❌ ${errorMsg}`
            } else if (typeof decoded === 'string') {
              newContent += decoded
            }
          } catch (e) {
            console.error('[SSE] JSON parse error:', e, 'data:', data)
          }
        }
      })
      
      if (newThinkingContent || newContent) {
        const currentMsgs = messagesMap.value[conversationId]
        const currentMsg = currentMsgs?.find((m) => m.id === assistantMessageId)
        
        updateMessage({
          content: (currentMsg?.content || '') + newContent,
          thinking_content: (currentMsg?.thinking_content || '') + newThinkingContent
        })
      }
    }
    
    xhr.onload = () => {
      console.log('[SSE] Request completed for conversation:', conversationId)
      xhrMap.delete(conversationId)
      assistantMessageIdMap.delete(conversationId)
      
      if (xhr.status === 401) {
        localStorage.removeItem('token')
        sendingMap.value[conversationId] = false
        import('element-plus').then(({ ElMessage }) => {
          ElMessage.error('登录已过期，请重新登录')
        })
        window.location.href = '/login'
        return
      }
      
      sendingMap.value[conversationId] = false
      const currentMsgs = messagesMap.value[conversationId]
      if (currentMsgs) {
        const msgIndex = currentMsgs.findIndex((m) => m.id === assistantMessageId)
        if (msgIndex !== -1) {
          const newMsgs = [...currentMsgs]
          newMsgs[msgIndex] = {
            ...newMsgs[msgIndex],
            is_streaming: false,
            is_thinking_expanded: false
          }
          messagesMap.value[conversationId] = newMsgs
        }
      }
    }
    
    xhr.onerror = () => {
      console.error('[SSE] Request error for conversation:', conversationId)
      xhrMap.delete(conversationId)
      assistantMessageIdMap.delete(conversationId)
      
      sendingMap.value[conversationId] = false
      const currentMsgs = messagesMap.value[conversationId]
      if (currentMsgs) {
        const msgIndex = currentMsgs.findIndex((m) => m.id === assistantMessageId)
        if (msgIndex !== -1) {
          const newMsgs = [...currentMsgs]
          newMsgs[msgIndex] = {
            ...newMsgs[msgIndex],
            content: newMsgs[msgIndex].content || '请求失败，请重试',
            is_streaming: false
          }
          messagesMap.value[conversationId] = newMsgs
        }
      }
    }
    
    xhr.ontimeout = () => {
      console.error('[SSE] Request timeout for conversation:', conversationId)
      xhrMap.delete(conversationId)
      assistantMessageIdMap.delete(conversationId)
      
      sendingMap.value[conversationId] = false
      const currentMsgs = messagesMap.value[conversationId]
      if (currentMsgs) {
        const msgIndex = currentMsgs.findIndex((m) => m.id === assistantMessageId)
        if (msgIndex !== -1) {
          const newMsgs = [...currentMsgs]
          newMsgs[msgIndex] = {
            ...newMsgs[msgIndex],
            is_streaming: false
          }
          messagesMap.value[conversationId] = newMsgs
        }
      }
    }
    
    xhr.onabort = () => {
      console.log('[SSE] Request aborted for conversation:', conversationId)
      xhrMap.delete(conversationId)
      assistantMessageIdMap.delete(conversationId)
      
      sendingMap.value[conversationId] = false
      const currentMsgs = messagesMap.value[conversationId]
      if (currentMsgs) {
        const msgIndex = currentMsgs.findIndex((m) => m.id === assistantMessageId)
        if (msgIndex !== -1) {
          const newMsgs = [...currentMsgs]
          newMsgs[msgIndex] = {
            ...newMsgs[msgIndex],
            is_streaming: false,
            incomplete: true
          }
          messagesMap.value[conversationId] = newMsgs
        }
      }
    }
    
    xhr.timeout = 120000
    xhr.send(JSON.stringify(body))
  }

  function regenerateMessage(conversationId: number, messageIndex: number) {
    const msgs = messagesMap.value[conversationId]
    if (!msgs) return
    
    const message = msgs[messageIndex]
    if (!message || message.role !== 'assistant') {
      return
    }

    let userMessage: ChatMessage | undefined
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (msgs[i]?.role === 'user') {
        userMessage = msgs[i]
        break
      }
    }

    if (!userMessage) {
      return
    }

    messagesMap.value[conversationId] = msgs.slice(0, messageIndex)
    sendMessage(conversationId, userMessage.content)
  }

  function clearMessages() {
    if (currentConversationId.value) {
      delete messagesMap.value[currentConversationId.value]
    }
  }

  function cancelRequest(conversationId: number) {
    const xhr = xhrMap.get(conversationId)
    if (xhr) {
      xhr.abort()
      xhrMap.delete(conversationId)
    }
    sendingMap.value[conversationId] = false
  }

  function toggleThinkingExpanded(messageId: number) {
    if (!currentConversationId.value) return
    const msgs = messagesMap.value[currentConversationId.value]
    if (!msgs) return
    
    const msgIndex = msgs.findIndex((m) => m.id === messageId)
    if (msgIndex !== -1) {
      const newMsgs = [...msgs]
      newMsgs[msgIndex] = {
        ...newMsgs[msgIndex],
        is_thinking_expanded: !newMsgs[msgIndex].is_thinking_expanded
      }
      messagesMap.value[currentConversationId.value] = newMsgs
    }
  }

  return {
    messages,
    loading,
    sending,
    currentConversationId,
    isSending,
    setCurrentConversation,
    getMessages,
    setMessages,
    fetchConversationHistory,
    sendMessage,
    sendMessageWithTool,
    regenerateMessage,
    clearMessages,
    cancelRequest,
    toggleThinkingExpanded
  }
})

import request from '@/utils/request'
