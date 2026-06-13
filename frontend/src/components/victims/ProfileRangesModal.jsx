import ProfileRangesPanel from './ProfileRangesPanel'
import { modalOverlay, modalPanel } from '../../utils/themeClasses'

export default function ProfileRangesModal({ profile, onClose }) {
  if (!profile) return null

  return (
    <div className={modalOverlay} onClick={onClose}>
      <div
        className={`${modalPanel} w-full max-w-md max-h-[85vh] overflow-y-auto p-4`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
            Personal Normal Ranges
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-500 hover:text-slate-900 dark:text-gray-400 dark:hover:text-white text-sm"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        <ProfileRangesPanel profile={profile} />
      </div>
    </div>
  )
}
