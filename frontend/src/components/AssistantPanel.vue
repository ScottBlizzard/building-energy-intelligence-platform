<script setup>
import { ref } from "vue";
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
  }
});

const emit = defineEmits(["ask"]);
const question = ref("当前样例数据有哪些异常记录？");

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
</script>

<template>
  <div class="assistant-panel">
    <div class="assistant-input">
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
      <h3>系统回答</h3>
      <p>{{ reply.answer }}</p>

      <div v-if="reply.citations?.length" class="citation-section">
        <h4 class="citation-title">📚 引用来源</h4>
        <div class="citation-cards">
          <CitationCard 
            v-for="citation in reply.citations" 
            :key="`${citation.title}-${citation.path}`"
            :citation="citation"
          />
        </div>
      </div>

      <div v-if="reply.follow_up?.length" class="citation-block">
        <strong>建议继续追问</strong>
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

.assistant-reply h3 {
  margin: 0 0 12px 0;
  color: #2c3e50;
  font-size: 16px;
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
}
</style>
