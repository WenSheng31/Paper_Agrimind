<template>
  <!-- 只在移動設備上顯示 -->
  <header
    class="border-b border-slate-200 bg-white px-4 py-3 lg:hidden dark:border-slate-700 dark:bg-slate-800"
  >
    <!-- 漢堡選單按鈕 -->
    <button
      @click="$emit('toggle-sidebar')"
      class="cursor-pointer rounded p-2 text-slate-700 transition hover:bg-slate-100
        dark:text-slate-200 dark:hover:bg-slate-700"
    >
      <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M4 6h16M4 12h16M4 18h16"
        ></path>
      </svg>
    </button>
  </header>
</template>

<script setup>
defineEmits(['toggle-sidebar'])
</script>
