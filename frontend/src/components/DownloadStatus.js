import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './DownloadStatus.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function DownloadStatus({ fileId, onComplete, onReset }) {
  const [status, setStatus] = useState('checking');
  const [filename, setFilename] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    let interval;

    const checkStatus = async () => {
      try {
        const response = await axios.get(`${API_URL}/status/${fileId}`);

        if (response.data.ready) {
          setStatus('ready');
          setFilename(response.data.filename);
          onComplete();
          clearInterval(interval);
        } else if (response.data.error) {
          setStatus('error');
          setError(response.data.error);
          clearInterval(interval);
        } else {
          setStatus('downloading');
        }
      } catch (err) {
        setStatus('error');
        setError('Failed to check download status');
        clearInterval(interval);
      }
    };

    // Check immediately
    checkStatus();

    // Then check every 2 seconds
    interval = setInterval(checkStatus, 2000);

    return () => clearInterval(interval);
  }, [fileId, onComplete]);

  const handleDownload = () => {
    window.open(`${API_URL}/video/${fileId}`, '_blank');
  };

  const handleNewDownload = async () => {
    // Optional: Clean up the file on server
    try {
      await axios.delete(`${API_URL}/cleanup/${fileId}`);
    } catch (err) {
      console.error('Cleanup failed:', err);
    }
    onReset();
  };

  return (
    <div className="download-status">
      {status === 'checking' && (
        <div className="status-card">
          <div className="status-icon checking">
            <span className="spinner-large"></span>
          </div>
          <h2>Checking Status...</h2>
          <p>Please wait while we check your download</p>
        </div>
      )}

      {status === 'downloading' && (
        <div className="status-card">
          <div className="status-icon downloading">
            <span className="spinner-large"></span>
          </div>
          <h2>Downloading...</h2>
          <p>Your video is being downloaded. This may take a few minutes.</p>
          <div className="progress-bar">
            <div className="progress-bar-fill"></div>
          </div>
        </div>
      )}

      {status === 'ready' && (
        <div className="status-card success">
          <div className="status-icon success">
            <span>✓</span>
          </div>
          <h2>Download Ready!</h2>
          <p className="filename">{filename}</p>
          <div className="button-group">
            <button className="download-button" onClick={handleDownload}>
              <span>📥</span>
              Download File
            </button>
            <button className="secondary-button" onClick={handleNewDownload}>
              Download Another
            </button>
          </div>
        </div>
      )}

      {status === 'error' && (
        <div className="status-card error">
          <div className="status-icon error">
            <span>✕</span>
          </div>
          <h2>Download Failed</h2>
          <p className="error-text">{error}</p>
          <button className="secondary-button" onClick={handleNewDownload}>
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}

export default DownloadStatus;
