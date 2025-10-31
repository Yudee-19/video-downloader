import React, { useState } from 'react';
import axios from 'axios';
import './DownloadForm.css';

const API_URL = 'http://localhost:8000';

function DownloadForm({ onDownloadStart }) {
  const [url, setUrl] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [audioOnly, setAudioOnly] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!url.trim()) {
      setError('Please enter a YouTube URL');
      return;
    }

    // Basic YouTube URL validation
    if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
      setError('Please enter a valid YouTube URL');
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/download`, {
        url: url.trim(),
        start_time: startTime || null,
        end_time: endTime || null,
        audio_only: audioOnly,
      });

      onDownloadStart(response.data.file_id);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start download. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="download-form">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="url">YouTube URL</label>
          <input
            type="text"
            id="url"
            placeholder="https://www.youtube.com/watch?v=..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={loading}
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="startTime">
              Start Time <span className="optional">(optional)</span>
            </label>
            <input
              type="text"
              id="startTime"
              placeholder="00:00:30"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              disabled={loading}
            />
            <small>Format: HH:MM:SS or seconds</small>
          </div>

          <div className="form-group">
            <label htmlFor="endTime">
              End Time <span className="optional">(optional)</span>
            </label>
            <input
              type="text"
              id="endTime"
              placeholder="00:02:00"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              disabled={loading}
            />
            <small>Format: HH:MM:SS or seconds</small>
          </div>
        </div>

        <div className="form-group checkbox-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={audioOnly}
              onChange={(e) => setAudioOnly(e.target.checked)}
              disabled={loading}
            />
            <span>Audio Only (MP3)</span>
          </label>
        </div>

        {error && <div className="error-message">{error}</div>}

        <button type="submit" className="submit-button" disabled={loading}>
          {loading ? (
            <>
              <span className="spinner"></span>
              Starting Download...
            </>
          ) : (
            <>
              <span>⬇️</span>
              Download
            </>
          )}
        </button>
      </form>
    </div>
  );
}

export default DownloadForm;
