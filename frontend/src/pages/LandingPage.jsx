import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowRight, Mic, Image, Zap, Globe, Languages, FileText, Sparkles, Users, Brain,
} from 'lucide-react';
import Navbar from '../components/layout/Navbar';
import Footer from '../components/layout/Footer';

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5 },
};

const badges = [
  { icon: Globe, label: '100+ Languages' },
  { icon: Brain, label: 'Gen-Z Slang Interpreter' },
  { icon: Mic, label: 'Voice Translation' },
  { icon: Image, label: 'OCR Translation' },
  { icon: Zap, label: 'Real-Time Translation' },
];

const features = [
  {
    icon: Languages,
    title: 'Text that flows naturally',
    desc: 'Real-time translation with tone control — formal, casual, professional, or friendly. Swap languages in one click.',
  },
  {
    icon: Mic,
    title: 'Speak, don\'t type',
    desc: 'Voice input and text-to-speech output. Perfect for conversations on the go or language practice.',
  },
  {
    icon: Image,
    title: 'Images to words',
    desc: 'Upload a photo, extract text with OCR, and get an instant translation. Menus, signs, documents — all covered.',
  },
  {
    icon: FileText,
    title: 'Documents, handled',
    desc: 'Drop in TXT, PDF, or DOCX files. We extract, translate, and let you download the result.',
  },
  {
    icon: Users,
    title: 'Parents ↔ Gen Z bridge',
    desc: 'Decode "bussin no cap" for mom and dad, or rephrase plain English so your kids actually listen. 200+ slang terms built in.',
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen relative overflow-hidden">
      <div className="glow-orb w-96 h-96 bg-brand-indigo top-0 -left-48" />
      <div className="glow-orb w-80 h-80 bg-brand-cyan top-1/3 -right-32" />
      <div className="glow-orb w-64 h-64 bg-purple-600 bottom-0 left-1/3" />

      <Navbar />

      <main className="relative pt-32 pb-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-12 gap-12 items-center">
            <motion.div {...fadeUp} className="lg:col-span-7">
              

              <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.05] mb-4">
                <span className="gradient-text">VaaniSetu</span>
              </h1>

              <p className="text-xl sm:text-2xl text-zinc-300 font-accent font-medium mb-3">
                Your smart multilingual companion
              </p>

              <p className="text-zinc-500 text-lg max-w-lg leading-relaxed mb-8">
                A bridge between languages, ideas, and conversations—making communication simple for everyone.
              </p>

              <div className="flex flex-wrap gap-3 mb-10">
                <Link to="/translate" className="btn-primary text-base px-6 py-3">
                  Start Translating <ArrowRight className="h-4 w-4" />
                </Link>
                <Link to="/translate?tab=voice" className="btn-secondary text-base px-6 py-3">
                  <Mic className="h-4 w-4" /> Try Voice Mode
                </Link>
              </div>

              <div className="flex flex-wrap gap-3">
                {badges.map(({ icon: Icon, label }) => (
                  <span
                    key={label}
                    className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl glass text-sm text-zinc-400"
                  >
                    <Icon className="h-4 w-4 text-brand-cyan" />
                    {label}
                  </span>
                ))}
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="lg:col-span-5"
            >
              <div className="card relative">
                <div className="absolute -top-3 -right-3 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-medium ring-1 ring-emerald-500/30">
                  Live demo
                </div>

                <div className="space-y-3">
                  {/* Example 1: Romanized Gujarati */}
                  <div className="p-3.5 rounded-xl bg-surface-800/60">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2 text-xs text-zinc-500">
                        <span>⌨️ Typed in English</span>
                        <span>→</span>
                        <span>🇮🇳 Gujarati detected</span>
                      </div>
                      <span className="text-xs text-violet-400 bg-violet-400/10 px-2 py-0.5 rounded-full">Romanized</span>
                    </div>
                    <p className="text-sm text-zinc-400 font-mono">"kem cho"</p>
                    <motion.p
                      animate={{ opacity: [0.6, 1, 0.6] }}
                      transition={{ duration: 2.5, repeat: Infinity }}
                      className="text-sm text-zinc-100 mt-1"
                    >
                      How are you? <span className="text-zinc-500 text-xs ml-1">· Gujarati (ગુજરાતી)</span>
                    </motion.p>
                  </div>

                  {/* Example 2: English → Spanish */}
                  <div className="p-3.5 rounded-xl bg-brand-indigo/10 ring-1 ring-brand-indigo/20">
                    <div className="flex items-center gap-2 mb-2 text-xs text-zinc-500">
                      <span>🇺🇸 English</span><span>→</span><span>🇪🇸 Spanish</span>
                    </div>
                    <p className="text-sm text-zinc-300">Good morning! How can I help you?</p>
                    <motion.p
                      animate={{ opacity: [0.7, 1, 0.7] }}
                      transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
                      className="text-sm text-zinc-100 mt-1"
                    >
                      ¡Buenos días! ¿Cómo puedo ayudarte?
                    </motion.p>
                    <div className="mt-2 flex items-center gap-2">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                      <span className="text-xs text-emerald-400">97% confidence</span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>

          <section className="mt-32">
            <motion.div {...fadeUp} className="mb-12 max-w-xl">
              <h2 className="font-display text-3xl sm:text-4xl font-bold mb-4">
                Everything you need to communicate across borders
              </h2>
              <p className="text-zinc-500 leading-relaxed">
                One workspace for text, voice, images, and documents — with history, tone control, and smart utilities built in.
              </p>
            </motion.div>

            <div className="grid sm:grid-cols-2 gap-5">
              {features.map((f, i) => (
                <motion.div
                  key={f.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="card group hover:shadow-glow-sm"
                >
                  <div className="p-3 rounded-xl bg-brand-indigo/10 w-fit mb-4 group-hover:bg-brand-indigo/20 transition-colors">
                    <f.icon className="h-5 w-5 text-brand-cyan" />
                  </div>
                  <h3 className="font-display font-semibold text-lg mb-2">{f.title}</h3>
                  <p className="text-sm text-zinc-500 leading-relaxed">{f.desc}</p>
                </motion.div>
              ))}
            </div>
          </section>

          <section className="mt-32 grid lg:grid-cols-2 gap-12 items-center">
            <div className="order-2 lg:order-1 card py-10 flex flex-col items-center">
              <motion.div
                animate={{ scale: [1, 1.08, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="h-20 w-20 rounded-full bg-brand-indigo/20 ring-2 ring-brand-indigo/40 flex items-center justify-center mb-4"
              >
                <Mic className="h-8 w-8 text-brand-cyan" />
              </motion.div>
              <p className="text-zinc-400 text-sm">"Translate this to French"</p>
              <motion.p
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                className="mt-4 text-lg text-zinc-100"
              >
                Traduisez ceci en français
              </motion.p>
            </div>
            <div className="order-1 lg:order-2">
              <h2 className="font-display text-3xl font-bold mb-4">Voice translation that feels natural</h2>
              <p className="text-zinc-500 leading-relaxed mb-6">
                Speak in your language, hear the translation aloud. Animated listening UI keeps you in the flow — no awkward pauses.
              </p>
              <Link to="/translate?tab=voice" className="btn-secondary">
                Open Voice Mode <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </section>

          <section className="mt-32 grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="font-display text-3xl font-bold mb-4">Point, scan, understand</h2>
              <p className="text-zinc-500 leading-relaxed mb-6">
                Photograph menus, signs, or handwritten notes. OCR extracts the text and translates it instantly — with confidence scores so you know what to trust.
              </p>
              <Link to="/translate?tab=ocr" className="btn-secondary">
                Try OCR Translation <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="card p-0 overflow-hidden">
              <div className="bg-surface-800 p-6 border-b border-white/5">
                <div className="flex items-center gap-2 text-xs text-zinc-500 mb-3">
                  <Image className="h-4 w-4" /> Uploaded image
                </div>
                <div className="h-32 rounded-lg bg-gradient-to-br from-surface-700 to-surface-900 flex items-center justify-center text-zinc-600 text-sm">
                  [ Restaurant menu photo ]
                </div>
              </div>
              <div className="p-6 space-y-3">
                <p className="text-xs text-zinc-500">Extracted: ラーメン — ¥980</p>
                <p className="text-zinc-100">Ramen — ¥980</p>
              </div>
            </div>
          </section>

          <section className="mt-32 grid lg:grid-cols-2 gap-12 items-center">
            <div className="card p-0 overflow-hidden order-2 lg:order-1">
              <div className="p-6 border-b border-white/5 bg-pink-500/5">
                <div className="flex items-center gap-2 text-xs text-zinc-500 mb-4">
                  <Users className="h-4 w-4 text-brand-cyan" /> Gen Z → Plain English
                </div>
                <p className="text-sm text-zinc-400 mb-3">"That fit is bussin no cap, you ate fr"</p>
                <p className="text-zinc-100">That outfit is really good, honestly. You did an amazing job, for real.</p>
              </div>
              <div className="p-4 flex flex-wrap gap-2">
                {['bussin → really good', 'no cap → honestly', 'ate → did amazingly'].map((t) => (
                  <span key={t} className="px-2.5 py-1 rounded-lg bg-surface-800 text-xs text-zinc-500">{t}</span>
                ))}
              </div>
            </div>
            <div className="order-1 lg:order-2">
              <h2 className="font-display text-3xl font-bold mb-4">Bridge the generation gap</h2>
              <p className="text-zinc-500 leading-relaxed mb-6">
                Parents don't speak Gen Z. Kids don't speak "90s." VaaniSetu's Slang Bridge translates both ways — with a built-in glossary of 200+ terms including rizz, mid, delulu, touch grass, Hinglish, gaming slang, and more.
              </p>
              <Link to="/translate?tab=slang" className="btn-secondary">
                Open Slang Bridge <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </section>

          <motion.section
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mt-32 card text-center py-16 relative overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-brand-indigo/10 via-transparent to-brand-cyan/10" />
            <div className="relative">
              <h2 className="font-display text-3xl sm:text-4xl font-bold mb-4">
                Ready to break language barriers?
              </h2>
              <p className="text-zinc-500 mb-8 max-w-md mx-auto">
                Join thousands who translate smarter with VaaniSetu. Free to start, no account required.
              </p>
              <Link to="/translate" className="btn-primary text-base px-8 py-3">
                Get started free <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </motion.section>
        </div>
      </main>

      <Footer />
    </div>
  );
}
