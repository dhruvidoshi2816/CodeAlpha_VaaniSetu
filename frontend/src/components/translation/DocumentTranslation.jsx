import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileUp, FileText, Download, X, Copy, Check } from 'lucide-react';
import toast from 'react-hot-toast';
import SearchableLanguageSelector from '../ui/SearchableLanguageSelector';
import { ConfidenceBadge, LoadingDots } from '../ui/LanguageSelector';
import { documentApi } from '../../api/client';
import { useLanguages } from '../../hooks/useTranslation';
import { downloadText } from '../../utils/constants';

const ACCEPTED = '.txt,.pdf,.docx';
const ALLOWED_EXTS = ['txt', 'pdf', 'docx'];

const FILE_ICONS = { pdf: '📄', docx: '📝', txt: '📃' };

export default function DocumentTranslation() {
  const { languages } = useLanguages();
  const [targetLang,     setTargetLang]     = useState('en');
  const [sourceLang,     setSourceLang]     = useState('auto');
  const [file,           setFile]           = useState(null);
  const [originalText,   setOriginalText]   = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [loading,        setLoading]        = useState(false);
  const [confidence,     setConfidence]     = useState(null);
  const [isDragging,     setIsDragging]     = useState(false);
  const [copied,         setCopied]         = useState(false);
  const inputRef = useRef(null);

  const handleFile = (f) => {
    if (!f) return;
    const ext = f.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTS.includes(ext)) { toast.error('Supported: TXT, PDF, DOCX'); return; }
    if (f.size > 20 * 1024 * 1024) { toast.error('File must be under 20 MB'); return; }
    setFile(f); setOriginalText(''); setTranslatedText(''); setConfidence(null);
  };

  const handleDrop = (e) => {
    e.preventDefault(); setIsDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleTranslate = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('document', file);
      formData.append('target_lang', targetLang);
      formData.append('source_lang', sourceLang);
      formData.append('save_history', 'true');
      const { data } = await documentApi.translate(formData);
      setOriginalText(data.original_text);
      setTranslatedText(data.translated_text);
      setConfidence(data.confidence);
      toast.success(`${data.filename} translated`);
    } catch (err) {
      toast.error(err.message);
    } finally { setLoading(false); }
  };

  const ext = file?.name.split('.').pop()?.toLowerCase() || '';
  const fileIcon = FILE_ICONS[ext] || '📄';

  return (
    <div className="space-y-5">
      <div className="grid sm:grid-cols-2 gap-4">
        <SearchableLanguageSelector languages={languages} value={sourceLang} onChange={setSourceLang} label="Document language" />
        <SearchableLanguageSelector languages={languages} value={targetLang} onChange={setTargetLang} label="Translate to" showAuto={false} />
      </div>

      <AnimatePresence mode="wait">
        {!file ? (
          <motion.div
            key="dropzone"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onClick={() => inputRef.current?.click()}
            className={`card border-dashed border-2 cursor-pointer flex flex-col items-center py-14 transition-all ${
              isDragging
                ? 'border-brand-indigo/70 bg-brand-indigo/5 scale-[1.01]'
                : 'border-white/10 hover:border-brand-indigo/40'
            }`}
          >
            <motion.div
              animate={{ y: isDragging ? -8 : 0 }}
              className={`p-4 rounded-2xl mb-4 transition-colors ${isDragging ? 'bg-brand-indigo/25' : 'bg-brand-indigo/10'}`}
            >
              <FileUp className="h-8 w-8 text-brand-cyan" />
            </motion.div>
            <p className="font-medium mb-1">{isDragging ? 'Drop to upload' : 'Upload a document'}</p>
            <p className="text-sm text-zinc-500">TXT, PDF, or DOCX · up to 20 MB</p>
            <p className="text-xs text-zinc-600 mt-2">or click to browse</p>
            <input ref={inputRef} type="file" accept={ACCEPTED} className="hidden"
              onChange={(e) => handleFile(e.target.files[0])} />
          </motion.div>
        ) : (
          <motion.div
            key="file"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="space-y-4"
          >
            {/* File info bar */}
            <div className="card flex items-center justify-between gap-4">
              <div className="flex items-center gap-3 min-w-0">
                <div className="p-2.5 rounded-xl bg-brand-indigo/15 text-xl shrink-0">{fileIcon}</div>
                <div className="min-w-0">
                  <p className="font-medium text-sm truncate">{file.name}</p>
                  <p className="text-xs text-zinc-500">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button onClick={handleTranslate} disabled={loading} className="btn-primary text-sm">
                  {loading ? 'Processing…' : 'Translate'}
                </button>
                <button onClick={() => setFile(null)} className="p-2 rounded-lg hover:bg-white/10 transition-colors">
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Results */}
            {(originalText || loading) && (
              <div className="grid lg:grid-cols-2 gap-4">
                <div className="card max-h-80 overflow-y-auto">
                  <span className="text-sm font-medium text-zinc-400 block mb-3">Original</span>
                  {loading ? <LoadingDots /> : (
                    <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">{originalText}</p>
                  )}
                </div>
                <div className="card max-h-80 overflow-y-auto">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium text-zinc-400">Translated</span>
                    <ConfidenceBadge confidence={confidence} />
                  </div>
                  <p className="text-sm text-zinc-100 leading-relaxed whitespace-pre-wrap">{translatedText}</p>
                  {translatedText && (
                    <div className="flex gap-2 mt-4">
                      <button
                        onClick={() => downloadText(translatedText, `translated-${file.name.split('.')[0]}.txt`)}
                        className="btn-secondary text-xs py-1.5 px-3">
                        <Download className="h-3.5 w-3.5" /> Download
                      </button>
                      <button
                        onClick={async () => {
                          await navigator.clipboard.writeText(translatedText);
                          setCopied(true); setTimeout(() => setCopied(false), 2000);
                        }}
                        className="btn-secondary text-xs py-1.5 px-3">
                        {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                        Copy
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
