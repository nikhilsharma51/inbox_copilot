/**
 * Formatting utilities for display
 */

/**
 * Convert ISO date to relative time (e.g., "2 hours ago", "yesterday")
 */
export function relativeTime(iso: string): string {
  const date = new Date(iso);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) {
    const days = Math.floor(seconds / 86400);
    return days === 1 ? 'yesterday' : `${days}d ago`;
  }

  // Fallback to date format for older dates
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Get initials from a name
 * e.g., "John Doe" -> "JD", "Alice" -> "A"
 */
export function initials(name: string): string {
  return name
    .split(' ')
    .map((part) => part[0]?.toUpperCase())
    .filter(Boolean)
    .join('')
    .slice(0, 2);
}

/**
 * Hash a string to one of 6 palette colors
 * Colors: forest, terracotta, sage, ink, paper, surface
 */
export function avatarColor(
  sender: string
): 'forest' | 'terracotta' | 'sage' | 'ink' | 'paper' | 'surface' {
  const colors = ['forest', 'terracotta', 'sage', 'ink', 'paper', 'surface'] as const;
  let hash = 0;

  for (let i = 0; i < sender.length; i++) {
    hash = ((hash << 5) - hash) + sender.charCodeAt(i);
    hash = hash & hash; // Convert to 32-bit integer
  }

  return colors[Math.abs(hash) % colors.length];
}

/**
 * Parse email sender string
 * e.g., "John Doe <john@example.com>" -> { name: "John Doe", email: "john@example.com" }
 * e.g., "john@example.com" -> { name: "john@example.com", email: "john@example.com" }
 */
export function parseSender(sender: string): { name: string; email: string } {
  const match = sender.match(/^(.+?)\s*<(.+?)>$/);

  if (match) {
    return {
      name: match[1].trim(),
      email: match[2].trim(),
    };
  }

  // No angle brackets, assume it's just an email
  return {
    name: sender,
    email: sender,
  };
}
