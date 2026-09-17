// Nav icon path data, 24x24, stroked (AppSidebar sets fill: none, stroke: currentColor).
// Kept as raw path data rather than an icon dependency — eight glyphs don't
// justify a package, and any Feather/Lucide path drops in here unchanged.
export const ICONS = {
  overview: 'M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z',
  inventory: 'M21 8l-9-5-9 5 9 5 9-5zM3 8v8l9 5 9-5V8M12 13v8',
  orders: 'M9 3h6l1 4H8l1-4zM5 7h14l-1 13H6L5 7z',
  restocking: 'M3 12a9 9 0 0 1 15.3-6.4M21 12a9 9 0 0 1-15.3 6.4M18 3v5h-5M6 21v-5h5',
  finance: 'M12 2v20M17 6H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6',
  demand: 'M3 17l6-6 4 4 8-8M21 7v5h-5',
  reports: 'M3 21h18M7 17V9M12 17V5M17 17v-6'
}
