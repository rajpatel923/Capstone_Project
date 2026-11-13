"use client"

import { useState, useRef, useCallback } from "react"
import { Upload, CheckCircle2, Minus } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import type { BulkEnrollRow, BulkEnrollResponse, BulkEnrollRowResult } from "@/types/api"

type Step = "pick" | "preview" | "importing" | "results"

type ParsedRow = BulkEnrollRow & { _rowIndex: number }

type ParseResult = {
  rows: ParsedRow[]
  formatDetected: "canvas-people" | "canvas-gradebook" | "generic" | "unknown"
  warnings: string[]
}

function parseCSV(text: string): ParseResult {
  const lines = text
    .split("\n")
    .map((l) => l.trimEnd().replace(/\r$/, ""))
    .filter(Boolean)

  if (lines.length < 2) {
    return { rows: [], formatDetected: "unknown", warnings: ["File appears empty or has no data rows"] }
  }

  const headers = lines[0].split(",").map((h) => h.trim().replace(/^"|"$/g, ""))

  const nameIdx = headers.findIndex((h) => h === "Name" || h === "Student")
  const emailIdx = headers.findIndex((h) => h === "Email" || h === "Email Address")

  let formatDetected: ParseResult["formatDetected"] = "generic"
  if (headers.includes("Name") && headers.includes("Email") && headers.includes("Section")) {
    formatDetected = "canvas-people"
  } else if (
    headers.includes("Student") &&
    headers.includes("Email Address") &&
    headers.includes("SIS User ID")
  ) {
    formatDetected = "canvas-gradebook"
  }

  const warnings: string[] = []
  if (nameIdx === -1) warnings.push('Could not find a "Name" or "Student" column')
  if (emailIdx === -1) warnings.push('Could not find an "Email" or "Email Address" column')
  if (nameIdx === -1 || emailIdx === -1) {
    return { rows: [], formatDetected, warnings }
  }

  const rows: ParsedRow[] = []
  for (let i = 1; i < lines.length; i++) {
    const cells = lines[i].split(",").map((c) => c.trim().replace(/^"|"$/g, ""))
    const full_name = cells[nameIdx] ?? ""
    const email = cells[emailIdx] ?? ""
    if (full_name === "Points Possible" || full_name === "" || email === "") continue
    rows.push({ full_name, email, _rowIndex: i })
  }

  return { rows, formatDetected, warnings }
}

const FORMAT_LABELS: Record<ParseResult["formatDetected"], string | null> = {
  "canvas-people": "Canvas People export",
  "canvas-gradebook": "Canvas Gradebook export",
  generic: null,
  unknown: null,
}

const STATUS_VARIANTS: Record<
  BulkEnrollRowResult["status"],
  "default" | "secondary" | "destructive"
> = {
  enrolled: "default",
  skipped: "secondary",
  error: "destructive",
}

type Props = {
  open: boolean
  onOpenChange: (v: boolean) => void
  onBulkEnroll: (students: BulkEnrollRow[]) => Promise<BulkEnrollResponse>
}

