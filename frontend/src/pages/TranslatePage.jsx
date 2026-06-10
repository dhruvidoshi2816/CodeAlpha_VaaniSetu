import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Languages, Users, Mic, Image, FileText } from 'lucide-react';
import Navbar from '../components/layout/Navbar';
import Sidebar from '../components/layout/Sidebar';
import TextTranslation from '../components/translation/TextTranslation';
import VoiceTranslation from '../components/translation/VoiceTranslation';
import OCRTranslation from '../components/translation/OCRTranslation';
import DocumentTranslation from '../components/translation/DocumentTranslation';
import SlangBridge from '../components/translation/SlangBridge';

const tabs = [
  { id: 'text',     label: 'Text',         icon: Languages },
  { id: 'slang',    label: 'Slang',        icon: Users },
  { id: 'voice',    label: 'Voice',        icon: Mic },
  { id: 'ocr',      label: 'OCR',          icon: Image },
  { id: 'document', label: 'Docs',         icon: FileText },
];

const tabComponents = {
  text:     TextTranslation,
  slang:    SlangBridge,
  voice:    VoiceTranslation,
  ocr:      OCRTranslation,
  document: DocumentTranslation,
};

export default function TranslatePage() {
  const [params, setParams] = useSearchParams();
  const activeTab = params.get('tab') || 'text';
  const ActiveComponent = tabComponents[activeTab] || TextTranslation;
  const setTab = (id) => setParams({ tab: id });

  return (
    <div className="min-h-screen relative">
      <div className="glow-orb w-72 h-72 bg-brand-indigo top-20 -right-36 opacity-15" />
      <Navbar />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-28 pb-16">
        <div className="mb-8">
          <h1 className="font-display text-3xl font-bold mb-1">Translation workspace</h1>
          <p className="text-zinc-500 text-sm">Text · Voice · OCR · Documents · Slang — all in one place.</p>
        </div>

        <div className="flex gap-6">
          <Sidebar />

          <div className="flex-1 min-w-0">
            {/* Mobile tab bar */}
            <div className="lg:hidden flex gap-1 p-1 rounded-xl glass mb-5 overflow-x-auto">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const active = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setTab(tab.id)}
                    className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                      active ? 'bg-brand-indigo/25 text-brand-cyan' : 'text-zinc-500 hover:text-zinc-300'
                    }`}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    {tab.label}
                  </button>
                );
              })}
            </div>

            <div className="card min-h-[500px]">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.18 }}
                >
                  <ActiveComponent />
                </motion.div>
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
