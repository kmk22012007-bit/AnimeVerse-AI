import React, { useState } from 'react'

/**
 * Maps known streaming providers to local public fallback SVG/PNG assets.
 * Used if remote CDN/Wikimedia URL fails to load or rate-limits.
 */
const LOCAL_LOGO_MAP = {
  'amazon mx player': '/logos/mx_player.svg',
  'mx player': '/logos/mx_player.svg',
  'vi movies and tv': '/logos/vi.svg',
  'vodafone idea': '/logos/vi.svg',
  'sony liv': '/logos/sony_liv.png',
  'netflix': '/logos/netflix.svg',
  'crunchyroll': '/logos/crunchyroll.png',
  'amazon prime video': '/logos/prime_video.png',
  'prime video': '/logos/prime_video.png',
  'jiohotstar': '/logos/hotstar.svg',
  'disney+ hotstar': '/logos/hotstar.svg',
  'disney plus hotstar': '/logos/hotstar.svg',
  'hotstar': '/logos/hotstar.svg',
  'disney+': '/logos/disney_plus.svg',
  'youtube': '/logos/youtube.svg',
  'muse asia': '/logos/youtube.svg',
  'ani-one asia': '/logos/youtube.svg',
  'tubi': '/logos/tubi.svg',
  'tubi tv': '/logos/tubi.svg',
  'max': '/logos/max.svg',
  'apple tv': '/logos/apple_tv.svg',
  'apple tv+': '/logos/apple_tv.svg',
  'apple tv store': '/logos/apple_tv.svg',
  'hulu': '/logos/hulu.svg',
}

/**
 * Returns brand-specific cyberpunk styling for fallback badge
 */
function getFallbackBrandStyle(name = '') {
  const n = name.toLowerCase()

  if (n.includes('mx player')) {
    return {
      initials: 'MX',
      bgClass: 'from-blue-600/30 to-cyan-500/20 text-cyan-300 border-cyan-400/40',
    }
  }
  if (n.includes('vi ') || n.includes('vodafone') || n.includes('idea')) {
    return {
      initials: 'Vi',
      bgClass: 'from-red-600/30 to-amber-500/20 text-amber-300 border-red-400/40',
    }
  }
  if (n.includes('sony')) {
    return {
      initials: 'SONY',
      bgClass: 'from-indigo-600/30 to-blue-500/20 text-blue-200 border-blue-400/40',
    }
  }
  if (n.includes('hotstar')) {
    return {
      initials: 'JH',
      bgClass: 'from-blue-800/40 to-cyan-600/20 text-cyan-200 border-cyan-400/30',
    }
  }
  if (n.includes('netflix')) {
    return {
      initials: 'NF',
      bgClass: 'from-red-900/40 to-red-600/20 text-red-400 border-red-500/40',
    }
  }
  if (n.includes('crunchyroll')) {
    return {
      initials: 'CR',
      bgClass: 'from-orange-800/40 to-amber-500/20 text-orange-300 border-orange-400/40',
    }
  }
  if (n.includes('prime')) {
    return {
      initials: 'PV',
      bgClass: 'from-sky-800/40 to-blue-600/20 text-sky-300 border-sky-400/40',
    }
  }
  if (n.includes('youtube') || n.includes('muse') || n.includes('ani-one')) {
    return {
      initials: 'YT',
      bgClass: 'from-red-900/40 to-red-600/20 text-red-300 border-red-500/40',
    }
  }
  if (n.includes('apple')) {
    return {
      initials: 'TV',
      bgClass: 'from-slate-800/40 to-slate-600/20 text-white border-slate-400/40',
    }
  }
  if (n.includes('disney')) {
    return {
      initials: 'D+',
      bgClass: 'from-indigo-900/40 to-blue-700/20 text-blue-200 border-blue-400/40',
    }
  }
  if (n.includes('tubi')) {
    return {
      initials: 'TUBI',
      bgClass: 'from-amber-700/30 to-orange-500/20 text-amber-300 border-amber-400/40',
    }
  }
  if (n.includes('hulu')) {
    return {
      initials: 'HULU',
      bgClass: 'from-emerald-800/40 to-green-600/20 text-emerald-300 border-emerald-400/40',
    }
  }

  // Generic fallback: first 2-3 clean uppercase initials
  const cleanWords = name.replace(/[^a-zA-Z0-9 ]/g, '').trim().split(/\s+/)
  let initials = cleanWords.slice(0, 2).map(w => w[0]?.toUpperCase()).join('')
  if (!initials) initials = name.slice(0, 2).toUpperCase()

  return {
    initials: initials || 'TV',
    bgClass: 'from-purple-900/40 to-indigo-800/30 text-purple-200 border-purple-500/30',
  }
}

/**
 * Robust ProviderLogo component with 3-tier resilience:
 * Tier 1: Remote API provider_logo_url
 * Tier 2: Local bundled high-res SVG/PNG asset
 * Tier 3: Cyberpunk brand initials badge
 */
export default function ProviderLogo({
  name = '',
  logoUrl = '',
  className = 'w-10 h-10',
  imgClassName = 'max-h-full max-w-full object-contain',
}) {
  const [loadStage, setLoadStage] = useState(0) // 0: remote url, 1: local asset fallback, 2: initials fallback

  const normalized = name.toLowerCase().trim()
  const localFallback = Object.entries(LOCAL_LOGO_MAP).find(([key]) =>
    normalized.includes(key) || key.includes(normalized)
  )?.[1]

  // If initial logoUrl is missing and local asset exists, start at stage 1
  const activeSrc = loadStage === 0
    ? (logoUrl || localFallback)
    : loadStage === 1
    ? localFallback
    : null

  const handleImageError = () => {
    if (loadStage === 0 && localFallback && localFallback !== logoUrl) {
      setLoadStage(1) // Try local asset
    } else {
      setLoadStage(2) // Fallback to initials badge
    }
  }

  // Initials badge fallback (Stage 2 or no image available)
  if (loadStage === 2 || !activeSrc) {
    const brand = getFallbackBrandStyle(name)
    return (
      <div
        className={`${className} rounded-xl bg-gradient-to-br ${brand.bgClass} border p-1 flex items-center justify-center flex-shrink-0 select-none shadow-sm`}
        title={name}
      >
        <span className="font-mono font-black text-[11px] leading-none tracking-tight uppercase">
          {brand.initials}
        </span>
      </div>
    )
  }

  return (
    <div
      className={`${className} rounded-xl bg-white/10 p-1.5 flex items-center justify-center flex-shrink-0 border border-white/10 overflow-hidden select-none`}
      title={name}
    >
      <img
        src={activeSrc}
        alt={name}
        className={imgClassName}
        onError={handleImageError}
        loading="lazy"
      />
    </div>
  )
}
