import React, { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function DownloadForm({ onDownloadStart }) {
  const [url, setUrl] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [audioOnly, setAudioOnly] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Video preview states
  const [showPreview, setShowPreview] = useState(false);
  const [videoId, setVideoId] = useState('');
  const [loadingPreview, setLoadingPreview] = useState(false);

  // Extract YouTube video ID from URL
  const extractYouTubeId = (url) => {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
  };

  const handleFetchVideo = () => {
    setError('');
    setShowPreview(false);
    setVideoId('');

    if (!url.trim()) {
      setError('Please enter a URL first');
      return;
    }

    // Check if it's YouTube
    const isYouTube = url.includes('youtube.com') || url.includes('youtu.be');
    const isInstagram = url.includes('instagram.com');

    if (isInstagram) {
      setError('Video preview is only available for YouTube videos');
      return;
    }

    if (!isYouTube) {
      setError('Please enter a valid YouTube URL');
      return;
    }

    setLoadingPreview(true);

    // Extract video ID
    const extractedId = extractYouTubeId(url);

    if (extractedId) {
      setVideoId(extractedId);
      setShowPreview(true);
      setLoadingPreview(false);
    } else {
      setError('Could not extract video ID from URL');
      setLoadingPreview(false);
    }
  };

  const handleAction = async (actionType) => {
    setError('');

    if (!url.trim()) {
      setError('Please enter a YouTube or Instagram URL');
      return;
    }

    // URL validation for YouTube and Instagram
    const isYouTube = url.includes('youtube.com') || url.includes('youtu.be');
    const isInstagram = url.includes('instagram.com');

    if (!isYouTube && !isInstagram) {
      setError('Please enter a valid YouTube or Instagram URL');
      return;
    }

    // For streaming downloads we just hand URL + options to parent
    setLoading(true);
    try {
      await onDownloadStart({
        url: url.trim(),
        start_time: startTime || null,
        end_time: endTime || null,
        audio_only: audioOnly,
        type: actionType
      });
    } catch (err) {
      console.error(err);
      setError('Failed to start download');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-dark-lighter border border-gray-800 rounded-2xl p-8 shadow-2xl">
      <form onSubmit={(e) => e.preventDefault()} className="space-y-6">
        <div>
          <label htmlFor="url" className="block text-gray-300 text-sm font-medium mb-3">
            YouTube Video URL
          </label>
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              </div>
              <input
                type="text"
                id="url"
                placeholder="https://www.youtube.com/watch?v=... or https://www.instagram.com/reel/..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={loading}
                className="w-full bg-dark border border-gray-700 text-white rounded-lg pl-12 pr-4 py-3.5 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all placeholder-gray-600 disabled:opacity-50"
              />
            </div>
            <button
              type="button"
              onClick={handleFetchVideo}
              disabled={loading || loadingPreview}
              className="bg-dark border border-gray-700 hover:border-primary text-gray-300 hover:text-primary font-medium px-6 py-3.5 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
            >
              {loadingPreview ? (
                <span className="flex items-center gap-2">
                  <span className="inline-block w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></span>
                  Fetching...
                </span>
              ) : (
                'Fetch Video'
              )}
            </button>
          </div>
        </div>

        {/* Video Preview */}
        {showPreview && videoId && (
          <div className="relative">
            <iframe
              className='w-full rounded-lg border border-gray-700'
              height="400"
              src={`https://www.youtube.com/embed/${videoId}`}
              title="YouTube video player"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              referrerPolicy="strict-origin-when-cross-origin"
              allowFullScreen
            />
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="startTime" className="block text-gray-300 text-sm font-medium mb-3">
              Start Time <span className="text-gray-500 text-xs font-normal">(optional)</span>
            </label>
            <input
              type="text"
              id="startTime"
              placeholder="00:00:30"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              disabled={loading}
              className="w-full bg-dark border border-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all placeholder-gray-600 disabled:opacity-50"
            />
            <small className="text-gray-500 text-xs mt-1.5 block">Format: HH:MM:SS or seconds</small>
          </div>

          <div>
            <label htmlFor="endTime" className="block text-gray-300 text-sm font-medium mb-3">
              End Time <span className="text-gray-500 text-xs font-normal">(optional)</span>
            </label>
            <input
              type="text"
              id="endTime"
              placeholder="00:02:00"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              disabled={loading}
              className="w-full bg-dark border border-gray-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all placeholder-gray-600 disabled:opacity-50"
            />
            <small className="text-gray-500 text-xs mt-1.5 block">Format: HH:MM:SS or seconds</small>
          </div>
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
              Audio Only (MP3)
            </span>
          </label>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-800 text-red-400 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <button
            type="button"
            onClick={() => handleAction('stream')}
            className="w-full bg-primary hover:bg-cyan-400 text-dark font-semibold px-6 py-3.5 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-primary/30 flex items-center justify-center gap-2"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="inline-block w-5 h-5 border-2 border-dark border-t-transparent rounded-full animate-spin"></span>
                Starting...
              </>
            ) : (
              <>
                <span>▶️</span>
                Stream
              </>
            )}
          </button>

          <button
            type="button"
            onClick={() => handleAction('download')}
            className="w-full bg-dark border border-gray-700 hover:border-primary text-gray-300 hover:text-primary font-semibold px-6 py-3.5 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg flex items-center justify-center gap-2"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="inline-block w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
                Starting...
              </>
            ) : (
              <>
                <span>⬇️</span>
                Download
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

export default DownloadForm;