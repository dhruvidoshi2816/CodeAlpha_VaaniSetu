import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Copy, Download, Trash2, Share2, Wand2, FileText, Check, Languages,
} from 'lucide-react';
import toast from 'react-hot-toast';
import SearchableLanguageSelector from '../ui/SearchableLanguageSelector';
import {
  SwapButton, ConfidenceBadge, LoadingDots, DetectedLanguageBadge,
} from '../ui/LanguageSelector';
import ToneSelector from '../ui/ToneSelector';
import { translateApi, aiApi, historyApi } from '../../api/client';
import { useLanguages, useDebounce, useKeyboardShortcuts } from '../../hooks/useTranslation';
import { downloadText, shareText } from '../../utils/constants';

export default function TextTranslation() {
  const { languages } = useLanguages();
  const [sourceLang,     setSourceLang]     = useState('auto');
  const [targetLang,     setTargetLang]     = useState('en');
  const [tone,           setTone]           = useState('professional');
  const [sourceText,     setSourceText]     = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [loading,        setLoading]        = useState(false);
  const [confidence,     setConfidence]     = useState(null);
  const [detectedLang,   setDetectedLang]   = useState(null);
  const [isRomanized,    setIsRomanized]    = useState(false);
  const [copied,         setCopied]         = useState(false);
  const [realtime,       setRealtime]       = useState(true);

  const debouncedText = useDebounce(sourceText, realtime ? 800 : 999_999);

  const translate = useCallback(async (text = sourceText) => {
    if (!text.trim()) {
      setTranslatedText(''); setConfidence(null);
      setDetectedLang(null); setIsRomanized(false);
      return;
    }
    setLoading(true);
    try {
      const { data } = await translateApi.translate({
        text, source_lang: sourceLang, target_lang: targetLang, tone,
      });
      setTranslatedText(data.translated_text);
      setConfidence(data.confidence);
      if (data.detected_lang_info && sourceLang === 'auto') {
        setDetectedLang(data.detected_lang_info);
        setIsRomanized(!!data.romanized_input);
      }
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  }, [sourceText, sourceLang, targetLang, tone]);

  useEffect(() => {
    if (realtime && debouncedText.trim()) translate(debouncedText);
  }, [debouncedText, sourceLang, targetLang, tone, realtime]);

  useKeyboardShortcuts({
    'ctrl+enter':   () => translate(),
    'ctrl+shift+c': () => handleCopy(),
  });

  const handleSwap = () => {
    if (sourceLang === 'auto') return;
    setSourceLang(targetLang); setTargetLang(sourceLang);
    setSourceText(translatedText); setTranslatedText(sourceText);
    setDetectedLang(null); setIsRomanized(false);
  };

  const handleCopy = async () => {
    if (!translatedText) return;
    await navigator.clipboard.writeText(translatedText);
    setCopied(true);
    toast.success('Copied to clipboard');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleClear = () => {
    setSourceText(''); setTranslatedText('');
    setConfidence(null); setDetectedLang(null); setIsRomanized(false);
  };

  const handleSave = async () => {
    if (!translatedText) return;
    try {
      await historyApi.save({
        original_text:   sourceText,
        translated_text: translatedText,
        source_lang:     sourceLang === 'auto' ? (detectedLang?.code || 'en') : sourceLang,
        target_lang:     targetLang,
        tone,
        confidence,
      });
      toast.success('Saved to history');
      syncHistoryCache({
        original_text: sourceText,
        translated_text: translatedText,
        source_lang: sourceLang === 'auto' ? (detectedLang?.code || 'en') : sourceLang,
        target_lang: targetLang,
        tone,
        confidence,
        created_at: new Date().toISOString(),
      });
    } catch (err) { toast.error(err.message); }
  };

  const syncHistoryCache = (entry) => {
    try {
      const key = 'vaanisetu-history-cache';
      const prev = JSON.parse(localStorage.getItem(key) || '[]');
      const next = [entry, ...prev.filter(
        (e) => !(e.original_text === entry.original_text && e.translated_text === entry.translated_text)
      )].slice(0, 50);
      localStorage.setItem(key, JSON.stringify(next));
    } catch { /* ignore quota errors */ }
  };

  const handleGrammar = async () => {
    if (!sourceText.trim()) return;
    setLoading(true);
    try {
      const { data } = await aiApi.grammar(sourceText);
      setSourceText(data.corrected_text);
      toast.success(data.used_ai ? 'Grammar corrected with AI' : 'Grammar check complete');
    } catch (err) { toast.error(err.message); }
    finally { setLoading(false); }
  };

  const handleSummarize = async () => {
    if (!sourceText.trim()) return;
    setLoading(true);
    try {
      const { data } = await aiApi.summarizeTranslate({
        text: sourceText, source_lang: sourceLang, target_lang: targetLang,
      });
      setSourceText(data.summary);
      setTranslatedText(data.translated_text);
      setConfidence(data.confidence);
      if (data.detected_lang_info) setDetectedLang(data.detected_lang_info);
      toast.success('Summarised and translated');
    } catch (err) { toast.error(err.message); }
    finally { setLoading(false); }
  };

  const handleShare = async () => {
    if (!translatedText) return;
    const result = await shareText(translatedText);
    if (result === 'copied') toast.success('Copied for sharing');
  };

  return (
    <div className="space-y-5">
      {/* Language row */}
      <div className="flex flex-col sm:flex-row sm:items-end gap-4">
        <div className="flex-1">
          <SearchableLanguageSelector languages={languages} value={sourceLang}
            onChange={(v) => { setSourceLang(v); setDetectedLang(null); setIsRomanized(false); }}
            label="From" />
        </div>
        <SwapButton onClick={handleSwap} disabled={sourceLang === 'auto'} />
        <div className="flex-1">
          <SearchableLanguageSelector languages={languages} value={targetLang}
            onChange={setTargetLang} label="To" showAuto={false} />
        </div>
      </div>

      {/* Detection badges */}
      <AnimatePresence>
        {detectedLang && sourceLang === 'auto' && (
          <motion.div
            initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="flex flex-wrap items-center gap-2"
          >
            <DetectedLanguageBadge langInfo={detectedLang} />
            {isRomanized && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium text-violet-400 bg-violet-400/10">
                <Languages className="h-3 w-3" />
                Romanized input detected
              </span>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Tone */}
      <div>
        <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2">Tone</p>
        <ToneSelector value={tone} onChange={setTone} />
      </div>

      {/* Panels */}
      <div className="grid lg:grid-cols-2 gap-4">
        {/* Source */}
        <div className="card relative">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-zinc-400">Source</span>
            <span className="text-xs text-zinc-600">{sourceText.length} / 10,000</span>
          </div>
          <textarea
            value={sourceText}
            onChange={(e) => setSourceText(e.target.value)}
            placeholder="Type or paste text… try 'kem cho' or 'kaise ho'"
            maxLength={10000}
            className="w-full h-48 bg-transparent resize-none focus:outline-none text-zinc-100 placeholder:text-zinc-600 leading-relaxed"
            aria-label="Source text"
          />
          <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-white/5">
            <button onClick={handleGrammar} disabled={!sourceText.trim()}
              className="btn-secondary text-xs py-1.5 px-3 disabled:opacity-40">
              <Wand2 className="h-3.5 w-3.5" /> Fix Grammar
            </button>
            <button onClick={handleSummarize} disabled={!sourceText.trim()}
              className="btn-secondary text-xs py-1.5 px-3 disabled:opacity-40">
              <FileText className="h-3.5 w-3.5" /> Summarise
            </button>
            <button onClick={handleClear} className="btn-secondary text-xs py-1.5 px-3">
              <Trash2 className="h-3.5 w-3.5" /> Clear
            </button>
          </div>
        </div>

        {/* Output */}
        <div className="card relative">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-zinc-400">Translation</span>
              {loading && <LoadingDots />}
            </div>
            <ConfidenceBadge confidence={confidence} />
          </div>
          <AnimatePresence mode="wait">
            <motion.div key={translatedText} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              className="h-48 overflow-y-auto">
              <p className="text-zinc-100 leading-relaxed whitespace-pre-wrap">
                {translatedText || <span className="text-zinc-600">Translation will appear here…</span>}
              </p>
            </motion.div>
          </AnimatePresence>
          <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-white/5">
            <button onClick={handleCopy} disabled={!translatedText}
              className="btn-secondary text-xs py-1.5 px-3 disabled:opacity-40">
              {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />} Copy
            </button>
            <button onClick={() => downloadText(translatedText)} disabled={!translatedText}
              className="btn-secondary text-xs py-1.5 px-3 disabled:opacity-40">
              <Download className="h-3.5 w-3.5" /> Download
            </button>
            <button onClick={handleShare} disabled={!translatedText}
              className="btn-secondary text-xs py-1.5 px-3 disabled:opacity-40">
              <Share2 className="h-3.5 w-3.5" /> Share
            </button>
            <button onClick={handleSave} disabled={!translatedText}
              className="btn-secondary text-xs py-1.5 px-3 disabled:opacity-40">
              Save
            </button>
          </div>
        </div>
      </div>

      {/* Real-time toggle */}
      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 text-sm text-zinc-500 cursor-pointer select-none">
          <input type="checkbox" checked={realtime} onChange={(e) => setRealtime(e.target.checked)}
            className="rounded border-zinc-600 text-brand-indigo focus:ring-brand-indigo" />
          Real-time translation
        </label>
        {!realtime && (
          <button onClick={() => translate()} disabled={loading} className="btn-primary">
            {loading ? 'Translating…' : 'Translate'}
          </button>
        )}
      </div>
    </div>
  );
}
