<script setup>
import { ref } from 'vue'
const form = ref({ name: 'Dana Whitfield', email: 'dana@tinycrm.test' })
</script>
<template>
  <section>
    <h1>Settings</h1>
    <form @submit.prevent>
      <label>Name <input v-model="form.name" /></label>
      <label>Email <input v-model="form.email" /></label>
      <button>Save</button>
    </form>
  </section>
</template>
<style scoped>
h1 { margin: 0 0 14px; font-size: 26px; }
form { display: grid; gap: 11px; max-width: 360px; }
input { display: block; width: 100%; padding: 7px; margin-top: 3px; }
button { padding: 8px; background: #7c2d12; color: #fff; border: 0; }
</style>
