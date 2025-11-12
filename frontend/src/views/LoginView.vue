<template>
  <div class="container-fluid vh-100 d-flex align-items-center justify-content-center bg-light">
    <div class="card" style="width: 400px;">
      <div class="card-body">
        <h3 class="card-title text-center mb-4">National Hospital</h3>
        
        <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>
        <form @submit.prevent="handleLogin">
          <div class="mb-3">
            <input type="text" class="form-control" id="username" v-model="username" placeholder="Username"required>
          </div>
          <div class="mb-3">
            <input type="password" class="form-control" id="password" v-model="password"placeholder="Password" required>
          </div>
          <div class="d-grid">
            <button type="submit" class="btn btn-primary" :disabled="loading">
              {{ loading ? 'Logging in...' : 'Login' }}
            </button>
          </div>
        </form>
        <div class="text-center mt-3">
          <small>Do not have an account? 
            <router-link to="/register" class="text-decoration-none">Register</router-link>
          </small>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
input{
  box-shadow: none !important;
}
</style>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true

  const result = await authStore.login(username.value, password.value)
  loading.value = false

  if (result.success) {
    const role = result.data.role
    const userId = result.data.user_id || result.data.doctor_id
    if (role === 'admin') {
      router.push('/admin/dashboard')
    } else if (role === 'doctor') {
      router.push(`/doctor/${userId}/dashboard`)
    } else {
      router.push(`/patient/${userId}/dashboard`)
    }
  } else {
    error.value = result.error
  }
}
</script>
