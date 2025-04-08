<template>
  <v-card class="translation-card mx-auto my-4" elevation="3" max-width="900" height="max-content">
    <v-card-title class="text-h5 primary--text pb-0">
      <v-icon large color="primary" class="mr-2">mdi-translate</v-icon>
      Мгновенный перевод
    </v-card-title>

    <v-card-text>
      <v-row>
        <!-- Translation Params Row -->
        <v-col cols="12" sm="6">
          <v-select v-model="translationModel" :items="store.models.getSelectItems()" label="Модель" variant="outlined"
            density="comfortable" class="language-selector"></v-select>
        </v-col>

        <v-col cols="12" sm="6">
          <v-select v-model="translationPrompt" :items="store.prompts.getSelectItems()" label="Промпт"
            variant="outlined" density="comfortable" class="language-selector"></v-select>
        </v-col>
      </v-row>

      <v-row>
        <!-- Language Selection Row -->
        <v-col cols="12" sm="6">
          <v-select v-model="sourceLanguage" :items="[
            { value: null, title: 'Автоматически' },
            ...store.languages.getSelectItems()
          ]" label="С языка" variant="outlined" density="comfortable" class="language-selector"></v-select>
        </v-col>

        <v-col cols="12" sm="6">
          <v-select v-model="targetLanguage" :items="store.languages.getSelectItems()" label="На язык"
            variant="outlined" density="comfortable" class="language-selector"></v-select>
        </v-col>
      </v-row>

      <v-row>
        <!-- Input and Output Area -->
        <v-col cols="12" sm="6">
          <v-textarea v-model="inputText" label="Введите текст" variant="outlined" auto-grow rows="5" hide-details
            class="translation-textarea" @input="handleInputChange"></v-textarea>

          <div class="d-flex justify-space-between align-center mt-2">
            <v-btn variant="text" size="small" :disabled="!inputText" @click="clearInputText">
              <v-icon>mdi-close</v-icon>
              Очистить
            </v-btn>

            <div class="text-caption text-grey">
              {{ inputText ? inputText.length : 0 }} символов
            </div>
          </div>
        </v-col>

        <v-col cols="12" sm="6">
          <v-textarea v-model="outputText" label="Перевод" variant="outlined" auto-grow rows="5" hide-details readonly
            class="translation-textarea"></v-textarea>

          <div class="d-flex justify-space-between mt-2">
            <v-btn variant="text" size="small" color="primary" :disabled="!outputText" @click="copyToInput">
              <v-icon class="mr-1">mdi-arrow-left</v-icon>
              Перенести в поле ввода
            </v-btn>

            <v-btn variant="text" size="small" color="primary" :disabled="!outputText" @click="copyToClipboard">
              <v-icon class="mr-1">mdi-content-copy</v-icon>
              Копировать
            </v-btn>
          </div>
        </v-col>
      </v-row>
    </v-card-text>

    <v-divider></v-divider>

    <v-card-actions>
      <v-btn color="primary" variant="elevated" :loading="isLoading" :disabled="!inputText || isLoading"
        @click="translateText" class="mx-auto mb-2">
        <v-icon left class="mr-1">mdi-translate</v-icon>
        Перевести
      </v-btn>
    </v-card-actions>

    <!-- Snackbar for notifications -->
    <v-snackbar v-model="snackbar" :color="snackbarColor" :timeout="3000" location="top">
      {{ snackbarText }}

      <template v-slot:actions>
        <v-btn color="white" variant="text" @click="snackbar = false">
          Закрыть
        </v-btn>
      </template>
    </v-snackbar>
  </v-card>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { fetch_data } from '../helpers';
import { Config, store } from '../settings';

// State variables
const sourceLanguage = ref(null);
const targetLanguage = ref(null);
const translationModel = ref(null);
const translationPrompt = ref(null);
const inputText = ref('');
const outputText = ref('');
const isLoading = ref(false);

// Snackbar
const snackbar = ref(false);
const snackbarText = ref('');
const snackbarColor = ref('success');

// Methods
const translateText = async () => {
  if (!inputText.value.trim()) return;

  isLoading.value = true;

  try {
    const response = await fetch_data(
      `${Config.backend_address}/translation/simple/`,
      'POST',
      JSON.stringify({
        text: inputText.value,
        source_language_id: sourceLanguage.value,
        target_language_id: targetLanguage.value,
        model_id: translationModel.value,
        prompt_id: translationPrompt.value,
      })
    );

    if (!response) {
      return;
    }
    outputText.value = response.text;
  } catch (error) {
    console.error('Translation error:', error);
    showSnackbar('Перевод не удался. Попробуйте ещё раз', 'error');
  } finally {
    isLoading.value = false;
  }
};

const copyToClipboard = async () => {
  if (!outputText.value) return;

  try {
    await navigator.clipboard.writeText(outputText.value);
    showSnackbar('Текст скопирован', 'success');
  } catch (err) {
    console.error('Failed to copy text: ', err);
    showSnackbar('Не получилось скопировать текст', 'error');
  }
};

const copyToInput = () => {
  if (!outputText.value) return;
  inputText.value = outputText.value;
  outputText.value = '';

  const temp = sourceLanguage.value;
  sourceLanguage.value = targetLanguage.value;
  targetLanguage.value = temp;
};

const clearInputText = () => {
  inputText.value = '';
  if (!outputText.value) return;
  outputText.value = '';
};

const handleInputChange = () => {
  // Optional: Auto-translate after user stops typing (uncomment to enable)
  /*
  if (typingTimeout.value) clearTimeout(typingTimeout.value);
  
  typingTimeout.value = setTimeout(() => {
    if (inputText.value.trim()) {
      translateText();
    }
  }, 1500);
  */
};

const showSnackbar = (text: string, color = 'success') => {
  snackbarText.value = text;
  snackbarColor.value = color;
  snackbar.value = true;
};

// Swap languages function
const swapLanguages = () => {
  const tempLang = sourceLanguage.value;
  sourceLanguage.value = targetLanguage.value;
  targetLanguage.value = tempLang;

  if (outputText.value) {
    inputText.value = outputText.value;
    outputText.value = '';
  }
};
</script>

<style scoped>
.translation-card {
  border-radius: 12px;
}

.translation-textarea {
  font-size: 16px;
}

.language-selector {
  max-width: 100%;
}
</style>
