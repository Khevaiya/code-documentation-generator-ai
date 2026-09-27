import { useState, useRef, useCallback } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || '';

export function useAnalysis() {
  const [job, setJob] = useState(null);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const pollRef = useRef(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const pollJob = useCallback((jobId) => {
    pollRef.current = setInterval(async () => {
      try {
        const res = await axios.get(`${API_BASE}/jobs/${jobId}`);
        setJob(res.data);
        if (res.data.status === 'completed' || res.data.status === 'failed') {
          stopPolling();
        }
      } catch (err) {
        console.error('Poll error:', err);
      }
    }, 5000);
  }, [stopPolling]);

  const submitGithub = useCallback(async (params) => {
    setError(null);
    setIsSubmitting(true);
    setJob(null);
    stopPolling();
    try {
      const form = new FormData();
      form.append('github_url', params.github_url);
      form.append('lenses', params.lenses.join(','));
      form.append('output_formats', params.output_formats.join(','));
      if (params.audience_role) form.append('audience_role', params.audience_role);
      if (params.project_name) form.append('project_name', params.project_name);
      const res = await axios.post(`${API_BASE}/analyze/github`, form);
      setJob(res.data);
      pollJob(res.data.job_id);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Unknown error');
    } finally {
      setIsSubmitting(false);
    }
  }, [stopPolling, pollJob]);

  const submitZip = useCallback(async (params) => {
    setError(null);
    setIsSubmitting(true);
    setJob(null);
    stopPolling();
    try {
      const form = new FormData();
      form.append('file', params.file);
      form.append('lenses', params.lenses.join(','));
      form.append('output_formats', params.output_formats.join(','));
      if (params.audience_role) form.append('audience_role', params.audience_role);
      if (params.project_name) form.append('project_name', params.project_name);
      const res = await axios.post(`${API_BASE}/analyze/upload`, form);
      setJob(res.data);
      pollJob(res.data.job_id);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Unknown error');
    } finally {
      setIsSubmitting(false);
    }
  }, [stopPolling, pollJob]);

  const reset = useCallback(() => {
    stopPolling();
    setJob(null);
    setError(null);
    setIsSubmitting(false);
  }, [stopPolling]);

  return { job, error, isSubmitting, submitGithub, submitZip, reset };
}
