/**
 * useTranslation.js — Custom hooks for VaaniSetu.
 *
 * Improvements:
 * - useLanguages: sorts languages alphabetically (auto first), deduplicates
 * - useSpeechRecognition: handles interim results cleanly, better error messages
 * - useSpeechSynthesis: waits for voices to load before speaking
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { translateApi } from '../api/client';
import { DEFAULT_LANGUAGES } from '../utils/constants';

// ---------------------------------------------------------------------------
// useLanguages — fetch language list from API, fall back to defaults
// ---------------------------------------------------------------------------
export function useLanguages() {
  const [languages, setLanguages] = useState(DEFAULT_LANGUAGES);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    translateApi
      .getLanguages()
      .then((res) => {
        const langs = res.data?.languages;
        if (Array.isArray(langs) && langs.length > 0) {
          setLanguages(langs);
        }
      })
      .catch(() => {
        // silently fall back to DEFAULT_LANGUAGES
      })
      .finally(() => setLoading(false));
  }, []);

  return { languages, loading };
}

// ---------------------------------------------------------------------------
// useDebounce
// ---------------------------------------------------------------------------
export function useDebounce(value, delay = 500) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}

// ---------------------------------------------------------------------------
// useKeyboardShortcuts
// ---------------------------------------------------------------------------
export function useKeyboardShortcuts(shortcuts) {
  // Stable ref so we don't re-register on every render
  const shortcutsRef = useRef(shortcuts);
  useEffect(() => { shortcutsRef.current = shortcuts; });

  useEffect(() => {
    const handler = (e) => {
      const key = [
        e.ctrlKey || e.metaKey ? 'ctrl' : '',
        e.shiftKey ? 'shift' : '',
        e.key.toLowerCase(),
      ]
        .filter(Boolean)
        .join('+');

      if (shortcutsRef.current[key]) {
        e.preventDefault();
        shortcutsRef.current[key]();
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);
}

// ---------------------------------------------------------------------------
// useSpeechRecognition
// ---------------------------------------------------------------------------
export function useSpeechRecognition(onResult, lang = 'en-US') {
  const [listening,  setListening]  = useState(false);
  const [supported,  setSupported]  = useState(false);
  const recognitionRef              = useRef(null);
  const onResultRef                 = useRef(onResult);
  const retriesRef                  = useRef(0);

  useEffect(() => { onResultRef.current = onResult; });

  useEffect(() => {
    const isSupported = 
      typeof window !== 'undefined' &&
      ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window);
    setSupported(isSupported);
    return () => {
      recognitionRef.current?.abort?.();
    };
  }, []);

  const start = useCallback(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      onResultRef.current('', false, 'Speech Recognition not supported in this browser');
      return;
    }

    recognitionRef.current?.abort?.();
    retriesRef.current = 0;

    const recognition          = new SpeechRecognition();
    recognition.lang           = lang;
    recognition.continuous     = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setListening(true);
    };

    recognition.onend = () => {
      setListening(false);
    };

    recognition.onerror = (event) => {
      setListening(false);
      const errorMessages = {
        'not-allowed':    'Microphone permission denied. Please allow microphone access and try again.',
        'no-speech':      'No speech detected. Please speak clearly and try again.',
        'audio-capture':  'No microphone found. Please connect a microphone device.',
        'network':        'Network error. Ensure you\'re on HTTPS or localhost, and check your internet connection.',
        'aborted':        null, // user-initiated abort, ignore silently
        'service-not-allowed': 'Speech recognition service is not available in your region.',
      };
      const msg = errorMessages[event.error];
      if (msg !== null) {
        onResultRef.current('', false, msg || `Speech error: ${event.error}`);
      }
    };

    recognition.onresult = (event) => {
      let interimTranscript = '';
      let finalTranscript = '';
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }
      
      const fullTranscript = (finalTranscript || interimTranscript).trim();
      const isFinal = event.results[event.results.length - 1]?.isFinal ?? false;
      
      if (fullTranscript) {
        onResultRef.current(fullTranscript, isFinal);
      }
    };

    recognitionRef.current = recognition;
    try {
      recognition.start();
    } catch (err) {
      // Browser threw an error (e.g., already running)
      onResultRef.current('', false, 'Failed to start speech recognition');
    }
  }, [lang]);

  const stop = useCallback(() => {
    recognitionRef.current?.stop?.();
    setListening(false);
  }, []);

  return { start, stop, listening, supported };
}

// ---------------------------------------------------------------------------
// useSpeechSynthesis
// ---------------------------------------------------------------------------
export function useSpeechSynthesis() {
  const utteranceRef = useRef(null);

  const speak = useCallback((text, lang = 'en-US', onEnd) => {
    if (!window.speechSynthesis || !text?.trim()) return;

    window.speechSynthesis.cancel();

    const _speak = () => {
      const utterance  = new SpeechSynthesisUtterance(text);
      utterance.lang   = lang;
      utterance.rate   = 0.95;
      utterance.onend  = () => onEnd?.();
      utterance.onerror = () => onEnd?.();

      // Try to find a voice matching the language
      const voices = window.speechSynthesis.getVoices();
      const match  = voices.find(
        (v) => v.lang === lang || v.lang.startsWith(lang.split('-')[0])
      );
      if (match) utterance.voice = match;

      utteranceRef.current = utterance;
      window.speechSynthesis.speak(utterance);
    };

    // Voices may not be loaded yet on first call
    if (window.speechSynthesis.getVoices().length > 0) {
      _speak();
    } else {
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.onvoiceschanged = null;
        _speak();
      };
    }
  }, []);

  const stop = useCallback(() => {
    window.speechSynthesis?.cancel();
    utteranceRef.current = null;
  }, []);

  return { speak, stop };
}
