<template>
  <div class="host-manager">
    <div class="host-list-container">
      <div 
        v-for="host in hosts" 
        :key="host.id" 
        class="host-item"
        :class="{ 'active': selectedHostId === host.id }"
        @click="$emit('select-host', host)"
      >
        <div class="host-icon">
          <el-icon :size="24"><Monitor /></el-icon>
        </div>
        <div class="host-info">
          <div class="host-name">{{ host.name }}</div>
          <div class="host-details">
            <span class="host-address">{{ host.host }}:{{ host.port }}</span>
            <span class="host-user">{{ host.username }}</span>
          </div>
        </div>
        <el-dropdown @command="(cmd) => handleCommand(cmd, host)" trigger="click">
          <el-button :icon="MoreFilled" circle size="small" class="more-btn" @click.stop />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="edit">编辑</el-dropdown-item>
              <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      
      <div v-if="hosts.length === 0" class="empty-hosts">
        <el-empty description="暂无主机" :image-size="80" />
        <p class="empty-tip">点击上方按钮添加主机</p>
      </div>
    </div>
    
    <!-- 编辑主机对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑主机"
      width="500px"
    >
      <el-form :model="editingHost" :rules="hostRules" ref="editForm" label-width="100px">
        <el-form-item label="主机名称" prop="name">
          <el-input v-model="editingHost.name" />
        </el-form-item>
        
        <el-form-item label="主机地址" prop="host">
          <el-input v-model="editingHost.host" />
        </el-form-item>
        
        <el-form-item label="端口" prop="port">
          <el-input-number v-model="editingHost.port" :min="1" :max="65535" />
        </el-form-item>
        
        <el-form-item label="用户名" prop="username">
          <el-input v-model="editingHost.username" />
        </el-form-item>
        
        <el-form-item label="密码">
          <el-input v-model="editingHost.password" type="password" placeholder="留空表示不修改" />
        </el-form-item>
        
        <el-form-item label="私钥">
          <el-input 
            v-model="editingHost.private_key" 
            type="textarea" 
            :rows="4"
            placeholder="留空表示不修改"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="updateHost">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Monitor, MoreFilled } from '@element-plus/icons-vue'
import api from '../stores/api'

const props = defineProps({
  hosts: {
    type: Array,
    required: true
  },
  selectedHostId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['select-host', 'delete-host', 'refresh'])

const showEditDialog = ref(false)
const editingHost = ref({})

const hostRules = {
  name: [{ required: true, message: '请输入主机名称', trigger: 'blur' }],
  host: [{ required: true, message: '请输入主机地址', trigger: 'blur' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }]
}

const handleCommand = (command, host) => {
  if (command === 'edit') {
    editingHost.value = { ...host, password: '', private_key: '' }
    showEditDialog.value = true
  } else if (command === 'delete') {
    ElMessageBox.confirm(
      `确定要删除主机 "${host.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).then(() => {
      emit('delete-host', host.id)
    }).catch(() => {})
  }
}

const updateHost = async () => {
  try {
    const updateData = {}
    if (editingHost.value.name) updateData.name = editingHost.value.name
    if (editingHost.value.host) updateData.host = editingHost.value.host
    if (editingHost.value.port) updateData.port = editingHost.value.port
    if (editingHost.value.username) updateData.username = editingHost.value.username
    if (editingHost.value.password) updateData.password = editingHost.value.password
    if (editingHost.value.private_key) updateData.private_key = editingHost.value.private_key
    
    await api.put(`/hosts/${editingHost.value.id}`, updateData)
    ElMessage.success('更新成功')
    showEditDialog.value = false
    emit('refresh')
  } catch (error) {
    ElMessage.error('更新失败')
  }
}
</script>

<style scoped>
.host-manager {
  height: 100%;
}

.host-list-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.host-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid transparent;
  position: relative;
}

.host-item:hover {
  background: rgba(96, 165, 250, 0.1);
  transform: translateX(4px);
  border-color: rgba(96, 165, 250, 0.3);
}

.host-item.active {
  background: rgba(96, 165, 250, 0.2);
  border-color: #60a5fa;
  box-shadow: 0 2px 8px rgba(96, 165, 250, 0.2);
}

.host-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(96, 165, 250, 0.1);
  border-radius: 8px;
  color: #60a5fa;
}

.host-info {
  flex: 1;
  min-width: 0;
}

.host-name {
  font-weight: 600;
  font-size: 14px;
  color: #e2e8f0;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.host-details {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: #94a3b8;
}

.host-address,
.host-user {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.host-address {
  flex: 1;
}

.more-btn {
  flex-shrink: 0;
  background: transparent;
  border: none;
  color: #94a3b8;
}

.more-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #e2e8f0;
}

.empty-hosts {
  padding: 40px 20px;
  text-align: center;
}

.empty-tip {
  margin-top: 12px;
  font-size: 12px;
  color: #94a3b8;
}
</style>