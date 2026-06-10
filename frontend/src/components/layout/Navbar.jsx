import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, Sun, Moon, Languages } from 'lucide-react';
import { useState } from 'react';
import { useTheme } from '../../context/ThemeContext';

const navLinks = [
  { to: '/', label: 'Home' },
  { to: '/translate', label: 'Translate' },
  { to: '/history', label: 'History' },
  { to: '/about', label: 'About' },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const { toggleTheme, isDark } = useTheme();

  return (
    <header className="fixed top-0 inset-x-0 z-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <nav className="mt-4 flex items-center justify-between rounded-2xl glass px-5 py-3">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-indigo/20 ring-1 ring-brand-indigo/30 group-hover:ring-brand-indigo/60 transition-all">
              <Languages className="h-5 w-5 text-brand-cyan" />
            </div>
            <span className="font-display font-semibold text-lg tracking-tight">VaaniSetu</span>
          </Link>

          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  location.pathname === link.to
                    ? 'text-white bg-white/10'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={toggleTheme}
              className="p-2.5 rounded-xl hover:bg-white/10 transition-colors"
              aria-label="Toggle theme"
            >
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>

            <Link to="/translate" className="hidden sm:inline-flex btn-primary text-sm py-2 px-4">
              Start Translating
            </Link>

            <button
              className="md:hidden p-2.5 rounded-xl hover:bg-white/10"
              onClick={() => setOpen(!open)}
              aria-label="Menu"
            >
              {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </nav>

        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="md:hidden mt-2 rounded-2xl glass p-4 space-y-1"
            >
              {navLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={() => setOpen(false)}
                  className={`block px-4 py-3 rounded-xl text-sm font-medium ${
                    location.pathname === link.to ? 'bg-white/10' : 'hover:bg-white/5'
                  }`}
                >
                  {link.label}
                </Link>
              ))}
              <Link to="/translate" onClick={() => setOpen(false)} className="block btn-primary text-center mt-2">
                Start Translating
              </Link>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </header>
  );
}
