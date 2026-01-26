<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-100 p-4 dark:bg-slate-900">
    <div class="text-center">
      <h1 class="mb-4 text-6xl font-bold text-emerald-600 dark:text-emerald-500">404</h1>
      <p class="mb-8 text-xl text-slate-600 dark:text-slate-400">抱歉，找不到您要訪問的頁面</p>
      <router-link
        to="/home"
        class="inline-block rounded bg-emerald-600 px-6 py-3 text-white transition
          hover:bg-emerald-700"
      >
        返回首頁
      </router-link>
    </div>
  </div>
</template>
