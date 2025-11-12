<template>
  <nav class="navbar navbar-light bg-white border-dark border-bottom px-2 mb-4">
    <div class="container-fluid">
      <button class="btn btn-sm btn-dark" @click="goBack">Back</button>
      <span class="navbar-brand mb-0 h5">Department Details</span>
      <div></div>
    </div>
  </nav>

  <div class="container-fluid">
    <div class="container">
      <div v-if="isLoading" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-2">Loading department information...</p>
      </div>

      <div v-else-if="error" class="alert alert-danger" role="alert">
        <h4 class="alert-heading">Error!</h4>
        <p>{{ error }}</p>
        <button class="btn btn-primary" @click="loadDepartment()">Try Again</button>
      </div>

      <div v-else>
        <div class="card mb-4">
          <div class="card-header bg-primary text-white">
            <h4 class="mb-0">{{ department.name }}</h4>
          </div>
          <div class="card-body">
            <h5>Overview</h5>
            <p>{{ department.description }}</p>
            <div class="mt-4">
              <h5>About the Department</h5>
              <p>{{ department.details || 'This department provides specialized medical care and treatment to patients.'
              }}</p>
            </div>
          </div>
        </div>

        <div class="card mb-4">

          <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center">
            <h5 class="mb-0">Doctors' list</h5>
            <button v-if="doctors.length > 4" class="btn btn-sm btn-primary" @click="showAllDoctors = !showAllDoctors">
              {{ showAllDoctors ? 'Show Less' : 'View All' }}
            </button>
          </div>

          <div class="card-body">
            <div class="row">
              <div class="col-12 col-md-6 mb-3" v-for="doctor in displayedDoctors" :key="doctor.id">
                <div class="card h-100">
                  <div class="card-body">
                    <div class="d-flex flex-column">
                      <div class="mb-3">
                        <h6 class="card-title mb-1">Dr. {{ doctor.name }}</h6>
                        <p class="card-text small text-muted mb-0">
                          <strong>{{ doctor.qualification || 'MBBS' }}</strong>
                        </p>
                        <p class="card-text small text-muted mb-0" v-if="doctor.specialization">
                          {{ doctor.specialization }}
                        </p>
                        <p class="card-text small text-muted mb-0" v-if="doctor.experience_years">
                          {{ doctor.experience_years }} years experience
                        </p>
                      </div>
                      <div class="d-flex gap-2">
                        <button class="btn btn-sm btn-outline-primary flex-fill" @click="checkAvailability(doctor.id)">
                          Check Availability
                        </button>
                        <button class="btn btn-sm btn-primary flex-fill" @click="openBookingModal(doctor.id)">
                          Book Appointment
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="doctors.length === 0" class="text-center text-muted py-4">
              <p>No doctors available in this department.</p>
            </div>
          </div>

        </div>
      </div>
    </div>

    <div class="modal" :class="{ 'show d-block': showAvailabilityModal }" tabindex="-1" v-if="showAvailabilityModal"
      @click.self="closeAvailabilityModal">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Dr. {{ selectedDoctor?.name }} - Availability</h5>
            <button type="button" class="btn-close" @click="closeAvailabilityModal"></button>
          </div>
          <div class="modal-body">
            <div v-if="loadingAvailability" class="text-center py-4">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
              <p class="mt-2">Loading availability...</p>
            </div>
            <div v-else-if="availableSlots.length === 0" class="alert alert-warning">No availability slots found for
              next 7 days.</div>
            <div v-else>
              <div v-for="slot in availableSlots" :key="slot.date" class="mb-3 border-bottom pb-3">
                <h6>{{ formatDate(slot.date) }}</h6>
                <div class="d-flex flex-wrap gap-2">
                  <span v-for="(time, index) in slot.slots" :key="index" class="badge bg-success py-2 px-3">
                    {{ time.start }} - {{ time.end }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show" v-if="showAvailabilityModal"></div>

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
                <input type="text" class="form-control" :value="department.name" readonly>
                <input type="hidden" v-model="bookingForm.department_id">
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
                <div v-else-if="availableTimeSlots.length === 0" class="alert alert-warning">No available slots for this
                  date.</div>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const API_BASE = 'http://localhost:5000'

axios.defaults.withCredentials = true
const departmentId = ref(route.params.id)
const department = ref({
  name: '',
  description: '',
  details: ''
})

const doctors = ref([])
const showAllDoctors = ref(false)
const showAvailabilityModal = ref(false)
const loadingAvailability = ref(false)
const selectedDoctor = ref(null)
const availableSlots = ref([])
const isLoading = ref(true)
const error = ref(null)
const showBookModal = ref(false)
const availableDoctors = ref([])
const availableTimeSlots = ref([])
const loadingSlots = ref(false)

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

const displayedDoctors = computed(() => {
  return showAllDoctors.value ? doctors.value : doctors.value.slice(0, 4)
})

function goBack() {
  const userId = authStore.user?.user_id
  if (userId) {
    router.push(`/patient/${userId}/dashboard`)
  } else {
    router.back()
  }
}

function openBookingModal(doctorId = null) {
  showBookModal.value = true
  bookingForm.value.department_id = departmentId.value
  loadDoctorsByDepartment()
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

async function loadDepartment() {
  try {
    isLoading.value = true
    error.value = null
    const response = await axios.get(`${API_BASE}/departments`)
    const depts = response.data
    const dept = depts.find(d => d.id === parseInt(departmentId.value))

    if (dept) {
      department.value = {
        id: dept.id,
        name: dept.name,
        description: dept.description,
        details: `The ${dept.name} department is dedicated to providing comprehensive care and treatment. Our team of experienced specialists work together to diagnose, treat, and manage various conditions using the latest medical technologies and evidence-based practices.`
      }
    } else {
      error.value = 'Department not found'
    }
    await loadDoctors()
  } catch (err) {
    console.error('Failed to load department:', err)
    error.value = 'Failed to load department information'
  } finally {
    isLoading.value = false
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

async function loadDoctors() {
  try {
    const response = await axios.get(`${API_BASE}/departments/${departmentId.value}/doctors`)
    doctors.value = response.data
  } catch (err) {
    console.error('Failed to load doctors:', err)
    error.value = 'Failed to load doctors information'
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
    const response = await axios.get(
      `${API_BASE}/doctors/${bookingForm.value.doctor_id}/available-slots`,
      {
        params: { date: bookingForm.value.date }
      }
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

async function checkAvailability(doctorId) {
  const doctor = doctors.value.find(d => d.id === doctorId)
  if (!doctor) return
  selectedDoctor.value = doctor
  showAvailabilityModal.value = true
  loadingAvailability.value = true
  availableSlots.value = []

  try {
    const today = new Date()
    const endDate = new Date(today)
    endDate.setDate(endDate.getDate() + 7)
    const response = await axios.get(
      `${API_BASE}/doctors/${doctorId}/availability`,
      {
        params: {
          start_date: today.toISOString().split('T')[0],
          end_date: endDate.toISOString().split('T')[0]
        }
      }
    )
    availableSlots.value = response.data || []
  } catch (error) {
    console.error('Failed to load availability:', error)
  } finally {
    loadingAvailability.value = false
  }
}

function closeAvailabilityModal() {
  showAvailabilityModal.value = false
  loadingAvailability.value = false
  selectedDoctor.value = null
  availableSlots.value = []
}

function formatDate(dateStr) {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

async function handleBookAppointment() {
  try {
    await axios.post(`${API_BASE}/appointment`, bookingForm.value, {
      withCredentials: true
    })
    alert('Appointment booked successfully!')
    closeBookingModal()

    const userId = authStore.user?.user_id
    if (userId) {
      router.push(`/patient/${userId}/dashboard`)
    }
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

onMounted(() => {
  loadDepartment()
})
</script>