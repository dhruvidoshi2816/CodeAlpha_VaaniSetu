// constants.js — VaaniSetu frontend utilities and static data

// ---------------------------------------------------------------------------
// Language flags (emoji) — extended to 100+ languages
// ---------------------------------------------------------------------------
export const LANGUAGE_FLAGS = {
  auto:    '🌐',
  // Indian
  hi:      '🇮🇳',
  gu:      '🇮🇳',
  mr:      '🇮🇳',
  bn:      '🇧🇩',
  pa:      '🇮🇳',
  ta:      '🇮🇳',
  te:      '🇮🇳',
  kn:      '🇮🇳',
  ml:      '🇮🇳',
  ur:      '🇵🇰',
  or:      '🇮🇳',
  as:      '🇮🇳',
  ne:      '🇳🇵',
  si:      '🇱🇰',
  sd:      '🇵🇰',
  ks:      '🇮🇳',
  sa:      '🇮🇳',
  mai:     '🇮🇳',
  bho:     '🇮🇳',
  doi:     '🇮🇳',
  kok:     '🇮🇳',
  mni:     '🇮🇳',
  sat:     '🇮🇳',
  // Global
  en:      '🇺🇸',
  es:      '🇪🇸',
  fr:      '🇫🇷',
  de:      '🇩🇪',
  it:      '🇮🇹',
  pt:      '🇵🇹',
  ru:      '🇷🇺',
  nl:      '🇳🇱',
  pl:      '🇵🇱',
  sv:      '🇸🇪',
  da:      '🇩🇰',
  fi:      '🇫🇮',
  no:      '🇳🇴',
  cs:      '🇨🇿',
  sk:      '🇸🇰',
  sl:      '🇸🇮',
  hr:      '🇭🇷',
  sr:      '🇷🇸',
  bs:      '🇧🇦',
  bg:      '🇧🇬',
  ro:      '🇷🇴',
  hu:      '🇭🇺',
  el:      '🇬🇷',
  uk:      '🇺🇦',
  lt:      '🇱🇹',
  lv:      '🇱🇻',
  et:      '🇪🇪',
  is:      '🇮🇸',
  ga:      '🇮🇪',
  cy:      '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
  eu:      '🇪🇸',
  ca:      '🇪🇸',
  gl:      '🇪🇸',
  sq:      '🇦🇱',
  mk:      '🇲🇰',
  hy:      '🇦🇲',
  ka:      '🇬🇪',
  az:      '🇦🇿',
  kk:      '🇰🇿',
  uz:      '🇺🇿',
  tk:      '🇹🇲',
  ky:      '🇰🇬',
  tg:      '🇹🇯',
  mn:      '🇲🇳',
  be:      '🇧🇾',
  mt:      '🇲🇹',
  af:      '🇿🇦',
  // Middle East
  ar:      '🇸🇦',
  he:      '🇮🇱',
  fa:      '🇮🇷',
  ps:      '🇦🇫',
  ku:      '🏳️',
  tr:      '🇹🇷',
  // East / SE Asia
  'zh-CN': '🇨🇳',
  'zh-TW': '🇹🇼',
  ja:      '🇯🇵',
  ko:      '🇰🇷',
  th:      '🇹🇭',
  vi:      '🇻🇳',
  id:      '🇮🇩',
  ms:      '🇲🇾',
  tl:      '🇵🇭',
  my:      '🇲🇲',
  km:      '🇰🇭',
  lo:      '🇱🇦',
  jv:      '🇮🇩',
  su:      '🇮🇩',
  ceb:     '🇵🇭',
  hmn:     '🏳️',
  // African
  sw:      '🇰🇪',
  am:      '🇪🇹',
  yo:      '🇳🇬',
  ig:      '🇳🇬',
  ha:      '🇳🇬',
  zu:      '🇿🇦',
  xh:      '🇿🇦',
  st:      '🇿🇦',
  sn:      '🇿🇼',
  so:      '🇸🇴',
  ny:      '🇲🇼',
  mg:      '🇲🇬',
  // Other
  ht:      '🇭🇹',
  la:      '🏛️',
  eo:      '🌍',
  yi:      '🏳️',
};

