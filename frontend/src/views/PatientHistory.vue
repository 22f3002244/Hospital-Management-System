<template>
  <nav class="navbar navbar-expand-lg bg-white border-bottom border-dark mb-4 px-3">
    <button class="btn btn-dark" @click="router.push(`/patient/${patientId}/dashboard`)">Home</button>
  </nav>

  <div class="container-fluid py-3">
    <h3 class="container text-center mb-4">Medical History</h3>

    <div class="container">
      <div v-if="isLoading" class="text-center my-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-2">Loading medical history...</p>
      </div>

      <div v-else-if="error" class="alert alert-danger" role="alert">
        <strong>Error:</strong> {{ error }}
      </div>
      
      <div class="text-end">
        <button class="btn btn-success btn-sm mb-2" @click="exportHistory" :disabled="exporting">
        <span v-if="exporting" class="spinner-border spinner-border-sm me-1"></span>
        {{ exporting ? 'Exporting...' : 'Export to CSV' }}
      </button>
      </div>
      
      <div v-if="emailStatus" class="alert mt-3" :class="emailStatus.type" role="alert">{{ emailStatus.message }}</div>
      <div v-else class="card border-dark">
        <div class="table-responsive">
          <div v-if="authStore.user">
            <table class="table table-bordered">
              <thead class="table-danger">
                <tr>
                  <th>Visit No.</th>
                  <th>Date</th>
                  <th>Doctor</th>
                  <th>Department</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(record, index) in history" :key="record.appointment_id">
                  <td>{{ history.length - index }}</td>
                  <td>
                    {{ formatDate(record.date) }}<br>
                  </td>
                  <td>Dr. {{ record.doctor }}</td>
                  <td>{{ record.department || 'N/A' }}</td>
                  <td>
                    <span class="badge" :class="getStatusBadge(record.status)">
                      {{ record.status }}
                    </span>
                  </td>
                  <td>
                    <button v-if="isDoctorOrAdmin" class="btn btn-sm btn-dark"
                      @click="viewDetails(record.appointment_id)">
                      View Details
                    </button>
                    <button v-else class="btn btn-sm btn-dark" @click="sendRecordByEmail(record.appointment_id)"
                      :disabled="sendingRecord === record.appointment_id">
                      <span v-if="sendingRecord === record.appointment_id"
                        class="spinner-border spinner-border-sm me-1"></span>
                      {{ sendingRecord === record.appointment_id ? 'Sending...' : 'Email PDF' }}
                    </button>
                  </td>
                </tr>
                <tr v-if="history.length === 0">
                  <td colspan="8" class="text-center text-muted py-4">
                    No medical history available
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const API_BASE = 'http://localhost:5000'

const patientId = ref(route.params.id)
const patientInfo = ref({
  name: '',
  email: '',
  phone: ''
})

const history = ref([])
const isLoading = ref(false)
const error = ref(null)
const sendingRecord = ref(null)
const emailStatus = ref(null)
const exporting = ref(false)

const isDoctorOrAdmin = computed(() => {
  const role = authStore.user?.role
  return role === 'doctor' || role === 'admin'
})

async function loadPatientHistory() {
  isLoading.value = true
  error.value = null
  try {
    console.log('Loading history for patient:', patientId.value)
    const response = await axios.get(
      `${API_BASE}/patient/${patientId.value}/history`,
      { withCredentials: true }
    )
    console.log('History response:', response.data)
    patientInfo.value = response.data.patient
    history.value = response.data.history
  } catch (err) {
    console.error('Failed to load patient history:', err)
    console.error('Error details:', err.response)
    if (err.response?.status === 403) {
      error.value = 'You do not have permission to view this patient\'s history.'
    } else if (err.response?.status === 404) {
      error.value = 'Patient not found.'
    } else if (err.response?.status === 401) {
      error.value = 'Please log in to view patient history.'
      setTimeout(() => {
        router.push('/login')
      }, 2000)
    } else {
      error.value = `Failed to load patient history: ${err.response?.data?.error || err.message}`
    }
  } finally {
    isLoading.value = false
  }
}

async function sendRecordByEmail(appointmentId) {
  sendingRecord.value = appointmentId
  emailStatus.value = null
  try {
    const response = await axios.post(
      `${API_BASE}/appointment/${appointmentId}/send-record`,
      {},
      { withCredentials: true }
    )

    emailStatus.value = {
      type: 'alert-success',
      message: response.data.message || 'Medical record sent successfully to your email!'
    }
    setTimeout(() => {
      emailStatus.value = null
    }, 2000)
  } catch (err) {
    console.error('Failed to send record:', err)
    emailStatus.value = {
      type: 'alert-danger',
      message: err.response?.data?.error || 'Failed to send medical record. Please try again.'
    }
  } finally {
    sendingRecord.value = null
  }
}

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

async function exportHistory() {
  exporting.value = true
  try {
    const response = await axios.post(
      `http://localhost:5000/export-patient/${patientId.value}`,
      {},
      { withCredentials: true }
    )
    alert('We have mailed you the CSV file!.')
  } catch (error) {
    console.error('Export failed:', error)
    alert('Failed to export history: ' + (error.response?.data?.error || error.message))
  } finally {
    exporting.value = false
  }
}

async function viewDetails(appointmentId) {
  try {
    const response = await axios.get(
      `${API_BASE}/appointment/${appointmentId}/details`,
      { withCredentials: true }
    )
    const data = response.data
    let message = `
Appointment ID: ${data.appointment_id}
Date: ${data.date} ${data.time}
Status: ${data.status}
Reason: ${data.reason || 'N/A'}

Doctor: Dr. ${data.doctor.name} (${data.doctor.specialization})
Department: ${data.doctor.department || 'N/A'}

Patient: ${data.patient.name}
Email: ${data.patient.email}
Phone: ${data.patient.phone}

Diagnosis: ${data.treatment.diagnosis || 'N/A'}
Prescription: ${data.treatment.prescription || 'N/A'}
Notes: ${data.treatment.notes || 'N/A'}
Follow-up Date: ${data.treatment.follow_up_date || 'N/A'}
    `

    alert(message)
  } catch (err) {
    console.error('Failed to fetch appointment details:', err)
    alert('Failed to load appointment details. You may not have access.')
  }
}

function getStatusBadge(status) {
  const badges = {
    'completed': 'bg-success',
    'booked': 'bg-primary',
    'confirmed': 'bg-info',
    'cancelled': 'bg-danger'
  }
  return badges[status] || 'bg-secondary'
}

onMounted(() => {
  console.log('Patient History page mounted')
  console.log('Patient ID:', patientId.value)
  loadPatientHistory()
})
</script>
