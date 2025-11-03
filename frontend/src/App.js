import React, { useState } from 'react';
import DownloadForm from './components/DownloadForm';
import DownloadStatus from './components/DownloadStatus';

function App() {
  const [fileId, setFileId] = useState(null);
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownloadStart = (id) => {
    setFileId(id);
    setIsDownloading(true);
  };

  const handleDownloadComplete = () => {
    setIsDownloading(false);
  };

  const handleReset = () => {
    setFileId(null);
    setIsDownloading(false);
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
          {!fileId ? (
            <DownloadForm onDownloadStart={handleDownloadStart} />
          ) : (
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
        </div>

        <footer className="text-center mt-16 pb-8">
          <p className="text-gray-500 text-sm">Built with React + FastAPI + yt-dlp</p>
        </footer>
      </div>
    </div>
  );
}

export default App;


