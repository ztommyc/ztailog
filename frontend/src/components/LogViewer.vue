<template>
  <div class="log-viewer">
    <el-card class="log-card">
      <template #header>
        <div class="log-header">
          <div class="header-left">
            <el-icon :size="20"><Document /></el-icon>
            <span class="host-name">{{ host.name }}</span>
            <el-tag :type="logTypeTag" size="small">{{ getLogTypeName() }}</el-tag>
          </div>
          
          <div class="header-right">
            <el-select v-model="currentLogType" placeholder="选择日志类型" @change="handleTypeChange" size="default">
              <el-option label="文件日志" value="file" />
              <el-option label="Docker日志" value="docker" />
              <el-option label="Podman日志" value="podman" />
              <el-option label="K8s日志" value="k8s" />
            </el-select>
            
            <el-button-group style="margin-left: 12px">
              <el-button :icon="Refresh" @click="refreshLogs" :disabled="!isConnected" size="default">刷新</el-button>
              <!-- 下载按钮组 -->
              <el-dropdown @command="handleDownload" trigger="click">
                <el-button :icon="Download" size="default">
                  下载 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
				
                <template #dropdown>
                  <el-dropdown-menu>
                    <template v-if="currentLogType === 'file'">
                      <el-dropdown-item command="full">下载全量文件</el-dropdown-item>
                      <el-dropdown-item command="current">下载当前日志</el-dropdown-item>
                    </template>
                    <template v-else>
                      <el-dropdown-item command="current">下载当前日志</el-dropdown-item>
                    </template>
                  </el-dropdown-menu>
                </template>
			</el-dropdown>
              
              <el-button 
                :type="isConnected ? 'danger' : 'success'" 
                :icon="isConnected ? VideoPause : VideoPlay"
                @click="toggleLogging"
                size="default"
              >
                {{ isConnected ? '停止' : '开始' }}
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>
      
      <div class="log-controls" v-if="currentLogType">
        <el-form :inline="true">
          <el-form-item label="显示行数">
            <el-input-number 
              v-model="linesToShow" 
              :min="10" 
              :max="1000" 
              @change="updateLogConfig"
              size="default"
            />
          </el-form-item>
          
          <el-form-item label="自动滚动" style="margin-left: 12px">
            <el-switch v-model="autoScroll" />
          </el-form-item>
          
          <el-form-item label="语法高亮" style="margin-left: 12px">
            <el-switch v-model="enableHighlight" />
          </el-form-item>
		  
          <!-- 新增：关键词过滤 -->
          <el-form-item label="关键词过滤" style="margin-left: 12px">
            <el-input 
              v-model="filterKeyword"
              placeholder="输入关键词过滤日志"
              style="width: 200px"
              size="default"
              clearable
              @clear="clearFilter"
              @keyup.enter="applyFilter"
            >         
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
        <template #append>
          <el-button @click="applyFilter" :type="filterActive ? 'primary' : 'default'">
            <el-icon><Filter /></el-icon>
          </el-button>
        </template>
      </el-input>
    </el-form-item>
    
    <!-- 过滤状态提示 -->
    <el-form-item v-if="filterActive" style="margin-left: 12px">
      <el-tag type="info" closable @close="clearFilter">
        过滤: {{ filterKeyword }} ({{ filteredCount }}/{{ originalLogLines.length }})
      </el-tag>
    </el-form-item>			
          <el-form-item v-if="currentLogType === 'file'" label="日志路径" class="log-path-input">
            <el-autocomplete
              v-model="logPath"
              :fetch-suggestions="querySearch"
              placeholder="/var/log/messages"
              style="width: 400px"
              size="default"
              clearable
              @select="handleSelectPath"
              @keyup.enter="handlePathEnter"
            >
                <template #default="{ item }">
                <div class="path-suggestion">
                  <div class="path-text">
                    <el-icon><Document /></el-icon>
                    <span>{{ item.value }}</span>
                  </div>
                  <div class="path-meta">
                    <span class="use-count">使用 {{ item.use_count }} 次</span>
                    <el-button 
                      type="danger" 
                      size="small" 
                      text 
                      @click.stop="deleteHistory(item.id)"
                      class="delete-btn"
                    >
                      删除
                    </el-button>
                  </div>
                </div>
              </template>
        </el-autocomplete>
            <el-button 
              v-if="logPathHistory.length > 0"
              type="danger" 
              text 
              size="small" 
              @click="clearAllHistory"
              style="margin-left: 8px"
            >
              清空历史
            </el-button>
          </el-form-item>
          
          <el-form-item v-if="currentLogType === 'docker'" label="选择容器">
            <el-select 
              v-model="selectedContainer" 
              placeholder="请选择容器"
              @change="handleContainerChange"
              style="width: 300px"
              size="default"
            >
              <el-option 
                v-for="container in dockerContainers" 
                :key="container.name"
                :label="container.name"
                :value="container.name"
              >
                <span>{{ container.name }}</span>
                <span style="float: right; color: #8492a6; font-size: 12px">
                  {{ container.status }}
                </span>
              </el-option>
            </el-select>
          </el-form-item>
          
          <el-form-item v-if="currentLogType === 'podman'" label="选择容器">
            <el-select 
              v-model="selectedContainer" 
              placeholder="请选择容器"
              @change="handleContainerChange"
              style="width: 300px"
              size="default"
            >
              <el-option 
                v-for="container in podmanContainers" 
                :key="container.name"
                :label="container.name"
                :value="container.name"
              >
                <span>{{ container.name }}</span>
                <span style="float: right; color: #8492a6; font-size: 12px">
                  {{ container.status }}
                </span>
              </el-option>
            </el-select>
          </el-form-item>
          
          <el-form-item v-if="currentLogType === 'k8s'" label="命名空间">
            <el-select 
              v-model="selectedNamespace" 
              placeholder="请选择命名空间"
              @change="loadK8sPods"
              style="width: 200px"
              size="default"
            >
              <el-option 
                v-for="ns in k8sNamespaces" 
                :key="ns"
                :label="ns"
                :value="ns"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item v-if="currentLogType === 'k8s'" label="Pod">
            <el-select 
              v-model="selectedPod" 
              placeholder="请选择Pod"
              @change="handleK8sChange"
              style="width: 300px"
              size="default"
            >
              <el-option 
                v-for="pod in k8sPods" 
                :key="pod"
                :label="pod"
                :value="pod"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      <!-- 提示信息放在顶部，在滚动区域之前 -->
      <div class="log-loading-top">
        <div v-if="isConnected && logLines.length === 0" class="loading-msg">
          <el-icon class="is-loading"><Loading /></el-icon>
          正在获取日志...
        </div>
        <div v-if="!isConnected && logLines.length === 0" class="loading-msg">
          <el-icon><InfoFilled /></el-icon>
          点击"开始"按钮查看日志
        </div>
      </div>	  
      <DynamicScroller
        ref="scroller"
        class="log-scroller"
        :items="logLines"
        :min-item-size="22"
        key-field="id"
        :emit-update="true"
      >
        <template v-slot="{ item, index, active }">
	
          <DynamicScrollerItem
            :item="item"
            :active="active"
            :size-dependencies="[item.text]"
            :data-index="index"
          >

            <div 
              class="log-line"
              v-html="enableHighlight ? highlightLine(item.text) : escapeHtml(item.text)"
            />
	
          </DynamicScrollerItem>

        </template>

      </DynamicScroller>   
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { ElMessage, ElLoading, ElMessageBox } from 'element-plus'
import { Document, Refresh, Download, VideoPlay, VideoPause, ArrowDown,Search, Filter } from '@element-plus/icons-vue'
import api, { downloadApi } from '../stores/api'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css'  // 使用 atom-one-dark 主题，适合深色背景
import { DynamicScroller, DynamicScrollerItem } from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'



