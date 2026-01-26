<template>
  <transition-group
    name="toast"
    tag="div"
    class="pointer-events-none fixed top-4 right-4 z-50 space-y-2"
  >
    <div
      v-for="toast in toasts"
      :key="toast.id"
      :class="[
        'pointer-events-auto max-w-md rounded border px-4 py-3 shadow-lg',
        toast.type === 'success'
          ? 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-900/80 dark:text-emerald-100'
          : 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900/50 dark:bg-rose-900/80 dark:text-rose-100',
      ]"
    >
      {{ toast.message }}
    </div>
  </transition-group>
</template>

<script setup>
import { toastState } from '@/composables/useToast'

const toasts = toastState.toasts
</script>

<style scoped>
.toast-enter-active {
  transition: all 0.3s ease-out;
}

.toast-leave-active {
  transition: all 0.2s ease-in;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
</style>
