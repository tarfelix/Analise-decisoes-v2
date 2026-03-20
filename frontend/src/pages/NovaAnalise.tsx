import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ai, processo } from '@/services/api'
import type { WizardStep } from '@/types'
import {
  Upload, FileText, ClipboardList, GitBranch, Clock, Mail, Check, Sparkles,
  Search, Loader2, ChevronRight, AlertCircle, BookOpen,
} from 'lucide-react'

const STEPS: Array<{ label: string; icon: React.ElementType }> = [
  { label: 'Processo & PDF', icon: Search },
  { label: 'Análise da Decisão', icon: FileText },
  { label: 'Pedidos', icon: ClipboardList },
  { label: 'ED & Recurso', icon: GitBranch },
  { label: 'Prazos', icon: Clock },
  { label: 'Email', icon: Mail },
]

interface PdfPiece {
  index: number
  level: number
  title: string
  start_page: number
  end_page: number
  pages: number
  type: string
  pje_id: string
}

export default function NovaAnalise() {
  const [step, setStep] = useState<WizardStep>(1)

  // Step 1 state
  const [area, setArea] = useState('trabalhista')
  const [pasta, setPasta] = useState('')
  const [processoData, setProcessoData] = useState<Record<string, unknown> | null>(null)
  const [processoLoading, setProcessoLoading] = useState(false)
  const [processoError, setProcessoError] = useState('')

  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [bookmarks, setBookmarks] = useState<PdfPiece[]>([])
  const [selectedPiece, setSelectedPiece] = useState<PdfPiece | null>(null)
  const [pdfLoading, setPdfLoading] = useState(false)

  const [decisionText, setDecisionText] = useState('')
  const [textLoading, setTextLoading] = useState(false)

  // Step 2 state
  const [extracted, setExtracted] = useState<Record<string, unknown> | null>(null)
  const [extractLoading, setExtractLoading] = useState(false)
  const [obsDecisao, setObsDecisao] = useState('')

  const canAdvance = step < 6
  const canGoBack = step > 1

  // --- Step 1: Buscar processo ---
  const handleBuscarProcesso = async () => {
    if (!pasta.trim()) return
    setProcessoLoading(true)
    setProcessoError('')
    try {
      const data = await processo.buscar(pasta.trim())
      setProcessoData(data)
    } catch (err) {
      setProcessoError(err instanceof Error ? err.message : 'Processo não encontrado')
      setProcessoData(null)
    } finally {
      setProcessoLoading(false)
    }
  }

  // --- Step 1: Upload PDF e extrair bookmarks ---
  const handlePdfUpload = async (file: File) => {
    setPdfFile(file)
    setPdfLoading(true)
    setBookmarks([])
    setSelectedPiece(null)
    try {
      const result = await processo.extractBookmarks(file)
      if (result.has_bookmarks) {
        setBookmarks(result.pieces || [])
        // Auto-select suggested decision
        if (result.suggested_decision) {
          setSelectedPiece(result.suggested_decision)
        }
      }
    } catch (err) {
      console.error('Bookmark extraction failed:', err)
    } finally {
      setPdfLoading(false)
    }
  }

  // --- Step 1: Extrair texto da peça selecionada ---
  const handleExtractPieceText = async () => {
    if (!pdfFile || !selectedPiece) return
    setTextLoading(true)
    try {
      const result = await processo.extractPieceText(
        pdfFile, selectedPiece.start_page, selectedPiece.end_page,
      )
      setDecisionText(result.text)
    } catch (err) {
      console.error('Text extraction failed:', err)
    } finally {
      setTextLoading(false)
    }
  }

  // --- Step 2: Análise por IA ---
  const handleAnalyzeWithAI = async () => {
    if (!decisionText) return
    setExtractLoading(true)
    try {
      const result = await ai.extractPdf(pdfFile!)
      setExtracted(result.extracted)
    } catch (err) {
      console.error('AI extraction failed:', err)
    } finally {
      setExtractLoading(false)
    }
  }

  // --- Advance step with auto-actions ---
  const handleNext = async () => {
    if (step === 1 && selectedPiece && !decisionText) {
      await handleExtractPieceText()
    }
    if (canAdvance) setStep((step + 1) as WizardStep)
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Nova Análise</h1>
        <p className="text-gray-500 mt-1">Análise de decisão judicial com IA copiloto</p>
      </div>

      {/* Wizard steps */}
      <div className="flex items-center justify-between mb-8 gap-1">
        {STEPS.map((s, i) => {
          const stepNum = (i + 1) as WizardStep
          const isActive = stepNum === step
          const isCompleted = stepNum < step
          return (
            <button
              key={i}
              onClick={() => stepNum <= step && setStep(stepNum)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive ? 'bg-primary-600 text-white font-medium'
                : isCompleted ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-400'
              }`}
            >
              {isCompleted ? <Check className="h-4 w-4" /> : <s.icon className="h-4 w-4" />}
              <span className="hidden xl:inline">{s.label}</span>
            </button>
          )
        })}
      </div>

      {/* Step content */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 min-h-[400px]">
        {step === 1 && (
          <StepProcessoPDF
            area={area} onAreaChange={setArea}
            pasta={pasta} onPastaChange={setPasta}
            processoData={processoData} processoLoading={processoLoading}
            processoError={processoError} onBuscar={handleBuscarProcesso}
            pdfFile={pdfFile} onPdfUpload={handlePdfUpload} pdfLoading={pdfLoading}
            bookmarks={bookmarks} selectedPiece={selectedPiece}
            onSelectPiece={setSelectedPiece}
            decisionText={decisionText} textLoading={textLoading}
            onExtractText={handleExtractPieceText}
          />
        )}
        {step === 2 && (
          <StepAnalise
            decisionText={decisionText}
            extracted={extracted}
            extractLoading={extractLoading}
            obsDecisao={obsDecisao}
            onObsChange={setObsDecisao}
            onAnalyze={handleAnalyzeWithAI}
          />
        )}
        {step === 3 && <StepPedidos />}
        {step === 4 && <StepRecurso />}
        {step === 5 && <StepPrazos />}
        {step === 6 && <StepEmail />}
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
          onClick={handleNext}
          disabled={!canAdvance}
          className="px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-30"
        >
          {step === 5 ? 'Gerar Email' : 'Próximo'}
        </button>
      </div>
    </div>
  )
}

// ==================== STEP 1: Processo & PDF ====================

function StepProcessoPDF({
  area, onAreaChange,
  pasta, onPastaChange,
  processoData, processoLoading, processoError, onBuscar,
  pdfFile, onPdfUpload, pdfLoading,
  bookmarks, selectedPiece, onSelectPiece,
  decisionText, textLoading, onExtractText,
}: {
  area: string; onAreaChange: (a: string) => void
  pasta: string; onPastaChange: (p: string) => void
  processoData: Record<string, unknown> | null; processoLoading: boolean
  processoError: string; onBuscar: () => void
  pdfFile: File | null; onPdfUpload: (f: File) => void; pdfLoading: boolean
  bookmarks: PdfPiece[]; selectedPiece: PdfPiece | null
  onSelectPiece: (p: PdfPiece) => void
  decisionText: string; textLoading: boolean; onExtractText: () => void
}) {
  // Zion activities
  const { data: atividadesData } = useQuery({
    queryKey: ['atividades'],
    queryFn: () => processo.atividades('Verificar'),
    staleTime: 60000,
  })
  const atividades = atividadesData?.atividades || []

  const decisoes = bookmarks.filter((b) => b.type.startsWith('DECISAO'))
  const pecasCliente = bookmarks.filter((b) =>
    ['PECA_CONTESTACAO', 'PECA_IMPUGNACAO', 'PECA_RAZOES_FINAIS'].includes(b.type),
  )

  return (
    <div className="space-y-6">
      {/* Área */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Área do Direito</label>
        <div className="flex gap-3">
          {['trabalhista', 'civel', 'empresarial'].map((a) => (
            <button
              key={a}
              onClick={() => onAreaChange(a)}
              className={`px-4 py-2 rounded-lg border transition-colors capitalize ${
                area === a ? 'bg-primary-600 text-white border-primary-600'
                : 'border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {a}
            </button>
          ))}
        </div>
      </div>

      {/* Atividades Zion */}
      {atividades.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <BookOpen className="inline h-4 w-4 mr-1" />
            Atividades abertas no Zion
          </label>
          <div className="border border-gray-200 rounded-lg max-h-40 overflow-y-auto">
            {atividades.slice(0, 10).map((at: Record<string, unknown>, i: number) => (
              <button
                key={i}
                onClick={() => {
                  const p = String(at.pasta || '')
                  if (p) {
                    onPastaChange(p)
                    // Auto-detect area from suffix: (T)=trabalhista, (C)=civel
                    const match = p.match(/\(([TCE])\)\s*$/i)
                    if (match) {
                      const areaMap: Record<string, string> = { T: 'trabalhista', C: 'civel', E: 'empresarial' }
                      const detected = areaMap[match[1].toUpperCase()]
                      if (detected) onAreaChange(detected)
                    }
                  }
                }}
                className="w-full text-left px-4 py-2 hover:bg-blue-50 border-b border-gray-100 last:border-0 text-sm flex justify-between"
              >
                <span className="font-mono text-primary-600">{String(at.pasta || '—')}</span>
                <span className="text-gray-500 truncate ml-4">{String(at.assunto || '')}</span>
                <span className="text-gray-400 ml-2 whitespace-nowrap">{String(at.data_fatal || '')}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Buscar processo */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Pasta do processo (DataJuri)
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={pasta}
            onChange={(e) => onPastaChange(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onBuscar()}
            placeholder="Ex: 12345 ou 0001234-56.2024.5.15.0001"
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
          />
          <button
            onClick={onBuscar}
            disabled={processoLoading || !pasta.trim()}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
          >
            {processoLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            Buscar
          </button>
        </div>
        {processoError && (
          <div className="mt-2 flex items-center gap-2 text-sm text-amber-600">
            <AlertCircle className="h-4 w-4" />
            {processoError}
          </div>
        )}
        {processoData && (
          <div className="mt-3 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center gap-2 text-green-800 mb-2">
              <Check className="h-5 w-5" />
              <span className="font-medium">Processo encontrado</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm text-gray-700">
              {Object.entries(processoData).slice(0, 8).map(([key, val]) => (
                <div key={key}>
                  <span className="text-gray-400">{key}:</span>{' '}
                  <span className="font-medium">{String(val || '—')}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Upload PDF */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Upload do PDF do PJe (com índice de peças)
        </label>
        <div
          className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:border-primary-400 transition-colors cursor-pointer"
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault()
            const file = e.dataTransfer.files[0]
            if (file?.type === 'application/pdf') onPdfUpload(file)
          }}
          onClick={() => {
            const input = document.createElement('input')
            input.type = 'file'
            input.accept = '.pdf'
            input.onchange = () => {
              const file = input.files?.[0]
              if (file) onPdfUpload(file)
            }
            input.click()
          }}
        >
          {pdfLoading ? (
            <div className="text-primary-600">
              <Loader2 className="h-8 w-8 mx-auto mb-2 animate-spin" />
              <p>Extraindo índice de peças...</p>
            </div>
          ) : pdfFile ? (
            <div className="text-green-600">
              <Check className="h-8 w-8 mx-auto mb-2" />
              <p className="font-medium">{pdfFile.name}</p>
              <p className="text-sm text-gray-500 mt-1">
                {bookmarks.length > 0 ? `${bookmarks.length} peças encontradas` : 'PDF sem índice — será analisado integralmente'}
              </p>
            </div>
          ) : (
            <div className="text-gray-500">
              <Upload className="h-8 w-8 mx-auto mb-2" />
              <p>Arraste o PDF do PJe aqui ou clique para selecionar</p>
              <p className="text-sm mt-1">O sistema extrai o índice de peças automaticamente</p>
            </div>
          )}
        </div>
      </div>

      {/* Seleção de peça */}
      {bookmarks.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Selecione a decisão a analisar
          </label>

          {/* Decisões encontradas */}
          {decisoes.length > 0 && (
            <div className="mb-3">
              <p className="text-xs text-gray-500 mb-1 uppercase font-medium">Decisões</p>
              <div className="space-y-1">
                {decisoes.map((p) => (
                  <PieceButton
                    key={p.index} piece={p}
                    selected={selectedPiece?.index === p.index}
                    onClick={() => onSelectPiece(p)}
                    highlight
                  />
                ))}
              </div>
            </div>
          )}

          {/* Peças do cliente (para análise de ED) */}
          {pecasCliente.length > 0 && (
            <div className="mb-3">
              <p className="text-xs text-gray-500 mb-1 uppercase font-medium">Peças do Cliente (úteis para ED)</p>
              <div className="space-y-1">
                {pecasCliente.map((p) => (
                  <PieceButton
                    key={p.index} piece={p}
                    selected={selectedPiece?.index === p.index}
                    onClick={() => onSelectPiece(p)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Todas as peças (colapsável) */}
          <details className="mt-2">
            <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
              Ver todas as {bookmarks.length} peças
            </summary>
            <div className="mt-2 max-h-60 overflow-y-auto space-y-1">
              {bookmarks.map((p) => (
                <PieceButton
                  key={p.index} piece={p}
                  selected={selectedPiece?.index === p.index}
                  onClick={() => onSelectPiece(p)}
                />
              ))}
            </div>
          </details>
        </div>
      )}

      {/* Preview da peça selecionada */}
      {selectedPiece && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 text-blue-800">
              <FileText className="h-5 w-5" />
              <span className="font-medium">Peça selecionada: {selectedPiece.title}</span>
            </div>
            <span className="text-sm text-blue-600">
              Páginas {selectedPiece.start_page}-{selectedPiece.end_page} ({selectedPiece.pages} pgs)
            </span>
          </div>
          {decisionText ? (
            <p className="text-sm text-green-700">
              <Check className="inline h-4 w-4 mr-1" />
              Texto extraído ({decisionText.length.toLocaleString()} caracteres)
            </p>
          ) : (
            <button
              onClick={onExtractText}
              disabled={textLoading}
              className="text-sm px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {textLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ChevronRight className="h-4 w-4" />}
              Extrair texto desta peça
            </button>
          )}
        </div>
      )}
    </div>
  )
}

function PieceButton({
  piece, selected, onClick, highlight,
}: {
  piece: PdfPiece; selected: boolean; onClick: () => void; highlight?: boolean
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-3 py-2 rounded-lg text-sm border transition-colors flex items-center justify-between ${
        selected
          ? 'bg-primary-50 border-primary-400 text-primary-800'
          : highlight
          ? 'bg-yellow-50 border-yellow-300 hover:bg-yellow-100'
          : 'bg-white border-gray-200 hover:bg-gray-50'
      }`}
    >
      <div className="flex items-center gap-2">
        {selected && <Check className="h-4 w-4 text-primary-600" />}
        <span className={highlight && !selected ? 'font-medium' : ''}>{piece.title}</span>
        <span className="text-xs px-2 py-0.5 bg-gray-100 rounded-full text-gray-500">{piece.type}</span>
      </div>
      <span className="text-xs text-gray-400">{piece.pages} pgs</span>
    </button>
  )
}

// ==================== STEP 2: Análise ====================

function StepAnalise({
  decisionText, extracted, extractLoading, obsDecisao, onObsChange, onAnalyze,
}: {
  decisionText: string
  extracted: Record<string, unknown> | null
  extractLoading: boolean
  obsDecisao: string
  onObsChange: (v: string) => void
  onAnalyze: () => void
}) {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Análise da Decisão</h2>

      {decisionText ? (
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Texto da decisão ({decisionText.length.toLocaleString()} chars)
            </span>
            <button
              onClick={onAnalyze}
              disabled={extractLoading}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
            >
              {extractLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              Analisar com IA
            </button>
          </div>
          <pre className="text-xs text-gray-600 max-h-48 overflow-auto whitespace-pre-wrap">
            {decisionText.slice(0, 2000)}...
          </pre>
        </div>
      ) : (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-amber-800">
          <AlertCircle className="inline h-5 w-5 mr-2" />
          Volte à etapa anterior e selecione uma peça para extrair o texto.
        </div>
      )}

      {extracted && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-yellow-800 mb-2">
            <Sparkles className="h-5 w-5" />
            <span className="font-medium">Dados extraídos pela IA — confirme cada campo</span>
          </div>
          <pre className="text-xs text-gray-600 overflow-auto max-h-64">
            {JSON.stringify(extracted, null, 2)}
          </pre>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Suas observações sobre a decisão
        </label>
        <textarea
          value={obsDecisao}
          onChange={(e) => onObsChange(e.target.value)}
          className="w-full h-40 border border-gray-300 rounded-lg p-4 focus:ring-2 focus:ring-primary-500 outline-none"
          placeholder="Adicione suas observações, pontos importantes, etc..."
        />
      </div>
    </div>
  )
}

// ==================== STEPS 3-6 (placeholders) ====================

function StepPedidos() {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Pedidos / Claims</h2>
      <p className="text-gray-500">Upload de tabela CSV/Excel ou cole o texto do DataJuri.</p>
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
      <p className="text-gray-500">A IA analisará a viabilidade de ED e sugerirá o recurso adequado.</p>
      <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-400">
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
      <div className="bg-gray-50 rounded-lg p-8 text-center text-gray-400">
        Prazos serão calculados com base na data de ciência e tipo de decisão
      </div>
    </div>
  )
}

function StepEmail() {
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
