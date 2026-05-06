<script setup>
import { ref } from "vue";

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

      <div v-if="reply.citations?.length" class="citation-block">
        <strong>引用来源</strong>
        <ul>
          <li v-for="citation in reply.citations" :key="`${citation.title}-${citation.path}`">
            {{ citation.title }} · {{ citation.path }}
          </li>
        </ul>
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
.follow-up-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.suggestion-chip {
  border: 1px solid rgba(18, 93, 115, 0.1);
  background: rgba(255, 255, 255, 0.85);
  color: var(--accent-deep);
  border-radius: 999px;
  padding: 8px 12px;
  font: inherit;
  cursor: pointer;
}
</style>
