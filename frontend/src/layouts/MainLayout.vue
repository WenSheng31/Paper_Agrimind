<template>
  <div class="min-h-screen overflow-hidden bg-slate-100 dark:bg-slate-900">
    <Sidebar :isOpen="isSidebarOpen" @close="isSidebarOpen = false" />

    <div
      class="flex min-h-screen flex-col transition-[padding-left] duration-300 ease-in-out lg:pl-64"
    >
      <Header @toggle-sidebar="isSidebarOpen = !isSidebarOpen" />

      <main class="flex flex-1 flex-col overflow-y-auto">
        <div class="flex-1">
          <router-view v-slot="{ Component }">
            <transition name="fade-page" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
        <Footer />
      </main>
    </div>

    <AiChatWidget />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Header from '@/components/layout/Header.vue'
import Sidebar from '@/components/layout/Sidebar.vue'
import Footer from '@/components/layout/Footer.vue'
import AiChatWidget from '@/components/ai/AiChatWidget.vue'

const isSidebarOpen = ref(false)
</script>
