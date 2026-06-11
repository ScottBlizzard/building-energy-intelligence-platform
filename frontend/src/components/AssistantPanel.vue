<script setup>
import { computed, ref } from "vue";
import CitationCard from "./CitationCard.vue";

const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  },
  reply: {
    type: Object,
    default: null
  },
  suggestions: {
    type: Array,
    default: () => []
  },
  modelOptions: {
    type: Array,
    default: () => []
  },
  selectedModelKey: {
    type: String,
    default: ""
  },
  llmEnabled: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(["ask", "update:selectedModelKey"]);
const question = ref("科研实验楼D哪一层异常最多？");
const configuredModelOptions = computed(() =>
  props.modelOptions.filter((item) => item.configured)
);
const selectedModelLabel = computed(() => {
  const match = props.modelOptions.find((item) => modelKey(item) === props.selectedModelKey);
  return match?.label || "本地规则问答";
});
const sourceBadges = computed(() => {
  if (!props.reply) {
    return [];
  }
  const badges = [];
  const sources = props.reply.grounding_sources || [];
  if (props.reply.grounding_used || sources.includes("work_orders")) {
    badges.push({ key: "work_orders", label: "基于实时工单数据回答", tone: "success" });
  }
  if (sources.includes("knowledge_base") || props.reply.citations?.length) {
    badges.push({ key: "knowledge_base", label: "基于知识库回答", tone: "info" });
  }
  if (props.reply.llm_used || sources.includes("external_llm")) {
    badges.push({ key: "external_llm", label: "外部模型增强", tone: "model" });
  }
  if (props.reply.grounding_status === "fallback_after_validation") {
    badges.push({ key: "fallback", label: "校验失败已降级", tone: "warning" });
  }
  return badges;
});
const referencedEntityText = computed(() => {
  const entities = props.reply?.referenced_entities || {};
  const parts = [];
  if (entities.work_order_ids?.length) {
    parts.push(`工单 ${entities.work_order_ids.join("、")}`);
  }
  if (entities.equipment_ids?.length) {
    parts.push(`设备 ${entities.equipment_ids.join("、")}`);
  }
  if (entities.statuses?.length) {
    parts.push(`状态 ${entities.statuses.join("、")}`);
  }
  return parts.join(" · ");
});

function modelKey(option) {
  return `${option.provider}::${option.model}`;
}

function submit() {
  if (!question.value.trim()) {
    return;
  }
  emit("ask", question.value.trim());
}

function useSuggestion(value) {
  question.value = value;
  emit("ask", value);
}

function askFollowUp(value) {
  useSuggestion(value);
}

function updateModel(event) {
  emit("update:selectedModelKey", event.target.value);
}
</script>

