<script setup>
const deals = [
  { id: 1, title: 'Annual license', value: 48000, stage: 'Negotiation' },
  { id: 2, title: 'Pilot program', value: 12000, stage: 'Proposal' },
  { id: 3, title: 'Support renewal', value: 7500, stage: 'Won' }
]
</script>
<template>
  <section>
    <h1>Deals</h1>
    <div class="grid">
      <div v-for="d in deals" :key="d.id" class="card">
        <h3>{{ d.title }}</h3>
        <p class="v">${{ d.value.toLocaleString() }}</p>
        <span class="tag">{{ d.stage }}</span>
      </div>
    </div>
  </section>
</template>
<style scoped>
h1 { margin: 0 0 14px; font-size: 26px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 17px; }
.card { background: #fff; border: 2px solid #e7d5c0; padding: 15px; }
.v { font-size: 22px; margin: 6px 0; }
.tag { background: #fed7aa; padding: 2px 8px; font-size: 12px; }
</style>
