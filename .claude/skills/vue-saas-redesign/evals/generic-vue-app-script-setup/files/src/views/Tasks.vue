<script setup>
import { ref } from 'vue'
const tasks = ref([
  { id: 1, text: 'Call Ava about renewal', done: false },
  { id: 2, text: 'Send Globex proposal', done: true }
])
</script>
<template>
  <section>
    <h1>Tasks</h1>
    <ul><li v-for="t in tasks" :key="t.id"><label><input type="checkbox" v-model="t.done" /> {{ t.text }}</label></li></ul>
  </section>
</template>
<style scoped>
h1 { margin: 0 0 14px; font-size: 26px; }
ul { list-style: none; padding: 0; } li { padding: 8px 0; }
</style>
