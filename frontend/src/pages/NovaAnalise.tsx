import { useState } from 'react'
import { ai, analises } from '@/services/api'
import type { WizardStep } from '@/types'
import { Upload, FileText, ClipboardList, GitBranch, Clock, Mail, Check, Sparkles } from 'lucide-react'

const STEPS: Array<{ label: string; icon: React.ElementType }> = [
  { label: 'Upload & Contexto', icon: Upload },
  { label: 'Análise da Decisão', icon: FileText },
  { label: 'Pedidos', icon: ClipboardList },
  { label: 'ED & Recurso', icon: GitBranch },
  { label: 'Prazos', icon: Clock },
  { label: 'Email', icon: Mail },
]

export default function NovaAnalise() {
  const [step, setStep] = useState<WizardStep>(1)
  const [analiseId, setAnaliseId] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [aiSuggestions, setAiSuggestions] = useState<Record<string, unknown>>({})
  const [confirmedFields] = useState<Set<string>>(new Set())

  // Form state
  const [area, setArea] = useState('trabalhista')
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [extracted, setExtracted] = useState<Record<string, unknown> | null>(null)

  const totalFields = Object.keys(aiSuggestions).length
  const confirmedCount = confirmedFields.size

  // Step 1: Upload PDF
  const handlePdfUpload = async (file: File) => {
    setPdfFile(file)
    setLoading(true)
    try {
      const result = await ai.extractPdf(file)
      setExtracted(result.extracted)
      setAiSuggestions(result.extracted || {})

      // Create analysis in DB
      const a = await analises.create({ area })
      setAnaliseId(a.id)
    } catch (err) {
      console.error('Extraction failed:', err)
    } finally {
      setLoading(false)
    }
  }

  const canAdvance = step < 6
  const canGoBack = step > 1

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Nova Análise</h1>
        <p className="text-gray-500 mt-1">Wizard de análise de decisão judicial com IA</p>
      </div>

      {/* Progress bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          {STEPS.map((s, i) => {
            const stepNum = (i + 1) as WizardStep
            const isActive = stepNum === step
            const isCompleted = stepNum < step
            return (
              <button
                key={i}
                onClick={() => stepNum <= step && setStep(stepNum)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-primary-600 text-white font-medium'
                    : isCompleted
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-500'
                }`}
              >
                {isCompleted ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <s.icon className="h-4 w-4" />
                )}
                <span className="hidden lg:inline">{s.label}</span>
              </button>
            )
          })}
        </div>

        {/* AI confirmation progress */}
        {totalFields > 0 && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Sparkles className="h-4 w-4 text-yellow-500" />
            <span>
              Você confirmou {confirmedCount}/{totalFields} campos sugeridos pela IA
            </span>
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-500 rounded-full h-2 transition-all"
                style={{ width: `${totalFields ? (confirmedCount / totalFields) * 100 : 0}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Step content */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        {step === 1 && (
          <StepUpload
            area={area}
            onAreaChange={setArea}
            onFileUpload={handlePdfUpload}
            loading={loading}
            extracted={extracted}
            pdfFile={pdfFile}
          />
        )}
        {step === 2 && <StepAnalise extracted={extracted} />}
        {step === 3 && <StepPedidos />}
        {step === 4 && <StepRecurso />}
        {step === 5 && <StepPrazos />}
        {step === 6 && <StepEmail analiseId={analiseId} />}
      </div>

      {/* Navigation */}
      <div className="flex justify-between mt-6">
        <button
          onClick={() => canGoBack && setStep((step - 1) as WizardStep)}
          disabled={!canGoBack}
          className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-30"
        >
          Voltar
        </button>
        <button
          onClick={() => canAdvance && setStep((step + 1) as WizardStep)}
          disabled={!canAdvance}
          className="px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-30"
        >
          {step === 5 ? 'Gerar Email' : 'Próximo'}
        </button>
      </div>
    </div>
  )
}

// --- Step Components ---

function StepUpload({
  area,
  onAreaChange,
  onFileUpload,
  loading,
  extracted,
  pdfFile,
}: {
  area: string
  onAreaChange: (a: string) => void
  onFileUpload: (f: File) => void
  loading: boolean
  extracted: Record<string, unknown> | null
  pdfFile: File | null
}) {
  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Área do Direito</label>
        <div className="flex gap-3">
          {['trabalhista', 'civel', 'empresarial'].map((a) => (
            <button
              key={a}
              onClick={() => onAreaChange(a)}
              className={`px-4 py-2 rounded-lg border transition-colors capitalize ${
                area === a
                  ? 'bg-primary-600 text-white border-primary-600'
                  : 'border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {a}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Upload da Decisão (PDF)
        </label>
        <div
          className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-primary-400 transition-colors cursor-pointer"
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault()
            const file = e.dataTransfer.files[0]
            if (file?.type === 'application/pdf') onFileUpload(file)
          }}
          onClick={() => {
            const input = document.createElement('input')
            input.type = 'file'
            input.accept = '.pdf'
            input.onchange = () => {
              const file = input.files?.[0]
              if (file) onFileUpload(file)
            }
            input.click()
          }}
        >
          {loading ? (
            <div className="text-primary-600">
              <Sparkles className="h-8 w-8 mx-auto mb-2 animate-pulse" />
              <p>Extraindo dados com IA...</p>
            </div>
          ) : pdfFile ? (
            <div className="text-green-600">
              <Check className="h-8 w-8 mx-auto mb-2" />
              <p className="font-medium">{pdfFile.name}</p>
              <p className="text-sm text-gray-500 mt-1">
                {extracted ? 'Dados extraídos com sucesso' : 'Processando...'}
              </p>
            </div>
          ) : (
            <div className="text-gray-500">
              <Upload className="h-8 w-8 mx-auto mb-2" />
              <p>Arraste o PDF aqui ou clique para selecionar</p>
              <p className="text-sm mt-1">Suporta decisões do PJe, eSAJ, eProc</p>
            </div>
          )}
        </div>
      </div>

      {extracted && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-yellow-800 mb-2">
            <Sparkles className="h-5 w-5" />
            <span className="font-medium">Dados extraídos pela IA — confirme cada campo</span>
          </div>
          <pre className="text-xs text-gray-600 overflow-auto max-h-96">
            {JSON.stringify(extracted, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

function StepAnalise(_props: { extracted: Record<string, unknown> | null }) {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Análise da Decisão</h2>
      <p className="text-gray-500">
        Revise os dados extraídos pela IA e adicione suas observações.
      </p>
      <textarea
        className="w-full h-64 border border-gray-300 rounded-lg p-4 focus:ring-2 focus:ring-primary-500 outline-none"
        placeholder="Observações sobre a decisão..."
      />
    </div>
  )
}

function StepPedidos() {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Pedidos / Claims</h2>
      <p className="text-gray-500">
        Upload de tabela CSV/Excel ou cole o texto do DataJuri.
      </p>
      <textarea
        className="w-full h-48 border border-gray-300 rounded-lg p-4 font-mono text-sm focus:ring-2 focus:ring-primary-500 outline-none"
        placeholder="Cole a tabela de pedidos aqui..."
      />
    </div>
  )
}

function StepRecurso() {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Embargos de Declaração & Recurso</h2>
      <p className="text-gray-500">
        A IA analisará a viabilidade de ED e sugerirá o recurso adequado.
      </p>
      <div className="bg-gray-50 rounded-lg p-4 text-center text-gray-400">
        Análise de ED será exibida aqui após processamento pela IA
      </div>
    </div>
  )
}

function StepPrazos() {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Prazos</h2>
      <p className="text-gray-500">Prazos calculados automaticamente. Edite conforme necessário.</p>
      <div className="bg-gray-50 rounded-lg p-4 text-center text-gray-400">
        Prazos serão calculados com base na data de ciência e tipo de decisão
      </div>
    </div>
  )
}

function StepEmail(_props: { analiseId: number | null }) {
  const [emailBody, setEmailBody] = useState('')
  const [copied, setCopied] = useState(false)

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(emailBody)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Email — Rascunho Final</h2>
      <textarea
        value={emailBody}
        onChange={(e) => setEmailBody(e.target.value)}
        className="w-full h-96 border border-gray-300 rounded-lg p-4 focus:ring-2 focus:ring-primary-500 outline-none"
        placeholder="O email será gerado aqui pela IA..."
      />
      <div className="flex gap-3">
        <button
          onClick={copyToClipboard}
          className="px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700"
        >
          {copied ? 'Copiado!' : 'Copiar para Clipboard'}
        </button>
        <button className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
          Salvar Análise
        </button>
      </div>
    </div>
  )
}
