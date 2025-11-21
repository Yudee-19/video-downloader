import React, { useState } from 'react';
import axios from 'axios';
import DownloadForm from './components/DownloadForm';
import DownloadStatus from './components/DownloadStatus';
import BatchDownloadForm from './components/BatchDownloadForm';
import BatchDownloadStatus from './components/BatchDownloadStatus';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [fileId, setFileId] = useState(null);
  const [batchId, setBatchId] = useState(null);
  const [totalVideos, setTotalVideos] = useState(0);
  const [isDownloading, setIsDownloading] = useState(false);
  const [mode, setMode] = useState('single'); // 'single' or 'batch'

  const handleDownloadStart = async (downloadRequest) => {
    // If type is 'download', use the /download endpoint (queued download)
    if (downloadRequest.type === 'download') {
      try {
        setIsDownloading(true);
        const response = await axios.post(`${API_URL}/download`, {
          url: downloadRequest.url,
          start_time: downloadRequest.start_time,
          end_time: downloadRequest.end_time,
          audio_only: downloadRequest.audio_only
        });
        setFileId(response.data.file_id);
        // Note: We don't set isDownloading(false) here because we want to show the status component
        // which will handle the polling and completion state.
      } catch (error) {
        console.error('Download start failed', error);
        setIsDownloading(false);
        alert('Failed to start download: ' + (error.response?.data?.detail || error.message));
      }
      return;
    }

    // Default to streaming behavior (type === 'stream' or undefined)
    // To use direct streaming, call the new /stream-download endpoint and
    // trigger a browser download.
    try {
      setIsDownloading(true);

      const params = new URLSearchParams();
      params.set('url', downloadRequest.url);
      // format_id is left as default; you can expose it in UI later

      const downloadUrl = `${API_URL}/stream-download?${params.toString()}`;

      const a = document.createElement('a');
      a.href = downloadUrl;
      a.target = '_blank';
      document.body.appendChild(a);
      console.log('Starting streaming download from', downloadUrl);
      a.click();
      document.body.removeChild(a);

      // No fileId for streaming; we immediately mark complete
      setIsDownloading(false);
    } catch (e) {
      console.error('Streaming download failed', e);
      setIsDownloading(false);
    }
  };

  const handleBatchDownloadStart = (id, total) => {
    setBatchId(id);
    setTotalVideos(total);
    setIsDownloading(true);
  };

  const handleDownloadComplete = () => {
    setIsDownloading(false);
  };

  const handleReset = () => {
    setFileId(null);
    setBatchId(null);
    setTotalVideos(0);
    setIsDownloading(false);
  };

  const toggleMode = () => {
    setMode(mode === 'single' ? 'batch' : 'single');
    handleReset();
  };

  return (
    <div className="min-h-screen">
      <div className="px-4 py-12">
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-primary to-cyan-300 bg-clip-text text-transparent">
            YouTube Downloader
          </h1>
          <p className="text-gray-400 text-lg">Download videos or trim specific parts with ease</p>
        </header>

        <div className="main-content container mx-auto max-w-4xl">
          {/* Mode Toggle */}
          {!fileId && !batchId && (
            <div className="flex justify-center mb-8">
              <div className="bg-dark-lighter border border-gray-800 rounded-lg p-1 inline-flex">
                <button
                  onClick={() => setMode('single')}
                  className={`px-6 py-2 rounded-md font-medium transition-all ${mode === 'single'
                    ? 'bg-primary text-dark'
                    : 'text-gray-400 hover:text-white'
                    }`}
                >
                  Single Download
                </button>
                <button
                  onClick={() => setMode('batch')}
                  className={`px-6 py-2 rounded-md font-medium transition-all ${mode === 'batch'
                    ? 'bg-primary text-dark'
                    : 'text-gray-400 hover:text-white'
                    }`}
                >
                  Batch Download
                </button>
              </div>
            </div>
          )}

          {/* Single Download Mode */}
          {mode === 'single' && !fileId && !batchId && (
            <DownloadForm onDownloadStart={handleDownloadStart} />
          )}

          {/* Batch Download Mode */}
          {mode === 'batch' && !fileId && !batchId && (
            <BatchDownloadForm onBatchDownloadStart={handleBatchDownloadStart} />
          )}

          {/* Single Download Status */}
          {fileId && (
            <>
              {isDownloading && (
                <div className="mb-4 text-center text-primary">
                  Download in progress...
                </div>
              )}
              <DownloadStatus
                fileId={fileId}
                onComplete={handleDownloadComplete}
                onReset={handleReset}
              />
            </>
          )}

          {/* Batch Download Status */}
          {batchId && (
            <BatchDownloadStatus
              batchId={batchId}
              totalVideos={totalVideos}
              onReset={handleReset}
            />
          )}
        </div>

        <footer className="text-center mt-16 pb-8">
          <p className="text-gray-500 text-sm">Built with React + FastAPI + yt-dlp + Redis</p>
        </footer>
      </div>
    </div>
  );
}

export default App;


