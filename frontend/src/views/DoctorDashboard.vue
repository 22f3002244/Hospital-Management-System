<template>
  <nav class="navbar navbar-light bg-white border-dark border-bottom mb-4">
    <div class="container-fluid">
      <span class="navbar-brand mb-0 h5">National Hospital</span>
      <div class="d-flex gap-2">
        <span class="navbar-text me-3">Welcome Dr. {{ doctorInfo.name }}</span>
        <button class="btn btn-dark" @click="router.push(`/doctor/${doctorId}/availability`)">Availability</button>
        <button class="btn btn-danger" @click="handleLogout">logout</button>
      </div>
    </div>
  </nav>

  <div class="container-fluid">
    <h3 class="container text-center mb-4">Wellcome to National Hospital</h3>

    <div class="container">

      <div class="card mb-4">
        <div class="card-header bg-primary text-white">
          <h5 class="mb-0">Upcoming Appointments</h5>
        </div>
        <div class="card-body">
          <div class="table-responsive">
            <table class="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Patient Name</th>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="apt in appointments" :key="apt.id">
                  <td>{{ apt.id }}</td>
                  <td>{{ apt.patient }}</td>
                  <td>{{ apt.date }}</td>
                  <td>{{ apt.time }}</td>
                  <td>
                    <span class="badge" :class="getStatusBadge(apt.status)">{{ apt.status }}</span>
                  </td>
                  <td>
                    <div v-if="apt.status === 'booked'">
                      <button class="btn btn-success btn-sm me-2" @click="updatePatientHistory(apt)">Update</button>
                      <button class="btn btn-danger btn-sm" @click="cancelAppointment(apt.id)">Cancel</button>
                    </div>
                    <div v-else>
                      <button class="btn btn-dark btn-sm me-2" :disabled="apt.status !== 'booked'">Update</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="appointments.length === 0">
                  <td colspan="7" class="text-center text-muted">No appointments found</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="card mb-4">
        <div class="card-header bg-dark text-white">
          <h5 class="mb-0">Recent Patients</h5>
        </div>
        <div class="card-body">
          <div class="table-responsive">
            <table class="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Patient Name</th>
                  <th>Last Visit</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="patient in recentPatients" :key="patient.id">
                  <td>{{ patient.id }}</td>
                  <td>{{ patient.name }}</td>
                  <td>{{ patient.last_visit }}</td>
                  <td>
                    <button class="btn btn-primary btn-sm" @click="viewPatientHistory(patient.id)">view</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

    </div>

    <div class="modal" :class="{ 'show d-block': showUpdateModal }" tabindex="-1" v-if="showUpdateModal">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Update Patient History</h5>
            <button type="button" class="btn-close" @click="showUpdateModal = false"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="handleUpdateHistory">
              <div class="mb-3">
                <label class="form-label">Tests Done</label>
                <input type="text" class="form-control" v-model="historyForm.tests" placeholder="ECG, Blood Test, etc.">
              </div>
              <div class="mb-3">
                <label class="form-label">Diagnosis</label>
                <textarea class="form-control" rows="3" v-model="historyForm.diagnosis" required></textarea>
              </div>
              <div class="mb-3">
                <label class="form-label">Prescription</label>
                <textarea class="form-control" rows="4" v-model="historyForm.prescription" required></textarea>
              </div>
              <div class="mb-3">
                <label class="form-label">Follow-up Date</label>
                <input type="date" class="form-control" v-model="historyForm.follow_up_date">
              </div>
              <div class="mb-3">
                <label class="form-label">Notes</label>
                <textarea class="form-control" rows="2" v-model="historyForm.notes"></textarea>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" @click="showUpdateModal = false">Close</button>
                <button type="submit" class="btn btn-primary">save</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show" v-if="showUpdateModal"></div>

  </div>
</template>

<script setup >
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const API_BASE = 'http://localhost:5000'
const doctorId = ref(route.params.id)

const doctorInfo = ref({
  name: '',
  specialization: '',
  department: '',
  email: ''
})

const appointments = ref([])
const recentPatients = ref([])
const showUpdateModal = ref(false)
const selectedAppointment = ref(null)

const historyForm = ref({
  visit_type: 'In-person',
  tests: '',
  diagnosis: '',
  prescription: '',
  medicines: [''],
  follow_up_date: '',
  notes: ''
})

async function loadDoctorDashboard() {
  try {
    const response = await axios.get(`${API_BASE}/doctor/${doctorId.value}/dashboard`, {withCredentials: true})
    doctorInfo.value = response.data.doctor
    appointments.value = response.data.appointments
    const patientMap = new Map()
    appointments.value.forEach(apt => {
      if (!patientMap.has(apt.patient_id)) {
        patientMap.set(apt.patient_id, {
          id: apt.patient_id,
          name: apt.patient,
          last_visit: apt.date
        })
      }
    })
    recentPatients.value = Array.from(patientMap.values())
  } catch (error) {
    console.error('Failed to load dashboard:', error)
  }
}

function updatePatientHistory(appointment) {
  selectedAppointment.value = appointment
  showUpdateModal.value = true
  historyForm.value = {
    visit_type: 'In-person',
    tests: '',
    diagnosis: '',
    prescription: '',
    medicines: [''],
    follow_up_date: '',
    notes: ''
  }
}

async function handleUpdateHistory() {
  try {
    await axios.post(
      `${API_BASE}/appointment/${selectedAppointment.value.id}/treatment`,
      historyForm.value,
      { withCredentials: true }
    )
    alert('Treatment record saved successfully!')
    showUpdateModal.value = false
    await loadDoctorDashboard()
  } catch (error) {
    console.error('Failed to save treatment:', error)
    alert('Failed to save treatment: ' + (error.response?.data?.error || error.message))
  }
}

function viewPatientHistory(patientId) {
  router.push(`/patient/${patientId}/history`)
}

async function cancelAppointment(appointmentId) {
  if (confirm('Are you sure you want to cancel this appointment?')) {
    try {
      await axios.delete(`${API_BASE}/appointment/${appointmentId}`, {
        withCredentials: true
      })
      alert('Appointment cancelled successfully!')
      await loadDoctorDashboard()
    } catch (error) {
      console.error('Failed to cancel appointment:', error)
      alert('Failed to cancel appointment: ' + (error.response?.data?.error || error.message))
    }
  }
}

function getStatusBadge(status) {
  const badges = {
    'booked': 'bg-primary',
    'completed': 'bg-success',
    'cancelled': 'bg-danger'
  }
  return badges[status] || 'bg-secondary'
}

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}

onMounted(() => {
  loadDoctorDashboard()
})
</script>