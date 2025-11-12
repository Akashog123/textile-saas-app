import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/main.css'
import axios from 'axios'

// Bootstrap 5
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap'

const app = createApp(App)


axios.defaults.baseURL = 'http://localhost:5001'
app.config.globalProperties.$axios = axios

app.use(router).mount('#app')
