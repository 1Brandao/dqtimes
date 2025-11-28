import axios from 'axios';

const API_BASE_URL = 'http://localhost:80';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - clear storage and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ========== AUTHENTICATION API ==========

/**
 * Register a new user
 * @param {string} email - User email
 * @param {string} password - User password (min 8 characters)
 * @returns {Promise<Object>} User data
 */
export const register = async (email, password) => {
  const response = await apiClient.post('/auth/register', {
    email,
    password,
  });
  return response.data;
};

/**
 * Login user and get access token
 * @param {string} email - User email
 * @param {string} password - User password
 * @returns {Promise<Object>} Token data with access_token and token_type
 */
export const login = async (email, password) => {
  const response = await apiClient.post('/auth/login', {
    email,
    password,
  });
  return response.data;
};

/**
 * Get current authenticated user info
 * @returns {Promise<Object>} User data
 */
export const getCurrentUser = async () => {
  const response = await apiClient.get('/auth/me');
  return response.data;
};

// ========== FORECASTING API ==========

/**
 * Submit forecast request with historical data list
 * @param {Array<number>} historicalData - Array of historical values
 * @param {number} forecastCount - Number of projections to generate
 * @returns {Promise<Object>} Forecast result with projections and probability
 */
export const submitForecastList = async (historicalData, forecastCount = 3) => {
  const formData = new FormData();
  formData.append('lista_historico', JSON.stringify(historicalData));
  formData.append('quantidade_projecoes', forecastCount);
 
  const response = await axios.post(
    `${API_BASE_URL}/projecao_lista/`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return response.data;
};

/**
 * Submit forecast request with CSV file
 * @param {File} file - CSV file with historical data
 * @param {number} forecastCount - Number of projections to generate
 * @returns {Promise<Object>} Forecast result
 */
export const submitForecastFile = async (file, forecastCount = 3) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('quantidade_projecoes', forecastCount);

  const response = await axios.post(
    `${API_BASE_URL}/projecao_dataframe/`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return response.data;
};

/**
 * Check API health status
 * @returns {Promise<Object>} Health status
 */
export const checkHealth = async () => {
  const response = await apiClient.get('/');
  return response.data;
};

export default apiClient;
