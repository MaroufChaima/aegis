import ProfileRangesPanel from './ProfileRangesPanel'

/**
 * Modal overlay showing personalized normal ranges for a victim.
 */
export default function ProfileRangesModal({ profile, onClose }) {
  if (!profile) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60"
      onClick={onClose}
    >
      <div
        className="bg-gray-800 border border-gray-600 rounded-lg shadow-xl w-full max-w-md max-h-[85vh] overflow-y-auto p-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-white">Personal Normal Ranges</h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-white text-sm"
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
