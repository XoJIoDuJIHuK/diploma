<template>
  <v-layout>
    <v-app>
      <v-app-bar color="primary" dark>
        <v-app-bar-title>{{ appName }}</v-app-bar-title>
        <div class="mr-4 user-links">
          <div>
            <div v-if="userRole === Config.userRoles.guest">
              <v-btn color="white" @click="
                () => {
                  loginData.isVisible = true;
                  loginData.isLogin = true;
                }
              " variant="elevated">Вход</v-btn>
              <v-btn @click="
                () => {
                  loginData.isVisible = true;
                  loginData.isLogin = false;
                }
              " variant="elevated" color="white" class="ml-4">Регистрация</v-btn>
            </div>
            <div v-else>
              <router-link to="/landing">
                <v-btn variant="elevated" color="white" class="nav-btn">
                  <v-icon left>mdi-home</v-icon>
                  <span class="nav-btn-text">Домашняя</span>
                </v-btn>
              </router-link>
            </div>
            <div v-if="userRole === Config.userRoles.user">
              <router-link to="/articles">
                <v-btn variant="elevated" color="white" class="nav-btn">
                  <v-icon left>mdi-file-document-edit-outline</v-icon>
                  <span class="nav-btn-text">Исходные статьи</span>
                </v-btn>
              </router-link>
              <router-link to="/configs">
                <v-btn variant="elevated" color="white" class="nav-btn">
                  <v-icon left>mdi-cogs</v-icon>
                  <span class="nav-btn-text">Настройки переводчика</span>
                </v-btn>
              </router-link>
              <router-link to="/market">
                <v-btn variant="elevated" color="white" class="nav-btn">
                  <v-icon left>mdi-cart-outline</v-icon>
                  <span class="nav-btn-text">Покупка токенов</span>
                </v-btn>
              </router-link>
            </div>
            <div v-else-if="userRole === Config.userRoles.mod">
              <router-link to="/reports">
                <v-btn variant="elevated" color="white" class="nav-btn">
                  <v-icon left>mdi-alert-octagon-outline</v-icon>
                  <span class="nav-btn-text">Жалобы</span>
                </v-btn>
              </router-link>
            </div>
            <div v-else-if="userRole === Config.userRoles.admin">
              <router-link to="/users">
                <v-btn variant="elevated" color="white" class="nav-btn">
                  <v-icon left>mdi-account-multiple-outline</v-icon>
                  <span class="nav-btn-text">Пользователи</span>
                </v-btn>
              </router-link>
              <router-link to="/analytics">
                <v-btn variant="elevated" color="white" class="nav-btn">
                  <v-icon left>mdi-chart-bar</v-icon>
                  <span class="nav-btn-text">Аналитика</span>
                </v-btn>
              </router-link>
              <router-link to="/prompts">
                <v-btn variant="elevated" color="white" class="nav-btn">
                  <v-icon left>mdi-format-text-wrapping-overflow</v-icon>
                  <span class="nav-btn-text">Промпты</span>
                </v-btn>
              </router-link>
              <router-link to="/models">
                <v-btn variant="elevated" color="white" class="nav-btn">
                  <v-icon left>mdi-robot-outline</v-icon>
                  <span class="nav-btn-text">Модели</span>
                </v-btn>
              </router-link>
            </div>
          </div>
          <div>
            <Notifications v-if="userRole === Config.userRoles.user" />
            <UserMenu v-if="userRole !== Config.userRoles.guest" class="mr-4" />
          </div>
        </div>
      </v-app-bar>
      <v-main>
        <router-view />
      </v-main>
      <v-footer color="primary">
        <v-row justify="center" no-gutters>
          <a :href="icon.href" v-for="icon in icons">
            <v-btn :key="icon.value" class="mx-4 white--text" icon>
              <v-icon size="30px" style="margin-top: 8px">{{
                icon.value
                }}</v-icon>
            </v-btn>
          </a>
        </v-row>
        <v-col class="text-center white--text">
          {{ new Date().getFullYear() }} — <strong>{{ appName }}</strong>
        </v-col>
      </v-footer>
      <v-container class="login-form-wrapper" v-if="loginData.isVisible">
        <v-container class="login-form">
          <v-card class="mx-auto" width="400" elevation="12">
            <v-card-title class="d-flex justify-space-between align-center pa-4">
              <span class="text-h5 font-weight-bold">
                {{ loginData.isLogin ? "Вход в систему" : "Регистрация" }}
              </span>
              <v-btn icon variant="text" @click="loginData.isVisible = false">
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </v-card-title>

            <v-divider></v-divider>

            <v-card-text class="px-6 py-4">
              <v-form v-model="loginData.form" @submit.prevent="onSubmit">
                <v-text-field v-if="!loginData.isLogin" v-model="loginData.name" :readonly="loginData.isLoading"
                  :rules="[rules.required, rules.maxLength(20)]" class="mb-4" variant="outlined" label="Имя"
                  density="comfortable" clearable></v-text-field>

                <v-text-field v-model="loginData.email" :readonly="loginData.isLoading"
                  :rules="[rules.required, rules.email, rules.maxLength(255)]" class="mb-4" variant="outlined"
                  label="Почта" density="comfortable" clearable></v-text-field>

                <v-text-field v-model="loginData.password"
                  :append-inner-icon="loginData.showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                  :type="loginData.showPassword ? 'text' : 'password'" :readonly="loginData.isLoading"
                  :rules="[rules.required]" variant="outlined" label="Пароль" density="comfortable"
                  placeholder="Введите пароль" clearable
                  @click:append-inner="loginData.showPassword = !loginData.showPassword"></v-text-field>

                <v-alert v-if="loginData.displayError" type="error" density="compact" variant="tonal" class="mb-4">
                  {{ loginData.displayError }}
                </v-alert>

                <v-btn :disabled="!loginData.form" :loading="loginData.isLoading" color="primary" size="large"
                  type="submit" variant="flat" block class="mb-2">
                  {{ loginData.isLogin ? "Войти" : "Зарегистрироваться" }}
                </v-btn>

                <v-btn v-if="loginData.isLogin" @click="onForgotPassword" color="secondary" size="large"
                  variant="outlined" block class="mb-2">
                  Восстановить пароль
                </v-btn>

                <v-btn v-if="loginData.isLogin" @click="onConfirmEmail" color="secondary" size="large"
                  variant="outlined" block class="mb-2">
                  Подтвердить почту
                </v-btn>

                <div class="text-center mt-3">
                  <v-btn variant="plain" size="small" @click="loginData.isLogin = !loginData.isLogin"
                    class="text-secondary">
                    {{ loginData.isLogin ? "Создать аккаунт" : "Уже есть аккаунт?" }}
                  </v-btn>
                </div>
              </v-form>
            </v-card-text>
          </v-card>
        </v-container>
      </v-container>
    </v-app>
  </v-layout>
