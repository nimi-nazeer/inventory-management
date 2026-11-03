// Stroke-style 24x24 icon paths (Lucide-compatible geometry, inline so no dependency is needed).
// Render with: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"
//   stroke-linecap="round" stroke-linejoin="round"><path v-for="d in icons[name]" :d="d" /></svg>
// Add or swap entries to match the app's nav items; keep the style consistent (stroke, no fills, no emoji).
export const icons = {
  dashboard: ['M3 3h7v9H3z', 'M14 3h7v5h-7z', 'M14 12h7v9h-7z', 'M3 16h7v5H3z'],
  inventory: ['M21 8l-9-5-9 5 9 5 9-5z', 'M3 8v8l9 5 9-5V8', 'M12 13v8'],
  orders: ['M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2', 'M9 3h6v4H9z', 'M9 12h6', 'M9 16h4'],
  finance: ['M12 2v20', 'M17 6.5C17 4.6 14.8 4 12 4S7 5 7 7s2 3 5 3.5 5 1.5 5 3.5-2.2 3-5 3-5-.6-5-2.5'],
  forecast: ['M3 3v18h18', 'M7 15l4-4 3 3 5-6'],
  restocking: ['M21 12a9 9 0 1 1-3-6.7', 'M21 3v6h-6'],
  reports: ['M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z', 'M14 3v5h5', 'M9 13h6', 'M9 17h6'],
  menu: ['M4 6h16', 'M4 12h16', 'M4 18h16'],
  chevronsLeft: ['M11 17l-5-5 5-5', 'M18 17l-5-5 5-5'],
  close: ['M18 6L6 18', 'M6 6l12 12']
}
