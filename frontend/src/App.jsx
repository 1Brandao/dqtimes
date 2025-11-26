import FileUpload from './components/FileUpload';

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-gray-800 mb-2">
            DQTimes
          </h1>
          <p className="text-gray-600 text-lg">

          </p>
        </div>
        
        <FileUpload />
      </div>
    </div>
  )
}

export default App
