<script setup>
const props = defineProps({
  citation: {
    type: Object,
    required: true
  },
  compact: {
    type: Boolean,
    default: false
  }
});

const getFileIcon = (path) => {
  if (path.includes('manuals')) return "📖";
  if (path.includes('faq')) return "❓";
  if (path.includes('glossary')) return "📚";
  return "📄";
};

const getFileType = (path) => {
  if (path.includes('manuals')) return "操作手册";
  if (path.includes('faq')) return "常见问题";
  if (path.includes('glossary')) return "术语解释";
  return "文档";
};

const truncateTitle = (title, maxLength = 30) => {
  return title.length > maxLength ? title.slice(0, maxLength) + "..." : title;
};
</script>

<template>
  <div class="citation-card" :class="{ 'citation-card--compact': compact }">
    <div class="citation-header">
      <span class="citation-icon">{{ getFileIcon(citation.path) }}</span>
      <div class="citation-info">
        <div class="citation-title" :title="citation.title">
          {{ truncateTitle(citation.title) }}
        </div>
        <div class="citation-type">{{ getFileType(citation.path) }}</div>
      </div>
    </div>
    <div class="citation-path" :title="citation.path">
      {{ citation.path }}
    </div>
    <div v-if="!compact" class="citation-actions">
      <a 
        :href="`/${citation.path}`" 
        target="_blank" 
        class="citation-link"
        @click.stop
      >
        查看原文
      </a>
    </div>
  </div>
</template>

<style scoped>
.citation-card {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  padding: 12px 16px;
  margin: 8px 0;
  transition: all 0.3s ease;
  cursor: pointer;
}

.citation-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: rgba(84, 112, 198, 0.3);
}

.citation-card--compact {
  padding: 8px 12px;
  margin: 4px 0;
}

.citation-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.citation-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.citation-info {
  flex: 1;
  min-width: 0;
}

.citation-title {
  font-weight: 500;
  font-size: 14px;
  color: #2c3e50;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.citation-type {
  font-size: 12px;
  color: #7f8c8d;
}

.citation-path {
  font-size: 11px;
  color: #95a5a6;
  font-family: monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 8px;
}

.citation-actions {
  display: flex;
  gap: 8px;
}

.citation-link {
  font-size: 12px;
  color: #5470c6;
  text-decoration: none;
  padding: 4px 8px;
  border: 1px solid #5470c6;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.citation-link:hover {
  background: #5470c6;
  color: white;
}

@media (max-width: 768px) {
  .citation-card {
    padding: 10px 12px;
  }
  
  .citation-header {
    gap: 8px;
  }
  
  .citation-icon {
    font-size: 18px;
  }
  
  .citation-title {
    font-size: 13px;
  }
}
</style>