const props = defineProps({
  host: {
    type: Object,
    required: true
  },
  logConfig: {
    type: Object,
    default: () => ({})
  }
})

// 监听 host 变化，重置所有状态
watch(() => props.host, (newHost, oldHost) => {
  console.log('主机切换:', oldHost?.id, '->', newHost?.id)
  
  if (newHost && (!oldHost || newHost.id !== oldHost.id)) {
    resetAllState()
  }
}, { immediate: false })







const emit = defineEmits(['close'])

const currentLogType = ref('file')
const logPath = ref('')
const linesToShow = ref(100)
const autoScroll = ref(true)
const enableHighlight = ref(true)

// 修改 logLines 为对象数组，用于虚拟滚动
const logLines = ref([])
let nextId = 0

// 添加日志行的函数
const addLogLine = (text) => {
  const newLine = { id: nextId++, text: text }
  
  // 保存到原始日志
  originalLogLines.value.push(newLine)
  
  // 如果正在过滤，只添加匹配的日志
  if (filterActive.value && filterKeyword.value) {
    const keyword = filterKeyword.value.toLowerCase()
    if (text.toLowerCase().includes(keyword)) {
      logLines.value.push(newLine)
      filteredCount.value++
    }
  } else {
    logLines.value.push(newLine)
  }
}



