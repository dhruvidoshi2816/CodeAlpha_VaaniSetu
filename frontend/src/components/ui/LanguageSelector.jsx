/**
 * LanguageSelector.jsx — Language dropdown with flag emoji and native script.
 *
 * Improvements:
 * - Shows native script in option labels (e.g. "Hindi (हिन्दी)")
 * - Searchable via native <select> (browser handles keyboard search)
 * - Accessible: proper label association, aria attributes
 * - Exports SwapButton, ConfidenceBadge, LoadingDots
 */

import { motion } from 'framer-motion';
import { getFlag } from '../../utils/constants';

export default function LanguageSelector({
  languages,
  value,
  onChange,
  label,
  showAuto = true,
  id,
}) {
  const filtered = showAuto
    ? languages
    : languages.filter((l) => l.code !== 'auto');

  const inputId = id || `lang-select-${label?.toLowerCase().replace(/\s+/g, '-') || 'default'}`;

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label
          htmlFor={inputId}
          className="text-xs font-medium text-zinc-500 uppercase tracking-wider"
        >
          {label}
        </label>
      )}
      <div className="relative">
        <select
          id={inputId}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="input-field appearance-none pr-10 py-2.5 text-sm cursor-pointer w-full"
          aria-label={label || 'Select language'}
        >
          {filtered.map((lang) => (
            <option key={lang.code} value={lang.code} className="bg-surface-800">
              {getFlag(lang.code)} {lang.name}
            </option>
          ))}
        </select>
        <span
          className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-500"
          aria-hidden="true"
        >
          ▾
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SwapButton
// ---------------------------------------------------------------------------
export function SwapButton({ onClick, disabled }) {
  return (
    <motion.button
      whileHover={{ scale: disabled ? 1 : 1.1, rotate: disabled ? 0 : 180 }}
      whileTap={{ scale: 0.95 }}
      transition={{ type: 'spring', stiffness: 300 }}
      onClick={onClick}
      disabled={disabled}
      className="p-2.5 rounded-xl glass hover:bg-brand-indigo/20 hover:ring-1 hover:ring-brand-indigo/30 transition-all shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
      aria-label="Swap languages"
      title="Swap languages"
    >
      ⇄
    </motion.button>
  );
}

// ---------------------------------------------------------------------------
// ConfidenceBadge
// ---------------------------------------------------------------------------
export function ConfidenceBadge({ confidence }) {
  if (confidence == null) return null;
  const pct   = Math.round(confidence * 100);
  const color =
    confidence >= 0.9  ? 'text-emerald-400 bg-emerald-400/10' :
    confidence >= 0.75 ? 'text-amber-400 bg-amber-400/10'     :
                         'text-orange-400 bg-orange-400/10';

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${color}`}
      title={`Translation confidence: ${pct}%`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />
      {pct}% confidence
    </span>
  );
}

// ---------------------------------------------------------------------------
// LoadingDots
// ---------------------------------------------------------------------------
export function LoadingDots() {
  return (
    <div className="flex items-center gap-1" aria-label="Loading" role="status">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-brand-cyan"
          animate={{ opacity: [0.3, 1, 0.3] }}
          transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
        />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// DetectedLanguageBadge — shows detected language with native script
// ---------------------------------------------------------------------------
export function DetectedLanguageBadge({ langInfo }) {
  if (!langInfo?.display) return null;
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium text-sky-400 bg-sky-400/10">
      <span aria-hidden="true">🔍</span>
      Detected: {langInfo.display}
    </span>
  );
}
