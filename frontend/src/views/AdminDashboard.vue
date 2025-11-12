<template>
  <nav class="navbar navbar-light bg-white mb-4 border-bottom border-dark">
    <div class="container-fluid">
      <span class="navbar-brand mb-0 h3">Admin Dashboard</span>
      <div class="d-flex gap-2">
        <span class="navbar-text me-3">Welcome Admin</span>
        <button class="btn btn-danger" @click="handleLogout">Logout</button>
      </div>
    </div>
  </nav>

  <div class="container-fluid">
    <div class="container">

      <div class="card mb-4 border-dark">
        <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center">
          <h5 class="mb-0">Registered Doctors</h5>
          <div>
            <span>Total Doctors: {{ stats.total_doctors }} | </span>
            <button class="btn btn-sm btn-success mx-2" @click="showAddDoctorModal = true">
              Add new Doctor
            </button>
          </div>
        </div>
        <div class="card-body">
          <div class="table-responsive">
            <table class="table table-hover">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Doctor's Name</th>
                  <th>Email ID</th>
                  <th>Qualification</th>
                  <th>Department</th>
                  <th>Experience</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="doctor in doctors" :key="doctor.id">
                  <td>{{ doctor.id }}</td>
                  <td>Dr. {{ doctor.name }}</td>
                  <td>{{ doctor.email }}</td>
                  <td>{{ doctor.qualification }}</td>
                  <td>{{ doctor.department }}</td>
                  <td>{{ doctor.experience_years }} years</td>
                  <td>
                    <button class="btn btn-sm btn-primary me-2" @click="editDoctor(doctor)">Edit</button>
                    <button class="btn btn-sm btn-danger" @click="confirmRemoveDoctor(doctor)">Remove</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="card mb-4 border-dark">
        <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center">
          <h5 class="mb-0">Registered Patients</h5>
          <span>Total Patients: {{ stats.total_patients }} </span>
        </div>
        <div class="card-body">
          <div class="table-responsive">
            <table class="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Patient Name</th>
                  <th>Email</th>
                  <th>Contact</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="patient in recentPatients" :key="patient.id">
                  <td>{{ patient.id }}</td>
                  <td>{{ patient.name }}</td>
                  <td>{{ patient.email || 'N/A' }}</td>
                  <td>{{ patient.phone }}</td>
                  <td>
                    <button class="btn btn-sm btn-primary me-2" @click="viewPatient(patient)">view</button>
                    <button class="btn btn-sm btn-danger" @click="confirmRemovePatient(patient)">Remove</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="card mb-4 border-dark">
        <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center">
          <h5 class="mb-0">Upcoming Appointments</h5>
          <span>Total Appointments: {{ stats.total_appointments }} | Pending Appointments: {{
            stats.pending_appointments}}</span>
        </div>
        <div class="card-body">
          <div class="table-responsive">
            <table class="table table-hover">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Patient Name</th>
                  <th>Doctor Name</th>
                  <th>Department</th>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="apt in recentAppointments" :key="apt.id">
                  <td>{{ apt.id }}</td>
                  <td>{{ apt.patient }}</td>
                  <td>Dr. {{ apt.doctor }}</td>
                  <td>{{ apt.department || 'N/A' }}</td>
                  <td>{{ apt.date }}</td>
                  <td>{{ apt.time }}</td>
                  <td>
                    <span class="badge" :class="getStatusBadge(apt.status)">{{ apt.status }}</span>
                  </td>
                  <td>
                    <button class="btn btn-primary btn-sm" @click="viewPatientHistory(apt.patient_id, apt.id)">
                      View
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

    </div>

    <div class="modal" :class="{ 'show d-block': showAddDoctorModal }" tabindex="-1" v-if="showAddDoctorModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Add a new Doctor</h5>
            <button type="button" class="btn-close" @click="closeAddDoctorModal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="handleAddDoctor">
              <div class="mb-3">
                <div class="input-group">
                  <span class="input-group-text">Dr.</span>
                  <input type="text" class="form-control" placeholder="Name" v-model="newDoctor.name" required>
                </div>
              </div>
              <div class="mb-3">
                <input type="text" class="form-control" placeholder="Username" v-model="newDoctor.username" required>
              </div>
              <div class="mb-3">
                <input type="password" class="form-control" placeholder="Password" v-model="newDoctor.password"
                  required>
              </div>
              <div class="mb-3">
                <input type="email" class="form-control" placeholder="Email" v-model="newDoctor.email">
              </div>
              <div class="mb-3">
                <select class="form-select" v-model="newDoctor.department_id" required>
                  <option value="" disabled selected>Specialization/Department</option>
                  <option v-for="dept in departments" :key="dept.id" :value="dept.id">
                    {{ dept.name }}
                  </option>
                </select>
              </div>
              <div class="mb-3">
                <input type="text" class="form-control" placeholder="Qualification" v-model="newDoctor.qualification">
              </div>
              <div class="mb-3">
                <input type="number" class="form-control" placeholder="Experience (years)"
                  v-model="newDoctor.experience_years">
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-dark" @click="closeAddDoctorModal">Close</button>
                <button type="submit" class="btn btn-success">Create</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show" v-if="showAddDoctorModal"></div>

    <div class="modal" :class="{ 'show d-block': showEditDoctorModal }" tabindex="-1" v-if="showEditDoctorModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Edit Doctor Profile</h5>
            <button type="button" class="btn-close" @click="closeEditDoctorModal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="handleUpdateDoctor">
              <div class="mb-3">
                <label class="form-label">Doctor Name</label>
                <div class="input-group">
                  <span class="input-group-text">Dr.</span>
                  <input type="text" class="form-control" v-model="editDoctorForm.name" required>
                </div>
              </div>
              <div class="mb-3">
                <label class="form-label">Email</label>
                <input type="email" class="form-control" v-model="editDoctorForm.email">
              </div>
              <div class="mb-3">
                <label class="form-label">Department</label>
                <select class="form-select" v-model="editDoctorForm.department_id" required>
                  <option value="" disabled>Select Department</option>
                  <option v-for="dept in departments" :key="dept.id" :value="dept.id">
                    {{ dept.name }}
                  </option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label">Qualification</label>
                <input type="text" class="form-control" v-model="editDoctorForm.qualification">
              </div>
              <div class="mb-3">
                <label class="form-label">Experience (years)</label>
                <input type="number" class="form-control" v-model="editDoctorForm.experience_years">
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" @click="closeEditDoctorModal">Close</button>
                <button type="submit" class="btn btn-primary">Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show" v-if="showEditDoctorModal"></div>

  </div>

