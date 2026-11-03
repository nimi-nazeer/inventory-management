<script setup>
const contacts = [
  { id: 1, name: 'Ava Lindqvist', company: 'Northwind', email: 'ava@northwind.test' },
  { id: 2, name: 'Marcus Oyelaran', company: 'Globex', email: 'marcus@globex.test' },
  { id: 3, name: 'Priya Raman', company: 'Initech', email: 'priya@initech.test' }
]
</script>
<template>
  <section>
    <h1>Contacts</h1>
    <table>
      <thead><tr><th>Name</th><th>Company</th><th>Email</th></tr></thead>
      <tbody><tr v-for="c in contacts" :key="c.id"><td>{{ c.name }}</td><td>{{ c.company }}</td><td>{{ c.email }}</td></tr></tbody>
    </table>
  </section>
</template>
<style scoped>
h1 { margin: 0 0 14px; font-size: 26px; }
table { width: 100%; border-collapse: collapse; background: #fff; }
th, td { text-align: left; padding: 9px 13px; border-bottom: 1px solid #e7d5c0; }
</style>