// ---------------------------------------------------------------------------
// Default language list — used as fallback when API is unreachable.
// Covers the most common languages so the app is usable offline.
// ---------------------------------------------------------------------------
export const DEFAULT_LANGUAGES = [
  { code: 'auto',   name: 'Auto Detect' },
  // Indian
  { code: 'hi',     name: 'Hindi (हिन्दी)' },
  { code: 'gu',     name: 'Gujarati (ગુજરાતી)' },
  { code: 'mr',     name: 'Marathi (मराठी)' },
  { code: 'bn',     name: 'Bengali (বাংলা)' },
  { code: 'pa',     name: 'Punjabi (ਪੰਜਾਬੀ)' },
  { code: 'ta',     name: 'Tamil (தமிழ்)' },
  { code: 'te',     name: 'Telugu (తెలుగు)' },
  { code: 'kn',     name: 'Kannada (ಕನ್ನಡ)' },
  { code: 'ml',     name: 'Malayalam (മലയാളം)' },
  { code: 'ur',     name: 'Urdu (اردو)' },
  { code: 'ne',     name: 'Nepali (नेपाली)' },
  // Global
  { code: 'en',     name: 'English' },
  { code: 'es',     name: 'Spanish (Español)' },
  { code: 'fr',     name: 'French (Français)' },
  { code: 'de',     name: 'German (Deutsch)' },
  { code: 'it',     name: 'Italian (Italiano)' },
  { code: 'pt',     name: 'Portuguese (Português)' },
  { code: 'ru',     name: 'Russian (Русский)' },
  { code: 'ar',     name: 'Arabic (العربية)' },
  { code: 'ja',     name: 'Japanese (日本語)' },
  { code: 'ko',     name: 'Korean (한국어)' },
  { code: 'zh-CN',  name: 'Chinese Simplified (中文简体)' },
  { code: 'zh-TW',  name: 'Chinese Traditional (中文繁體)' },
  { code: 'tr',     name: 'Turkish (Türkçe)' },
  { code: 'fa',     name: 'Persian (فارسی)' },
  { code: 'th',     name: 'Thai (ภาษาไทย)' },
  { code: 'vi',     name: 'Vietnamese (Tiếng Việt)' },
  { code: 'id',     name: 'Indonesian (Bahasa Indonesia)' },
  { code: 'ms',     name: 'Malay (Bahasa Melayu)' },
  { code: 'he',     name: 'Hebrew (עברית)' },
  { code: 'el',     name: 'Greek (Ελληνικά)' },
  { code: 'nl',     name: 'Dutch (Nederlands)' },
  { code: 'pl',     name: 'Polish (Polski)' },
  { code: 'uk',     name: 'Ukrainian (Українська)' },
  { code: 'sv',     name: 'Swedish (Svenska)' },
  { code: 'no',     name: 'Norwegian (Norsk)' },
  { code: 'da',     name: 'Danish (Dansk)' },
  { code: 'fi',     name: 'Finnish (Suomi)' },
  { code: 'sw',     name: 'Swahili (Kiswahili)' },
  { code: 'tl',     name: 'Filipino' },
  { code: 'ro',     name: 'Romanian (Română)' },
  { code: 'cs',     name: 'Czech (Čeština)' },
  { code: 'hu',     name: 'Hungarian (Magyar)' },
  { code: 'af',     name: 'Afrikaans' },
];

// ---------------------------------------------------------------------------
// Tone modes
// ---------------------------------------------------------------------------
export const TONE_MODES = [
  { id: 'formal',       label: 'Formal',       desc: 'Polished and respectful' },
  { id: 'casual',       label: 'Casual',       desc: 'Relaxed and natural' },
  { id: 'professional', label: 'Professional', desc: 'Clear business tone' },
  { id: 'friendly',     label: 'Friendly',     desc: 'Warm and approachable' },
];

// ---------------------------------------------------------------------------
// Slang modes
// ---------------------------------------------------------------------------
export const SLANG_MODES = [
  {
    id:           'genz_to_plain',
    label:        'Gen-Z → Plain English',
    desc:         'Decode slang for parents, teachers & older generations',
    source_label: 'What they said (Gen Z)',
    target_label: 'Plain English',
  },
  {
    id:           'plain_to_genz',
    label:        'Plain English → Gen Z',
    desc:         'Rephrase so teens & young adults relate',
    source_label: 'What you mean (Plain)',
    target_label: 'Gen Z friendly',
  },
];

