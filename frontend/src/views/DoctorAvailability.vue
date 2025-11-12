<template>
  <nav class="navbar navbar-light bg-white border-dark border-bottom mb-4 px-4">
    <button class="btn btn-dark" @click="router.back()">
      Back
    </button>
  </nav>

  <div v-if="saveStatus" class="container alert px-4" :class="saveStatus.type" role="alert">
    {{ saveStatus.message }}
  </div>
  <div class="container-fluid py-3">
    <div class="container">

      <div class="card border-dark">
        <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center">
          <h5 class="mb-0">Set Your Availability</h5>
          <span class="small">7 days availability is provided</span>
          <button class="btn btn-danger bg-opacity-25" @click="saveAvailability">Save Availability</button>
        </div>

        <div class="card-body">
          <div v-for="(day, index) in availability" :key="index" class="mb-4 border-bottom pb-3">
            <div class="row align-items-center">
              <div class="col-md-2">
                <strong>{{ day.date }}</strong>
                <div class="small text-muted">{{ day.day }}</div>
              </div>
              <div class="col-md-8">
                <div class="row g-2">
                  <div class="col-md-6" v-for="(slot, slotIndex) in day.slots" :key="slotIndex">
                    <div class="input-group input-group-sm">
                      <input type="time" class="form-control" v-model="slot.start"
                        :class="{ 'is-invalid': !slot.start && slot.end }">
                      <span class="input-group-text">to</span>
                      <input type="time" class="form-control" v-model="slot.end"
                        :class="{ 'is-invalid': slot.start && !slot.end }">
                      <button class="btn btn-outline-danger" type="button" @click="removeSlot(index, slotIndex)"
                        v-if="day.slots.length > 1">
                        &times;
                      </button>
                    </div>
                    <div class="invalid-feedback d-block" v-if="!slot.start && slot.end">Please set start time</div>
                    <div class="invalid-feedback d-block" v-if="slot.start && !slot.end">Please set end time</div>
                  </div>
                </div>
                <button class="btn btn-sm btn-outline-primary mt-2" @click="addSlot(index)">+ Add Time Slot</button>
              </div>
              <div class="col-md-2 text-end">
                <button class="btn" :class="day.enabled ? 'btn-success' : 'btn-secondary'" @click="toggleDay(index)">
                  {{ day.enabled ? 'Enabled' : 'Disabled' }}
                </button>
              </div>
            </div>
          </div>
        </div>

      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const doctorId = ref(route.params.id)
const saveStatus = ref(null)
const availability = ref([])
const isLoading = ref(false)

function initializeAvailability() {
  const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
  const today = new Date()
  availability.value = []
  for (let i = 0; i < 7; i++) {
    const date = new Date(today)
    date.setDate(today.getDate() + i)
    availability.value.push({
      date: date.toISOString().split('T')[0],
      day: days[date.getDay()],
      enabled: false,
      slots: [
        { start: '', end: '' }
      ]
    })
  }
}

async function loadExistingAvailability() {
  try {
    const today = new Date().toISOString().split('T')[0]
    const endDate = new Date()
    endDate.setDate(endDate.getDate() + 6)
    const end = endDate.toISOString().split('T')[0]
    const response = await fetch(
      `http://localhost:5000/doctors/${doctorId.value}/availability?start_date=${today}&end_date=${end}`,
      { credentials: 'include' }
    )

    if (response.ok) {
      const existingData = await response.json()
      availability.value.forEach(day => {
        const existing = existingData.find(e => e.date === day.date)
        if (existing && existing.slots.length > 0) {
          day.slots = existing.slots
          day.enabled = true
        } else {
          day.enabled = false
          day.slots = [{ start: '', end: '' }]
        }
      })
    }
  } catch (error) {
    console.error('Error loading availability:', error)
  }
}

function addSlot(dayIndex) {
  availability.value[dayIndex].slots.push({ start: '', end: '' })
}

function removeSlot(dayIndex, slotIndex) {
  availability.value[dayIndex].slots.splice(slotIndex, 1)
}

function toggleDay(dayIndex) {
  availability.value[dayIndex].enabled = !availability.value[dayIndex].enabled
  if (availability.value[dayIndex].enabled && availability.value[dayIndex].slots.length === 0) {
    availability.value[dayIndex].slots.push({ start: '', end: '' })
  }
}

async function saveAvailability() {
  saveStatus.value = null
  let isValid = true
  for (const day of availability.value) {
    if (day.enabled) {
      const validSlots = day.slots.filter(slot => slot.start && slot.end)
      if (validSlots.length === 0) {
        saveStatus.value = {
          type: 'alert-danger',
          message: `Please add at least one time slot for ${day.day} or disable the day.`
        }
        return
      }
      for (const slot of day.slots) {
        if ((slot.start && !slot.end) || (!slot.start && slot.end)) {
          isValid = false
          break
        }
        if (slot.start && slot.end && slot.start >= slot.end) {
          saveStatus.value = {
            type: 'alert-danger',
            message: 'End time must be after start time.'
          }
          return
        }
      }
    }
  }
  if (!isValid) {
    saveStatus.value = {
      type: 'alert-danger',
      message: 'Please complete all time slots or remove incomplete ones.'
    }
    return
  }

  isLoading.value = true
  try {
    const response = await fetch(`http://localhost:5000/doctors/${doctorId.value}/availability`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', },
      credentials: 'include',
      body: JSON.stringify(availability.value)
    })
    const data = await response.json()
    if (response.ok) {
      saveStatus.value = {
        type: 'alert-success',
        message: 'Availability saved successfully!'
      }
      setTimeout(() => {
        router.push(`/doctor/${doctorId.value}/dashboard`)
      }, 2000)
    } else {
      saveStatus.value = {
        type: 'alert-danger',
        message: data.error || 'Failed to save availability.'
      }
    }
  } catch (error) {
    saveStatus.value = {
      type: 'alert-danger',
      message: 'Network error. Please try again.'
    }
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  initializeAvailability()
  loadExistingAvailability()
})
</script>