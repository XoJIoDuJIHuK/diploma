<template>
  <div class="reports-container">
    <!-- FILTERS & SORT CONTROLS -->
    <v-container class="pa-0 mb-6">
      <v-row align="center" justify="space-between" no-gutters>
        <!-- Status filter -->
        <v-col cols="12" sm="4" class="pr-sm-2">
          <v-select v-model="selectedStatuses" :items="Object.values(Config.reportStatuses)" label="Статус" clearable
            density="comfortable" variant="outlined" />
        </v-col>
        <!-- Reason filter -->
        <v-col cols="12" sm="4" class="px-sm-2">
          <v-select v-model="selectedReasons" :items="store.reportReasons.getSelectItems()" label="Причина" clearable
            density="comfortable" variant="outlined" />
        </v-col>
      </v-row>
      <v-row>
        <v-btn-toggle v-model="sortKey" mandatory class="mr-2" tile>
          <v-btn value="created_at">По дате создания</v-btn>
          <v-btn value="closed_at">По дате закрытия</v-btn>
        </v-btn-toggle>

        <v-btn icon @click="sortDesc = !sortDesc">
          <v-icon>{{ sortDesc ? 'mdi-arrow-down' : 'mdi-arrow-up' }}</v-icon>
        </v-btn>
      </v-row>
    </v-container>

    <Suspense>
      <template #default>
        <v-container v-if="reports" class="pa-0">
          <v-card v-for="report in reports" :key="report.article_id + '::' + report.created_at" class="mb-6"
            variant="outlined">
            <v-card-item>
              <v-row align="center" no-gutters>
                <v-col cols="12" sm="auto" class="pe-sm-4">
                  <router-link :to="`/articles/${report.article_id}/report/`" class="text-decoration-none">
                    <v-btn variant="outlined" color="primary" prepend-icon="mdi-file-document-outline">
                      {{ report.article_title }}
                    </v-btn>
                  </router-link>
                </v-col>

                <v-col cols="12" sm="auto" class="mt-2 mt-sm-0">
                  <v-chip :color="getStatusColor(report.status)" variant="outlined" size="small">
                    {{ report.status }}
                  </v-chip>
                </v-col>
              </v-row>

              <!-- Reason / Created info -->
              <v-row class="mt-3">
                <v-col cols="12" sm="6">
                  <strong>Причина:</strong> {{ report.reason_text }}
                </v-col>
                <v-col cols="12" sm="6">
                  <strong>Создана:</strong>
                  {{ formatDate(report.created_at) }}
                  пользователем {{ report.created_by_user_name }}
                </v-col>
              </v-row>

              <!-- Closed info (if any) -->
              <v-row v-if="report.closed_at" class="mt-2">
                <v-col cols="12">
                  <strong>Закрыта:</strong>
                  {{ formatDate(report.closed_at) }}
                  пользователем {{ report.closed_by_user_name }}
                </v-col>
              </v-row>
            </v-card-item>
          </v-card>
        </v-container>
      </template>

      <template #fallback>
        <v-container class="text-center py-8">
          <v-progress-circular indeterminate color="primary" size="64" />
          <div class="mt-4 text-body-1">Загрузка жалоб...</div>
        </v-container>
      </template>
    </Suspense>

    <!-- No reports message -->
    <v-container v-if="!isLoading && !reports.length" class="pt-6">
      <v-alert type="success" variant="tonal" icon="mdi-check-circle-outline">
        Жалоб нет. Хорошая работа!
      </v-alert>
    </v-container>

    <!-- pagination -->
    <v-container v-if="pagination.total_pages > 1" class="d-flex justify-center pt-6">
      <v-pagination v-model="pagination.page" :length="pagination.total_pages" :total-visible="7" active-color="primary"
        variant="flat" />
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch, watchEffect, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { fetch_data } from '../helpers';
import { Config, store } from '../settings';

type Report = {
  article_id: string;
  article_title: string;
  reason_text: string;
  status: string;
  text: string;
  closed_at: Date | null;
  created_at: Date;
  closed_by_user_name: string | null;
  created_by_user_name: string;
}

const route = useRoute();
const router = useRouter();
const isLoading = ref(true);
const reports = ref<Array<Report>>([]);
const pagination = reactive({
  page: route.query.page ? parseInt(route.query.page as string) : 1,
  total_pages: 1,
});

const selectedStatuses = ref<string>('');
const selectedReasons = ref<string[]>('');
const sortKey = ref<'created_at' | 'closed_at'>('created_at');
const sortDesc = ref(false);


function formatDate(d: Date | string) {
  return new Date(d).toLocaleString();
}

function getStatusColor(reportStatus: string): string {
  switch (reportStatus) {
    case Config.reportStatuses.open:
      return 'blue';
    case Config.reportStatuses.closedByUser:
      return 'orange';
    case Config.reportStatuses.satisfied:
      return 'green';
    case Config.reportStatuses.rejected:
      return 'red';
    default:
      console.error('Unexpected report status: ', reportStatus);
      return 'pink';
  }
}

onMounted(updateReportsList);

async function updateReportsList() {
  let url = new URL(`${Config.backend_address}/reports/`);
  for (let key in route.query) {
    if (route.query[key] != '') {
      url.searchParams.append(key, route.query[key] === '' ? null : route.query[key]);
    }
  }
  const response = await fetch_data(url.toString());
  if (response) {
    reports.value = response.data.list;
    Object.assign(pagination, response.pagination);
  }
  isLoading.value = false;
}

watch(
  [() => pagination.page, selectedStatuses, selectedReasons, sortKey, sortDesc],
  async () => {
    isLoading.value = true;
    await router.push({
      query: {
        ...route.query,
        page: pagination.page,
        status: selectedStatuses.value || '',
        reason_id: selectedReasons.value || '',
        sort_by: sortKey.value,
        desc: sortDesc.value
      }
    });
    await updateReportsList();
  }
);

// watchEffect(async () => {
//   await updateReportsList();
// });
</script>

<style scoped>
.reports-container {
  max-width: 1200px;
  margin: 0 auto;
}

.v-card {
  transition: box-shadow 0.2s ease;
}

.v-card:hover {
  box-shadow:
    0 3px 5px -1px rgba(0, 0, 0, 0.1),
    0 5px 8px 0 rgba(0, 0, 0, 0.1),
    0 1px 14px 0 rgba(0, 0, 0, 0.1);
}
</style>
