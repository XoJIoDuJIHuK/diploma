<template>
  <div class="sessions-container">
    <div class="d-flex justify-end mb-4 mt-4">
      <v-btn @click="closeSessions" variant="elevated" color="red-darken-2" prepend-icon="mdi-close-circle-outline">
        Закрыть все сессии
      </v-btn>
    </div>

    <v-card border flat class="elevation-1">
      <v-list lines="two" class="py-0">
        <v-list-item v-for="session in sessions" :key="session.id" :title="`${session.ip}`"
          :subtitle="`Устройство: ${formatUserAgent(session.user_agent)}`">
          <template v-slot:append>
            <v-chip size="small" variant="outlined" color="grey-darken-1" class="text-caption">
              {{ formatDate(session.created_at) }}
            </v-chip>
          </template>
        </v-list-item>

        <v-list-item v-if="!sessions.length">
          <v-list-item-title class="text-grey">
            Открытых сессий нет. Странно
          </v-list-item-title>
        </v-list-item>
      </v-list>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, Ref, ref } from 'vue';
import { fetch_data, logout } from '../helpers';
import { Config } from '../settings';
import { UnnecessaryEventEmitter } from '../eventBus';

interface Session {
  id: string;
  ip: string;
  user_agent: string;
  created_at: string;
}

const sessions: Ref<Array<Session>> = ref([]);

onMounted(async () => {
  const response = await fetch_data(`${Config.backend_address}/sessions/`)
  if (response) {
    sessions.value = response.data.list;
  }
})

function formatUserAgent(ua: string): string {
  return ua;
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString();
}

async function closeSessions() {
  const response = await fetch_data(
    `${Config.backend_address}/sessions/close/`,
    'POST',
  )
  if (response) {
    UnnecessaryEventEmitter.emit(Config.alertMessageKey, {
      title: response.message,
      text: undefined,
      severity: 'info'
    })
    await logout();
  }
}
</script>

<style scoped>
.sessions-container {
  max-width: 800px;
  margin: 0 auto;
}
</style>
