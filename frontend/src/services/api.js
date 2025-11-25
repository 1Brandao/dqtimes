import axios from 'axios';

const API_BASE_URL = 'http://localhost:80';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
