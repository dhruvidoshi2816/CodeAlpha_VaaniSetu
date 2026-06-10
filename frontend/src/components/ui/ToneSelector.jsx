import { motion } from 'framer-motion';
import { TONE_MODES } from '../../utils/constants';

export default function ToneSelector({ value, onChange }) {
  return (
    <div className="flex flex-wrap gap-2">
      {TONE_MODES.map((tone) => (
        <motion.button
          key={tone.id}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onChange(tone.id)}
          className={`px-3.5 py-2 rounded-xl text-xs font-medium transition-all ${
            value === tone.id
              ? 'bg-brand-indigo/25 text-brand-cyan ring-1 ring-brand-indigo/40'
              : 'glass hover:bg-white/10 text-zinc-400'
          }`}
          title={tone.desc}
        >
          {tone.label}
        </motion.button>
      ))}
    </div>
  );
}
