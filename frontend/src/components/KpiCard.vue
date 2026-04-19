<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  caption: {
    type: String,
    default: ""
  }
});
</script>

<template>
  <article class="kpi-card">
    <span class="kpi-card__title">{{ title }}</span>
    <strong class="kpi-card__value">{{ value }}</strong>
    <span class="kpi-card__caption">{{ caption }}</span>
  </article>
</template>

