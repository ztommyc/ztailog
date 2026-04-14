<template>
  <div class="app-container">
    <el-container class="main-container">
      <!-- 左侧主机列表区域 -->
      <el-aside :width="sidebarWidth" class="sidebar" ref="sidebarRef">
        <div class="sidebar-header">
          <div class="logo">
            <el-icon :size="28"><Monitor /></el-icon>
            <h2>Ztailog</h2>
          </div>
          <el-button type="primary" size="small" @click="showAddHost = true" class="add-host-btn">
            <el-icon><Plus /></el-icon>
            添加主机
          </el-button>
        </div>
        
        <div class="host-list">
          <host-manager 
            :hosts="hosts" 
            :selected-host-id="selectedHost?.id"
            @select-host="handleSelectHost"
            @delete-host="handleDeleteHost"
            @refresh="loadHosts"
          />
        </div>
        <!-- 底部添加仓库链接 -->
        <div class="sidebar-footer">
          <div class="repo-links">
            <a href="https://gitee.com/ztommy/ztailog.git" target="_blank" class="repo-link">
              <el-icon><Connection /></el-icon>
              Gitee
            </a>
            <a href="https://github.com/ztommyc/ztailog.git" target="_blank" class="repo-link">
              <el-icon><Connection /></el-icon>
              GitHub
            </a>
          </div>
          <div class="version">v1.0.0</div>
        </div>		
		
      </el-aside>
      
      <!-- 拖拽条 -->
      <div 
        class="resize-handle"
        @mousedown="startResize"
        :class="{ 'resizing': isResizing }"
      >
        <div class="resize-line"></div>
      </div>
      
      <!-- 右侧内容区域 -->
      <el-main class="content-area">
        <log-viewer
          v-if="selectedHost"
          :host="selectedHost"
          :log-config="logConfig"
          @close="selectedHost = null"
        />
        <div v-else class="empty-state">
          <el-empty description="请从左侧选择一台主机查看日志" />
        </div>
      </el-main>
    </el-container>
    
    <!-- 添加主机对话框 -->
    <el-dialog
      v-model="showAddHost"
      title="添加SSH主机"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="newHost" :rules="hostRules" ref="hostForm" label-width="100px">
        <el-form-item label="主机名称" prop="name">
          <el-input v-model="newHost.name" placeholder="例如：生产服务器-01" />
        </el-form-item>
        
        <el-form-item label="主机地址" prop="host">
          <el-input v-model="newHost.host" placeholder="192.168.1.100" />
        </el-form-item>
        
        <el-form-item label="端口" prop="port">
          <el-input-number v-model="newHost.port" :min="1" :max="65535" />
        </el-form-item>
        
        <el-form-item label="用户名" prop="username">
          <el-input v-model="newHost.username" placeholder="root" />
        </el-form-item>
        
        <el-form-item label="密码">
          <el-input v-model="newHost.password" type="password" placeholder="密码（与密钥二选一）" />
        </el-form-item>
        
        <el-form-item label="私钥">
          <el-input 
            v-model="newHost.private_key" 
            type="textarea" 
            :rows="4"
            placeholder="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddHost = false">取消</el-button>
        <el-button type="primary" @click="addHost">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Monitor, Plus, Connection } from '@element-plus/icons-vue'
import HostManager from './components/HostManager.vue'
import LogViewer from './components/LogViewer.vue'
import api from './stores/api'

const hosts = ref([])
const selectedHost = ref(null)
const logConfig = ref({})
const showAddHost = ref(false)
const sidebarRef = ref(null)

// 侧边栏宽度控制
const sidebarWidth = ref('20%')
const minWidth = 200  // 最小宽度 200px
const maxWidthPercent = 40  // 最大宽度 40%
const isResizing = ref(false)

const newHost = ref({
  name: '',
  host: '',
  port: 22,
  username: '',
  password: '',
  private_key: ''
})

const hostRules = {
  name: [{ required: true, message: '请输入主机名称', trigger: 'blur' }],
  host: [{ required: true, message: '请输入主机地址', trigger: 'blur' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }]
}

const loadHosts = async () => {
  try {
    const response = await api.get('/hosts')
    hosts.value = response.data
  } catch (error) {
    ElMessage.error('加载主机列表失败')
  }
}

const handleSelectHost = async (host) => {
  // 先重置状态
  selectedHost.value = null
  // 等待 Vue 更新
  await nextTick()
  selectedHost.value = host
  try {
    const response = await api.get(`/hosts/${host.id}/log-config`)
    logConfig.value = response.data
  } catch (error) {
    console.error('加载日志配置失败', error)
  }
}

