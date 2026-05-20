import { Star } from 'lucide-react'

interface StarRatingProps {
  rating: number
  size?: number
  showValue?: boolean
}

export default function StarRating({ rating, size = 16, showValue = false }: StarRatingProps) {
  const stars = Array.from({ length: 5 }, (_, i) => {
    const filled = i + 1 <= rating
    const halfFilled = !filled && i + 0.5 <= rating
    return { filled, halfFilled }
  })

  return (
    <div className="flex items-center gap-1">
      <div className="flex items-center">
        {stars.map((star, i) => (
          <span key={i} className="relative inline-block" style={{ width: size, height: size }}>
            {/* Empty star base */}
            <Star
              size={size}
              className="text-gray-300"
              fill="currentColor"
            />
            {/* Filled overlay */}
            {(star.filled || star.halfFilled) && (
              <span
                className="absolute inset-0 overflow-hidden"
                style={{ width: star.halfFilled ? '50%' : '100%' }}
              >
                <Star
                  size={size}
                  className="text-yellow-400"
                  fill="currentColor"
                />
              </span>
            )}
          </span>
        ))}
      </div>
      {showValue && (
        <span className="text-sm text-gray-600 ml-1">{rating.toFixed(1)}</span>
      )}
    </div>
  )
}
