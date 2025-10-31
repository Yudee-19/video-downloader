import React, { useState } from 'react';
import './App.css';
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
    <div className="App">
      <div className="container">
        <header className="app-header">
          <h1>🎥 YouTube Downloader</h1>
          <p>Download videos and audio from YouTube easily</p>
        </header>

        <div className="main-content">
          {!fileId ? (
            <DownloadForm onDownloadStart={handleDownloadStart} />
          ) : (
            <DownloadStatus
              fileId={fileId}
              onComplete={handleDownloadComplete}
              onReset={handleReset}
            />
          )}
        </div>

        <footer className="app-footer">
          <p>Built with React + FastAPI + yt-dlp</p>
        </footer>
      </div>
    </div>
  );
}

export default App;
