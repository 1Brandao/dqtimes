# DQTimes Frontend

React + Vite frontend for DQTimes time series forecasting API with CUDA-accelerated predictions.

## Tech Stack

- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Hook Form** - Form validation and handling
- **Axios** - HTTP client for API requests

## Prerequisites

- Node.js 18+ and npm
- DQTimes backend running on `http://localhost:80`

## Getting Started

### Installation

```bash
cd frontend
npm install
```

### Development Server

```bash
npm run dev
```

The app will open at `http://localhost:3000` with hot module replacement enabled.

### Build for Production

```bash
npm run build
```

Outputs optimized static files to `dist/` folder.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── ForecastForm.jsx      # Main form component with file upload
│   ├── services/
│   │   └── api.js                # FastAPI client (axios)
│   ├── App.jsx                   # Root component
│   ├── main.jsx                  # Entry point
│   └── index.css                 # Tailwind imports
├── index.html
├── vite.config.js                # Vite configuration with proxy
├── tailwind.config.js
└── package.json
```

## Features

### 1. Manual Input Mode
- Enter comma-separated historical values
- Specify number of forecasts (1-30)
- Get instant predictions with probability metrics

### 2. CSV Upload Mode
- Upload CSV files with historical data
- Automatic processing via `/projecao_dataframe/` endpoint
- Supports DataFrames with multiple columns

### 3. API Integration
- Connects to FastAPI backend at `http://localhost:80`
- Two endpoints:
  - `/projecao_lista/` - For array-based forecasts
  - `/projecao_dataframe/` - For CSV file uploads
- Displays final projection and probability of increase

## API Configuration

The Vite dev server proxies `/api/*` requests to `http://localhost:80`. To change the backend URL:

1. Edit `vite.config.js`:
```js
server: {
  proxy: {
    '/api': {
      target: 'http://your-backend-url',
      changeOrigin: true,
    }
  }
}
```

2. Update `src/services/api.js`:
```js
const API_BASE_URL = 'http://your-backend-url';
```

## Development Tips

### Running with Backend

Make sure the DQTimes backend is running:

```bash
# In the root project directory
docker-compose up
```

Backend should be accessible at `http://localhost:80`.

### CORS Configuration

If you encounter CORS issues, ensure the FastAPI backend allows origins from `http://localhost:3000`. Check `dqtimes/app/main.py` for CORS middleware settings.

### Hot Reload

Vite automatically reloads the page when you save changes to:
- `.jsx` files
- `.css` files
- Configuration files

## Example Usage

### Manual Input
```
Historical Data: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
Number of Forecasts: 3
```

### CSV File Format
```csv
date,value
2024-01-01,100
2024-01-02,102
2024-01-03,105
...
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Troubleshooting

### Port Already in Use
Change the port in `vite.config.js`:
```js
server: {
  port: 3001, // Change to any available port
}
```

### Backend Connection Failed
1. Verify backend is running: `curl http://localhost:80`
2. Check browser console for CORS errors
3. Ensure no firewall is blocking port 80

### Build Errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Contributing

When adding new features:
1. Create components in `src/components/`
2. Add API functions in `src/services/api.js`
3. Follow the existing Tailwind CSS styling patterns
4. Use React Hook Form for form handling

## License

Same as parent DQTimes project.
