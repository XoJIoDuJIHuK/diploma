<template>
  <SimpleTranslator v-if="Config.is_simplified_translation_enabled" />

  <v-container>
    <v-row class="text-center">
      <v-col cols="12">
        <h1 class="text-h3 font-weight-bold mb-4">
          Добро пожаловать в GPTranslate
        </h1>
        <p class="text-body-1 mb-8">
          Превосходный инструмент для перевода текстов любой сложности.<br />
          Начните пользоваться уже сегодня!
        </p>
      </v-col>
    </v-row>

    <v-row class="mt-10">
      <v-col>
        <h2 class="text-h5 font-weight-bold">Наши преимущества</h2>
      </v-col>
    </v-row>
    <v-row class="text-center">
      <v-col cols="12" sm="4" v-for="(feature, index) in features" :key="index">
        <v-card class="pa-4 mx-auto" elevation="2" max-width="350">
          <v-container class="flex flex-row justify-center h-auto">
            <v-icon
              :icon="feature.icon"
              size="x-large"
              color="primary"
            ></v-icon>
          </v-container>
          <v-card-title class="text-h5 mt-2">{{ feature.title }}</v-card-title>
          <v-card-text class="text-body-2">{{
            feature.description
          }}</v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-10">
      <v-col cols="12">
        <h2 class="text-h5 font-weight-bold mb-4">Наша статистика</h2>
        <v-card>
          <v-card-text>
            <canvas id="translationChart"></canvas>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { Config } from "../settings";
import { Chart, registerables } from "chart.js";
import SimpleTranslator from "../components/SimpleTranslator.vue";

const features = ref([
  {
    icon: "mdi-translate",
    title: "Поражающая воображение скорость",
    description:
      "Переводите множество документов большого объёма в сжатые сроки",
  },
  {
    icon: "mdi-chart-line",
    title: "Большой выбор моделей для перевода",
    description:
      "Мы предлагаем прозрачный выбор инструментов, которыми вы пользуетесь",
  },
  {
    icon: "mdi-account",
    title: "Сохранение настроек",
    description:
      "Нужно часто переводить похожие тексты на одни и те же языки? Сохраните настройку и пользуйтесь ей",
  },
]);

onMounted(async () => {
  const ctx = document.getElementById("translationChart");
  Chart.register(...registerables);
  //@ts-ignore
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Английский", "Французский", "Русский", "Немецкий", "Китайский"],
      datasets: [
        {
          label: "Количество переводов",
          data: [120, 90, 60, 30, 50],
          backgroundColor: [
            "rgba(75, 192, 192, 0.6)",
            "rgba(153, 102, 255, 0.6)",
            "rgba(255, 159, 64, 0.6)",
            "rgba(255, 99, 132, 0.6)",
            "rgba(54, 162, 235, 0.6)",
          ],
          borderColor: [
            "rgba(75, 192, 192, 1)",
            "rgba(153, 102, 255, 1)",
            "rgba(255, 159, 64, 1)",
            "rgba(255, 99, 132, 1)",
            "rgba(54, 162, 235, 1)",
          ],
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    },
  });
});
</script>

<style scoped>
/* .fill-height {
  min-height: calc(100vh - 64px);
} */

.feature-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
  align-items: center;
}

.v-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
}

.v-icon {
  margin-bottom: 16px;
}

.v-card-title {
  margin-bottom: auto;
  text-align: center;
  text-wrap: wrap;
}

.v-card-text {
  margin-top: auto;
  text-align: center;
}

.gradient-background {
  background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
  color: white;
}

.v-row {
  max-height: max-content;
}
.v-col {
  max-height: max-content;
}
</style>
