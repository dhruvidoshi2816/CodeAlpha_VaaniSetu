import { Link } from 'react-router-dom';
import { Languages, Github, Twitter, Mail } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-white/5 mt-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
          <div className="md:col-span-2">
            <Link to="/" className="flex items-center gap-2 mb-4">
              <Languages className="h-6 w-6 text-brand-cyan" />
              <span className="font-display font-semibold text-xl">VaaniSetu</span>
            </Link>
            <p className="text-zinc-500 text-sm max-w-sm leading-relaxed">
              Your smart multilingual companion. Translate conversations, documents, images,
              and modern slang in seconds.
            </p>
          </div>

          <div>
            <h4 className="font-medium text-sm mb-4">Product</h4>
            <ul className="space-y-2 text-sm text-zinc-500">
              <li><Link to="/translate" className="hover:text-zinc-300 transition-colors">Translate</Link></li>
              <li><Link to="/translate?tab=voice" className="hover:text-zinc-300 transition-colors">Voice Mode</Link></li>
              <li><Link to="/translate?tab=slang" className="hover:text-zinc-300 transition-colors">Slang Bridge</Link></li>
              <li><Link to="/translate?tab=ocr" className="hover:text-zinc-300 transition-colors">OCR</Link></li>
              <li><Link to="/history" className="hover:text-zinc-300 transition-colors">History</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-medium text-sm mb-4">Company</h4>
            <ul className="space-y-2 text-sm text-zinc-500">
              <li><Link to="/about" className="hover:text-zinc-300 transition-colors">About</Link></li>
              <li><a href="#" className="hover:text-zinc-300 transition-colors">Privacy</a></li>
              <li><a href="#" className="hover:text-zinc-300 transition-colors">Terms</a></li>
            </ul>
          </div>
        </div>

        <div className="mt-10 pt-8 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-zinc-600">© VaaniSetu • Bridging languages, generations, and ideas.</p>
          <div className="flex items-center gap-4">
            <a href="#" className="text-zinc-500 hover:text-zinc-300 transition-colors"><Github className="h-4 w-4" /></a>
            <a href="#" className="text-zinc-500 hover:text-zinc-300 transition-colors"><Twitter className="h-4 w-4" /></a>
            <a href="#" className="text-zinc-500 hover:text-zinc-300 transition-colors"><Mail className="h-4 w-4" /></a>
          </div>
        </div>
      </div>
    </footer>
  );
}
