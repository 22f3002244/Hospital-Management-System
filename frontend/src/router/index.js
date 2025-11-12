import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import AdminDashboard from '@/views/AdminDashboard.vue'
import DoctorDashboard from '@/views/DoctorDashboard.vue'
import PatientDashboard from '@/views/PatientDashboard.vue'
import PatientHistory from '@/views/PatientHistory.vue'
import DoctorAvailability from '@/views/DoctorAvailability.vue'
import DepartmentView from '@/views/DepartmentView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login'
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresGuest: true }
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { requiresGuest: true }
    },
    {
      path: '/admin/dashboard',
      name: 'admin-dashboard',
      component: AdminDashboard,
      meta: { requiresAuth: true, role: 'admin' }
    },
    {
      path: '/doctor/:id/dashboard',
      name: 'doctor-dashboard',
      component: DoctorDashboard,
      meta: { requiresAuth: true, role: 'doctor' }
    },
    {
      path: '/department/:id',
      name: 'DepartmentDetails',
      component: DepartmentView,
    },
    {
      path: '/patient/:id/dashboard',
      name: 'patient-dashboard',
      component: PatientDashboard,
      meta: { requiresAuth: true, role: 'patient' }
    },
    {
      path: '/patient/:id/history',
      name: 'patient-history',
      component: PatientHistory,
      meta: { requiresAuth: true }
    },
    {
      path: '/doctor/:id/availability',
      name: 'doctor-availability',
      component: DoctorAvailability,
      meta: { requiresAuth: true, role: 'doctor' }
    },
    {
      path: '/departments/:id',
      name: 'department',
      component: DepartmentView,
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    if (authStore.user.role === 'admin') {
      next('/admin/dashboard')
    } else if (authStore.user.role === 'doctor') {
      next(`/doctor/${authStore.user.user_id}/dashboard`)
    } else {
      next(`/patient/${authStore.user.user_id}/dashboard`)
    }
  } else if (to.meta.role && authStore.user.role !== to.meta.role) {
    next('/')
  } else {
    next()
  }
})

export default router