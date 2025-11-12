<template>
  <nav class="navbar navbar-expand-lg bg-white border-bottom border-dark mb-4">
    <div class="container-fluid">
      <span class="navbar-brand mb-0 h5">National Hospital</span>
      <div class="d-flex gap-2">
        <span class="navbar-text me-3">Welcome {{ patientInfo.name }}</span>
        <button class="btn btn-dark" @click="router.push(`/patient/${patientId}/history`)">History</button>
        <button class="btn btn-dark" @click="showEditProfile = true">My Profile</button>
        <button class="btn btn-danger" @click="handleLogout">logout</button>
      </div>
    </div>
  </nav>

  <div class="container-fluid py-3">
    <h3 class="container mb-4 text-center">Welcome to National Hospital</h3>

    <div class="container mb-1">

      <div class="card mb-4 border-dark">
        <div class="card-header bg-primary bg-opacity-75 text-white d-flex justify-content-between align-items-center">
          <h5 class="mb-0">Departments</h5>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-4 mb-3" v-for="dept in departments" :key="dept.id">
              <div class="card">
                <div class="card-body">
                  <h6 class="card-title">{{ dept.name }}</h6>
                  <p class="card-text small text-muted">{{ dept.description }}</p>
                  <button class="btn btn-outline-dark mt-2 w-100" @click="viewDepartmentDetails(dept.id)">View
                    Details</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="card mb-4 border-dark">
        <div class="card-header bg-danger text-white d-flex justify-content-between align-items-center">
          <h5 class="mb-0">Upcoming Appointments</h5>
          <button class="btn btn-light btn-sm" @click="openBookingModal()">Book New Appointment</button>
        </div>
        <div class="card-body">
          <div class="table-responsive">
            <table class="table table-hover">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Doctor Name</th>
                  <th>Department</th>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="apt in appointments" :key="apt.id">
                  <td>{{ apt.id }}</td>
                  <td>Dr. {{ apt.doctor }}</td>
                  <td>{{ apt.department || 'N/A' }}</td>
                  <td>{{ apt.date }}</td>
                  <td>{{ apt.time }}</td>
                  <td>
                    <span class="badge" :class="getStatusBadge(apt.status)">{{ apt.status }}</span>
                  </td>
                  <td>
                    <button class="btn btn-sm btn-info me-2" @click="viewAppointmentDetails(apt)">view details</button>
                    <button class="btn btn-sm btn-danger" @click="cancelAppointment(apt.id)"
                      v-if="apt.status === 'booked'">cancel</button>
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

    </div>

    <div class="modal" :class="{ 'show d-block': showEditProfile }" tabindex="-1" v-if="showEditProfile">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Edit Profile</h5>
            <button type="button" class="btn-close" @click="showEditProfile = false"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="handleUpdateProfile">
              <div class="mb-3">
                <label class="form-label">Full Name</label>
                <input type="text" class="form-control" v-model="profileForm.full_name">
              </div>
              <div class="mb-3">
                <label class="form-label">Email</label>
                <input type="email" class="form-control" v-model="profileForm.email">
              </div>
              <div class="mb-3">
                <label class="form-label">Phone</label>
                <input type="tel" class="form-control" v-model="profileForm.phone">
              </div>
              <div class="mb-3">
                <label class="form-label">Age</label>
                <input type="number" class="form-control" v-model="profileForm.age">
              </div>
              <div class="mb-3">
                <label class="form-label">Gender</label>
                <select class="form-select" v-model="profileForm.gender">
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" @click="showEditProfile = false">Close</button>
                <button type="submit" class="btn btn-primary">Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show" v-if="showEditProfile"></div>

    <div class="modal" :class="{ 'show d-block': showBookModal }" tabindex="-1" v-if="showBookModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Book Appointment</h5>
            <button type="button" class="btn-close" @click="closeBookingModal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="handleBookAppointment">
              <div class="mb-3">
                <label class="form-label">Department</label>
                <select class="form-select" v-model="bookingForm.department_id" @change="loadDoctorsByDepartment"
                  required>
                  <option value="">Select Department</option>
                  <option v-for="dept in departments" :key="dept.id" :value="dept.id">{{ dept.name }}</option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label">Doctor</label>
                <select class="form-select" v-model="bookingForm.doctor_id" @change="onDoctorChange" required>
                  <option value="">Select Doctor</option>
                  <option v-for="doc in availableDoctors" :key="doc.id" :value="doc.id">Dr. {{ doc.name }}</option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label">Date</label>
                <input type="date" class="form-control" v-model="bookingForm.date" :min="minDate"
                  @change="checkAvailableSlots" required>
              </div>
              <div class="mb-3" v-if="bookingForm.date && bookingForm.doctor_id">
                <label class="form-label">Available Time Slots</label>
                <div v-if="loadingSlots" class="text-center">
                  <div class="spinner-border spinner-border-sm" role="status">
                    <span class="visually-hidden">Loading...</span>
                  </div>
                  <span class="ms-2">Loading available slots...</span>
                </div>
                <div v-else-if="availableTimeSlots.length === 0" class="alert alert-warning">
                  No available slots for this date. Please choose another date.
                </div>
                <div v-else class="d-flex flex-wrap gap-2">
                  <button type="button" v-for="slot in availableTimeSlots" :key="slot.start" class="btn btn-sm"
                    :class="bookingForm.time === slot.start ? 'btn-primary' : 'btn-outline-primary'"
                    @click="selectTimeSlot(slot.start)">
                    {{ slot.start }}
                  </button>
                </div>
              </div>
              <div class="mb-3">
                <label class="form-label">Selected Time</label>
                <input type="text" class="form-control" v-model="bookingForm.time" readonly required>
              </div>
              <div class="mb-3">
                <label class="form-label">Reason for Visit</label>
                <textarea class="form-control" rows="3" v-model="bookingForm.reason"></textarea>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" @click="closeBookingModal">Close</button>
                <button type="submit" class="btn btn-primary" :disabled="!bookingForm.time">Book Appointment</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show" v-if="showBookModal"></div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const appointments = ref([])
