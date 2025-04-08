<template>
  <div>
    <!-- Translation Form Modal -->
    <v-dialog v-model="translationConfigState.isVisible" max-width="600" persistent
      v-if="article.original_article_id === null">
      <v-card class="pa-6">
        <v-card-title class="d-flex justify-space-between align-center mb-4">
          <span class="text-h5">Настройки перевода</span>
          <v-btn icon @click="translationConfigState.isVisible = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-card-text>
          <v-form>
            <v-select label="Конфигурации" :items="configs.map(config => ({ value: config, title: config.name }))"
              item-title="title" clearable variant="outlined" class="mb-4" @update:model-value="(newValue) => {
                translationConfigState.model_id = newValue.model_id;
                translationConfigState.prompt_id = newValue.prompt_id;
                translationConfigState.language_ids = newValue.language_ids;
              }"></v-select>

            <v-select v-model="translationConfigState.model_id" label="Модель" :items="store.models.getSelectItems()"
              clearable variant="outlined" class="mb-4"></v-select>

            <v-select v-model="translationConfigState.prompt_id" label="Стиль перевода"
              :items="store.prompts.getSelectItems()" clearable variant="outlined" class="mb-4"></v-select>

            <v-select v-model="translationConfigState.language_ids" label="Конечные языки"
              :items="store.languages.getSelectItems()" multiple clearable variant="outlined" class="mb-6"></v-select>

            <div class="d-flex justify-end gap-4">
              <v-btn variant="outlined" color="grey-darken-1" @click="translationConfigState.isVisible = false">
                Отмена
              </v-btn>
              <v-btn variant="flat" color="primary" @click="startTranslation">
                Запуск
              </v-btn>
            </div>
          </v-form>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Article Content -->
    <v-container class="article-container">
      <v-card class="article-card" elevation="4">
        <v-card-title class="article-header">
          <div class="d-flex flex-column w-100">
            <div class="d-flex justify-space-between align-start mb-2">
              <h1 class="article-title">{{ article.title }}</h1>

              <div class="article-actions">
                <template v-if="article.original_article_id === null">
                  <router-link :to="`/articles/${article.id}/update`">
                    <v-btn variant="outlined" color="green" size="small" class="mr-2">
                      <v-icon start icon="mdi-pencil"></v-icon>
                      Изменить
                    </v-btn>
                  </router-link>
                  <v-btn variant="outlined" color="blue" size="small" @click="translationConfigState.isVisible = true">
                    <v-icon start icon="mdi-earth"></v-icon>
                    Перевести
                  </v-btn>
                </template>
                <router-link v-if="article.original_article_id"
                  :to="`/articles/${article.id}/report/${article.report_exists ? '' : 'create'}`">
                  <v-btn variant="outlined" color="error" size="small" class="ml-2">
                    <v-icon start icon="mdi-bug"></v-icon>
                    Report
                  </v-btn>
                </router-link>
              </div>
            </div>

            <div class="d-flex align-center article-meta">
              <v-chip variant="outlined" size="small" class="mr-2">
                <v-icon start icon="mdi-calendar"></v-icon>
                {{ (new Date(article.created_at)).toLocaleString() }}
              </v-chip>

              <v-chip variant="outlined" size="small">
                <v-icon start icon="mdi-translate"></v-icon>
                {{ store.languages.getValue(article.language_id) ?
                  store.languages.getValue(article.language_id)!.iso_code :
                  'Language not specified' }}
              </v-chip>

            </div>
          </div>
        </v-card-title>

        <v-card-text class="article-content">
          <div v-html="renderedMarkdown" class="markdown-renderer"></div>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, Ref, ref } from 'vue';
import { get_article } from './helpers';
import { useRoute, useRouter } from 'vue-router';
import { Config, store } from '../../settings';
import { fetch_data } from '../../helpers';
import { UnnecessaryEventEmitter } from '../../eventBus';
import { marked } from 'marked';

interface Config {
  name: string;
  text: string;
}

const route = useRoute();
const router = useRouter();
const renderedMarkdown = ref('');

const article = reactive({
  title: 'Не загружен',
  text: 'Не загружен',
  language_id: null,
  created_at: '',
  original_article_id: null,
  report_exists: false,
})
const translationConfigState = reactive({
  isVisible: false,
  model_id: undefined,
  prompt_id: undefined,
  language_ids: [],
})
const configs: Ref<Array<Config>> = ref([])

onMounted(async () => {
  const article_id = String(route.params.article_id)
  let response = await get_article(article_id)
  if (!response) {
    await router.push('/error')
  }
  Object.assign(article, response)
  renderedMarkdown.value = await marked(article.text);


  response = await fetch_data(`${Config.backend_address}/configs/`)
  if (response) {
    configs.value = response.data.list
  }
})


async function startTranslation() {
  const result = await fetch_data(
    `${Config.backend_address}/translation/`,
    'POST',
    JSON.stringify({
      article_id: article.id,
      model_id: translationConfigState.model_id,
      prompt_id: translationConfigState.prompt_id,
      source_language_id: article.language_id,
      target_language_ids: translationConfigState.language_ids
    }),
  )
  if (result) {
    UnnecessaryEventEmitter.emit(Config.alertMessageKey, {
      title: result.message,
      text: undefined,
      severity: 'info'
    })
    translationConfigState.isVisible = false;
  }
}
</script>

<style scoped>
.article-container {
  max-width: 1200px;
  padding: 24px;
}

.article-card {
  border-radius: 8px;
  overflow: hidden;
}

.article-header {
  padding: 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.article-title {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 8px;
  word-break: break-word;
}

.article-meta {
  margin-top: 8px;
}

.article-content {
  padding: 24px;
}

.article-actions {
  flex-shrink: 0;
  margin-left: 16px;
}

.markdown-renderer {
  font-family: 'Roboto', 'Helvetica', 'Arial', sans-serif;
  line-height: 1.8;
  color: rgba(0, 0, 0, 0.87);
  word-wrap: break-word;
}

.markdown-renderer :deep(h1) {
  font-size: 2rem;
  margin: 1.5rem 0 1rem;
  font-weight: 500;
}

.markdown-renderer :deep(h2) {
  font-size: 1.75rem;
  margin: 1.25rem 0 0.75rem;
  font-weight: 500;
}

.markdown-renderer :deep(h3) {
  font-size: 1.5rem;
  margin: 1rem 0 0.5rem;
  font-weight: 500;
}

.markdown-renderer :deep(p) {
  margin: 0 0 1rem;
}

.markdown-renderer :deep(a) {
  color: #1976d2;
  text-decoration: none;
}

.markdown-renderer :deep(a:hover) {
  text-decoration: underline;
}

.markdown-renderer :deep(ul),
.markdown-renderer :deep(ol) {
  margin: 0 0 1rem 1.5rem;
  padding: 0;
}

.markdown-renderer :deep(li) {
  margin-bottom: 0.5rem;
}

.markdown-renderer :deep(code) {
  font-family: 'Roboto Mono', monospace;
  background-color: rgba(0, 0, 0, 0.05);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-size: 0.9em;
}

.markdown-renderer :deep(pre) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 1em;
  border-radius: 4px;
  overflow-x: auto;
  margin: 0 0 1rem;
}

.markdown-renderer :deep(blockquote) {
  border-left: 4px solid #dfe2e5;
  color: #6a737d;
  padding: 0 1em;
  margin: 0 0 1rem;
}

.gap-4 {
  gap: 16px;
}
</style>
