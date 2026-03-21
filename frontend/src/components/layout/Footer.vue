<template>
  <footer class="mt-auto border-t border-slate-200 bg-white px-6 py-4 dark:border-slate-700 dark:bg-slate-800">
    <div class="text-center text-base text-slate-500 dark:text-slate-400">
      <p>&copy; {{ year }} EvoTechLab. All rights reserved.</p>
    </div>
  </footer>
</template>

<script setup>
const year = new Date().getFullYear()
</script>