const departments = ref([])
const availableDoctors = ref([])
const availableTimeSlots = ref([])
const loadingSlots = ref(false)
const showEditProfile = ref(false)
const showBookModal = ref(false)
const API_BASE = 'http://localhost:5000'

const patientId = ref(route.params.id)
const patientInfo = ref({
  name: '',
  email: '',
  phone: '',
  age: null,
  gender: ''
})

const profileForm = ref({
  full_name: '',
  email: '',
  phone: '',
  age: null,
  gender: ''
})

const bookingForm = ref({
  department_id: '',
  doctor_id: '',
  date: '',
  time: '',
  reason: ''
})

const minDate = computed(() => {
  const today = new Date()
  return today.toISOString().split('T')[0]
})

function viewDepartmentDetails(departmentId) {
  router.push(`/department/${departmentId}`)
}

function openBookingModal(doctorId = null, departmentId = null) {
  showBookModal.value = true
  if (departmentId) {
    bookingForm.value.department_id = departmentId
    loadDoctorsByDepartment()
  }
  if (doctorId) {
    bookingForm.value.doctor_id = doctorId
  }
}

function closeBookingModal() {
  showBookModal.value = false
  bookingForm.value = {
    department_id: '',
    doctor_id: '',
    date: '',
    time: '',
    reason: ''
  }
  availableTimeSlots.value = []
}

async function loadPatientDashboard() {
  try {
    const response = await axios.get(`${API_BASE}/patient/${patientId.value}/dashboard`, { withCredentials: true })
    patientInfo.value = response.data.patient
    appointments.value = response.data.appointments
    profileForm.value = {
      full_name: patientInfo.value.name,
      email: patientInfo.value.email,
      phone: patientInfo.value.phone,
      age: patientInfo.value.age,
      gender: patientInfo.value.gender
    }
  } catch (error) {
    console.error('Failed to load dashboard:', error)
  }
}

async function loadDepartments() {
  try {
    const response = await axios.get(`${API_BASE}/departments`)
    departments.value = response.data
  } catch (error) {
    console.error('Failed to load departments:', error)
  }
}

async function loadDoctorsByDepartment() {
  if (!bookingForm.value.department_id) {
    availableDoctors.value = []
    return
  }
  try {
    const response = await axios.get(`${API_BASE}/departments/${bookingForm.value.department_id}/doctors`)
    availableDoctors.value = response.data
    bookingForm.value.doctor_id = ''
    bookingForm.value.time = ''
    availableTimeSlots.value = []
  } catch (error) {
    console.error('Failed to load doctors:', error)
    availableDoctors.value = []
  }
}

function onDoctorChange() {
  bookingForm.value.time = ''
  availableTimeSlots.value = []
  if (bookingForm.value.date) {
    checkAvailableSlots()
  }
}

