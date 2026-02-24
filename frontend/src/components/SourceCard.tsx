import { motion } from 'framer-motion'
import { Source } from '../services/api'

interface Props {
  source: Source
  index: number
}

export default function SourceCard({ source, index }: Props) {
  // Extract a clean title from the filename
  const getTitle = (filename: string) => {
    // Remove extension and clean up
    const name = filename.replace(/\.[^/.]+$/, '')
    // Convert underscores/dashes to spaces and title case
    return name
      .replace(/[-_]/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase())
  }

  // Generate subtitle from page/snippet
  const getSubtitle = () => {
    if (source.page) {
      return `Page ${source.page}`
    }
    if (source.snippet) {
      // Extract first meaningful line, clean it up
      const firstLine = source.snippet.split('\n')[0].trim()
      return firstLine.length > 60 ? firstLine.slice(0, 57) + '...' : firstLine
    }
    return source.file
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.3 }}
      whileHover={{ scale: 1.02, y: -2 }}
      className="source-card group cursor-default"
    >
      {/* Source label */}
      <span className="source-label">
        SOURCE {index + 1}
      </span>

      {/* Title */}
      <h4 className="source-title">
        {getTitle(source.file)}
      </h4>

      {/* Subtitle */}
      <p className="source-subtitle">
        {getSubtitle()}
      </p>

      {/* Hover glow effect */}
      <div className="source-glow" />
    </motion.div>
  )
}
