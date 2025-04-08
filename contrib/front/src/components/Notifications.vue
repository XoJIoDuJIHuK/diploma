<template>
  <v-menu location="end" persistent>
    <template v-slot:activator="{ props }">
      <v-btn v-bind="props" icon="mdi-bell" color="white" variant="text" class="notification-button"
        :style="{ position: 'relative' }">
        <v-badge :content="notifications.length" color="red" :model-value="notifications.length > 0" dot offset-x="-5"
          offset-y="20">
          <v-icon>mdi-bell</v-icon>
        </v-badge>
      </v-btn>
    </template>

    <v-sheet elevation="8" class="notification-sheet">
      <v-container>
        <v-row justify="space-between" align="center">
          <v-col cols="auto">
            <div class="text-h6 font-weight-semibold">Уведомления</div>
          </v-col>
          <v-col cols="auto">
            <v-btn @click="clearNotifications" variant="tonal" color="primary" size="small">
              Очистить все
            </v-btn>
          </v-col>
        </v-row>
        <v-divider class="my-2"></v-divider>
        <v-container v-if="notifications.length > 0" class="notifications-container pa-0">
          <v-card v-for="(notification, index) in notifications" :key="index" class="notification-card mb-3"
            elevation="1">
            <v-card-title class="text-subtitle-1 font-weight-bold pb-1">
              {{ notification.title }}
            </v-card-title>
            <v-card-text class="pt-1">
              <div class="text-body-2">{{ notification.text }}</div>
              <div class="text-caption text-grey mt-2">
                {{ formatRelativeTime(notification.created_at) }}
              </div>
            </v-card-text>
          </v-card>
        </v-container>
        <v-row v-else>
          <v-col class="text-center text-grey-darken-1">
            Уведомлений нет
          </v-col>
        </v-row>
      </v-container>
    </v-sheet>
  </v-menu>
</template>

<script setup lang="ts">
import { onMounted, Ref, ref } from 'vue';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
import { fetch_data, getWebsocket } from '../helpers';
import { Config } from '../settings';
import { UnnecessaryEventEmitter } from '../eventBus';

interface Notification {
  title: string;
  text: string;
  type: string;
  created_at: string;
}

const notifications: Ref<Array<Notification>> = ref([]);
const socket: Ref<null | WebSocket> = ref(null);
console.log(notifications.value.length)

const formatRelativeTime = (timestamp: string): string => {
  try {
    return formatDistanceToNow(new Date(timestamp), {
      addSuffix: true,
      locale: ru
    });
  } catch {
    return '';
  }
};

onMounted(async () => {
  const userRole = JSON.parse(localStorage.getItem(Config.userInfoProperty) as string).role;
  const response = await fetch_data(`${Config.backend_address}/notifications/`);
  if (response) notifications.value = response.data.list;

  if (userRole === Config.userRoles.admin) return;

  try {
    const connectedSocket = await getWebsocket(`${Config.websocket_address}/notifications/`);
    if (!connectedSocket) return;
    socket.value = connectedSocket;
    socket.value.addEventListener('message', event => {
      const notification = JSON.parse(event.data);
      notification.timestamp = new Date().toISOString(); // Add timestamp to new notifications

      UnnecessaryEventEmitter.emit(Config.alertMessageKey, {
        title: notification.title,
        text: notification.text,
        severity: notification.type
      });
      notifications.value.push(notification);
    });
  } catch (e) {
    console.log('Notifications websocket error:', e);
  }
});

async function clearNotifications() {
  const response = await fetch_data(
    `${Config.backend_address}/notifications/`,
    'PUT',
  );
  if (response) {
    notifications.value = [];
    UnnecessaryEventEmitter.emit(Config.alertMessageKey, {
      title: response.message,
      text: undefined,
      severity: 'info'
    });
  }
}
</script>

<style scoped>
.notification-button {
  min-width: auto;
  margin-right: 14px;
}


.notification-chip {
  position: absolute;
  top: -5px;
  right: -10px;
}

.notification-sheet {
  display: flex;
  flex-direction: column;
  margin-top: 50px;
  z-index: 9001;
  min-width: 350px;
  max-width: 400px;
}

.notifications-container {
  max-height: 400px;
  overflow-y: auto;
}

.notification-card {
  width: 100%;
}
</style>