</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const router = useRouter()
const authStore = useAuthStore()
const recentPatients = ref([])
const recentAppointments = ref([])
const doctors = ref([])
const departments = ref([])
const showAddDoctorModal = ref(false)
const showEditDoctorModal = ref(false)
const API_BASE = 'http://localhost:5000'

const stats = ref({
  total_patients: 0,
  total_doctors: 0,
  total_appointments: 0,
  pending_appointments: 0
})

const newDoctor = ref({
  name: '',
  username: '',
  password: '',
  email: '',
  department_id: '',
  qualification: '',
  experience_years: null
})

const editDoctorForm = ref({
  id: null,
  name: '',
  email: '',
  department_id: '',
  qualification: '',
  experience_years: null
})

function viewPatientHistory(patientId) {
  router.push(`/patient/${patientId}/history`)
}

async function loadDashboard() {
  try {
    const response = await axios.get(`${API_BASE}/admin/dashboard`, {
      withCredentials: true
    })
    stats.value = response.data.stats
    recentPatients.value = response.data.recent_patients
    recentAppointments.value = response.data.recent_appointments
  } catch (error) {
    console.error('Failed to load dashboard:', error)
    if (error.response?.status === 401) {
      alert('Session expired. Please login again.')
      router.push('/login')
    }
  }
}

async function loadDepartments() {
  try {
    const response = await axios.get(`${API_BASE}/departments`)
    departments.value = response.data
  } 
  catch (error) {
    console.error('Failed to load departments:', error)
  }
}

