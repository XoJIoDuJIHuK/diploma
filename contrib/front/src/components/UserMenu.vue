<template>
  <v-menu location="end">
    <template v-slot:activator="{ props }">
      <v-btn v-bind="props" variant="elevated" color="white" class="user-menu-button">
        <span class="user-name">{{ userInfo.name }}</span>
        <span v-if="userInfo.role === Config.userRoles.user" class="user-balance">
          | {{ store.balance }}
        </span>
      </v-btn>
    </template>

    <v-list class="user-menu-list">
      <v-list-item>
        <router-link to="/sessions" class="menu-link">
          <v-btn variant="tonal" color="primary" block>
            <v-list-item-title>Сессии</v-list-item-title>
          </v-btn>
        </router-link>
      </v-list-item>

      <v-list-item>
        <router-link to="/personal" class="menu-link">
          <v-btn variant="tonal" color="primary" block>
            <v-list-item-title>Смена имени</v-list-item-title>
          </v-btn>
        </router-link>
      </v-list-item>

      <v-list-item>
        <v-btn variant="tonal" color="primary" @click="logout" block>
          <v-list-item-title>Выйти</v-list-item-title>
        </v-btn>
      </v-list-item>
    </v-list>
  </v-menu>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue';
import { logout } from '../helpers';
import { Config, store } from '../settings';

const userInfo = reactive({
  id: '',
  name: '',
  email: '',
  role: '',
})

onMounted(async () => {
  const cachedUserInfo = localStorage.getItem(Config.userInfoProperty) ? JSON.parse(localStorage.getItem(Config.userInfoProperty) as string) : {};
  if (!userInfo) {
    await logout();
  }
  userInfo.id = cachedUserInfo.id;
  userInfo.name = cachedUserInfo.name;
  userInfo.email = cachedUserInfo.email;
  userInfo.role = cachedUserInfo.role;
})


</script>

<style scoped>
.user-menu-button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: max-content;
}

.user-name {
  flex-grow: 1;
  text-align: left;
  margin-right: 0.5rem;
}

.user-balance {
  white-space: nowrap;
}

.user-menu-list {
  width: 200px;
}

.menu-link {
  text-decoration: none;
  color: inherit;
  display: block;
}
</style>
