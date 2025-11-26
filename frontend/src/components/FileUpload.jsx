import { useState } from 'react';
import { submitForecastFile } from '../services/api';

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [hasHeader, setHasHeader] = useState(true);
  const [hasIndexCol, setHasIndexCol] = useState(false);

  // Configurações de validação
  const ACCEPTED_FORMATS = ['.csv', '.txt'];
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

  const validateFile = (selectedFile) => {
    if (!selectedFile) {
      return 'Por favor, selecione um arquivo.';
    }

    const fileName = selectedFile.name.toLowerCase();
    const isValidFormat = ACCEPTED_FORMATS.some(format => fileName.endsWith(format));
    
    if (!isValidFormat) {
      return `Formato inválido. Apenas arquivos ${ACCEPTED_FORMATS.join(', ')} são aceitos.`;
    }

    if (selectedFile.size > MAX_FILE_SIZE) {
      return `Arquivo muito grande. Tamanho máximo: ${MAX_FILE_SIZE / (1024 * 1024)}MB.`;
    }

    return null;
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    processFile(selectedFile);
  };

  const processFile = (selectedFile) => {
    setError('');
    setSuccess('');

    const validationError = validateFile(selectedFile);
    if (validationError) {
      setError(validationError);
      setFile(null);
      return;
    }

    setFile(selectedFile);
    setSuccess(`Arquivo "${selectedFile.name}" carregado com sucesso!`);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file) {
      setError('Por favor, selecione um arquivo antes de enviar.');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const result = await submitForecastFile(file, 3, hasHeader, hasIndexCol);
      setSuccess(`Previsão gerada com sucesso! Total de páginas: ${result.total_pages}`);
      console.log('Resultado da previsão:', result);
    } catch (err) {
      const errorMessage = err.response?.data?.detail 
        || err.message 
        || 'Erro ao processar o arquivo. Verifique se o backend está rodando.';
      
      setError(`❌ ${errorMessage}`);
      console.error('Erro completo:', {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status,
        config: err.config
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setFile(null);
    setError('');
    setSuccess('');
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-xl shadow-lg">
      <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">
        Upload de Arquivos para Previsão
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Área de Upload com Drag & Drop */}
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all ${
            dragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="file-upload"
            accept=".csv,.txt"
            onChange={handleFileChange}
            className="hidden"
          />
          
          <label
            htmlFor="file-upload"
            className="cursor-pointer flex flex-col items-center space-y-3"
          >
            <svg
              className="w-16 h-16 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <div className="text-gray-600">
              <span className="font-semibold text-blue-600 hover:text-blue-700">
                Clique para selecionar
              </span>{' '}
              ou arraste o arquivo aqui
            </div>
            <p className="text-sm text-gray-500">
              CSV ou TXT (máx. 10MB)
            </p>
          </label>
        </div>

        {/* Arquivo Selecionado */}
        {file && (
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <svg
                className="w-8 h-8 text-green-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <div>
                <p className="font-medium text-gray-800">{file.name}</p>
                <p className="text-sm text-gray-500">
                  {(file.size / 1024).toFixed(2)} KB
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleClear}
              className="text-red-500 hover:text-red-700 font-medium"
            >
              Remover
            </button>
          </div>
        )}

        {/* Opções de Configuração do CSV */}
        {file && (
          <div className="space-y-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <h3 className="font-semibold text-gray-700 text-sm mb-2">
              Configurações do Arquivo
            </h3>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="hasHeader"
                checked={hasHeader}
                onChange={(e) => setHasHeader(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <label htmlFor="hasHeader" className="text-sm text-gray-700 cursor-pointer">
                Arquivo possui cabeçalho (primeira linha)
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="hasIndexCol"
                checked={hasIndexCol}
                onChange={(e) => setHasIndexCol(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <label htmlFor="hasIndexCol" className="text-sm text-gray-700 cursor-pointer">
                Remover primeira coluna (índice/data)
              </label>
            </div>
          </div>
        )}

        {/* Mensagens de Feedback */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start space-x-3">
              <svg
                className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </div>
        )}

        {success && !error && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start space-x-3">
              <svg
                className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <p className="text-green-700 text-sm">{success}</p>
            </div>
          </div>
        )}

        {/* Botão de Envio */}
        <button
          type="submit"
          disabled={!file || loading}
          className={`w-full py-3 px-6 rounded-lg font-semibold text-white transition-all ${
            !file || loading
              ? 'bg-gray-300 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 active:scale-95'
          }`}
        >
          {loading ? (
            <span className="flex items-center justify-center space-x-2">
              <svg
                className="animate-spin h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <span>Processando...</span>
            </span>
          ) : (
            'Enviar e Gerar Previsão'
          )}
        </button>
      </form>

      {/* Informações Adicionais */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h3 className="font-semibold text-blue-900 mb-2">
          Formatos Aceitos:
        </h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• CSV: arquivo com dados separados por vírgula</li>
          <li>• TXT: arquivo de texto simples</li>
          <li>• Tamanho máximo: 10MB</li>
        </ul>
      </div>
    </div>
  );
};

export default FileUpload;
