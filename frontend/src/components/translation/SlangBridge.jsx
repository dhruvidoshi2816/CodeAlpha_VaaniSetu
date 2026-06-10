import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Copy, Share2, Trash2, Check, ArrowLeftRight, Sparkles, BookOpen, Users,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { ConfidenceBadge, LoadingDots } from '../ui/LanguageSelector';
import { slangApi, historyApi } from '../../api/client';
import { useDebounce, useKeyboardShortcuts } from '../../hooks/useTranslation';
import { shareText, SLANG_MODES, SLANG_EXAMPLES } from '../../utils/constants';

export default function SlangBridge() {
  const [mode,          setMode]          = useState('genz_to_plain');
  const [sourceText,    setSourceText]    = useState('');
  const [translatedText,setTranslatedText]= useState('');
  const [matchedTerms,  setMatchedTerms]  = useState([]);
  const [glossary,      setGlossary]      = useState([]);
  const [loading,       setLoading]       = useState(false);
  const [confidence,    setConfidence]    = useState(null);
  const [copied,        setCopied]        = useState(false);
  const [usedAi,        setUsedAi]        = useState(false);

  const debouncedText = useDebounce(sourceText, 700);
  const activeMode    = SLANG_MODES.find((m) => m.id === mode) || SLANG_MODES[0];

  useEffect(() => {
    slangApi.getGlossary(60)
      .then((res) => setGlossary(res.data.glossary || []))
      .catch(() => {});
  }, []);

  const translate = useCallback(async (text = sourceText) => {
    if (!text.trim()) {
      setTranslatedText('');
      setMatchedTerms([]);
      setConfidence(null);
      return;
    }
    setLoading(true);
    try {
      const { data } = await slangApi.translate({ text, mode, use_ai: true });
      setTranslatedText(data.translated_text);
      setMatchedTerms(data.matched_terms || []);
      setConfidence(data.confidence);
      setUsedAi(data.used_ai);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  }, [sourceText, mode]);

  useEffect(() => {
    if (debouncedText.trim()) translate(debouncedText);
  }, [debouncedText, mode]);

  useKeyboardShortcuts({ 'ctrl+enter': () => translate() });

  const handleSwap = () => {
    setMode(mode === 'genz_to_plain' ? 'plain_to_genz' : 'genz_to_plain');
    setSourceText(translatedText);
    setTranslatedText(sourceText);
    setMatchedTerms([]);
  };

  const handleCopy = async () => {
    if (!translatedText) return;
    await navigator.clipboard.writeText(translatedText);
    setCopied(true);
    toast.success('Copied');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSave = async () => {
    if (!translatedText) return;
    try {
      await historyApi.save({
        original_text:   sourceText,
        translated_text: translatedText,
        source_lang:     mode === 'genz_to_plain' ? 'genz' : 'plain',
        target_lang:     mode === 'genz_to_plain' ? 'plain' : 'genz',
        tone:            mode,
        confidence,
      });
      toast.success('Saved to history');
    } catch (err) {
      toast.error(err.message);
    }
  };

  const handleShare = async () => {
    if (!translatedText) return;
    const result = await shareText(translatedText, 'VaaniSetu Slang Bridge');
    if (result === 'copied') toast.success('Copied for sharing');
  };

  const examples = SLANG_EXAMPLES[mode] || [];

  return (
    <div className="space-y-5">
      {/* Info banner */}
      <div className="flex items-start gap-3 p-4 rounded-xl bg-gradient-to-r from-brand-indigo/10 to-pink-500/5 border border-brand-indigo/20">
        <Users className="h-5 w-5 text-brand-cyan shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium mb-1">Gen-Z Slang Interpreter</p>
          <p className="text-xs text-zinc-500 leading-relaxed">
            Decode rizz, bussin, delulu, and cooked for parents — or rephrase plain English
            so teens actually get it. 200+ slang terms with optional AI polish.
          </p>
        </div>
      </div>

      {/* Mode selector */}
      <div className="flex flex-col sm:flex-row gap-3">
        {SLANG_MODES.map((m) => (
          <button
            key={m.id}
            onClick={() => {
              setMode(m.id);
              setTranslatedText('');
              setMatchedTerms([]);
            }}
            className={`flex-1 p-4 rounded-xl text-left transition-all ${
              mode === m.id
                ? 'bg-brand-indigo/20 ring-1 ring-brand-indigo/40'
                : 'glass hover:bg-white/5'
            }`}
          >
            <p className="text-sm font-medium mb-1">{m.label}</p>
            <p className="text-xs text-zinc-500">{m.desc}</p>
          </button>
        ))}
      </div>

      {/* Swap button */}
      <div className="flex items-center justify-center">
        <motion.button
          whileHover={{ scale: 1.05, rotate: 180 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleSwap}
          className="p-2.5 rounded-xl glass hover:bg-brand-indigo/20 text-sm flex items-center gap-2"
        >
          <ArrowLeftRight className="h-4 w-4" /> Flip direction
        </motion.button>
      </div>

      {/* Example phrases */}
      <div className="flex flex-wrap gap-2">
        <span className="text-xs text-zinc-500 w-full mb-1">Try an example:</span>
        {examples.map((ex) => (
          <button
            key={ex}
            onClick={() => setSourceText(ex)}
            className="px-3 py-1.5 rounded-lg glass text-xs text-zinc-400 hover:text-zinc-200 hover:bg-white/10 transition-colors"
          >
            {ex.length > 45 ? `${ex.slice(0, 45)}…` : ex}
          </button>
        ))}
      </div>

      {/* Translation panels */}
      <div className="grid lg:grid-cols-2 gap-4">
        {/* Source */}
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-zinc-400">{activeMode.source_label}</span>
            <span className="text-xs text-zinc-600">{sourceText.length} chars</span>
          </div>
          <textarea
            value={sourceText}
            onChange={(e) => setSourceText(e.target.value)}
            placeholder={
              mode === 'genz_to_plain'
                ? 'e.g. "That fit is bussin no cap, you ate fr"…'
                : 'e.g. "Please do your homework before dinner"…'
            }
            className="w-full h-40 bg-transparent resize-none focus:outline-none text-zinc-100 placeholder:text-zinc-600 leading-relaxed"
            aria-label="Slang source text"
          />
          <button
            onClick={() => { setSourceText(''); setTranslatedText(''); setMatchedTerms([]); }}
            className="btn-secondary text-xs py-1.5 px-3 mt-3"
          >
            <Trash2 className="h-3.5 w-3.5" /> Clear
          </button>
        </div>

        {/* Output */}
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-zinc-400">{activeMode.target_label}</span>
              {loading && <LoadingDots />}
              {usedAi && !loading && (
                <span className="inline-flex items-center gap-1 text-xs text-brand-cyan">
                  <Sparkles className="h-3 w-3" /> AI polished
                </span>
              )}
            </div>
            <ConfidenceBadge confidence={confidence} />
          </div>
          <AnimatePresence mode="wait">
            <motion.p
              key={translatedText}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="h-40 overflow-y-auto text-zinc-100 leading-relaxed whitespace-pre-wrap"
            >
              {translatedText || (
                <span className="text-zinc-600">Translation will appear here…</span>
              )}
            </motion.p>
          </AnimatePresence>
          <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-white/5">
            <button onClick={handleCopy} disabled={!translatedText} className="btn-secondary text-xs py-1.5 px-3 disabled:opacity-40">
              {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />} Copy
            </button>
            <button onClick={handleShare} disabled={!translatedText} className="btn-secondary text-xs py-1.5 px-3 disabled:opacity-40">
              <Share2 className="h-3.5 w-3.5" /> Share
            </button>
            <button onClick={handleSave} disabled={!translatedText} className="btn-secondary text-xs py-1.5 px-3 disabled:opacity-40">
              Save
            </button>
          </div>
        </div>
      </div>

      {/* Matched terms */}
      {matchedTerms.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="card">
          <div className="flex items-center gap-2 mb-3">
            <BookOpen className="h-4 w-4 text-brand-cyan" />
            <span className="text-sm font-medium">Slang decoded ({matchedTerms.length} terms)</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {matchedTerms.map((term, i) => (
              <span
                key={`${term.slang}-${i}`}
                className="inline-flex flex-col px-3 py-2 rounded-xl bg-surface-800/60 border border-white/5"
              >
                <span className="text-xs font-medium text-brand-cyan">{term.slang}</span>
                <span className="text-xs text-zinc-500">{term.meaning}</span>
              </span>
            ))}
          </div>
        </motion.div>
      )}

      {/* Glossary */}
      {glossary.length > 0 && (
        <details className="card group">
          <summary className="text-sm font-medium cursor-pointer flex items-center gap-2 list-none">
            <BookOpen className="h-4 w-4 text-zinc-500 group-open:text-brand-cyan transition-colors" />
            Slang glossary ({glossary.length}+ terms)
          </summary>
          <div className="mt-4 grid sm:grid-cols-2 lg:grid-cols-3 gap-2 max-h-48 overflow-y-auto">
            {glossary.map((item) => (
              <button
                key={item.slang}
                onClick={() => setSourceText(`What does "${item.slang}" mean?`)}
                className="text-left px-3 py-2 rounded-lg hover:bg-white/5 transition-colors"
              >
                <span className="text-xs font-medium text-brand-cyan">{item.slang}</span>
                <span className="block text-xs text-zinc-500 truncate">{item.meaning}</span>
              </button>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
