import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import "./assets/main.css";
//import 'leaflet/dist/leaflet.css';

// Bootstrap 5
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap-icons/font/bootstrap-icons.css";
import "bootstrap";

const app = createApp(App);

app.use(router).mount("#app");
