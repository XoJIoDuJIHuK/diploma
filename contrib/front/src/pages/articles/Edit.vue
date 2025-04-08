<template>
  <v-container class="article-editor">
    <v-form ref="form" v-model="valid" lazy-validation>
      <v-card flat class="mb-6">
        <v-card-text>
          <v-text-field v-model="article.title" label="Название статьи" :rules="[rules.required, rules.maxLength(50)]"
            required variant="outlined" density="comfortable" class="mb-4"></v-text-field>

          <v-switch v-model="useWysiwyg" label="Использовать текстовый редактор" color="primary" class="mt-0 mb-4"
            inset></v-switch>

          <template v-if="useWysiwyg">
            <v-row class="editor-container">
              <v-col cols="12" md="6" class="pr-md-3">
                <v-textarea v-model="article.text" @input="updateMarkdown" class="markdown-textarea"
                  placeholder="Введите текст статьи здесь..." auto-grow variant="outlined" rows="10"
                  hide-details></v-textarea>
              </v-col>
              <v-col cols="12" md="6" class="pl-md-3">
                <div class="preview-label">Предпросмотр:</div>
                <div v-if="renderedMarkdown" v-html="renderedMarkdown"></div>
                <div v-else>
                  <p class="placeholder-text">Предпросмотр
                    появится здесь</p>
                </div>
              </v-col>
            </v-row>
          </template>
          <template v-else>
            <v-file-input v-model="article.file" label="Загрузите файл (.txt, .md)" accept=".txt,.md"
              @change="handleFileChange" :rules="[rules.required]" required variant="outlined" density="comfortable"
              prepend-icon="mdi-paperclip" class="mb-4"></v-file-input>
          </template>

          <v-select v-if="!route.params.article_id" v-model="article.language_id"
            :items="store.languages.getSelectItems()" label="Язык (необязательно)" variant="outlined"
            density="comfortable" chips clearable class="mb-4"></v-select>
        </v-card-text>

        <v-card-actions class="px-4 pb-4">
          <v-btn color="primary" :disabled="!valid" @click="saveArticle" size="large" variant="flat" block>
            {{ isEditing ? 'Сохранить изменения' : 'Создать статью' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-form>
  </v-container>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue';
import { Config, store, validationRules as rules } from '../../settings';
import { useRoute, useRouter } from 'vue-router';
import { fetch_data } from '../../helpers';
import { get_article } from './helpers';
import { UnnecessaryEventEmitter } from '../../eventBus';
import { marked } from 'marked';

const form = ref(null);
const valid = ref(false);
const useWysiwyg = ref(true);
const article = reactive({
  title: '',
  text: '',
  file: null,
  language_id: null,
});

const route = useRoute();
const router = useRouter();

const isEditing = ref(false);


const localText = ref('');
const emit = defineEmits(['update:text']);
const renderedMarkdown = ref('');
const updateMarkdown = async () => {
  emit('update:text', localText.value);
  renderedMarkdown.value = await marked.parse(localText.value || '')
}
watch(() => article.text, (newValue) => {
  localText.value = newValue
  updateMarkdown()
}, { immediate: true })


onMounted(async () => {
  const article_id = route.params.article_id
  if (article_id) {
    isEditing.value = true;
    try {
      const response = await get_article(article_id as string)
      if (!response) {
        await router.push('/error')
        return
      }
      Object.assign(article, response);
    } catch (error) {
      console.error('Error fetching article:', error);
    }
  }
});

const handleFileChange = async (file: any) => {
  if (file) {
    const reader = new FileReader();
    reader.onload = (e: ProgressEvent) => {
      article.text = (e.target! as FileReader).result as string;
    };
    reader.readAsText(file.target.files[0]);
  }
};

const saveArticle = async () => {
  console.log(form, typeof form)
  //@ts-ignore
  if (form!.value!.validate()) {
    try {
      const apiUrl = isEditing.value
        ? `${Config.backend_address}/articles/${route.params.article_id}/`
        : `${Config.backend_address}/articles/`;
      const method = isEditing.value ? 'PUT' : 'POST';
      const response = await fetch_data(
        apiUrl,
        method,
        JSON.stringify({
          title: article.title,
          text: article.text,
          language_id: article.language_id
        })
      )
      if (response) {
        UnnecessaryEventEmitter.emit(Config.alertMessageKey, {
          title: 'Статья сохранена',
          text: undefined,
          severity: 'info'
        })
        await router.push(`/articles/${response.data.article.id}/get`)
      }
    } catch (error) {
      console.error('Error saving article:', error);
    }
  }
};
</script>

<style lang="scss" scoped>
.article-editor {
  max-width: 1200px;
  margin: 0 auto;
  padding-top: 24px;

  .editor-container {
    margin-top: 8px;
  }

  .markdown-textarea {
    font-family: 'Roboto Mono', monospace;
    font-size: 0.9rem;
    line-height: 1.6;
    background-color: #fafafa;
    border-radius: 4px;
  }

  .preview-label {
    font-size: 0.875rem;
    color: rgba(0, 0, 0, 0.6);
    margin-bottom: 8px;
    font-weight: 500;
  }

  .markdown-renderer {
    min-height: 200px;
    width: 100%;
    padding: 16px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    background-color: #ffffff;
    line-height: 1.6;

    :deep(h1) {
      font-size: 1.5rem;
      margin: 1rem 0;
      padding-bottom: 0.3rem;
      border-bottom: 1px solid #eaecef;
    }

    :deep(h2) {
      font-size: 1.3rem;
      margin: 0.8rem 0;
    }

    :deep(p) {
      margin: 0.5rem 0;
    }

    :deep(ul),
    :deep(ol) {
      padding-left: 2rem;
    }

    :deep(code) {
      background-color: #f5f5f5;
      padding: 0.2rem 0.4rem;
      border-radius: 3px;
      font-family: 'Roboto Mono', monospace;
    }

    :deep(pre) {
      background-color: #f5f5f5;
      padding: 1rem;
      border-radius: 4px;
      overflow-x: auto;
    }

    :deep(blockquote) {
      border-left: 4px solid #dfe2e5;
      color: #6a737d;
      padding: 0 1em;
      margin: 0.5rem 0;
    }
  }

  .placeholder-text {
    color: rgba(0, 0, 0, 0.38);
    font-style: italic;
  }
}
</style>