</template>

<script setup lang="ts">
import UserMenu from "./UserMenu.vue";
import { ref, reactive, onMounted } from "vue";
import { fetch_data, fetchPersonalInfo } from "../helpers";
import Notifications from "./Notifications.vue";
import { Config, validationRules as rules } from "../settings";
import { UnnecessaryEventEmitter } from "../eventBus";

const loginData = reactive({
  form: false,
  displayError: "",
  isVisible: false,
  isLogin: true,
  isLoading: false,
  showPassword: false,
  email: "",
  password: "",
  name: "",
});
const userRole = ref(Config.userRoles.guest);

const oauthProviders = [
  {
    code: "google",
    name: "Google",
    icon: "google",
  },
];

const icons = ref([
  {
    href: "https://www.linkedin.com/in/aleh-t-30580927b/",
    value: "mdi-linkedin",
  },
  { href: "https://t.me/XoJIoDuJIHuK", value: "mdi-telegram" },
  { href: "https://vk.com/jertva_rastishki", value: "mdi-vk" },
  { href: "http://github.com/XoJIoDuJIHuK", value: "mdi-github" },
]);
const appName = ref("GPTranslate");

async function onSubmit() {
  loginData.isLoading = true;
  try {
    const result = await fetch_data(
      `${Config.backend_address}/auth/${loginData.isLogin ? "login" : "register"
      }/`,
      "POST",
      JSON.stringify({
        email: loginData.email,
        password: loginData.password,
        name: loginData.name,
      }),
      false,
      true
    );
    if (result) {
      loginData.isVisible = false;
      loginData.form = false;
      loginData.email = "";
      loginData.password = "";
      loginData.name = "";
      loginData.showPassword = false;

      if (!loginData.isLogin) return;

      await fetchPersonalInfo();

      UnnecessaryEventEmitter.emit(Config.alertMessageKey, {
        title: result.detail,
        text: undefined,
        severity: "info",
      });

      location.reload();
    }
  } catch (e) {
    loginData.displayError = e as string;
    setTimeout(function () {
      loginData.displayError = "";
    }, 3000);
  }
  loginData.isLoading = false;
}

