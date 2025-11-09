import React, { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function BatchDownloadForm({ onBatchDownloadStart }) {
  const [urls, setUrls] = useState(['', '', '']);
  const [audioOnly, setAudioOnly] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleUrlChange = (index, value) => {
    const newUrls = [...urls];
    newUrls[index] = value;
    setUrls(newUrls);
  };

  const addUrlField = () => {
    setUrls([...urls, '']);
  };

  const removeUrlField = (index) => {
    if (urls.length > 1) {
      const newUrls = urls.filter((_, i) => i !== index);
      setUrls(newUrls);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Filter out empty URLs
    const validUrls = urls.filter(url => url.trim() !== '');

    if (validUrls.length === 0) {
      setError('Please enter at least one URL');
      return;
    }

    // Validate URLs
    const invalidUrls = validUrls.filter(url => {
      const isYouTube = url.includes('youtube.com') || url.includes('youtu.be');
      const isInstagram = url.includes('instagram.com');
      return !isYouTube && !isInstagram;
    });

    if (invalidUrls.length > 0) {
      setError('All URLs must be valid YouTube or Instagram links');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/batch-download`, {
        urls: validUrls,
        audio_only: audioOnly,
      });

      onBatchDownloadStart(response.data.batch_id, validUrls.length);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start batch download. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-dark-lighter border border-gray-800 rounded-2xl p-8 shadow-2xl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">Batch Download</h2>
        <p className="text-gray-400">Download multiple videos at once</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-3">
          <label className="block text-gray-300 text-sm font-medium mb-3">
            Video URLs
          </label>

          {urls.map((url, index) => (
            <div key={index} className="flex gap-3">
              <div className="flex-1 relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                </div>
                <input
                  type="text"
                  placeholder={`Video URL ${index + 1}`}
                  value={url}
                  onChange={(e) => handleUrlChange(index, e.target.value)}
                  disabled={loading}
                  className="w-full bg-dark border border-gray-700 text-white rounded-lg pl-12 pr-4 py-3.5 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all placeholder-gray-600 disabled:opacity-50"
                />
              </div>
              {urls.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeUrlField(index)}
                  disabled={loading}
                  className="bg-dark border border-red-800 text-red-400 hover:bg-red-900/20 font-medium px-4 py-3.5 rounded-lg transition-all disabled:opacity-50"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              )}
            </div>
          ))}

          <button
            type="button"
            onClick={addUrlField}
            disabled={loading || urls.length >= 10}
            className="w-full bg-dark border border-gray-700 hover:border-primary text-gray-300 hover:text-primary font-medium px-6 py-3 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Add Another URL {urls.length >= 10 && '(Max 10)'}
          </button>
        </div>

        <div className="flex items-center">
          <label className="flex items-center cursor-pointer group">
            <input
              type="checkbox"
              checked={audioOnly}
              onChange={(e) => setAudioOnly(e.target.checked)}
              disabled={loading}
              className="w-5 h-5 text-primary border-gray-700 rounded disabled:opacity-50 cursor-pointer"
            />
            <span className="ml-3 text-gray-300 font-medium group-hover:text-white transition-colors">
              Audio Only (MP3) - All videos
            </span>
          </label>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-800 text-red-400 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <button
          type="submit"
          className="w-full bg-primary hover:bg-cyan-400 text-dark font-semibold px-6 py-3.5 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-primary/30 flex items-center justify-center gap-2"
          disabled={loading}
        >
          {loading ? (
            <>
              <span className="inline-block w-5 h-5 border-2 border-dark border-t-transparent rounded-full animate-spin"></span>
              Starting Batch Download...
            </>
          ) : (
            <>
              <span>⚡</span>
              Download All ({urls.filter(u => u.trim()).length} videos)
            </>
          )}
        </button>
      </form>
    </div>
  );
}

export default BatchDownloadForm;
