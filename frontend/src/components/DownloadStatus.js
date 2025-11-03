import React, { useState, useEffect } from 'react';
import axios from 'axios';

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
    <div className="max-w-2xl mx-auto">
      {status === 'checking' && (
        <div className="bg-dark-lighter border border-gray-800 rounded-2xl p-12 shadow-2xl text-center">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          </div>
          <h2 className="text-2xl font-bold text-white mb-3">Checking Status...</h2>
          <p className="text-gray-400">Please wait while we check your download</p>
        </div>
      )}

      {status === 'downloading' && (
        <div className="bg-dark-lighter border border-gray-800 rounded-2xl p-12 shadow-2xl text-center">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          </div>
          <h2 className="text-2xl font-bold text-white mb-3">Downloading...</h2>
          <p className="text-gray-400 mb-6">Your video is being downloaded. This may take a few minutes.</p>
          <div className="w-full bg-dark border border-gray-700 rounded-full h-2 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-primary to-cyan-300 animate-pulse"></div>
          </div>
        </div>
      )}

      {status === 'ready' && (
        <div className="bg-dark-lighter border border-green-800/50 rounded-2xl p-12 shadow-2xl text-center">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-green-500/20 border-2 border-green-500 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-white mb-3">Download Ready!</h2>
          <p className="text-gray-400 mb-2">Your file is ready to download</p>
          <p className="text-primary font-medium mb-8 break-all px-4">{filename}</p>
          <div className="space-y-3">
            <button
              onClick={handleDownload}
              className="w-full bg-primary hover:bg-cyan-400 text-dark font-semibold px-6 py-3.5 rounded-lg transition-all shadow-lg shadow-primary/30 flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
              </svg>
              Download File
            </button>
            <button
              onClick={handleNewDownload}
              className="w-full bg-dark border border-gray-700 text-gray-300 hover:text-white hover:border-gray-600 font-medium px-6 py-3.5 rounded-lg transition-all"
            >
              Download Another
            </button>
          </div>
        </div>
      )}

      {status === 'error' && (
        <div className="bg-dark-lighter border border-red-800/50 rounded-2xl p-12 shadow-2xl text-center">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-red-500/20 border-2 border-red-500 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-white mb-3">Download Failed</h2>
          <p className="text-red-400 mb-8 px-4">{error}</p>
          <button
            onClick={handleNewDownload}
            className="w-full bg-dark border border-gray-700 text-gray-300 hover:text-white hover:border-gray-600 font-medium px-6 py-3.5 rounded-lg transition-all"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}

export default DownloadStatus;