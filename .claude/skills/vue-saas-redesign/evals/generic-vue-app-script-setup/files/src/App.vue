<script setup>
import { ref } from 'vue'
const user = ref({ name: 'Dana Whitfield' })
</script>

<template>
  <div class="wrap">
    <header class="bar">
      <strong class="brand">TinyCRM</strong>
      <nav>
        <router-link to="/">Contacts</router-link>
        <router-link to="/deals">Deals</router-link>
        <router-link to="/tasks">Tasks</router-link>
        <router-link to="/settings">Settings</router-link>
      </nav>
      <span class="me">{{ user.name }}</span>
    </header>
    <main class="page"><router-view /></main>
  </div>
</template>

<style>
body { margin: 0; font-family: Georgia, serif; background: #fffaf3; color: #3b2f2f; }
.bar { display: flex; align-items: center; gap: 18px; padding: 14px 22px; background: #7c2d12; color: #fff; }
.bar nav { display: flex; gap: 14px; margin-left: 24px; flex: 1; }
.bar a { color: #fed7aa; text-decoration: none; padding: 6px 10px; border-radius: 4px; }
.bar a.router-link-exact-active { background: #9a3412; color: #fff; }
.page { padding: 26px 30px; }
.me { font-size: 14px; }
</style>
