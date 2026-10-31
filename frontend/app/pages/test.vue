<script setup lang="ts">
import InstanceConsole from '~/components/instance/Backups.vue'
</script>

<template>
  <div class="min-h-screen bg-background p-8">
    <div class="mx-auto h-[800px] max-w-7xl">
      <!-- 直接给它传一个假的 ID，看效果就行 -->
      <InstanceConsole instance-id="test-123" status="running" />
    </div>
  </div>
</template>
