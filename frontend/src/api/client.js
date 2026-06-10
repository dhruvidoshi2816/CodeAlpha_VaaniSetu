/**
 * client.js — Axios API client for VaaniSetu.
 *
 * Improvements:
 * - Separate timeout for file uploads (120 s) vs regular requests (30 s)
 * - Retry logic for network errors (up to 2 retries with back-off)
 * - Normalised error messages from all response shapes
 * - Named exports for every API surface
 */

import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api';

// ---------------------------------------------------------------------------
// Base instance
// ---------------------------------------------------------------------------
const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
});

// ---------------------------------------------------------------------------
// Response interceptor — normalise errors
// ---------------------------------------------------------------------------
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const config = err.config || {};

    // Retry on network errors or 5xx (max 2 retries)
    config._retryCount = config._retryCount || 0;
    const isNetworkError = !err.response;
    const isServerError  = err.response?.status >= 500;

    if ((isNetworkError || isServerError) && config._retryCount < 2) {
      config._retryCount += 1;
      await new Promise((r) => setTimeout(r, 600 * config._retryCount));
      return api(config);
    }

    // Extract the most useful error message
    const data    = err.response?.data;
    const message =
      (typeof data === 'object' && (data?.error || data?.message)) ||
      (typeof data === 'string' && data) ||
      err.message ||
      'Something went wrong';

    return Promise.reject(new Error(message));
  }
);

// ---------------------------------------------------------------------------
// Upload instance — longer timeout for OCR / document uploads
// ---------------------------------------------------------------------------
const uploadApi = axios.create({
  baseURL: API_URL,
  timeout: 120_000,
});
uploadApi.interceptors.response.use(
  (res) => res,
  (err) => {
    const data    = err.response?.data;
    const message =
      (typeof data === 'object' && (data?.error || data?.message)) ||
      err.message ||
      'Upload failed';
    return Promise.reject(new Error(message));
  }
);

// ---------------------------------------------------------------------------
// API surfaces
// ---------------------------------------------------------------------------

export const translateApi = {
  /** GET /translate/languages — returns [{code, name, native}] */
  getLanguages: () => api.get('/translate/languages'),

  /** POST /translate/detect — returns {code, name, native, display, confidence} */
  detect: (text) => api.post('/translate/detect', { text }),

  /** POST /translate/translate */
  translate: (data) => api.post('/translate/translate', data),
};

export const ocrApi = {
  /** POST /ocr/extract — OCR only */
  extract: (formData) =>
    uploadApi.post('/ocr/extract', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  /** POST /ocr/translate-image — OCR + translate */
  translateImage: (formData) =>
    uploadApi.post('/ocr/translate-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
};

export const documentApi = {
  /** POST /document/translate */
  translate: (formData) =>
    uploadApi.post('/document/translate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
};

export const historyApi = {
  /** GET /history/ */
  getAll: (params) => api.get('/history/', { params }),

  /** POST /history/ */
  save: (data) => api.post('/history/', data),

  /** PATCH /history/:id/favorite */
  toggleFavorite: (id) => api.patch(`/history/${id}/favorite`),

  /** DELETE /history/:id */
  delete: (id) => api.delete(`/history/${id}`),

  /** DELETE /history/clear */
  clear: () => api.delete('/history/clear'),
};

export const aiApi = {
  /** POST /ai/grammar */
  grammar: (text) => api.post('/ai/grammar', { text }),

  /** POST /ai/summarize-translate */
  summarizeTranslate: (data) => api.post('/ai/summarize-translate', data),
};

export const slangApi = {
  /** GET /slang/modes */
  getModes: () => api.get('/slang/modes'),

  /** GET /slang/glossary?limit=N */
  getGlossary: (limit = 60) => api.get('/slang/glossary', { params: { limit } }),

  /** POST /slang/translate */
  translate: (data) => api.post('/slang/translate', data),
};

export default api;