async function checkAvailableSlots() {
  if (!bookingForm.value.doctor_id || !bookingForm.value.date) {
    return
  }
  loadingSlots.value = true
  availableTimeSlots.value = []
  bookingForm.value.time = ''
  try {
    const response = await axios.get(`${API_BASE}/doctors/${bookingForm.value.doctor_id}/available-slots`,
      { params: { date: bookingForm.value.date } }
    )
    if (response.data.slots && response.data.slots.length > 0) {
      const slots = []
      const currentTime = response.data.slots[0].current_time

      response.data.slots.forEach(slot => {
        const start = slot.start
        const end = slot.end
        const bookedTimes = slot.booked_times || []
        const startTime = parseTime(start)
        const endTime = parseTime(end)

        let currentSlot = startTime
        while (currentSlot + 30 <= endTime) {
          const timeStr = formatTime(currentSlot)
          if (bookedTimes.includes(timeStr)) {
            currentSlot += 30
            continue
          }
          if (currentTime) {
            const slotMinutes = parseTime(timeStr)
            const currentMinutes = parseTime(currentTime)
            if (slotMinutes <= currentMinutes) {
              currentSlot += 30
              continue
            }
          }
          slots.push({ start: timeStr })
          currentSlot += 30
        }
      })
      availableTimeSlots.value = slots
      if (slots.length === 0 && response.data.slots.length > 0) {
        alert('All time slots for this date are either booked or have passed. Please select another date.')
      }
    }
  } catch (error) {
    console.error('Failed to load available slots:', error)
    const errorMsg = error.response?.data?.error || 'Unable to load available time slots. Please try again.'
    alert(errorMsg)
  } finally {
    loadingSlots.value = false
  }
}

function parseTime(timeStr) {
  const [hours, minutes] = timeStr.split(':').map(Number)
  return hours * 60 + minutes
}

function formatTime(minutes) {
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}`
}

function selectTimeSlot(time) {
  bookingForm.value.time = time
}

async function handleUpdateProfile() {
  try {
    await axios.put(`${API_BASE}/patient/${patientId.value}`, profileForm.value, {
      withCredentials: true
    })
    showEditProfile.value = false
    await loadPatientDashboard()
    alert('Profile updated successfully!')
  } catch (error) {
    console.error('Failed to update profile:', error)
    alert('Failed to update profile. Please try again.')
  }
}

async function handleBookAppointment() {
  try {
    await axios.post(`${API_BASE}/appointment`, bookingForm.value, {
      withCredentials: true
    })
    alert('Appointment booked successfully!')
    closeBookingModal()
    await loadPatientDashboard()
  } catch (error) {
    console.error('Failed to book appointment:', error)

    let errorMsg = 'Failed to book appointment. Please try again.'
    if (error.response?.status === 409) {
      errorMsg = error.response.data.error || 'This time slot is already booked. Please select another time.'
      await checkAvailableSlots()
    } else if (error.response?.status === 400) {
      errorMsg = error.response.data.error || 'Invalid booking details. Please check your selection.'
    } else if (error.response?.data?.error) {
      errorMsg = error.response.data.error
    }
    alert(errorMsg)
  }
}

function viewAppointmentDetails(appointment) {
  alert(`Appointment Details:\nDoctor: Dr. ${appointment.doctor}\nDepartment: ${appointment.department}\nDate: ${appointment.date}\nTime: ${appointment.time}\nStatus: ${appointment.status}\nReason: ${appointment.reason || 'N/A'}`)
}

async function cancelAppointment(appointmentId) {
  if (confirm('Are you sure you want to cancel this appointment?')) {
    try {
      await axios.delete(`${API_BASE}/appointment/${appointmentId}`, {
        withCredentials: true,
        headers: { 'Content-Type': 'application/json' },
        data: {}
      })
      alert('Appointment cancelled successfully!')
      await loadPatientDashboard()
    } catch (error) {
      console.error('Failed to cancel appointment:', error)
      alert(error.response?.data?.error || 'Failed to cancel appointment. Please try again.')
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

watch(() => route.query.doctor, (doctorId) => {
  if (doctorId && showBookModal.value === false) {
    const doctor = availableDoctors.value.find(d => d.id === parseInt(doctorId))
    if (doctor) {
      openBookingModal(parseInt(doctorId), doctor.department_id)
    }
  }
}, { immediate: true })

onMounted(async () => {
  await loadPatientDashboard()
  await loadDepartments()
  if (route.query.doctor) {
    const doctorId = parseInt(route.query.doctor)
    for (const dept of departments.value) {
      try {
        const response = await axios.get(`${API_BASE}/departments/${dept.id}/doctors`)
        const doctor = response.data.find(d => d.id === doctorId)
        if (doctor) {
          openBookingModal(doctorId, dept.id)
          break
        }
      } catch (error) {
        console.error('Error loading doctors for department:', dept.id)
      }
    }
  }
})
</script>