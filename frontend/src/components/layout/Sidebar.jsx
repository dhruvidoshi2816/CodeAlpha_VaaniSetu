import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Languages, History, FileText, Mic, Image, Sparkles, ChevronLeft, ChevronRight, Users,
} from 'lucide-react';
import { useState } from 'react';

const sidebarItems = [
  { to: '/translate', label: 'Text', icon: Languages, tab: 'text' },
  { to: '/translate?tab=slang', label: 'Slang Bridge', icon: Users, tab: 'slang' },
  { to: '/translate?tab=voice', label: 'Voice', icon: Mic, tab: 'voice' },
  { to: '/translate?tab=ocr', label: 'OCR', icon: Image, tab: 'ocr' },
  { to: '/translate?tab=document', label: 'Documents', icon: FileText, tab: 'document' },
  { to: '/history', label: 'History', icon: History, tab: null },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const activeTab = params.get('tab') || 'text';
  const isTranslatePage = location.pathname === '/translate';

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 240 }}
      className="hidden lg:flex flex-col h-[calc(100vh-7rem)] sticky top-28 rounded-2xl glass p-3"
    >
      <div className="flex items-center justify-between mb-4 px-2">
        {!collapsed && (
          <span className="text-xs font-medium uppercase tracking-wider text-zinc-500">
            Workspace
          </span>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1.5 rounded-lg hover:bg-white/10 ml-auto"
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      <nav className="flex-1 space-y-1">
        {sidebarItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            item.tab === null
              ? location.pathname === item.to
              : isTranslatePage && activeTab === item.tab;

          return (
            <Link
              key={item.label}
              to={item.to}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? 'bg-brand-indigo/20 text-brand-cyan ring-1 ring-brand-indigo/30'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {!collapsed && (
        <div className="mt-auto p-3 rounded-xl bg-gradient-to-br from-brand-indigo/10 to-brand-cyan/5 border border-brand-indigo/20">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="h-4 w-4 text-brand-cyan" />
            <span className="text-xs font-medium">Pro tip</span>
          </div>
          <p className="text-xs text-zinc-500 leading-relaxed">
            Press <kbd className="px-1.5 py-0.5 rounded bg-white/10 text-zinc-300">Ctrl+Enter</kbd>{' '}
            to translate instantly.
          </p>
        </div>
      )}
    </motion.aside>
  );
}