// 其他变量
const logPathHistory = ref([])
const dockerContainers = ref([])
const podmanContainers = ref([])
const selectedContainer = ref('')
const k8sNamespaces = ref([])
const k8sPods = ref([])
const selectedNamespace = ref('default')
const selectedPod = ref('')

const filterKeyword = ref('')
const filterActive = ref(false)
const originalLogLines = ref([])  // 原始日志行
const filteredCount = ref(0)



// WebSocket相关
let ws = null
const isConnected = ref(false)
const scroller = ref(null)


// 消息缓冲变量
let messageBuffer = ''  // 消息缓冲
let bufferTimer = null  // 缓冲定时器

const logPathInputRef = ref(null)

const logContainer = ref(null)


let userScrolled = false
let scrollTimer = null  // 添加这行

// 加载日志路径历史
const loadLogPathHistory = async () => {
  if (currentLogType.value === 'file') {
    try {
      const response = await api.get(`/hosts/${props.host.id}/log-history`)
      logPathHistory.value = response.data
    } catch (error) {
      console.error('加载历史路径失败:', error)
    }
  }
}

// 保存日志路径到历史
const saveLogPathHistory = async (path) => {
  if (!path || path.trim() === '') return
  
  try {
    await api.post(`/hosts/${props.host.id}/log-history`, null, {
      params: { log_path: path }
    })
    // 重新加载历史
    await loadLogPathHistory()
  } catch (error) {
    console.error('保存历史路径失败:', error)
  }
}

// 删除单条历史
const deleteHistory = async (historyId) => {
  try {
    await ElMessageBox.confirm('确定要删除这条历史记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete(`/hosts/${props.host.id}/log-history/${historyId}`)
    await loadLogPathHistory()
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 清空所有历史
const clearAllHistory = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有历史记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete(`/hosts/${props.host.id}/log-history`)
    await loadLogPathHistory()
    ElMessage.success('历史记录已清空')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清空失败')
    }
  }
}

// 搜索建议
const querySearch = (queryString, cb) => {
  const results = logPathHistory.value.map(item => ({
    value: item.log_path,
    id: item.id,
    use_count: item.use_count
  }))
  
  if (queryString) {
    const filtered = results.filter(item => 
      item.value.toLowerCase().includes(queryString.toLowerCase())
    )
    cb(filtered)
  } else {
    cb(results)
  }
}

// 选择历史路径
const handleSelectPath = (item) => {
  logPath.value = item.value
}

// 处理回车键
const handlePathEnter = () => {
  if (logPath.value && logPath.value.trim()) {
    saveLogPathHistory(logPath.value)
  }
}


const logTypeTag = computed(() => {
  const map = {
    file: 'info',
    docker: 'success',
    podman: 'warning',
    k8s: 'danger'
  }
  return map[currentLogType.value]
})

const getLogTypeName = () => {
  const map = {
    file: '文件日志',
    docker: 'Docker日志',
    podman: 'Podman日志',
    k8s: 'K8s日志'
  }
  return map[currentLogType.value]
}

// HTML 转义
const escapeHtml = (text) => {
/*   const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }
  return text.replace(/[&<>"']/g, (m) => map[m]) */
  return text;
}

// 使用 highlight.js 高亮单行
// 自定义关键词高亮（叠加在 highlight.js 之上）
const highlightLine = (line) => {
  if (!line) return ''
  
  // 先转义 HTML
  let escaped = escapeHtml(line)
  
  // 使用 highlight.js 进行基础语法高亮
  let highlighted = escaped
  try {
    const result = hljs.highlightAuto(escaped, ['accesslog', 'apache', 'nginx', 'json', 'shell'])
    highlighted = result.value
  } catch (e) {
    console.warn('高亮失败:', e)
    highlighted = escaped
  }
  
  // 自定义关键词高亮（错误、警告、成功等）
  const customKeywords = [
    { pattern: /\b(error|fail|failed|exception|fatal|critical|panic|err)\b/gi, class: 'hljs-error-keyword' },
    { pattern: /\b(warning|warn|alert)\b/gi, class: 'hljs-warning-keyword' },
    { pattern: /\b(success|done|completed|ok|succeeded|started)\b/gi, class: 'hljs-success-keyword' },
    { pattern: /\b(info|information|notice)\b/gi, class: 'hljs-info-keyword' }
  ]
  
  customKeywords.forEach(rule => {
    highlighted = highlighted.replace(rule.pattern, (match) => {
      return `<span class="${rule.class}">${match}</span>`
    })
  })
 

  // 添加关键词高亮
  if (filterActive.value && filterKeyword.value) {
    const keyword = filterKeyword.value
    const regex = new RegExp(`(${escapeRegex(keyword)})`, 'gi')
    highlighted = highlighted.replace(regex, '<mark class="keyword-highlight">$1</mark>')
  }
 
  return highlighted
}

