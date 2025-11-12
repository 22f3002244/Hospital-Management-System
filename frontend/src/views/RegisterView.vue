<template>
  <div class="container-fluid vh-100 d-flex align-items-center justify-content-center bg-light">
    <div class="card" style="width: 500px;">
      <div class="card-body">
        <h3 class="card-title text-center mb-4">Create Account</h3>
        <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>
        <div v-if="success" class="alert alert-success" role="alert">Registration successful! Redirecting to login...
        </div>

        <form @submit.prevent="handleRegister">
          <div class="mb-3">
            <input type="text" class="form-control" id="username" placeholder="Username" v-model="formData.username"
              required>
          </div>
          <div class="mb-3">
            <input type="password" class="form-control" id="password" placeholder="Password" v-model="formData.password"
              required>
          </div>
          <div class="mb-3">
            <input type="text" class="form-control" placeholder="Full Name" id="fullName" v-model="formData.full_name">
          </div>
          <div class="mb-3">
            <input type="email" class="form-control" placeholder="Email" id="email" v-model="formData.email">
          </div>
          <div class="row">
            <div class="col-md-6 mb-3">
              <input type="number" class="form-control" id="age" placeholder="Age" v-model="formData.age">
            </div>
            <div class="col-md-6 mb-3">
              <select class="form-select" id="gender" v-model="formData.gender">
                <option value="" disabled selected>Gender</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          <div class="mb-3">
            <input type="tel" class="form-control" id="phone" placeholder="Contact No." v-model="formData.phone">
          </div>
          <div class="mb-3">
            <textarea class="form-control" id="address" rows="2" placeholder="Address"
              v-model="formData.address"></textarea>
          </div>
          <div class="d-grid">
            <button type="submit" class="btn btn-primary" :disabled="loading">
              {{ loading ? 'Registering...' : 'Register' }}
            </button>
          </div>
        </form>

        <div class="text-center mt-3">
          <small>Already have an account?
            <router-link to="/login" class="text-decoration-none">Login</router-link>
          </small>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
input,
textarea {
  box-shadow: none !important;
}
</style>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const error = ref('')
const success = ref(false)
const loading = ref(false)

const formData = ref({
  username: '',
  password: '',
  full_name: '',
  email: '',
  phone: '',
  age: '',
  gender: '',
  address: ''
})

async function handleRegister() {
  error.value = ''
  loading.value = true
  const result = await authStore.register(formData.value)
  loading.value = false
  if (result.success) {
    success.value = true
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } else {
    error.value = result.error
  }
}
</script>