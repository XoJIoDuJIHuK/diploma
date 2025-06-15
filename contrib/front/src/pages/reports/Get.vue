<template>
  <v-card class="mx-auto mx-4" max-width="900">
    <v-card-title>
      <div>
        <span class="headline">Жалоба пользователя {{ report.user_name }}</span>
      </div>
      <v-spacer />
      <v-chip small text-color="white" :color="report.status === Config.reportStatuses.open
        ? 'warning'
        : report.status === Config.reportStatuses.satisfied
          ? 'success'
          : report.status === Config.reportStatuses.rejected
            ? 'error'
            : 'grey'
        ">
        {{ report.status }}
      </v-chip>
    </v-card-title>

    <v-card-subtitle class="grey--text">
      <v-icon small class="mr-1">mdi-calendar</v-icon>
      {{ (new Date(report.created_at)).toLocaleString() }}
    </v-card-subtitle>

    <v-divider />

    <v-card-text>
      <v-row>
        <v-col cols="12" md="4">
          <strong>Причина</strong>
          <p class="mt-1">{{ report.reason_text }}</p>
        </v-col>
        <v-col cols="12" md="8">
          <strong>Текст жалобы</strong>
          <p class="mt-1">{{ report.text }}</p>
        </v-col>
      </v-row>

      <v-row dense>
        <v-col cols="12" md="6">
          <strong>Исходный текст</strong><br>
          <strong>{{ report.source_title }}</strong>
          <v-sheet class="pa-3 markdown-box" elevation="1">
            <div v-html="renderedSourceMarkdown"></div>
          </v-sheet>
        </v-col>
        <v-col cols="12" md="6">
          <strong>Перевод</strong><br>
          <strong>{{ report.article_title }}</strong>
          <v-sheet class="pa-3 markdown-box" elevation="1">
            <div v-html="renderedTranslatedMarkdown"></div>
          </v-sheet>
        </v-col>
      </v-row>
    </v-card-text>

    <v-card-actions>
      <template v-if="userRole === Config.userRoles.mod && report.status === Config.reportStatuses.open">
        <v-btn color="success" @click="updateStatus(Config.reportStatuses.satisfied)" small>
          <v-icon left>mdi-check</v-icon> Удовлетворить
        </v-btn>
        <v-btn color="error" @click="updateStatus(Config.reportStatuses.rejected)" small>
          <v-icon left>mdi-close</v-icon> Отклонить
        </v-btn>
      </template>
      <template v-else-if="report.status === Config.reportStatuses.open">
        <v-btn color="warning" @click="updateStatus(Config.reportStatuses.closedByUser)" small>
          <v-icon left>mdi-lock</v-icon> Закрыть
        </v-btn>
      </template>
      <v-spacer />
    </v-card-actions>

    <v-divider />

    <v-card-text>
      <div class="section-title">Комментарии</div>
      <v-list two-line dense>
        <v-list-item v-for="comment in comments" :key="comment.id" :class="{
          'my-comment': currentUserId === comment.sender_id,
          'other-comment': currentUserId !== comment.sender_id
        }">
          <v-list-item-avatar>
            <v-icon color="grey lighten-1">mdi-account</v-icon>
          </v-list-item-avatar>
          <v-list-item-content>
            <v-list-item-title>{{ comment.sender_name }}</v-list-item-title>
            <v-list-item-subtitle>{{ comment.text }}</v-list-item-subtitle>
          </v-list-item-content>
          <v-list-item-action-text class="grey--text text-caption">
            {{ (new Date(comment.created_at)).toLocaleString() }}
          </v-list-item-action-text>
        </v-list-item>

        <v-list-item v-if="comments.length === 0">
          <v-list-item-content class="text-center grey--text">
            Пусто.
          </v-list-item-content>
        </v-list-item>
      </v-list>

      <v-row v-if="report.status === Config.reportStatuses.open" align="center" class="mt-4">
        <v-col cols="9">
          <v-textarea v-model="commentText" label="Введите текст" outlined dense :rows="1" :auto-grow="true"
            :max-height="4 * lineHeight" />
        </v-col>
        <v-col cols="3" class="text-right">
          <v-btn color="info" @click="sendComment" rounded small>
            <v-icon left>mdi-send</v-icon> Отправить
          </v-btn>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, Ref, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router';
import { fetch_data, getWebsocket } from '../../helpers';
import { Config } from '../../settings';
import { UnnecessaryEventEmitter } from '../../eventBus';
import { marked } from "marked";

const comments: Ref<Array<any>> = ref([]);
const commentText = ref('');
const report = reactive({
  text: '',
  reason_text: '',
  status: '',
  created_at: new Date(),
  closed_at: null,
  closed_by_user_name: null,
  source_text: '',
  source_language_id: null,
  translated_text: '',
  translated_language_id: null
});
const route = useRoute();
const router = useRouter();
const socket: Ref<WebSocket | null> = ref(null);
const renderedSourceMarkdown = ref('');
const renderedTranslatedMarkdown = ref('');

const currentUserId = ref(null);
const userRole = JSON.parse(localStorage.getItem(Config.userInfoProperty) as string).role

onMounted(async () => {
  currentUserId.value = JSON.parse(localStorage.userInfo).id;
  let response = await fetch_data(`${Config.backend_address}/articles/${route.params.article_id}/report/`)
  if (!response) await router.push('/error')
  else Object.assign(report, response.data.report)
  renderedSourceMarkdown.value = await marked(report.source_text);
  renderedTranslatedMarkdown.value = await marked(report.translated_text);

  response = await fetch_data(`${Config.backend_address}/articles/${route.params.article_id}/report/comments/`)
  comments.value = response ? response.data.list : [];

  const connectedSocket = await getWebsocket(`${Config.websocket_address}/articles/${route.params.article_id}/report/comments/ws/`);
  if (!connectedSocket) return;
  socket.value = connectedSocket;
  socket.value.addEventListener('message', event => {
    comments.value.push(JSON.parse(event.data))
  })
})

async function sendComment() {
  const response = await fetch_data(
    `${Config.backend_address}/articles/${route.params.article_id}/report/comments/`,
    'POST',
    JSON.stringify({
      text: commentText.value
    }),
  )
  if (response) {
    commentText.value = '';
    // comments.value.push(response.data.comment)
  }
}

async function updateStatus(newStatus: string) {
  const response = await fetch_data(
    `${Config.backend_address}/articles/${route.params.article_id}/report/status/?new_status=${newStatus}`,
    'PATCH',
  )
  if (response) {
    UnnecessaryEventEmitter.emit(Config.alertMessageKey, {
      title: 'Статус обновлён',
      text: undefined,
      severity: 'info'
    });
    report.status = newStatus;
  }
}

</script>

<style scoped>
.section-title {
  font-weight: 500;
  margin-bottom: 16px;
}

.markdown-box {
  background-color: #fafafa;
  border-radius: 4px;
}

.my-comment {
  background-color: rgba(100, 181, 246, 0.1) !important;
}

.other-comment {
  background-color: rgba(139, 195, 74, 0.1) !important;
}
</style>
