/**
 * SearchableLanguageSelector.jsx
 * A polished, searchable language dropdown with flag emoji + native script.
 * Replaces the basic <select> with a custom combobox for better UX.
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ChevronDown, Check } from 'lucide-react';
import { getFlag } from '../../utils/constants';

export default function SearchableLanguageSelector({
  languages = [],
  value,
  onChange,
  label,
  showAuto = true,
  placeholder = 'Search language…',
}) {
  const [open,   setOpen]   = useState(false);
  const [query,  setQuery]  = useState('');
  const containerRef        = useRef(null);
  const searchRef           = useRef(null);
  const listRef             = useRef(null);

  const filtered = (showAuto ? languages : languages.filter((l) => l.code !== 'auto'))
    .filter((l) => {
      if (!query.trim()) return true;
      const q = query.toLowerCase();
      return (
        l.name.toLowerCase().includes(q) ||
        (l.native || '').toLowerCase().includes(q) ||
        l.code.toLowerCase().includes(q)
      );
    });

  const selected = languages.find((l) => l.code === value);

  // Close on outside click
  useEffect(() => {
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
        setQuery('');
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Focus search when opened
  useEffect(() => {
    if (open) {
      setTimeout(() => searchRef.current?.focus(), 50);
      // Scroll selected item into view
      setTimeout(() => {
        const el = listRef.current?.querySelector('[data-selected="true"]');
        el?.scrollIntoView({ block: 'nearest' });
      }, 80);
    }
  }, [open]);

  const handleSelect = useCallback((code) => {
    onChange(code);
    setOpen(false);
    setQuery('');
  }, [onChange]);

  // Keyboard navigation
  const handleKeyDown = (e) => {
    if (e.key === 'Escape') { setOpen(false); setQuery(''); }
    if (e.key === 'Enter' && filtered.length > 0) handleSelect(filtered[0].code);
  };

  return (
    <div ref={containerRef} className="flex flex-col gap-1.5 relative">
      {label && (
        <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider">
          {label}
        </label>
      )}

      {/* Trigger button */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="input-field flex items-center justify-between gap-2 text-sm cursor-pointer text-left"
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span className="flex items-center gap-2 min-w-0">
          <span className="text-base leading-none shrink-0">
            {selected ? getFlag(selected.code) : '🌐'}
          </span>
          <span className="truncate text-zinc-100">
            {selected ? selected.name : 'Select language'}
          </span>
        </span>
        <ChevronDown
          className={`h-4 w-4 text-zinc-500 shrink-0 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Dropdown */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full left-0 right-0 mt-1.5 z-50 rounded-xl border border-white/15 shadow-glass overflow-hidden bg-surface-950"
            style={{ maxHeight: '320px' }}
          >
            {/* Search input */}
            <div className="p-2 border-b border-white/8">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-zinc-500 pointer-events-none" />
                <input
                  ref={searchRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={placeholder}
                  className="w-full pl-8 pr-3 py-2 text-sm bg-white/5 rounded-lg border border-white/10
                             text-zinc-100 placeholder:text-zinc-600
                             focus:outline-none focus:ring-1 focus:ring-brand-indigo/50"
                />
              </div>
            </div>

            {/* Options list */}
            <div ref={listRef} className="overflow-y-auto" style={{ maxHeight: '256px' }}>
              {filtered.length === 0 ? (
                <p className="text-center text-sm text-zinc-500 py-6">No languages found</p>
              ) : (
                filtered.map((lang) => {
                  const isSelected = lang.code === value;
                  return (
                    <button
                      key={lang.code}
                      type="button"
                      data-selected={isSelected}
                      onClick={() => handleSelect(lang.code)}
                      className={`w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-left transition-colors ${
                        isSelected
                          ? 'bg-brand-indigo/20 text-brand-cyan'
                          : 'text-zinc-300 hover:bg-white/8 hover:text-zinc-100'
                      }`}
                    >
                      <span className="text-base leading-none shrink-0">{getFlag(lang.code)}</span>
                      <span className="flex-1 truncate">{lang.name}</span>
                      {isSelected && <Check className="h-3.5 w-3.5 shrink-0 text-brand-cyan" />}
                    </button>
                  );
                })
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
