import axios from "axios";

const marketingApi = axios.create({
  baseURL: "http://127.0.0.1:5001/api/v1/marketing",
});

export default marketingApi;
