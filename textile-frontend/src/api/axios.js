// frontend/src/api.js
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:5001/api/v1',   // ✅ Added /api/v1 here
  withCredentials: true,                     // ✅ Keep this if Flask CORS supports credentials
  headers: {
    'Content-Type': 'application/json',
  },
})

export default api