async function loadDoctors() {
  try {
    const response = await axios.get(`${API_BASE}/admin/doctors`, {
      withCredentials: true
    })
    doctors.value = response.data
  } catch (error) {
    console.error('Failed to load doctors:', error.response?.data || error.message)
  }
}

function closeAddDoctorModal() {
  showAddDoctorModal.value = false
  newDoctor.value = {
    name: '',
    username: '',
    password: '',
    email: '',
    department_id: '',
    qualification: '',
    experience_years: null
  }
}

async function handleAddDoctor() {
  try {
    const response = await axios.post(`${API_BASE}/admin/doctor`, newDoctor.value, {
      withCredentials: true
    })
    console.log('Doctor added:', response.data)
    alert('Doctor added successfully!')
    closeAddDoctorModal()
    await loadDoctors()
    await loadDashboard()
  } catch (error) {
    console.error('Failed to add doctor:', error.response?.data || error.message)
    alert(error.response?.data?.error || 'Failed to add doctor')
  }
}

function editDoctor(doctor) {
  const department = departments.value.find(d => d.name === doctor.department)
  editDoctorForm.value = {
    id: doctor.id,
    name: doctor.name,
    email: doctor.email || '',
    department_id: department ? department.id : '',
    qualification: doctor.qualification || '',
    experience_years: doctor.experience_years || null
  }
  showEditDoctorModal.value = true
}

function closeEditDoctorModal() {
  showEditDoctorModal.value = false
  editDoctorForm.value = {
    id: null,
    name: '',
    email: '',
    department_id: '',
    qualification: '',
    experience_years: null
  }
}

async function handleUpdateDoctor() {
  try {
    const updateData = {
      name: editDoctorForm.value.name,
      email: editDoctorForm.value.email,
      department_id: editDoctorForm.value.department_id,
      qualification: editDoctorForm.value.qualification,
      experience_years: editDoctorForm.value.experience_years
    }
    await axios.put(
      `${API_BASE}/admin/doctor/${editDoctorForm.value.id}`, updateData,
      { withCredentials: true }
    )
    alert('Doctor profile updated successfully!')
    closeEditDoctorModal()
    await loadDoctors()
    await loadDashboard()
  } catch (error) {
    console.error('Failed to update doctor:', error)
    alert(error.response?.data?.error || 'Failed to update doctor profile. Please try again.')
  }
}

async function confirmRemoveDoctor(doctor) {
  const confirmed = confirm(`Are you sure you want to remove Dr. ${doctor.name} (ID: ${doctor.id})?`)
  if (confirmed) {
    try {
      await axios.delete(`${API_BASE}/admin/doctor/${doctor.id}`, {
        withCredentials: true
      })
      alert(`Doctor ${doctor.name} removed successfully.`)
      await loadDoctors()
      await loadDashboard()
    } catch (error) {
      console.error('Failed to remove doctor:', error)
      alert(error.response?.data?.error || 'Failed to remove doctor')
    }
  }
}

async function viewPatient(patient) {
  alert(`Patient Details:
  ID: ${patient.id}
  Name: ${patient.name}
  Email: ${patient.email || 'N/A'}
  Contact: ${patient.phone || 'N/A'}`)
}

async function confirmRemovePatient(patient) {
  const confirmed = confirm(`Are you sure you want to remove ${patient.name} (ID: ${patient.id})?`)
  if (confirmed) {
    try {
      await axios.delete(`${API_BASE}/admin/patient/${patient.id}`, {
        withCredentials: true
      })
      alert(`Patient ${patient.name} removed successfully.`)
      await loadDashboard()
    } catch (error) {
      console.error('Failed to remove patient:', error)
      alert(error.response?.data?.error || 'Failed to remove patient')
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
  loadDashboard()
  loadDepartments()
  loadDoctors()
})
</script>

<style scoped>
input, textarea {
  box-shadow: none !important;
}

body {
  min-height: 100vh;
}
</style>