const handleDeleteHost = async (hostId) => {
  try {
    await api.post(`/hosts/${hostId}/delete`)
    ElMessage.success('删除成功')
    await loadHosts()
    if (selectedHost.value?.id === hostId) {
      selectedHost.value = null
    }
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const addHost = async () => {
  try {
    await api.post('/hosts', newHost.value)
    ElMessage.success('添加成功')
    showAddHost.value = false
    newHost.value = {
      name: '',
      host: '',
      port: 22,
      username: '',
      password: '',
      private_key: ''
    }
    await loadHosts()
  } catch (error) {
    ElMessage.error('添加失败')
  }
}

// 拖拽调整宽度功能
const startResize = (e) => {
  e.preventDefault()
  isResizing.value = true
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

const handleResize = (e) => {
  if (!isResizing.value) return
  
  const containerWidth = document.querySelector('.main-container').offsetWidth
  const newWidth = e.clientX
  
  // 计算百分比
  let percent = (newWidth / containerWidth) * 100
  
  // 限制最小和最大宽度
  const minPercent = (minWidth / containerWidth) * 100
  if (percent < minPercent) percent = minPercent
  if (percent > maxWidthPercent) percent = maxWidthPercent
  
  sidebarWidth.value = `${percent}%`
}

const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  
  // 保存宽度到 localStorage
  localStorage.setItem('sidebarWidth', sidebarWidth.value)
}

// 加载保存的宽度
const loadSavedWidth = () => {
  const savedWidth = localStorage.getItem('sidebarWidth')
  if (savedWidth) {
    sidebarWidth.value = savedWidth
  }
}

onMounted(() => {
  loadHosts()
  loadSavedWidth()
})

onUnmounted(() => {
  if (isResizing.value) {
    stopResize()
  }
})
</script>

<style scoped>
.app-container {
  height: 100vh;
  overflow: hidden;
}

.main-container {
  height: 100%;
  position: relative;
}

.sidebar {
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  color: #e2e8f0;
  display: flex;
  flex-direction: column;
  border-right: none;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  transition: width 0.1s ease;
}

.sidebar-header {
  padding: 20px 16px;
  border-bottom: 1px solid #334155;
  margin-bottom: 16px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.logo .el-icon {
  color: #60a5fa;
}

.logo h2 {
  margin: 0;
  font-size: 20px;
  background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 600;
}

.add-host-btn {
  width: 100%;
  background: rgba(96, 165, 250, 0.2);
  border-color: #60a5fa;
  color: #60a5fa;
}

.add-host-btn:hover {
  background: rgba(96, 165, 250, 0.3);
  border-color: #60a5fa;
  color: #60a5fa;
}

.host-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px 16px 16px;
}

/* 拖拽条样式 */
.resize-handle {
  position: relative;
  width: 6px;
  cursor: col-resize;
  background: transparent;
  transition: background 0.2s ease;
  z-index: 10;
}

.resize-handle:hover {
  background: #60a5fa;
}

.resize-handle.resizing {
  background: #60a5fa;
}

.resize-line {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: 100%;
  background: #cbd5e1;
  transition: all 0.2s ease;
}

.resize-handle:hover .resize-line {
  background: #60a5fa;
  width: 3px;
}

.resize-handle.resizing .resize-line {
  background: #60a5fa;
  width: 3px;
}

.content-area {
  background: #f8fafc;
  padding: 20px;
  overflow-y: auto;
  height: 100%;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

/* 自定义滚动条 */
.sidebar::-webkit-scrollbar {
  width: 6px;
}

.sidebar::-webkit-scrollbar-track {
  background: #1e293b;
}

.sidebar::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 3px;
}

.sidebar::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .resize-handle {
    display: none;
  }
  
  .sidebar {
    position: absolute;
    z-index: 1000;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    width: 280px !important;
  }
  
  .sidebar.open {
    transform: translateX(0);
  }
}

/* 添加底部样式 */
.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #334155;
  margin-top: auto;
}

.repo-links {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 8px;
}

.repo-link {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #94a3b8;
  text-decoration: none;
  font-size: 12px;
  transition: color 0.2s;
}

.repo-link:hover {
  color: #60a5fa;
}

.version {
  text-align: center;
  color: #475569;
  font-size: 11px;
}
</style>