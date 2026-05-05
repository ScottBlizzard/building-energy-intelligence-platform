<script setup>
// EmptyState.vue - 空状态展示组件
// 用途：当数据为空或不可用时的友好提示界面
// 特点：
// - 可自定义图标、标题和描述
// - 支持可选的操作按钮
// - 响应式设计，适配移动端
// - 提供视觉反馈，改善用户体验

defineProps({
  icon: {
    type: String,
    default: '📭'
  },
  title: {
    type: String,
    default: '暂无数据'
  },
  description: {
    type: String,
    default: '当前没有可用的数据'
  },
  actionText: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['action']);
</script>

<template>
  <div class="empty-state">
    <div class="empty-icon">{{ icon }}</div>
    <h3 class="empty-title">{{ title }}</h3>
    <p class="empty-description">{{ description }}</p>
    <button 
      v-if="actionText" 
      class="primary-button" 
      type="button"
      @click="$emit('action')"
    >
      {{ actionText }}
    </button>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  min-height: 200px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.8;
}

.empty-title {
  margin: 0 0 8px;
  font-size: 18px;
  color: var(--ink-strong);
}

.empty-description {
  margin: 0 0 16px;
  color: var(--ink-soft);
  font-size: 14px;
  max-width: 300px;
}

.primary-button {
  border: 0;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--accent), var(--accent-deep));
  color: white;
  padding: 10px 16px;
  font: inherit;
  cursor: pointer;
  font-size: 14px;
}
</style>