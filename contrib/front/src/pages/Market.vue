<template>
  <v-container class="product-list-container">
    <v-row justify="center">
      <v-col cols="12" sm="8" md="6">
        <v-card v-for="product in products" :key="product.id" class="product-item mb-4" elevation="2">
          <v-card-text class="text-center">
            <h3 class="text-h5 mb-2">{{ product.name }}</h3>
            <p class="text-subtitle-1 mb-4">
              {{ (product.price.amount / 100).toFixed(2) }}
              {{ product.price.currency.toUpperCase() }}
            </p>
            <v-btn :href="`${Config.backend_address}/payment/create-checkout-session/${product.id}`" color="primary"
              variant="flat" block>
              Купить
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { fetch_data } from '../helpers';
import { Config } from '../settings';
import { onMounted, ref, Ref } from 'vue';

interface Price {
  amount: number;
  currency: string;
}
interface Product {
  id: string;
  name: string;
  price: Price;
}

const products: Ref<Array<Product>> = ref([]);

onMounted(async () => {
  const response = await fetch_data(
    `${Config.backend_address}/payment/products/`
  );
  products.value = response.data.list;
});
</script>


<style scoped>
.product-list-container {
  padding-top: 32px;
  padding-bottom: 32px;
}

.product-item {
  transition: transform 0.2s ease-in-out;
}

.product-item:hover {
  transform: translateY(-2px);
}
</style>