// 处理完整的日志行（消息缓冲和重组）
const processCompleteLines = (data) => {
  const fullData = messageBuffer + data
  const lines = fullData.split(/\r?\n/)
  
  messageBuffer = lines.pop() || ''
  
  if (messageBuffer) {
    if (bufferTimer) clearTimeout(bufferTimer)
    bufferTimer = setTimeout(() => {
      if (messageBuffer) {
        addLogLine(messageBuffer)
        messageBuffer = ''
        scrollToBottom()
      }
      bufferTimer = null
    }, 500)
  } else if (bufferTimer) {
    clearTimeout(bufferTimer)
    bufferTimer = null
  }
  
  lines.forEach(line => {
    if (line !== undefined) {
      const lastLine = logLines.value[logLines.value.length - 1]
      if (!lastLine || lastLine.text !== line) {
        addLogLine(line)
      }
    }
  })
  
  if (autoScroll.value) {
    scrollToBottom()
  }
}

// 清空日志
const clearLogs = () => {
  logLines.value = []
  originalLogLines.value = []
  nextId = 0
  clearFilter()
}
// 滚动到底部函数
const scrollToBottom = () => {
  nextTick(() => {
    if (scroller.value) {
      // 滚动到底部
      scroller.value.scrollToBottom()
    }
  })
}


// 清空缓冲
const flushBuffer = () => {
  if (bufferTimer) {
    clearTimeout(bufferTimer)
    bufferTimer = null
  }
  if (messageBuffer && messageBuffer.trim()) {
    addLogLine(messageBuffer)
    messageBuffer = ''
  }
}

// 重置缓冲
const resetBuffer = () => {
  messageBuffer = ''
  if (bufferTimer) {
    clearTimeout(bufferTimer)
    bufferTimer = null
  }
}

// 获取本地时间字符串（YYYYMMDD_HHMMSS）
const getLocalTimestamp = () => {
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`
}

// 下载处理函数
const handleDownload = async (command) => {
  if (command === 'current') {
    downloadCurrentLog()
  } else if (command === 'full') {
    await downloadFullLog()
  }
}

// 下载全量文件（支持大文件自动压缩）
const downloadFullLog = async () => {
  // 检查是否为文件日志
  if (currentLogType.value !== 'file') {
    ElMessage.warning('仅支持下载文件日志')
    return
  }
  
  // 检查是否已输入日志路径
  if (!logPath.value) {
    ElMessage.warning('请输入日志路径')
    return
  }
  
  // 显示加载提示
  const loading = ElLoading.service({
    lock: true,
    text: '正在下载文件，请稍候...',
    background: 'rgba(0, 0, 0, 0.7)',
    spinner: 'el-icon-loading'
  })
  
  try {
    // 发起下载请求，使用 downloadApi 实例（responseType: 'blob'）
    const response = await downloadApi.get(`/hosts/${props.host.id}/download`, {
      params: { file_path: logPath.value },
      timeout: 300000, // 5分钟超时，适合大文件
      onDownloadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const percent = (progressEvent.loaded / progressEvent.total * 100).toFixed(0)
          loading.setText(`正在下载文件: ${percent}%`)
        }
      }
    })
    
    // 关闭加载提示
    loading.close()
    
    // 生成安全文件名（将路径中的斜杠替换为横线）
    const safePath = logPath.value.replace(/\//g, '-').replace(/^-/, '')
    const timestamp = getLocalTimestamp()
    
    // 获取响应内容类型
    const contentType = response.headers['content-type'] || response.headers['Content-Type']
    let filename
    
    // 根据内容类型决定文件扩展名
    if (contentType && contentType.includes('application/zip')) {
      // 压缩文件
      filename = `${props.host.host}_${safePath}_${timestamp}.zip`
    } else {
      // 普通文本文件
      filename = `${props.host.host}_full_${safePath}_${timestamp}.log`
    }
    
    // 创建 Blob 对象
    const blob = new Blob([response.data], { type: contentType || 'text/plain' })
    
    // 创建下载链接
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    
    // 清理
    setTimeout(() => {
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }, 100)
    
    // 显示成功消息
    const fileSize = (blob.size / 1024 / 1024).toFixed(2)
    if (contentType && contentType.includes('application/zip')) {
      ElMessage.success(`文件已压缩下载成功，压缩后大小: ${fileSize} MB`)
    } else {
      ElMessage.success(`文件下载成功，大小: ${fileSize} MB`)
    }
    
  } catch (error) {
    // 关闭加载提示
    loading.close()
    
    console.error('下载失败:', error)
    
    // 处理不同类型的错误
    let errorMsg = '下载失败'
    if (error.response) {
      // 服务器返回错误
      if (error.response.data instanceof Blob) {
        // 尝试读取 Blob 中的错误信息
        const text = await error.response.data.text()
        try {
          const json = JSON.parse(text)
          errorMsg = json.detail || errorMsg
        } catch {
          errorMsg = text || errorMsg
        }
      } else if (error.response.data?.detail) {
        errorMsg = error.response.data.detail
      }
    } else if (error.code === 'ECONNABORTED') {
      errorMsg = '下载超时，文件可能过大，请重试'
    } else if (error.message) {
      errorMsg = error.message
    }
    
    ElMessage.error(errorMsg)
  }
}

// 下载当前查看的日志（增量日志，支持所有类型）
const downloadCurrentLog = () => {
  if (logLines.value.length === 0) {
    ElMessage.warning('暂无日志内容')
    return
  }
  
  let filename = ''
  const timestamp = getLocalTimestamp()
  const hostName = props.host.host
  
  // 根据日志类型生成不同的文件名
  switch (currentLogType.value) {
    case 'file':
      const safePath = logPath.value.replace(/\//g, '-').replace(/^-/, '')
      filename = `${hostName}_realtime_${safePath}_${timestamp}.log`
      break
    case 'docker':
      const dockerName = selectedContainer.value || 'unknown'
      filename = `${hostName}_realtime_docker_${dockerName}_${timestamp}.log`
      break
    case 'podman':
      const podmanName = selectedContainer.value || 'unknown'
      filename = `${hostName}_realtime_podman_${podmanName}_${timestamp}.log`
      break
    case 'k8s':
      const k8sNamespace = selectedNamespace.value || 'default'
      const k8sPod = selectedPod.value || 'unknown'
      filename = `${hostName}_realtime_k8s_${k8sNamespace}_${k8sPod}_${timestamp}.log`
      break
    default:
      filename = `${hostName}_realtime_log_${timestamp}.log`
  }
  
  // 添加日志头信息
  const header = `# Ztailog 日志导出
# 主机: ${props.host.name} (${props.host.host})
# 日志类型: ${getLogTypeName()}
# 导出时间: ${new Date().toLocaleString()}
# 日志行数: ${logLines.value.length}
# ${'-'.repeat(60)}\n\n`
  
  const content = header + logLines.value.join('\n')
  
  // 下载文件
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  
  ElMessage.success(`当前日志下载成功，共 ${logLines.value.length} 行`)
}

