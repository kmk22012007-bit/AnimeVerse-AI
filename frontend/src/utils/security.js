/**
 * Security utilities for AnimeVerse AI
 */

/**
 * Validates external URLs to prevent javascript: or data: pseudo-protocol attacks.
 * Strictly permits only http:// and https:// protocols.
 */
export const isSafeUrl = (url) => {
  if (!url || typeof url !== 'string') return false;
  const trimmed = url.trim().toLowerCase();
  return trimmed.startsWith('https://') || trimmed.startsWith('http://');
};
