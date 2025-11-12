import axios from "axios";

const catalogApi = axios.create({
  baseURL: "http://127.0.0.1:5001/api/v1/catalog",
  headers: { "Content-Type": "application/json" },
});

export default catalogApi;