const loadContainers = async () => {
  if (currentLogType.value === 'docker') {
    try {
      const response = await api.get(`/hosts/${props.host.id}/containers/docker`)
      dockerContainers.value = response.data
      if (dockerContainers.value.length > 0 && !selectedContainer.value) {
        selectedContainer.value = dockerContainers.value[0].name
      }
    } catch (error) {
      ElMessage.error('加载Docker容器失败')
    }
  } else if (currentLogType.value === 'podman') {
    try {
      const response = await api.get(`/hosts/${props.host.id}/containers/podman`)
      podmanContainers.value = response.data
      if (podmanContainers.value.length > 0 && !selectedContainer.value) {
        selectedContainer.value = podmanContainers.value[0].name
      }
    } catch (error) {
      ElMessage.error('加载Podman容器失败')
    }
  } else if (currentLogType.value === 'k8s') {
    try {
      const response = await api.get(`/hosts/${props.host.id}/containers/k8s`)
      k8sNamespaces.value = Object.keys(response.data)
      if (k8sNamespaces.value.length > 0) {
        selectedNamespace.value = k8sNamespaces.value[0]
        await loadK8sPods()
      }
    } catch (error) {
      ElMessage.error('加载K8s命名空间失败')
    }
  }
}

const loadK8sPods = async () => {
  try {
    const response = await api.get(`/hosts/${props.host.id}/containers/k8s`)
    k8sPods.value = response.data[selectedNamespace.value] || []
    if (k8sPods.value.length > 0 && !selectedPod.value) {
      selectedPod.value = k8sPods.value[0]
    }
  } catch (error) {
    ElMessage.error('加载K8s Pod失败')
  }
}