export const SLANG_EXAMPLES = {
  genz_to_plain: [
    'That fit is bussin no cap, you ate fr',
    'Lowkey mid but the vibes were valid ngl',
    'He got mad rizz but sus energy tbh',
    'This song slaps different, goated fr fr',
    'Stop ghosting me bestie, spill the tea',
    'Touch grass, that take is giving delulu',
    'Bro is so cooked, he glazed the whole time',
    'She understood the assignment, no cap she ate',
  ],
  plain_to_genz: [
    'Please finish your homework before dinner',
    'That outfit looks really good on you, great job',
    'I honestly think that idea is suspicious',
    'The party was exciting and fun last night',
    'I cannot stop thinking about what happened',
    'You should go outside and take a break from your phone',
    'I am very focused on finishing this project',
    'That was an amazing performance, well done',
  ],
};

// ---------------------------------------------------------------------------
// Speech recognition language map — BCP-47 codes for Web Speech API
// Extended to cover all major languages in the registry
// ---------------------------------------------------------------------------
export const SPEECH_LANG_MAP = {
  en:      'en-US',
  es:      'es-ES',
  fr:      'fr-FR',
  de:      'de-DE',
  it:      'it-IT',
  pt:      'pt-PT',
  ru:      'ru-RU',
  ja:      'ja-JP',
  ko:      'ko-KR',
  'zh-CN': 'zh-CN',
  'zh-TW': 'zh-TW',
  ar:      'ar-SA',
  hi:      'hi-IN',
  bn:      'bn-IN',
  gu:      'gu-IN',
  mr:      'mr-IN',
  pa:      'pa-IN',
  ta:      'ta-IN',
  te:      'te-IN',
  kn:      'kn-IN',
  ml:      'ml-IN',
  ur:      'ur-PK',
  ne:      'ne-NP',
  si:      'si-LK',
  tr:      'tr-TR',
  nl:      'nl-NL',
  pl:      'pl-PL',
  sv:      'sv-SE',
  da:      'da-DK',
  fi:      'fi-FI',
  no:      'nb-NO',
  cs:      'cs-CZ',
  el:      'el-GR',
  he:      'he-IL',
  th:      'th-TH',
  vi:      'vi-VN',
  id:      'id-ID',
  ms:      'ms-MY',
  tl:      'fil-PH',
  uk:      'uk-UA',
  ro:      'ro-RO',
  hu:      'hu-HU',
  bg:      'bg-BG',
  hr:      'hr-HR',
  sk:      'sk-SK',
  sl:      'sl-SI',
  sr:      'sr-RS',
  ca:      'ca-ES',
  eu:      'eu-ES',
  gl:      'gl-ES',
  af:      'af-ZA',
  sw:      'sw-KE',
  am:      'am-ET',
  fa:      'fa-IR',
  km:      'km-KH',
  lo:      'lo-LA',
  my:      'my-MM',
  ka:      'ka-GE',
  hy:      'hy-AM',
  az:      'az-AZ',
  kk:      'kk-KZ',
  uz:      'uz-UZ',
  mn:      'mn-MN',
  mt:      'mt-MT',
  is:      'is-IS',
  ga:      'ga-IE',
  cy:      'cy-GB',
};

// ---------------------------------------------------------------------------
// Utility functions
// ---------------------------------------------------------------------------

export function getFlag(code) {
  if (!code) return '🏳️';
  const key = code in LANGUAGE_FLAGS ? code : code.toLowerCase();
  if (key in LANGUAGE_FLAGS) return LANGUAGE_FLAGS[key];
  const lower = code.toLowerCase();
  const hit = Object.keys(LANGUAGE_FLAGS).find((k) => k.toLowerCase() === lower);
  return hit ? LANGUAGE_FLAGS[hit] : '🏳️';
}

export function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', {
    month:  'short',
    day:    'numeric',
    year:   'numeric',
    hour:   '2-digit',
    minute: '2-digit',
  });
}

export function downloadText(content, filename = 'translation.txt') {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function shareText(text, title = 'VaaniSetu Translation') {
  if (navigator.share) {
    try {
      await navigator.share({ title, text });
      return 'shared';
    } catch {
      // user cancelled — fall through to clipboard
    }
  }
  await navigator.clipboard.writeText(text);
  return 'copied';
}

export function getConfidenceColor(confidence) {
  if (confidence >= 0.9)  return 'text-emerald-400';
  if (confidence >= 0.75) return 'text-amber-400';
  return 'text-orange-400';
}

export function getConfidenceLabel(confidence) {
  if (confidence >= 0.9)  return 'High confidence';
  if (confidence >= 0.75) return 'Good confidence';
  return 'Moderate confidence';
}

/**
 * Get the speech recognition BCP-47 code for a language code.
 * Falls back to 'en-US' if not found.
 */
export function getSpeechLang(code) {
  return SPEECH_LANG_MAP[code] || 'en-US';
}