async function onForgotPassword() {
  if (!loginData.email) {
    loginData.displayError = "Введите почту";
    return;
  }
  const response = await fetch_data(
    `${Config.backend_address}/auth/restore-password/request/?email=${loginData.email}`,
    "POST"
  );
  if (response) {
    UnnecessaryEventEmitter.emit(Config.alertMessageKey, {
      title: response.message,
      text: undefined,
      severity: "info",
    });
    loginData.isVisible = false;
  }
}

async function onConfirmEmail() {
  if (!loginData.email) {
    loginData.displayError = "Введите почту";
    return;
  }
  const response = await fetch_data(
    `${Config.backend_address}/auth/confirm-email/request/?email=${loginData.email}`,
    "POST"
  );
  if (response) {
    UnnecessaryEventEmitter.emit(Config.alertMessageKey, {
      title: response.message,
      text: undefined,
      severity: "info",
    });
    loginData.isVisible = false;
  }
}
onMounted(async () => {
  if (await fetchPersonalInfo(false)) {
    userRole.value = localStorage.getItem(Config.userInfoProperty)
      ? JSON.parse(localStorage.getItem(Config.userInfoProperty) as string).role
      : Config.userRoles.guest;
  }
});
</script>

<style scoped>
header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: max-content;
  margin: 0;
  padding: 0;
}

.v-app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.v-footer {
  max-height: fit-content;
}

.v-app-bar {
  display: flex;
  flex-direction: row;
}

.v-row {
  width: 100%;
}

.v-col:nth-child(2) {
  max-width: fit-content;
  margin-right: 10px;
}

.v-col:nth-child(3) {
  max-width: fit-content;
}


.login-form {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 9999;
  max-width: 95vw;
}

.login-form-wrapper {
  z-index: 9998;
  margin: 0;
  padding: 0;
  position: fixed;
  width: 100vw;
  max-width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(3px);
}


.user-links {
  display: flex;
  align-items: center;
  transition: all 0.3s ease-in-out;
  overflow-x: hidden;
  width: max-content;
  max-width: 100%;
  height: 100%;
}

.user-links>div {
  display: flex;
  flex-direction: row;
  align-items: inherit;
  width: max-content;
  max-width: max-content;
}

.nav-btn {
  overflow: hidden;
  width: min-content;
  min-width: auto;
  margin-right: 1em;
  padding-left: 7px;
  padding-right: 0px;
  transition: width 0.5s ease-in-out, padding 0.5s ease-in-out;
  display: inline-flex;
  justify-content: center;
}

.nav-btn-text {
  width: 0;
  padding-left: 7px;
  padding-right: 7px;
  white-space: nowrap;
  transform-origin: left center;
  transform: scaleX(0);
  transition: transform 0.5s ease-in-out, padding 0.5s ease-in-out;
}

.nav-btn:hover .nav-btn-text {
  width: max-content;
  transform: scaleX(1);
  padding-left: 7px;
}

.nav-btn:hover {
  width: auto;
  min-width: 100px;
  padding-left: 15px;
  padding-right: 15px;
  justify-content: flex-start;
}

.nav-btn:hover .nav-btn-text {
  opacity: 1;
  padding-left: 7px;
}
</style>
