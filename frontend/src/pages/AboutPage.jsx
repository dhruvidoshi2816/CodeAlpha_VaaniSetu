import { motion } from 'framer-motion';
import {
  Languages, Mic, Image, FileText, History, Wand2, Sparkles, Users,
  Server, Palette, Code2,
} from 'lucide-react';
import Navbar from '../components/layout/Navbar';
import Footer from '../components/layout/Footer';

const missionPoints = [
  'Break down language barriers for everyday communication',
  'Make translation fast, accurate, and accessible to everyone',
  'Support multiple input modes — text, voice, images, and files',
  'Bridge the generation gap with Gen Z slang translation (200+ terms)',
  'Preserve context with tone-aware translations',
];

const featureList = [
  { icon: Languages, title: 'Text Translation', desc: 'Real-time translation with 100+ languages, tone modes, and native script display.' },
  { icon: Users, title: 'Gen-Z Slang Interpreter', desc: 'Slang ↔ plain English. 200+ terms including Hinglish, gaming, anime, and UK/AU slang.' },
  { icon: Mic, title: 'Voice Translation', desc: 'Speech-to-text input and text-to-speech playback.' },
  { icon: Image, title: 'OCR Translation', desc: 'Extract and translate text from uploaded images.' },
  { icon: FileText, title: 'Document Translation', desc: 'Process TXT, PDF, and DOCX files.' },
  { icon: History, title: 'History Dashboard', desc: 'Search, favorite, and manage past translations.' },
  { icon: Wand2, title: 'Smart Utilities', desc: 'Grammar correction and summarize-then-translate.' },
];

const techStack = [
  { category: 'Frontend', items: ['React.js + Vite', 'Tailwind CSS', 'Framer Motion', 'React Router', 'Axios'] },
  { category: 'Backend', items: ['Python Flask', 'Flask-CORS', 'SQLite', 'deep-translator', 'Provider fallback (Google → MyMemory)'] },
  { category: 'Features', items: ['Tesseract OCR', 'Web Speech API', 'Gen-Z slang engine (200+ terms)', 'OpenAI tone rewriting (optional)'] },
];

export default function AboutPage() {
  return (
    <div className="min-h-screen">
      <Navbar />

      <main className="pt-28 pb-20">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-16"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full glass text-xs text-zinc-400 mb-6">
              <Sparkles className="h-3.5 w-3.5 text-brand-cyan" />
              About VaaniSetu
            </div>
            <h1 className="font-display text-4xl sm:text-5xl font-bold mb-6">
              Language shouldn't be a barrier
            </h1>
            <p className="text-lg text-zinc-500 leading-relaxed">
              VaaniSetu is a multilingual translation platform designed for real-world use — whether you're
              closing a business deal, traveling abroad, or studying a new language. We built it to feel
              like a product you'd actually want to use every day.
            </p>
          </motion.div>

          <section className="mb-16">
            <h2 className="font-display text-2xl font-bold mb-6 flex items-center gap-2">
              <Palette className="h-5 w-5 text-brand-cyan" /> Our mission
            </h2>
            <ul className="space-y-3">
              {missionPoints.map((point, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-start gap-3 text-zinc-400"
                >
                  <span className="mt-2 h-1.5 w-1.5 rounded-full bg-brand-indigo shrink-0" />
                  {point}
                </motion.li>
              ))}
            </ul>
          </section>

          <section className="mb-16">
            <h2 className="font-display text-2xl font-bold mb-6">Features</h2>
            <div className="grid sm:grid-cols-2 gap-4">
              {featureList.map((f) => (
                <div key={f.title} className="card">
                  <f.icon className="h-5 w-5 text-brand-cyan mb-3" />
                  <h3 className="font-medium mb-1">{f.title}</h3>
                  <p className="text-sm text-zinc-500">{f.desc}</p>
                </div>
              ))}
            </div>
          </section>

          <section>
            <h2 className="font-display text-2xl font-bold mb-6 flex items-center gap-2">
              <Code2 className="h-5 w-5 text-brand-cyan" /> Technologies
            </h2>
            <div className="grid sm:grid-cols-3 gap-4">
              {techStack.map((group) => (
                <div key={group.category} className="card">
                  <div className="flex items-center gap-2 mb-4">
                    <Server className="h-4 w-4 text-zinc-500" />
                    <h3 className="font-medium text-sm">{group.category}</h3>
                  </div>
                  <ul className="space-y-2">
                    {group.items.map((item) => (
                      <li key={item} className="text-sm text-zinc-500">{item}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}
