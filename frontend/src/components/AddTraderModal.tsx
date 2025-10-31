import { useState } from 'react'
import { X, ExternalLink } from 'lucide-react'
import { addTrader } from '@/api/api'

interface AddTraderModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export default function AddTraderModal({
  isOpen,
  onClose,
  onSuccess,
}: AddTraderModalProps) {
  const [input, setInput] = useState('')
  const [label, setLabel] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (!isOpen) return null

  // Extract address from Polymarket URL or use direct address
  const extractAddress = (value: string): string | null => {
    const trimmed = value.trim()

    // Check if it's a Polymarket profile URL
    const urlMatch = trimmed.match(/polymarket\.com\/profile\/(0x[a-fA-F0-9]{40})/)
    if (urlMatch) {
      return urlMatch[1].toLowerCase()
    }

    // Check if it's a direct Ethereum address
    if (trimmed.startsWith('0x') && trimmed.length === 42) {
      return trimmed.toLowerCase()
    }

    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    const address = extractAddress(input)

    if (!address) {
      setError('Please enter a valid Ethereum address or Polymarket profile URL')
      return
    }

    setLoading(true)

    try {
      await addTrader({ address, label: label || undefined })
      setInput('')
      setLabel('')
      onSuccess()
      onClose()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add trader')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Add New Trader</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-3 text-sm">
              {error}
            </div>
          )}

          {/* Link to Polymarket Leaderboard */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <div className="flex-1">
                <p className="text-sm text-blue-900 font-medium mb-1">
                  Find traders to track
                </p>
                <p className="text-xs text-blue-700">
                  Browse the Polymarket leaderboard to find top traders, then copy their profile URL
                </p>
              </div>
            </div>
            <a
              href="https://polymarket.com/leaderboard"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Open Polymarket Leaderboard
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>

          <div>
            <label
              htmlFor="input"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Trader Address or Profile URL *
            </label>
            <input
              type="text"
              id="input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="0x... or https://polymarket.com/profile/0x..."
              className="input"
              required
            />
            <p className="mt-1 text-xs text-gray-500">
              Paste either:
              <br />
              • Ethereum address: <code className="text-gray-700">0x75e765...</code>
              <br />
              • Polymarket profile URL: <code className="text-gray-700">https://polymarket.com/profile/0x75e765...</code>
            </p>
          </div>

          <div>
            <label
              htmlFor="label"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Name/Label *
            </label>
            <input
              type="text"
              id="label"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="e.g., 25usdc, TopTrader, etc."
              className="input"
              required
            />
            <p className="mt-1 text-xs text-gray-500">
              Choose a friendly name to identify this trader in your dashboard
            </p>
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary flex-1"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary flex-1"
              disabled={loading}
            >
              {loading ? 'Adding...' : 'Add Trader'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
