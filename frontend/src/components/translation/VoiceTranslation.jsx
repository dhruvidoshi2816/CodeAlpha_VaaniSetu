import { useState, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Mic, MicOff, Volume2, Square } from 'lucide-react';
import toast from 'react-hot-toast';
import SearchableLanguageSelector from '../ui/SearchableLanguageSelector';
import { ConfidenceBadge, LoadingDots } from '../ui/LanguageSelector';
import { translateApi } from '../../api/client';
import {
  useLanguages,
  useSpeechRecognition,
  useSpeechSynthesis,
} from '../../hooks/useTranslation';
import { getSpeechLang } from '../../utils/constants';

export default function VoiceTranslation() {
  const { languages } = useLanguages();
  const [sourceLang,     setSourceLang]     = useState('auto');
  const [targetLang,     setTargetLang]     = useState('en');
  const [sourceText,     setSourceText]     = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [loading,        setLoading]        = useState(false);
  const [confidence,     setConfidence]     = useState(null);
  const [speaking,       setSpeaking]       = useState(false);

  const { speak, stop } = useSpeechSynthesis();

  const handleTranslate = useCallback(async (text) => {
    const input = (text ?? sourceText).trim();
    if (!input) return;
    setLoading(true);
    try {
      const { data } = await translateApi.translate({
        text:        input,
        source_lang: sourceLang,
        target_lang: targetLang,
      });
      setTranslatedText(data.translated_text);
      setConfidence(data.confidence);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  }, [sourceText, sourceLang, targetLang]);

  const onSpeechResult = useCallback((transcript, isFinal, error) => {
    if (error) {
      toast.error(error);
      return;
    }
    setSourceText(transcript);
    if (isFinal && transcript.trim()) {
      handleTranslate(transcript);
    }
  }, [handleTranslate]);

  const { start, stop: stopListening, listening, supported } = useSpeechRecognition(
    onSpeechResult,
    getSpeechLang(sourceLang),
  );

  const handleSpeak = () => {
    if (!translatedText) return;
    if (speaking) {
      stop();
      setSpeaking(false);
    } else {
      setSpeaking(true);
      speak(translatedText, getSpeechLang(targetLang), () => setSpeaking(false));
    }
  };

  // Stop synthesis when component unmounts
  useEffect(() => () => stop(), [stop]);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="grid sm:grid-cols-2 gap-4">
        <SearchableLanguageSelector
          languages={languages}
          value={sourceLang}
          onChange={setSourceLang}
          label="Speak in"
          showAuto={false}
        />
        <SearchableLanguageSelector
          languages={languages}
          value={targetLang}
          onChange={setTargetLang}
          label="Translate to"
          showAuto={false}
        />
      </div>

      <motion.div
        layout
        className="card flex flex-col items-center py-12 relative overflow-hidden"
      >
        <motion.div
          className="absolute inset-0 bg-gradient-to-b from-brand-indigo/5 to-transparent pointer-events-none"
          animate={{ opacity: listening ? 1 : 0.5 }}
        />

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => {
            if (!supported) {
              toast.error('Voice recognition requires Chrome or Edge');
              return;
            }
            if (listening) stopListening();
            else start();
          }}
          aria-label={listening ? 'Stop listening' : 'Start listening'}
          className={`relative z-10 h-24 w-24 rounded-full flex items-center justify-center transition-all ${
            listening
              ? 'bg-red-500/20 ring-4 ring-red-500/40 shadow-[0_0_40px_rgba(239,68,68,0.3)]'
              : 'bg-brand-indigo/20 ring-2 ring-brand-indigo/40 hover:ring-brand-indigo/60'
          }`}
        >
          {listening ? (
            <>
              <MicOff className="h-8 w-8 text-red-400" />
              {[0, 1, 2].map((i) => (
                <motion.span
                  key={i}
                  className="absolute inset-0 rounded-full border-2 border-red-400/30"
                  animate={{ scale: [1, 1.5], opacity: [0.6, 0] }}
                  transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.4 }}
                />
              ))}
            </>
          ) : (
            <Mic className="h-8 w-8 text-brand-cyan" />
          )}
        </motion.button>

        {listening && (
          <div className="flex items-end gap-1 h-8 mt-6">
            {[0, 1, 2, 3, 4].map((i) => (
              <motion.div
                key={i}
                className="w-1 rounded-full bg-brand-cyan"
                animate={{ height: [8, 24, 12, 28, 10] }}
                transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.1 }}
              />
            ))}
          </div>
        )}

        <p className="mt-4 text-sm text-zinc-500">
          {listening
            ? 'Listening… speak now'
            : 'Tap to speak — auto-translates when you finish'}
        </p>

        {!supported && (
          <p className="mt-2 text-xs text-amber-400">
            Voice recognition requires Chrome or Edge
          </p>
        )}

        {sourceText && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 w-full max-w-lg p-4 rounded-xl bg-surface-800/50 text-center"
          >
            <p className="text-sm text-zinc-400 mb-1">You said</p>
            <p className="text-zinc-100">{sourceText}</p>
          </motion.div>
        )}
      </motion.div>

      {sourceText && !listening && (
        <button
          onClick={() => handleTranslate()}
          disabled={loading}
          className="btn-primary w-full sm:w-auto"
        >
          {loading ? 'Translating…' : 'Translate again'}
        </button>
      )}

      {(translatedText || loading) && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-zinc-400">Translation</span>
            <div className="flex items-center gap-3">
              {loading && <LoadingDots />}
              <ConfidenceBadge confidence={confidence} />
            </div>
          </div>
          <p className="text-lg text-zinc-100 leading-relaxed mb-4 min-h-[3rem]">
            {loading ? '…' : translatedText}
          </p>
          <button
            onClick={handleSpeak}
            disabled={!translatedText}
            className="btn-secondary text-sm"
          >
            {speaking ? <Square className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
            {speaking ? 'Stop' : 'Listen'}
          </button>
        </motion.div>
      )}
    </motion.div>
  );
}
