import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function BatchDownloadStatus({ batchId, totalVideos, onReset }) {
  const [batchStatus, setBatchStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let interval;

    const checkBatchStatus = async () => {
      try {
        const response = await axios.get(`${API_URL}/batch-status/${batchId}`);
        setBatchStatus(response.data);
        setLoading(false);

        // Stop polling if all downloads are complete or failed
        if (response.data.in_progress === 0) {
          clearInterval(interval);
        }
      } catch (err) {
        setError('Failed to check batch status');
        setLoading(false);
        clearInterval(interval);
      }
    };

    // Check immediately
    checkBatchStatus();

    // Then check every 2 seconds
    interval = setInterval(checkBatchStatus, 2000);

    return () => clearInterval(interval);
  }, [batchId]);

  const handleDownload = (fileId) => {
    window.open(`${API_URL}/video/${fileId}`, '_blank');
  };

  const handleCleanup = async () => {
    try {
      await axios.delete(`${API_URL}/batch-cleanup/${batchId}`);
    } catch (err) {
      console.error('Cleanup failed:', err);
    }
    onReset();
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-400';
      case 'failed':
        return 'text-red-400';
      case 'downloading':
      case 'trimming':
        return 'text-blue-400';
      case 'queued':
        return 'text-yellow-400';
      default:
        return 'text-gray-400';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return (
          <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'failed':
        return (
          <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      case 'downloading':
      case 'trimming':
        return (
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        );
      case 'queued':
        return (
          <svg className="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-dark-lighter border border-gray-800 rounded-2xl p-12 shadow-2xl text-center">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          </div>
          <h2 className="text-2xl font-bold text-white mb-3">Loading Batch Status...</h2>
          <p className="text-gray-400">Please wait</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-dark-lighter border border-red-800/50 rounded-2xl p-12 shadow-2xl text-center">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-red-500/20 border-2 border-red-500 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-white mb-3">Error</h2>
          <p className="text-red-400 mb-8">{error}</p>
          <button
            onClick={onReset}
            className="w-full bg-dark border border-gray-700 text-gray-300 hover:text-white hover:border-gray-600 font-medium px-6 py-3.5 rounded-lg transition-all"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!batchStatus) return null;

  const allCompleted = batchStatus.in_progress === 0;
  const progressPercentage = Math.round((batchStatus.completed / batchStatus.total) * 100);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-dark-lighter border border-gray-800 rounded-2xl p-8 shadow-2xl">
        {/* Header Stats */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-white mb-4">Batch Download Progress</h2>

          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-dark border border-gray-700 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-white">{batchStatus.total}</div>
              <div className="text-gray-400 text-sm mt-1">Total</div>
            </div>
            <div className="bg-dark border border-green-800/50 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-green-400">{batchStatus.completed}</div>
              <div className="text-gray-400 text-sm mt-1">Completed</div>
            </div>
            <div className="bg-dark border border-blue-800/50 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-blue-400">{batchStatus.in_progress}</div>
              <div className="text-gray-400 text-sm mt-1">In Progress</div>
            </div>
            <div className="bg-dark border border-red-800/50 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-red-400">{batchStatus.failed}</div>
              <div className="text-gray-400 text-sm mt-1">Failed</div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-dark border border-gray-700 rounded-full h-4 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary to-cyan-300 transition-all duration-500"
              style={{ width: `${progressPercentage}%` }}
            ></div>
          </div>
          <div className="text-right text-gray-400 text-sm mt-2">{progressPercentage}% Complete</div>
        </div>

        {/* Individual Downloads */}
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {batchStatus.downloads.map((download, index) => (
            <div
              key={download.file_id}
              className="bg-dark border border-gray-700 rounded-lg p-4 hover:border-gray-600 transition-all"
            >
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 mt-1">
                  {getStatusIcon(download.status)}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="text-white font-medium mb-1">
                        Video {index + 1}
                      </div>
                      <div className="text-gray-500 text-xs mb-2 truncate">
                        {download.url}
                      </div>
                      {download.filename && (
                        <div className="text-primary text-sm truncate">
                          {download.filename}
                        </div>
                      )}
                      {download.error && (
                        <div className="text-red-400 text-sm mt-1">
                          {download.error}
                        </div>
                      )}
                    </div>

                    <div className="flex-shrink-0">
                      <div className={`text-sm font-medium ${getStatusColor(download.status)} capitalize`}>
                        {download.status}
                      </div>
                      <div className="text-gray-500 text-xs mt-1">
                        {download.progress}
                      </div>
                    </div>
                  </div>
                </div>

                {download.ready && (
                  <button
                    onClick={() => handleDownload(download.file_id)}
                    className="bg-primary hover:bg-cyan-400 text-dark font-medium px-4 py-2 rounded-lg transition-all flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                    </svg>
                    Download
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="mt-6 pt-6 border-t border-gray-700">
          {allCompleted && (
            <div className="space-y-3">
              <div className="bg-green-900/20 border border-green-800 text-green-400 px-4 py-3 rounded-lg text-sm text-center">
                ✅ All downloads completed! ({batchStatus.completed} successful, {batchStatus.failed} failed)
              </div>
              <button
                onClick={handleCleanup}
                className="w-full bg-dark border border-gray-700 text-gray-300 hover:text-white hover:border-gray-600 font-medium px-6 py-3.5 rounded-lg transition-all"
              >
                Start New Batch Download
              </button>
            </div>
          )}
          {!allCompleted && (
            <div className="bg-blue-900/20 border border-blue-800 text-blue-400 px-4 py-3 rounded-lg text-sm text-center">
              ⏳ Downloading {batchStatus.in_progress} video(s)... Please wait
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default BatchDownloadStatus;
