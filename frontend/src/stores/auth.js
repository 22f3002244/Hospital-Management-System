import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE = 'http://localhost:5000'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const isAuthenticated = computed(() => !!user.value)
  async function login(username, password) {
    try {
      const response = await axios.post(`${API_BASE}/login`, 
        { username, password },
        { withCredentials: true }
      )
      user.value = {
        role: response.data.role,
        user_id: response.data.user_id || response.data.doctor_id,
        name: response.data.name
      }
      return { success: true, data: response.data }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'Login failed' 
      }
    }
  }

  async function register(userData) {
    try {
      const response = await axios.post(`${API_BASE}/register`, userData)
      return { success: true, data: response.data }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'Registration failed' 
      }
    }
  }

  async function logout() {
    try {
      await axios.post(`${API_BASE}/logout`, {}, { withCredentials: true })
      user.value = null
      return { success: true }
    } catch (error) {
      return { success: false, error: 'Logout failed' }
    }
  }
  
  return {user,isAuthenticated, login,register,logout}
})