export function BulkUploadDialog({ open, onOpenChange, onBulkEnroll }: Props) {
  const [step, setStep] = useState<Step>("pick")
  const [isDragging, setIsDragging] = useState(false)
  const [parseResult, setParseResult] = useState<ParseResult | null>(null)
  const [enrollResult, setEnrollResult] = useState<BulkEnrollResponse | null>(null)
  const [parseError, setParseError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const reset = () => {
    setStep("pick")
    setIsDragging(false)
    setParseResult(null)
    setEnrollResult(null)
    setParseError(null)
  }

  const handleClose = (v: boolean) => {
    if (!v) reset()
    onOpenChange(v)
  }

  const handleFile = useCallback((file: File) => {
    if (!file.name.endsWith(".csv") && file.type !== "text/csv") {
      setParseError("Please select a .csv file")
      return
    }
    setParseError(null)
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result as string
      const result = parseCSV(text)
      setParseResult(result)
      setStep("preview")
    }
    reader.onerror = () => setParseError("Failed to read file")
    reader.readAsText(file)
  }, [])

  const handleImport = async () => {
    if (!parseResult) return
    setStep("importing")
    try {
      const result = await onBulkEnroll(
        parseResult.rows.map(({ full_name, email }) => ({ full_name, email })),
      )
      setEnrollResult(result)
      setStep("results")
    } catch (err) {
      setParseError((err as Error).message)
      setStep("pick")
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-2xl">
        {step === "pick" && (
          <>
            <DialogHeader>
              <DialogTitle>Import Students from CSV</DialogTitle>
              <DialogDescription>
                Upload a Canvas People export or any CSV with{" "}
                <code className="text-xs">Name</code> and{" "}
                <code className="text-xs">Email</code> columns. Each student will be enrolled
                and emailed their TOTP setup code.
              </DialogDescription>
            </DialogHeader>

            <div
              className={`mt-2 flex flex-col items-center gap-4 rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
                isDragging ? "border-primary bg-primary/5" : "border-zinc-200"
              }`}
              onDragOver={(e) => {
                e.preventDefault()
                setIsDragging(true)
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(e) => {
                e.preventDefault()
                setIsDragging(false)
                const file = e.dataTransfer.files[0]
                if (file) handleFile(file)
              }}
            >
              <div className="flex size-12 items-center justify-center rounded-full bg-zinc-100">
                <Upload className="size-5 text-zinc-500" />
              </div>
              <div>
                <p className="text-sm font-medium">Drop your CSV here</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  or click below to browse
                </p>
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
              >
                Browse file
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) handleFile(file)
                  e.target.value = ""
                }}
              />
            </div>

            {parseError && (
              <p className="text-sm text-destructive">{parseError}</p>
            )}
          </>
        )}

        {step === "preview" && parseResult && (
          <>
            <DialogHeader>
              <div className="flex items-center gap-2">
                <DialogTitle>
                  Preview — {parseResult.rows.length} student{parseResult.rows.length !== 1 ? "s" : ""} detected
                </DialogTitle>
                {FORMAT_LABELS[parseResult.formatDetected] && (
                  <Badge variant="secondary" className="text-xs font-normal">
                    {FORMAT_LABELS[parseResult.formatDetected]}
                  </Badge>
                )}
              </div>
            </DialogHeader>

            {parseResult.warnings.map((w, i) => (
              <p key={i} className="text-sm text-amber-600">
                ⚠ {w}
              </p>
            ))}

            {parseResult.rows.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                No valid rows found. Check that your CSV has Name and Email columns.
              </p>
            ) : (
              <div className="max-h-72 overflow-y-auto rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Full Name</TableHead>
                      <TableHead>Email</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {parseResult.rows.map((row) => (
                      <TableRow key={row._rowIndex}>
                        <TableCell className="font-medium">{row.full_name}</TableCell>
                        <TableCell className="text-muted-foreground">{row.email}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={() => setStep("pick")}>
                Back
              </Button>
              <Button
                onClick={handleImport}
                disabled={parseResult.rows.length === 0}
              >
                Import {parseResult.rows.length} student{parseResult.rows.length !== 1 ? "s" : ""}
              </Button>
            </DialogFooter>
          </>
        )}

        {step === "importing" && (
          <>
            <DialogHeader>
              <DialogTitle>Importing…</DialogTitle>
            </DialogHeader>
            <div className="flex flex-col gap-3 py-6">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-8 w-full" />
              ))}
            </div>
          </>
        )}

        {step === "results" && enrollResult && (
          <>
            <DialogHeader>
              <DialogTitle>Import Complete</DialogTitle>
            </DialogHeader>

            <div className="flex items-center gap-2">
              <Badge>{enrollResult.enrolled_count} enrolled</Badge>
              {enrollResult.skipped_count > 0 && (
                <Badge variant="destructive">
                  {enrollResult.skipped_count} skipped
                </Badge>
              )}
            </div>

            {!enrollResult.email_enabled && (
              <p className="text-sm text-muted-foreground">
                Emails were not sent — SMTP is not configured. Students will need their TOTP QR codes shared manually.
              </p>
            )}

            <div className="max-h-72 overflow-y-auto rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Member ID</TableHead>
                    <TableHead className="text-center">Email Sent</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {enrollResult.results.map((row, i) => (
                    <TableRow key={i}>
                      <TableCell className="font-medium">{row.full_name}</TableCell>
                      <TableCell className="text-muted-foreground">{row.email}</TableCell>
                      <TableCell>
                        <Badge variant={STATUS_VARIANTS[row.status]}>
                          {row.status}
                          {row.reason ? ` — ${row.reason}` : ""}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {row.member_id ?? "—"}
                      </TableCell>
                      <TableCell className="text-center">
                        {row.email_sent ? (
                          <CheckCircle2 className="mx-auto size-4 text-green-600" />
                        ) : (
                          <Minus className="mx-auto size-4 text-zinc-300" />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <DialogFooter>
              <Button onClick={() => handleClose(false)}>Done</Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