// 修改 startLogging 中的清空逻辑
const startLogging = () => {
  if (ws) {
    ws.close()
  }
  
  resetBuffer()
  clearLogs()  // 清空日志
  
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.hostname}:60501/ws/logs/${props.host.id}`
  
  ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    isConnected.value = true
    logLines.value = []
    resetBuffer()
    // 如果是文件日志，保存路径到历史
    if (currentLogType.value === 'file' && logPath.value) {
      saveLogPathHistory(logPath.value)
    }
    let message = {}
    if (currentLogType.value === 'file') {
      if (!logPath.value) {
        ElMessage.warning('请输入日志路径')
        ws.close()
        return
      }
      message = {
        type: 'file',
        path: logPath.value,
        lines: linesToShow.value
      }
    } else if (currentLogType.value === 'docker') {
      if (!selectedContainer.value) {
        ElMessage.warning('请选择容器')
        ws.close()
        return
      }
      message = {
        type: 'docker',
        container: selectedContainer.value,
        lines: linesToShow.value
      }
    } else if (currentLogType.value === 'podman') {
      if (!selectedContainer.value) {
        ElMessage.warning('请选择容器')
        ws.close()
        return
      }
      message = {
        type: 'podman',
        container: selectedContainer.value,
        lines: linesToShow.value
      }
    } else if (currentLogType.value === 'k8s') {
      if (!selectedNamespace.value || !selectedPod.value) {
        ElMessage.warning('请选择命名空间和Pod')
        ws.close()
        return
      }
      message = {
        type: 'k8s',
        namespace: selectedNamespace.value,
        pod: selectedPod.value,
        lines: linesToShow.value
      }
    }
    
    ws.send(JSON.stringify(message))
  }
  
  ws.onmessage = (event) => {
  // 确保数据是字符串格式
  let data
  try {
    data = JSON.parse(event.data)
  } catch (e) {
    console.error('解析消息失败:', e)
    return
  }
  
  if (data.type === 'log') {
    // 确保数据是 UTF-8 字符串
    let logData = data.data
    // 处理可能的编码问题
    if (typeof logData === 'string') {
      // 移除可能存在的 BOM 头
      if (logData.charCodeAt(0) === 0xFEFF) {
        logData = logData.slice(1)
      }
      processCompleteLines(logData)
    }
  }else if (data.type === 'heartbeat') {
   // 心跳消息，保持连接
  }else if (data.type === 'error') {
    console.error('服务器错误:', data.message)
    ElMessage.error(data.message)
	    // 如果是文件类型错误，自动停止
    if (data.message.includes('不是文本文件')) {
      stopLogging()
    }
  }
  else if (data.type === 'warning') {
    console.warn('服务器警告:', data.message)
    ElMessage.warning(data.message)
  }
  else if (data.type === 'started') {
    console.log('开始跟踪:', data.message)
    ElMessage.success(data.message)
  }else if (data.type === 'stopped') {
    console.log('停止跟踪:', data.message)
    ElMessage.info(data.message)
  }
  }
  
  ws.onclose = () => {
    isConnected.value = false
    // 连接关闭时清空缓冲
    flushBuffer()
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket错误:', error)
    ElMessage.error('WebSocket连接失败')
    isConnected.value = false
  }
}

const stopLogging = () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'stop' }))
    ws.close()
  }
  isConnected.value = false
  // 停止时清空缓冲
  flushBuffer()
}

const toggleLogging = () => {
  if (isConnected.value) {
    stopLogging()
  } else {
    startLogging()
  }
}

const refreshLogs = () => {
  if (isConnected.value) {
    stopLogging()
    setTimeout(() => {
      startLogging()
    }, 500)
  }
}

const updateLogConfig = async () => {
  try {
    await api.put(`/hosts/${props.host.id}/log-config/${currentLogType.value}`, {
      default_lines: linesToShow.value
    })
  } catch (error) {
    console.error('更新配置失败', error)
  }
  
  if (isConnected.value) {
    refreshLogs()
  }
}

const handleTypeChange = () => {
  console.log('日志类型切换:', currentLogType.value)	
  if (isConnected.value) {
    stopLogging()
  }
  clearLogs()
  resetBuffer()
  loadContainers()
  linesToShow.value = props.logConfig[currentLogType.value] || 100
  if (currentLogType.value === 'file') {
    loadLogPathHistory()
  }
  // 如果是 Docker/Podman，清空之前的容器选择
  if (currentLogType.value === 'docker' || currentLogType.value === 'podman') {
    selectedContainer.value = ''
  }
  
  // 如果是 K8s，重置命名空间和 Pod
  if (currentLogType.value === 'k8s') {
    selectedNamespace.value = 'default'
    selectedPod.value = ''
  }  
}


const handleContainerChange = () => {
  if (isConnected.value) {
    refreshLogs()
  }
}

const handleK8sChange = () => {
  if (isConnected.value) {
    refreshLogs()
  }
}

// 重置所有状态的函数
const resetAllState = () => {
  console.log('重置所有状态')
  
  // 停止当前连接
  if (ws && ws.readyState === WebSocket.OPEN) {
    stopLogging()
  }
  
  // 重置日志类型
  currentLogType.value = 'file'
  
  // 重置文件日志相关
  logPath.value = ''
  
  // 重置容器相关
  selectedContainer.value = ''
  dockerContainers.value = []
  podmanContainers.value = []
  
  // 重置 K8s 相关
  selectedNamespace.value = 'default'
  selectedPod.value = ''
  k8sNamespaces.value = []
  k8sPods.value = []
  
  // 清空日志行
  logLines.value = []
  
  // 重置连接状态
  isConnected.value = false
  
  // 重置缓冲
  resetBuffer()
  
  // 加载新主机的配置
  if (currentLogType.value === 'file') {
    loadLogPathHistory()
  }
  loadContainers()
  linesToShow.value = props.logConfig[currentLogType.value] || 100
}


// 过滤函数
const applyFilter = () => {
  if (!filterKeyword.value || filterKeyword.value.trim() === '') {
    clearFilter()
    return
  }
  
  filterActive.value = true
  const keyword = filterKeyword.value.toLowerCase()
  
  // 过滤日志行
  const filtered = originalLogLines.value.filter(line => {
    const text = typeof line === 'string' ? line : line.text
    return text.toLowerCase().includes(keyword)
  })
  
  filteredCount.value = filtered.length
  
  // 更新显示
  if (logLines.value.length > 0 && typeof logLines.value[0] === 'object') {
    // 对象数组格式
    logLines.value = filtered
  } else {
    // 字符串数组格式
    logLines.value = filtered
  }
  
  if (filtered.length === 0) {
    ElMessage.info('没有找到包含关键词的日志')
  } else {
    ElMessage.success(`找到 ${filtered.length} 条匹配的日志`)
  }
}

// 清除过滤
const clearFilter = () => {
  filterActive.value = false
  filterKeyword.value = ''
  
  // 恢复原始日志
  if (originalLogLines.value.length > 0) {
    logLines.value = [...originalLogLines.value]
  }
  
  filteredCount.value = 0
  ElMessage.info('已清除过滤')
}

// 高亮关键词（在已有高亮基础上添加）
const highlightKeyword = (text, keyword) => {
  if (!keyword || !filterActive.value) return text
  
  const regex = new RegExp(`(${escapeRegex(keyword)})`, 'gi')
  return text.replace(regex, '<mark class="keyword-highlight">$1</mark>')
}

// 转义正则表达式特殊字符
const escapeRegex = (str) => {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

onMounted(() => {
  linesToShow.value = props.logConfig.file || 100
  loadContainers()
  if (currentLogType.value === 'file') {
    loadLogPathHistory()
  }
  watch(logLines, () => {
  if (autoScroll.value && isConnected.value) {
    // 使用多次 nextTick 确保 DOM 完全更新
    nextTick(() => {
      if (logContainer.value) {
        logContainer.value.scrollTop = logContainer.value.scrollHeight
      }
      // 第二次确保，处理异步渲染
      setTimeout(() => {
        if (logContainer.value && autoScroll.value) {
          logContainer.value.scrollTop = logContainer.value.scrollHeight
        }
      }, 50)
    })
  }
}, { deep: false })
  
  
  
})

onUnmounted(() => {
  console.log('LogViewer 卸载，清理资源')	
  if (ws) {
    ws.close()
  }
  resetBuffer()
  // 移除事件监听
  if (logContainer.value) {
    logContainer.value.removeEventListener('scroll', handleScroll)
  }
  if (scrollTimer) {
    clearTimeout(scrollTimer)
  }  
})



watch(currentLogType, handleTypeChange)
</script>

<style scoped>
.log-viewer {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.log-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.log-card :deep(.el-card__header) {
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  padding: 16px 20px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.host-name {
  font-weight: bold;
  font-size: 16px;
  color: #1f2937;
}

.header-right {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.log-controls {
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.log-controls :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 16px;
}

.log-scroller {
  flex: 1;
  min-height: 0;  /* 关键：允许 flex 子元素收缩 */
  height: 100%;
  background: #1e1e1e;
}

.log-content {
  flex: 1;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 0 0 12px 12px;

}

.log-line {
  padding: 2px 12px;
  border-bottom: 1px solid #2d2d2d;
  font-family: 'Courier New', 'Monaco', monospace;
  font-size: 12px;
  white-space: pre-wrap;      /* 改为 pre-wrap，允许自动换行 */
  word-wrap: break-word;      /* 长单词换行 */
  word-break: break-all;      /* 强制换行 */
  overflow-x: hidden;         /* 隐藏水平滚动条 */
  background: transparent;
  color: #abb2bf;
  line-height: 1.4;           /* 增加行高，让换行后更易读 */
}


.log-line:hover {
  background: #2d2d2d;
}

.log-loading {
  padding: 20px;
  text-align: center;
  color: #9ca3af;
  font-style: italic;
  background: #1e1e1e;
}
/* 确保 highlight.js 样式覆盖正确 */
.log-line :deep(.hljs) {
  background: transparent;
  padding: 0;
  color: #abb2bf;
}
/* highlight.js 样式覆盖 - 适配深色背景 */
.log-line :deep(.hljs-keyword),
.log-line :deep(.hljs-literal),
.log-line :deep(.hljs-symbol),
.log-line :deep(.hljs-name) {
  color: #c678dd;
}

.log-line :deep(.hljs-string),
.log-line :deep(.hljs-doctag) {
  color: #98c379;
}

.log-line :deep(.hljs-number),
.log-line :deep(.hljs-regexp),
.log-line :deep(.hljs-link) {
  color: #d19a66;
}

.log-line :deep(.hljs-comment),
.log-line :deep(.hljs-quote) {
  color: #5c6370;
  font-style: italic;
}


.log-line :deep(.hljs-meta) {
  color: #e5c07b;
}

.log-line :deep(.hljs-title),
.log-line :deep(.hljs-section),
.log-line :deep(.hljs-selector-id) {
  color: #e5c07b;
}

.log-line :deep(.hljs-attr),
.log-line :deep(.hljs-variable),
.log-line :deep(.hljs-template-variable),
.log-line :deep(.hljs-type) {
  color: #e06c75;
}

.log-line :deep(.hljs-built_in),
.log-line :deep(.hljs-builtin-name) {
  color: #56b6c2;
}

.log-line :deep(.hljs-tag) {
  color: #e06c75;
}

/* 错误、警告等关键词自定义高亮 - 叠加在 highlight.js 之上 */
/* 自定义关键词高亮 */
.log-line :deep(.hljs-error-keyword) {
  color: #e06c75;
  font-weight: bold;
  background-color: rgba(224, 108, 117, 0.15);
  border-radius: 3px;
  padding: 0 2px;
}

.log-line :deep(.hljs-warning-keyword) {
  color: #e5c07b;
  font-weight: bold;
  background-color: rgba(229, 192, 123, 0.15);
  border-radius: 3px;
  padding: 0 2px;
}

.log-line :deep(.hljs-success-keyword) {
  color: #98c379;
  font-weight: bold;
  background-color: rgba(152, 195, 121, 0.15);
  border-radius: 3px;
  padding: 0 2px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .log-controls :deep(.el-form-item) {
    margin-bottom: 12px;
    width: 100%;
  }
  
  .log-controls :deep(.el-input),
  .log-controls :deep(.el-select) {
    width: 100% !important;
  }
  
  .header-right {
    width: 100%;
    justify-content: flex-start;
  }
}

/* 添加历史路径相关样式 */
.log-path-input {
  min-width: 450px;
}

.path-suggestion {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 4px 0;
}

.path-text {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  overflow: hidden;
}

.path-text .el-icon {
  flex-shrink: 0;
}

.path-text span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: monospace;
  font-size: 12px;
}

.path-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.use-count {
  font-size: 11px;
  color: #909399;
}

.delete-btn {
  font-size: 12px;
  padding: 0 4px;
}

.delete-btn:hover {
  color: #f56c6c;
}

/* 自动完成下拉框样式 */
:deep(.el-autocomplete-suggestion) {
  max-height: 300px;
  overflow-y: auto;
}

:deep(.el-autocomplete-suggestion li) {
  padding: 8px 12px;
}

:deep(.el-autocomplete-suggestion li:hover) {
  background-color: #f5f7fa;
}
/* 顶部提示信息 */
.log-loading-top {
  background: #1e1e1e;
  border-bottom: 1px solid #2d2d2d;
  flex-shrink: 0;
}

.loading-msg {
  padding: 12px 20px;
  text-align: center;
  color: #9ca3af;
  font-style: italic;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
}

.loading-msg .el-icon {
  font-size: 16px;
}


/* 关键词高亮样式 */
.keyword-highlight {
  background-color: #ffeb3b;
  color: #000000;
  font-weight: bold;
  padding: 0 2px;
  border-radius: 3px;
}

/* 过滤输入框样式 */
.el-input-group__append .el-button {
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
}
/* 过滤状态标签 */
.el-tag {
  cursor: pointer;
}

</style>