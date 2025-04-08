<template>
  <v-data-table :items="prompts" :headers="headers">
    <template v-slot:top>
      <v-toolbar flat>
        <v-toolbar-title>Пользователи</v-toolbar-title>
        <v-divider class="mx-4" inset vertical></v-divider>

        <v-spacer></v-spacer>

        <v-dialog v-model="dialog" max-width="600px">
          <template v-slot:activator="{ props }">
            <v-btn class="mb-2" color="primary" dark v-bind="props" @click="() => {
              Object.assign(editedItem, defaultItem);
              editedIndex = -1;
            }">
              Создать
            </v-btn>
          </template>
          <v-card>
            <v-card-title class="pa-4 bg-primary">
              <span class="text-h5 text-white">{{ formTitle }}</span>
            </v-card-title>

            <v-card-text class="pa-6">
              <v-container class="pa-0">
                <v-row>
                  <v-col cols="12" md="6">
                    <v-text-field v-model="editedItem.name" label="Имя" variant="outlined" density="comfortable"
                      :rules="[rules.required, rules.maxLength(20)]" class="mb-4"></v-text-field>
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-text-field v-model="editedItem.email" label="Почта" variant="outlined" density="comfortable"
                      :rules="[rules.required, rules.email, rules.maxLength(255)]" class="mb-4"></v-text-field>
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-text-field v-model="editedItem.password" :label="editedIndex === -1 ? 'Пароль' : 'Новый пароль'" variant="outlined" density="comfortable"
                      type="text" class="mb-4"></v-text-field>
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-select v-model="editedItem.role" :items="rolesForSelect" label="Роль" variant="outlined"
                      density="comfortable" class="mb-4"></v-select>
                  </v-col>

                  <v-col cols="12" md="6">
                    <v-number-input v-model="editedItem.balance" :reverse="false" controlVariant="split"
                      label="Баланс токенов" :hideInput="false" variant="outlined" density="comfortable"
                      class="mb-4"></v-number-input>
                  </v-col>

                  <v-col cols="12" md="6" class="d-flex align-center">
                    <v-checkbox v-model="editedItem.email_verified" label="Почта верифицирована" density="comfortable"
                      class="mt-0"></v-checkbox>
                  </v-col>
                </v-row>
              </v-container>
            </v-card-text>

            <v-card-actions class="pa-4 bg-grey-lighten-3">
              <v-spacer></v-spacer>
              <v-btn color="grey-darken-2" variant="outlined" @click="close" class="mr-2">
                Отмена
              </v-btn>
              <v-btn :loading="editButtonLoading" color="primary" variant="flat" @click="save">
                Сохранить
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </v-toolbar>
    </template>
    <template v-slot:item.actions="{ item }">
      <v-icon class="me-2" size="small" @click="editItem(item)">mdi-pencil</v-icon>
      <v-icon size="small" @click="deleteItem(item)">{{ deleteButtonLoading ? 'mdi-loading' : 'mdi-delete' }}</v-icon>
    </template>
  </v-data-table>
</template>

<script setup lang="ts">
import { fetch_data } from '../helpers';
import { computed, onMounted, reactive, ref, Ref } from 'vue';
import { Config, DataTableHeader, validationRules as rules } from '../settings';
import { Method } from '../helpers';
import { UnnecessaryEventEmitter } from '../eventBus';

type User = {
  id: string;
  name: string;
  email: string;
  email_verified: boolean;
  password: string;
  role: string;
  balance: number;
}

const prompts: Ref<User[]> = ref([]);
const editedIndex = ref(-1);
const dialog = ref(false);
const dialogDelete = ref(false);
const formTitle = computed(() => editedIndex.value === -1 ? 'Новый пользователь' : 'Редактировать пользователя');
const editButtonLoading = ref(false);
const deleteButtonLoading = ref(false);
const editedItem = reactive({
  id: '',
  name: '',
  email: '',
  email_verified: false,
  password: '',
  role: Config.userRoles.user,
  balance: 0,
})
const defaultItem = Object.assign({}, editedItem);
console.log(defaultItem)

const rolesForSelect: any[] = [];
for (let role in Config.userRoles) {
  if (role === 'guest') continue;
  rolesForSelect.push({
    //@ts-ignore
    title: Config.userRoles[role],
    //@ts-ignore
    value: Config.userRoles[role]
  })
}
const headers = computed<DataTableHeader[]>(() => {
  const rawHeaders = [
    { key: 'id', title: 'ID', sortable: false, },
    { key: 'name', title: 'Имя', },
    { key: 'email', title: 'Почта', sortable: false, },
    { key: 'email_verified', title: 'Почта верифицирована', sortable: false, },
    { key: 'balance', title: 'Баланс токенов', sortable: false, },
    { key: 'role', title: 'Роль', },
    { key: 'actions', title: 'Действия', align: 'end', sortable: false, },
  ];
  // @ts-ignore
  const headers: DataTableHeader[] = rawHeaders.map(e => {
    const baseHeader = {
      key: '',
      title: '',
      align: 'start',
      sortable: true,
      width: undefined,
    };
    Object.assign(baseHeader, e);
    return baseHeader;
  });

  return headers;
});

onMounted(async () => {
  const response = await fetch_data(`${Config.backend_address}/users/`);
  if (!response) return
  prompts.value = response.data.list;
})

async function editItem(item: User) {
  editedIndex.value = prompts.value.indexOf(item)
  Object.assign(editedItem, item)
  dialog.value = true
}

async function deleteItem(item: User) {
  const response = await fetch_data(
    `${Config.backend_address}/users/${item.id}/`,
    'DELETE'
  )
  if (response) {
    UnnecessaryEventEmitter.emit(Config.alertMessageKey, {
      title: 'Пользователь удалён',
      text: undefined,
      severity: 'success'
    })
    dialogDelete.value = true;
    location.reload();
  }
}

async function close() {
  dialog.value = false
  Object.assign(editedItem, defaultItem)
  editedIndex.value = -1
}

async function save() {
  editButtonLoading.value = true
  let url = `${Config.backend_address}/users/`;
  let method = 'POST';
  if (editedIndex.value > -1) {
    url += `${editedItem.id}/`;
    method = 'PUT';
  }
  const response = await fetch_data(
    url,
    method as Method,
    JSON.stringify(editedItem)
  )
  editButtonLoading.value = false;
  if (response) {
    UnnecessaryEventEmitter.emit(Config.alertMessageKey, {
      title: 'Пользователь сохранён',
      text: undefined,
      severity: 'success'
    })
    location.reload();
  }
}
</script>

<style scoped></style>
