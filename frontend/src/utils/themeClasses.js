/**
 * Shared Tailwind class strings for light/dark theme consistency.
 * Light mode is default; dark: variants apply when html has class "dark".
 */

export const shell = 'min-h-screen bg-slate-50 text-slate-900 dark:bg-gray-900 dark:text-white'

export const header =
  'bg-white border-b border-slate-200 dark:bg-gray-800 dark:border-gray-700'

export const pageTitle = 'text-lg font-bold text-slate-900 dark:text-white'

export const muted = 'text-slate-500 dark:text-gray-400'

export const mutedSm = 'text-xs text-slate-500 dark:text-gray-400'

export const card =
  'bg-white border border-slate-200 rounded-xl shadow-sm dark:bg-gray-800 dark:border-gray-700'

export const cardInner =
  'bg-slate-50 border border-slate-200 rounded-lg dark:bg-gray-900 dark:border-gray-700'

export const sectionTitle =
  'text-sm font-semibold text-slate-600 dark:text-gray-300 uppercase tracking-widest'

export const btnGhost =
  'text-slate-600 hover:text-slate-900 dark:text-gray-400 dark:hover:text-white transition-colors'

export const tabActive =
  'bg-slate-100 text-slate-900 dark:bg-gray-700 dark:text-white'

export const tabInactive =
  'text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-700/50'

export const tableWrap =
  'overflow-x-auto rounded-lg border border-slate-200 dark:border-gray-700'

export const tableHead =
  'text-xs uppercase bg-slate-100 text-slate-500 dark:bg-gray-800 dark:text-gray-400'

export const tableBody = 'text-sm text-left text-slate-800 dark:text-gray-200'

export const tableDivide = 'divide-y divide-slate-200 dark:divide-gray-700'

export const modalOverlay = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 dark:bg-black/60'

export const modalPanel =
  'bg-white border border-slate-200 rounded-lg shadow-xl dark:bg-gray-800 dark:border-gray-600'

export const errorBanner =
  'rounded-lg bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm dark:bg-red-900/30 dark:border-red-700 dark:text-red-300'
