import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Star, Trash2, Copy, Filter, X } from 'lucide-react';
import toast from 'react-hot-toast';
import Navbar from '../components/layout/Navbar';
import { historyApi } from '../api/client';
import { formatDate, getFlag } from '../utils/constants';

export default function HistoryPage() {
  const [history,      setHistory]      = useState([]);
  const [search,       setSearch]       = useState('');
  const [favoritesOnly,setFavoritesOnly]= useState(false);
  const [loading,      setLoading]      = useState(true);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const { data } = await historyApi.getAll({ search, favorite: favoritesOnly });
      setHistory(data.history);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(fetchHistory, 300);
    return () => clearTimeout(timer);
  }, [search, favoritesOnly]);

  const toggleFavorite = async (id) => {
    try {
      const { data } = await historyApi.toggleFavorite(id);
      setHistory((prev) =>
        prev.map((item) =>
          item.id === id ? { ...item, is_favorite: data.is_favorite ? 1 : 0 } : item
        )
      );
    } catch (err) { toast.error(err.message); }
  };

  const deleteItem = async (id) => {
    try {
      await historyApi.delete(id);
      setHistory((prev) => prev.filter((item) => item.id !== id));
      toast.success('Deleted');
    } catch (err) { toast.error(err.message); }
  };

  const clearAll = async () => {
    if (!window.confirm('Clear all translation history? This cannot be undone.')) return;
    try {
      await historyApi.clear();
      setHistory([]);
      toast.success('History cleared');
    } catch (err) { toast.error(err.message); }
  };

  const copyText = async (text) => {
    await navigator.clipboard.writeText(text);
    toast.success('Copied');
  };

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 pt-28 pb-16">

        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="font-display text-3xl font-bold mb-2">Translation history</h1>
            <p className="text-zinc-500 text-sm">Search, favorite, and revisit your past translations.</p>
          </div>
          {history.length > 0 && (
            <button
              onClick={clearAll}
              className="btn-secondary text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 shrink-0"
            >
              <X className="h-4 w-4" /> Clear all
            </button>
          )}
        </div>

        {/* Search + filter */}
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search translations…"
              className="input-field pl-11"
            />
          </div>
          <button
            onClick={() => setFavoritesOnly(!favoritesOnly)}
            className={`btn-secondary shrink-0 ${favoritesOnly ? 'ring-1 ring-amber-400/40 text-amber-400' : ''}`}
          >
            <Filter className="h-4 w-4" />
            {favoritesOnly ? 'Favorites' : 'All'}
          </button>
        </div>

        {/* Content */}
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="card h-28 animate-pulse bg-surface-800/50" />
            ))}
          </div>
        ) : history.length === 0 ? (
          <div className="card text-center py-16">
            <p className="text-zinc-500">No translations found.</p>
            <p className="text-sm text-zinc-600 mt-1">Start translating to build your history.</p>
          </div>
        ) : (
          <div className="space-y-3">
            <AnimatePresence>
              {history.map((item) => (
                <motion.div
                  key={item.id}
                  layout
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  className="card group"
                >
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex items-center gap-2 text-xs text-zinc-500 flex-wrap">
                      <span>{getFlag(item.source_lang)} {item.source_lang}</span>
                      <span>→</span>
                      <span>{getFlag(item.target_lang)} {item.target_lang}</span>
                      <span className="text-zinc-700">·</span>
                      <span>{formatDate(item.created_at)}</span>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                      <button
                        onClick={() => toggleFavorite(item.id)}
                        className={`p-2 rounded-lg hover:bg-white/10 transition-colors ${item.is_favorite ? 'text-amber-400' : 'text-zinc-500'}`}
                      >
                        <Star className={`h-4 w-4 ${item.is_favorite ? 'fill-current' : ''}`} />
                      </button>
                      <button
                        onClick={() => copyText(item.translated_text)}
                        className="p-2 rounded-lg hover:bg-white/10 text-zinc-500 transition-colors"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => deleteItem(item.id)}
                        className="p-2 rounded-lg hover:bg-red-500/10 text-zinc-500 hover:text-red-400 transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  <p className="text-sm text-zinc-400 mb-2 line-clamp-2">{item.original_text}</p>
                  <p className="text-sm text-zinc-100 line-clamp-2">{item.translated_text}</p>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  );
}
