<script setup>
defineProps({
  eyebrow: {
    type: String,
    default: ""
  },
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ""
  }
});
</script>

<template>
  <section class="section-card">
    <div class="section-card__header">
      <span v-if="eyebrow" class="section-card__eyebrow">{{ eyebrow }}</span>
      <h2 class="section-card__title">{{ title }}</h2>
      <p v-if="description" class="section-card__description">{{ description }}</p>
    </div>
    <div class="section-card__body">
      <slot />
    </div>
  </section>
</template>

