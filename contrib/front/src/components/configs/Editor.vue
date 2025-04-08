<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h4 class="text-h6 mb-2">Название</h4>
        <v-text-field v-model="currentEditConfig.name" :rules="[rules.required, rules.maxLength(20)]" outlined dense
          placeholder="Введите название"></v-text-field>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <h4 class="text-h6 mb-2">Модель</h4>
        <v-select v-model="currentEditConfig.model_id" :items="store.models.getSelectItems()" outlined dense clearable
          placeholder="Выберите модель"></v-select>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <h4 class="text-h6 mb-2">Стиль</h4>
        <v-select v-model="currentEditConfig.prompt_id" :items="store.prompts.getSelectItems()" outlined dense clearable
          placeholder="Выберите стиль"></v-select>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <h4 class="text-h6 mb-2">Языки</h4>
        <v-select v-model="currentEditConfig.language_ids" :items="store.languages.getSelectItems()" outlined dense
          clearable multiple placeholder="Выберите языки"></v-select>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" class="d-flex justify-end">
        <v-btn @click="onCancel" color="error" class="mr-3" outlined>
          Отмена
        </v-btn>
        <v-btn @click="onSave" color="primary" :disabled="!isConfigValid(currentEditConfig)">
          Сохранить
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { store, validationRules as rules } from '../../settings';

function isConfigValid(config) {
  console.log(Boolean(config.name), typeof config.name, config.name.length)
  return Boolean(config.name) && typeof config.name === 'string' && config.name.length < 20 && config.name.length > 0
}
//@ts-ignore
const props = defineProps({
  currentEditConfig: {
    type: Object,
    required: true,
  },
  onSave: {
    type: Function,
    required: true,
  },
  onCancel: {
    type: Function,
    required: true,
  },
})
</script>
