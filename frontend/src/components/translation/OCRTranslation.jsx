import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, ImageIcon, Scan, X, Copy, Check } from 'lucide-react';
import toast from 'react-hot-toast';
import SearchableLanguageSelector from '../ui/SearchableLanguageSelector';
import { ConfidenceBadge, LoadingDots } from '../ui/LanguageSelector';
import { ocrApi } from '../../api/client';
import { useLanguages } from '../../hooks/useTranslation';

export default function OCRTranslation() {
  const { languages } = useLanguages();
  const [targetLang,     setTargetLang]     = useState('en');
  const [sourceLang,     setSourceLang]     = useState('auto');
  const [preview,        setPreview]        = useState(null);
  const [file,           setFile]           = useState(null);
  const [extractedText,  setExtractedText]  = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [loading,        setLoading]        = useState(false);
  const [ocrConfidence,  setOcrConfidence]  = useState(null);
  const [transConfidence,setTransConfidence]= useState(null);
  const [isDragging,     setIsDragging]     = useState(false);
  const [copiedOcr,      setCopiedOcr]      = useState(false);
  const [copiedTrans,    setCopiedTrans]     = useState(false);
  const inputRef = useRef(null);

  const handleFile = (f) => {
    if (!f) return;
    if (!f.type.startsWith('image/')) { toast.error('Please upload an image file'); return; }
    if (f.size > 10 * 1024 * 1024) { toast.error('Image must be under 10 MB'); return; }
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setExtractedText(''); setTranslatedText('');
    setOcrConfidence(null); setTransConfidence(null);
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
      formData.append('image', file);
      formData.append('target_lang', targetLang);
      formData.append('source_lang', sourceLang);
      const { data } = await ocrApi.translateImage(formData);
      setExtractedText(data.extracted_text);
      setTranslatedText(data.translated_text);
      setOcrConfidence(data.ocr_confidence);
      setTransConfidence(data.translation_confidence);
      toast.success('Image translated');
    } catch (err) {
      toast.error(err.message);
    } finally { setLoading(false); }
  };

  const copyText = async (text, setCopied) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const clear = () => {
    setFile(null); setPreview(null);
    setExtractedText(''); setTranslatedText('');
    setOcrConfidence(null); setTransConfidence(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div className="space-y-5">
      <div className="grid sm:grid-cols-2 gap-4">
        <SearchableLanguageSelector languages={languages} value={sourceLang} onChange={setSourceLang} label="Image language" />
        <SearchableLanguageSelector languages={languages} value={targetLang} onChange={setTargetLang} label="Translate to" showAuto={false} />
      </div>

      <AnimatePresence mode="wait">
        {!preview ? (
          <motion.div
            key="dropzone"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onClick={() => inputRef.current?.click()}
            className={`card border-dashed border-2 cursor-pointer flex flex-col items-center justify-center py-16 transition-all ${
              isDragging
                ? 'border-brand-indigo/70 bg-brand-indigo/5 scale-[1.01]'
                : 'border-white/10 hover:border-brand-indigo/40'
            }`}
          >
            <motion.div
              animate={{ y: isDragging ? -8 : [0, -6, 0] }}
              transition={isDragging ? { duration: 0.2 } : { duration: 3, repeat: Infinity }}
              className={`p-4 rounded-2xl mb-4 transition-colors ${
                isDragging ? 'bg-brand-indigo/25' : 'bg-brand-indigo/10 group-hover:bg-brand-indigo/20'
              }`}
            >
              <Upload className="h-8 w-8 text-brand-cyan" />
            </motion.div>
            <p className="font-medium mb-1">
              {isDragging ? 'Drop to upload' : 'Drop an image here'}
            </p>
            <p className="text-sm text-zinc-500">PNG, JPG, WEBP up to 10 MB</p>
            <p className="text-xs text-zinc-600 mt-2">or click to browse</p>
            <input ref={inputRef} type="file" accept="image/*" className="hidden"
              onChange={(e) => handleFile(e.target.files[0])} />
          </motion.div>
        ) : (
          <motion.div
            key="results"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="grid lg:grid-cols-2 gap-4"
          >
            {/* Image preview + action */}
            <div className="card relative">
              <button onClick={clear}
                className="absolute top-4 right-4 p-1.5 rounded-lg hover:bg-white/10 z-10 transition-colors">
                <X className="h-4 w-4" />
              </button>
              <img src={preview} alt="Upload preview"
                className="rounded-xl w-full max-h-64 object-contain bg-surface-900" />
              <button onClick={handleTranslate} disabled={loading} className="btn-primary w-full mt-4">
                {loading
                  ? <span className="flex items-center gap-2"><Scan className="h-4 w-4 animate-pulse" /> Scanning…</span>
                  : <span className="flex items-center gap-2"><ImageIcon className="h-4 w-4" /> Extract &amp; Translate</span>
                }
              </button>
            </div>

            {/* Results */}
            <div className="space-y-4">
              <div className="card">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-zinc-400">Extracted Text</span>
                  <div className="flex items-center gap-2">
                    <ConfidenceBadge confidence={ocrConfidence} />
                    {extractedText && (
                      <button onClick={() => copyText(extractedText, setCopiedOcr)}
                        className="p-1.5 rounded-lg hover:bg-white/10 text-zinc-500 transition-colors">
                        {copiedOcr ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                      </button>
                    )}
                  </div>
                </div>
                {loading
                  ? <div className="space-y-2 min-h-[80px]"><LoadingDots /></div>
                  : <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap min-h-[80px]">
                      {extractedText || <span className="text-zinc-600">Text from image will appear here…</span>}
                    </p>
                }
              </div>

              <div className="card">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-zinc-400">Translation</span>
                  <div className="flex items-center gap-2">
                    <ConfidenceBadge confidence={transConfidence} />
                    {translatedText && (
                      <button onClick={() => copyText(translatedText, setCopiedTrans)}
                        className="p-1.5 rounded-lg hover:bg-white/10 text-zinc-500 transition-colors">
                        {copiedTrans ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                      </button>
                    )}
                  </div>
                </div>
                <p className="text-sm text-zinc-100 leading-relaxed whitespace-pre-wrap min-h-[80px]">
                  {translatedText || <span className="text-zinc-600">Translation will appear here…</span>}
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
