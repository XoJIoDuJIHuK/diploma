<template>
  <v-card class="article-card mt-4">
    <v-card-title>
      {{ article.title }}
      <v-spacer></v-spacer>
      <span class="article-language">
        {{ store.languages.getValue(article.language_id) === null ? '' :
          store.languages.getValue(article.language_id)!.iso_code }}
      </span>
    </v-card-title>
    <v-card-text>
      <p>Дата создания: {{ (new Date(article.created_at)).toLocaleString() }}</p>
    </v-card-text>
    <v-card-actions>
      <router-link :to="`/articles/${article.id}/get`">
        <v-btn variant="tonal" color="blue">
          <v-icon icon="mdi-eye" />Посмотреть
        </v-btn>
      </router-link>
      <router-link :to="`/articles/${article.id}/update`" v-if="isOriginal">
        <v-btn variant="tonal" color="green">
          <v-icon icon="mdi-pencil" />Изменить
        </v-btn>
      </router-link>
      <v-btn variant="tonal" color="red" @click="() => { delete_article(article.id) }">
        <v-icon icon="mdi-delete" />Удалить
      </v-btn>
      <router-link :to="`/articles/${article.id}/translations`" v-if="isOriginal">
        <v-btn variant="tonal" color="blue">
          <v-icon icon="mdi-earth" />Переводы
        </v-btn>
      </router-link>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { store } from '../../settings';
import { VCard, VCardTitle, VCardText, VSpacer, VIcon } from 'vuetify/components';
import { fetch_data } from '../../helpers';
import { Config } from '../../settings';
import { UnnecessaryEventEmitter } from '../../eventBus';

//@ts-ignore
const props = defineProps({
  article: {
    type: Object,
    required: true,
  },
  isOriginal: {
    type: Boolean,
    required: true,
  }
});

async function delete_article(article_id: string) {
  const result = await fetch_data(
    `${Config.backend_address}/articles/${article_id}/`,
    'DELETE',
  )
  if (result) {
    UnnecessaryEventEmitter.emit(Config.alertMessageKey, {
      title: undefined,
      text: 'Статья успешно удалена',
      severity: 'success'
    })
    location.reload()
  }
}
</script>
