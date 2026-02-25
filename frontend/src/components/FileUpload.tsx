import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Upload,
  File,
  FileText,
  FileSpreadsheet,
  Presentation,
  CheckCircle,
  AlertCircle,
  Loader2,
  X,
  Sparkles,
  Database,
  GitBranch,
  Clock,
  Info,
  Lock
} from 'lucide-react'
import { api, IngestResponse } from '../services/api'
import { cn } from '../lib/utils'

// Upload is disabled for demo - files are pre-loaded
const UPLOAD_DISABLED = true

export default function FileUpload() {
  const [files, setFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [result, setResult] = useState<IngestResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      (file) =>
        file.name.endsWith('.csv') ||
        file.name.endsWith('.pdf') ||
        file.name.endsWith('.ppt') ||
        file.name.endsWith('.pptx')
    )
    setFiles((prev) => [...prev, ...droppedFiles])
  }, [])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      setFiles((prev) => [...prev, ...selectedFiles])
    }
  }

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (files.length === 0) return

    setIsUploading(true)
    setError(null)
    setResult(null)

    try {
      const response = await api.ingest(files)
      setResult(response)
      setFiles([])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  const getFileIcon = (filename: string) => {
    if (filename.endsWith('.csv')) return FileSpreadsheet
    if (filename.endsWith('.ppt') || filename.endsWith('.pptx')) return Presentation
    return FileText
  }

  const getFileColor = (filename: string) => {
    if (filename.endsWith('.csv')) return 'text-green-400'
    if (filename.endsWith('.ppt') || filename.endsWith('.pptx')) return 'text-orange-400'
    return 'text-blue-400'
  }

  return (
    <div className="space-y-6">
      {/* Disabled Notice Banner */}
      {UPLOAD_DISABLED && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-2xl p-5 border border-amber-500/20 bg-amber-500/5"
        >
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center flex-shrink-0">
              <Info className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground flex items-center gap-2">
                <Lock className="w-4 h-4 text-amber-400" />
                Upload Disabled for Demo
              </h3>
              <p className="text-sm text-muted-foreground mt-1">
                All financial documents have been pre-loaded successfully. Upload functionality is disabled to prevent excessive API load during the demo.
              </p>
              <div className="flex flex-wrap gap-3 mt-3 text-xs">
                <span className="flex items-center gap-1.5 px-2.5 py-1 bg-green-500/10 text-green-400 rounded-lg">
                  <CheckCircle className="w-3.5 h-3.5" />
                  100K+ vectors indexed
                </span>
                <span className="flex items-center gap-1.5 px-2.5 py-1 bg-blue-500/10 text-blue-400 rounded-lg">
                  <Database className="w-3.5 h-3.5" />
                  5K+ graph nodes
                </span>
                <span className="flex items-center gap-1.5 px-2.5 py-1 bg-purple-500/10 text-purple-400 rounded-lg">
                  <GitBranch className="w-3.5 h-3.5" />
                  25K+ relationships
                </span>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Main Upload Card */}
      <div className={cn("glass rounded-2xl p-6", UPLOAD_DISABLED && "opacity-50 pointer-events-none")}>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
            <Upload className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">Upload Documents</h2>
            <p className="text-sm text-muted-foreground">Add financial data for analysis</p>
          </div>
        </div>

        {/* Drop zone */}
        <motion.div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={cn(
            "relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300",
            isDragging
              ? "border-primary bg-primary/5"
              : "border-white/10 hover:border-white/20 hover:bg-white/[0.02]"
          )}
        >
          <AnimatePresence>
            {isDragging && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-primary/10 rounded-2xl flex items-center justify-center"
              >
                <p className="text-primary font-medium">Drop files here</p>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">
            <Upload className="w-8 h-8 text-muted-foreground" />
          </div>

          <p className="text-foreground font-medium mb-2">
            Drag and drop files here
          </p>
          <p className="text-sm text-muted-foreground mb-6">
            or click to browse
          </p>

          <label className="inline-block">
            <input
              type="file"
              multiple
              accept=".csv,.pdf,.ppt,.pptx"
              onChange={handleFileSelect}
              className="hidden"
            />
            <motion.span
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="inline-flex items-center gap-2 px-6 py-3 bg-white/10 hover:bg-white/15 border border-white/10 text-foreground rounded-xl cursor-pointer transition-all duration-300"
            >
              <File className="w-4 h-4" />
              Select Files
            </motion.span>
          </label>

          <div className="flex items-center justify-center gap-4 mt-6 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <FileSpreadsheet className="w-3.5 h-3.5 text-green-400" />
              CSV
            </span>
            <span className="flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-blue-400" />
              PDF
            </span>
            <span className="flex items-center gap-1.5">
              <Presentation className="w-3.5 h-3.5 text-orange-400" />
              PPT/PPTX
            </span>
          </div>
        </motion.div>

        {/* File list */}
        <AnimatePresence>
          {files.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mt-6 space-y-3"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-foreground">
                  Selected Files ({files.length})
                </h3>
                <button
                  onClick={() => setFiles([])}
                  className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                >
                  Clear all
                </button>
              </div>

              <div className="space-y-2">
                {files.map((file, index) => {
                  const FileIcon = getFileIcon(file.name)
                  return (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 10 }}
                      transition={{ delay: index * 0.05 }}
                      className="flex items-center justify-between bg-white/[0.03] border border-white/10 px-4 py-3 rounded-xl group hover:bg-white/[0.05] transition-all duration-300"
                    >
                      <div className="flex items-center gap-3">
                        <FileIcon className={cn("w-5 h-5", getFileColor(file.name))} />
                        <div>
                          <span className="text-sm text-foreground">{file.name}</span>
                          <span className="ml-2 text-xs text-muted-foreground">
                            ({(file.size / 1024).toFixed(1)} KB)
                          </span>
                        </div>
                      </div>
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => removeFile(index)}
                        className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-300"
                      >
                        <X className="w-4 h-4" />
                      </motion.button>
                    </motion.div>
                  )
                })}
              </div>

              <motion.button
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={handleUpload}
                disabled={isUploading}
                className={cn(
                  "w-full py-4 rounded-xl font-medium flex items-center justify-center gap-3 transition-all duration-300",
                  "disabled:opacity-50 disabled:cursor-not-allowed",
                  isUploading
                    ? "bg-white/10 text-foreground"
                    : "bg-primary text-primary-foreground glow-primary hover:brightness-110"
                )}
              >
                {isUploading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Processing documents...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Upload & Process
                  </>
                )}
              </motion.button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Result */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="glass rounded-2xl p-6 border-green-500/20"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-green-400/10 flex items-center justify-center">
                <CheckCircle className="w-5 h-5 text-green-400" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground">Upload Successful</h3>
                <p className="text-sm text-muted-foreground">Documents have been processed</p>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                icon={FileText}
                label="Documents"
                value={result.documents_processed}
                color="text-blue-400"
              />
              <StatCard
                icon={Database}
                label="Chunks"
                value={result.chunks_created}
                color="text-purple-400"
              />
              <StatCard
                icon={Sparkles}
                label="Entities"
                value={result.entities_extracted}
                color="text-primary"
              />
              <StatCard
                icon={GitBranch}
                label="Graph Edges"
                value={result.graph_edges_created}
                color="text-cyan-400"
              />
            </div>

            <div className="mt-4 flex items-center justify-center gap-2 text-xs text-muted-foreground">
              <Clock className="w-3.5 h-3.5" />
              <span>Processed in {result.processing_time_seconds.toFixed(1)}s</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="glass rounded-2xl p-6 border-red-500/20"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-red-400/10 flex items-center justify-center">
                <AlertCircle className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground">Upload Failed</h3>
                <p className="text-sm text-red-400">{error}</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

interface StatCardProps {
  icon: React.ElementType
  label: string
  value: number
  color: string
}

function StatCard({ icon: Icon, label, value, color }: StatCardProps) {
  return (
    <div className="bg-white/[0.03] border border-white/10 rounded-xl p-4 text-center">
      <Icon className={cn("w-5 h-5 mx-auto mb-2", color)} />
      <p className="text-2xl font-bold text-foreground">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  )
}