<template>
  <div class="assistant-panel">
    <div class="assistant-input">
      <div class="model-selector-row">
        <label class="model-selector">
          <span>问答模型</span>
          <select
            :value="selectedModelKey"
            :disabled="loading || !llmEnabled || !configuredModelOptions.length"
            @change="updateModel"
          >
            <option value="">本地规则问答</option>
            <option
              v-for="item in configuredModelOptions"
              :key="modelKey(item)"
              :value="modelKey(item)"
            >
              {{ item.label }}
            </option>
          </select>
        </label>
        <span class="model-status" :class="{ 'model-status--online': llmEnabled && configuredModelOptions.length }">
          {{ llmEnabled && configuredModelOptions.length ? "外部模型可用" : "本地兜底" }}
        </span>
      </div>
      <textarea
        v-model="question"
        rows="3"
        placeholder="输入一个与能耗、COP、异常、建筑列表有关的问题"
      />
      <button class="primary-button" type="button" :disabled="loading" @click="submit">
        {{ loading ? "回答中..." : "发送问题" }}
      </button>
    </div>

    <div class="suggestion-list">
      <button
        v-for="item in suggestions"
        :key="item"
        type="button"
        class="suggestion-chip"
        @click="useSuggestion(item)"
      >
        {{ item }}
      </button>
    </div>

    <div v-if="reply" class="assistant-reply">
      <div class="reply-header">
        <h3>系统回答</h3>
        <span class="reply-model">
          {{ reply.llm_used ? `外部模型：${selectedModelLabel}` : "本地规则问答" }}
        </span>
      </div>
      <div v-if="sourceBadges.length" class="source-badge-row">
        <span
          v-for="badge in sourceBadges"
          :key="badge.key"
          class="source-badge"
          :class="`source-badge--${badge.tone}`"
        >
          {{ badge.label }}
        </span>
      </div>
      <p v-if="referencedEntityText" class="entity-line">{{ referencedEntityText }}</p>
      <div v-if="reply.validation_warnings?.length" class="validation-warning">
        <strong>回答校验</strong>
        <span v-for="item in reply.validation_warnings" :key="item">{{ item }}</span>
      </div>
      <p>{{ reply.answer }}</p>

      <div v-if="reply.citations?.length" class="citation-section">
        <h4 class="citation-title">引用来源</h4>
        <div class="citation-cards">
          <CitationCard 
            v-for="citation in reply.citations" 
            :key="`${citation.title}-${citation.path}`"
            :citation="citation"
          />
        </div>
      </div>

      <div v-if="reply.follow_up?.length" class="citation-block">
        <strong>建议继续提问</strong>
        <div class="follow-up-list">
          <button
            v-for="item in reply.follow_up"
            :key="item"
            type="button"
            class="suggestion-chip"
            @click="askFollowUp(item)"
          >
            {{ item }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.assistant-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.assistant-input {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.model-selector-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.model-selector {
  display: grid;
  gap: 6px;
  min-width: min(100%, 320px);
}

.model-selector span {
  color: #48606b;
  font-size: 12px;
  font-weight: 600;
}

.model-selector select {
  min-height: 38px;
  border: 1px solid rgba(18, 93, 115, 0.18);
  border-radius: 6px;
  color: #183642;
  background: #fff;
  padding: 0 10px;
  font: inherit;
}

.model-status,
.reply-model {
  border: 1px solid rgba(18, 93, 115, 0.14);
  border-radius: 999px;
  color: #6b7f86;
  background: rgba(255, 255, 255, 0.84);
  font-size: 12px;
  padding: 6px 10px;
}

.model-status--online {
  color: #0f6b4f;
  background: rgba(226, 246, 237, 0.9);
  border-color: rgba(15, 107, 79, 0.2);
}

.assistant-input textarea {
  width: 100%;
  padding: 12px;
  border: 2px solid rgba(18, 93, 115, 0.2);
  border-radius: 8px;
  font-family: inherit;
  font-size: 14px;
  resize: vertical;
  transition: border-color 0.3s ease;
}

.assistant-input textarea:focus {
  outline: none;
  border-color: #5470c6;
}

.primary-button {
  align-self: flex-end;
  background: #5470c6;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.primary-button:hover:not(:disabled) {
  background: #4565b8;
  transform: translateY(-1px);
}

.primary-button:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
}

.suggestion-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggestion-chip {
  border: 1px solid rgba(18, 93, 115, 0.2);
  background: rgba(255, 255, 255, 0.9);
  color: #5470c6;
  border-radius: 16px;
  padding: 6px 12px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.suggestion-chip:hover {
  background: #5470c6;
  color: white;
  border-color: #5470c6;
}

.assistant-reply {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.reply-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.assistant-reply h3 {
  margin: 0 0 12px 0;
  color: #2c3e50;
  font-size: 16px;
}

.reply-header h3 {
  margin: 0;
}

.source-badge-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0 0 10px;
}

.source-badge {
  border: 1px solid rgba(18, 93, 115, 0.14);
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  padding: 5px 9px;
}

.source-badge--success {
  background: rgba(226, 246, 237, 0.9);
  border-color: rgba(15, 107, 79, 0.2);
  color: #0f6b4f;
}

.source-badge--info {
  background: rgba(229, 242, 255, 0.9);
  border-color: rgba(37, 99, 235, 0.16);
  color: #2450a6;
}

.source-badge--model {
  background: rgba(244, 238, 255, 0.9);
  border-color: rgba(123, 97, 255, 0.18);
  color: #5540b8;
}

.source-badge--warning {
  background: rgba(255, 246, 214, 0.94);
  border-color: rgba(190, 128, 0, 0.2);
  color: #8a5b00;
}

.entity-line {
  border-left: 3px solid rgba(15, 139, 141, 0.28);
  color: #48606b !important;
  font-size: 13px;
  margin: 0 0 12px !important;
  padding-left: 10px;
}

.validation-warning {
  display: grid;
  gap: 4px;
  border: 1px solid rgba(190, 128, 0, 0.18);
  border-radius: 10px;
  background: rgba(255, 248, 222, 0.9);
  color: #735000;
  font-size: 13px;
  margin-bottom: 12px;
  padding: 10px 12px;
}

.validation-warning strong {
  color: #735000;
}

.assistant-reply p {
  margin: 0 0 16px 0;
  line-height: 1.6;
  color: #34495e;
}

.citation-section {
  margin-top: 20px;
}

.citation-title {
  margin: 0 0 12px 0;
  color: #5470c6;
  font-size: 14px;
  font-weight: 600;
}

.citation-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.follow-up-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

@media (max-width: 768px) {
  .assistant-panel {
    gap: 16px;
  }
  
  .assistant-reply {
    padding: 16px;
  }
  
  .primary-button {
    align-self: stretch;
  }

  .model-selector-row {
    align-items: stretch;
  }
}
</style>
