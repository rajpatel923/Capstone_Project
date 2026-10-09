"use client"

import { use, useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, RotateCcw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { LedgerSheet } from "@/components/dashboard/ledger-sheet"
import { StudentForm } from "@/components/dashboard/student-form"
import { useStudent } from "@/hooks/use-student"
import { studentsApi } from "@/lib/api/students"
import { useAuth } from "@clerk/nextjs"
import { toast } from "sonner"
import type { StudentEnrollResponse } from "@/types/api"

export default function StudentDetailPage(props: PageProps<"/students/[id]">) {
  const { id } = use(props.params)
  const router = useRouter()
  const { getToken } = useAuth()
  const { student, ledger, isLoading, refetch } = useStudent(Number(id))

  const [ledgerOpen, setLedgerOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [qrResult, setQrResult] = useState<StudentEnrollResponse | null>(null)

  const handleResetTotp = async () => {
    try {
      const result = await studentsApi.resetTotp(getToken, Number(id))
      toast.success("TOTP reset")
      setQrResult(result)
    } catch (err) {
      toast.error((err as Error).message)
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  if (!student) {
    return <p className="text-sm text-muted-foreground">Student not found.</p>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="size-4" />
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold">{student.full_name}</h1>
              <Badge variant={student.active ? "default" : "outline"}>
                {student.active ? "Active" : "Inactive"}
              </Badge>
            </div>
            <p className="mt-0.5 text-sm text-muted-foreground">{student.email}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => setEditOpen(true)}>
            Edit
          </Button>
          <Button variant="outline" onClick={handleResetTotp}>
            <RotateCcw className="mr-2 size-4" />
            Reset TOTP
          </Button>
        </div>
      </div>

      {/* Info card */}
      <div className="rounded-lg border bg-white px-6 py-5">
        <dl className="grid grid-cols-3 gap-6">
          <div>
            <dt className="text-xs text-muted-foreground uppercase tracking-wider">Member ID</dt>
            <dd className="mt-1 font-mono text-sm font-semibold">{student.member_id}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground uppercase tracking-wider">Credits</dt>
            <dd className="mt-1 text-sm font-semibold">
              {ledger?.balance ?? "—"}
              <button
                onClick={() => setLedgerOpen(true)}
                className="ml-2 text-xs text-primary underline-offset-2 hover:underline"
              >
                View ledger
              </button>
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground uppercase tracking-wider">Enrolled</dt>
            <dd className="mt-1 text-sm">{new Date(student.created_at).toLocaleDateString()}</dd>
          </div>
        </dl>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="ledger">
        <TabsList>
          <TabsTrigger value="ledger">Credit Ledger</TabsTrigger>
        </TabsList>
        <TabsContent value="ledger" className="mt-4">
          <div className="rounded-lg border bg-white p-4">
            <dl className="space-y-2">
              {(ledger?.entries ?? []).length === 0 && (
                <p className="py-8 text-center text-sm text-muted-foreground">No transactions</p>
              )}
              {(ledger?.entries ?? []).map((entry) => (
                <div key={entry.id} className="flex items-center justify-between border-b py-2 last:border-0">
                  <div>
                    <p className="text-sm capitalize">{entry.reason.replace(/_/g, " ")}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(entry.created_at).toLocaleString()}
                    </p>
                  </div>
                  <span className={`font-mono text-sm font-semibold ${entry.delta > 0 ? "text-green-600" : "text-red-500"}`}>
                    {entry.delta > 0 ? `+${entry.delta}` : entry.delta}
                  </span>
                </div>
              ))}
            </dl>
          </div>
        </TabsContent>
      </Tabs>

      <LedgerSheet
        open={ledgerOpen}
        onOpenChange={setLedgerOpen}
        ledger={ledger}
        studentName={student.full_name}
      />

      <StudentForm
        open={editOpen}
        onOpenChange={setEditOpen}
        mode="edit"
        student={student}
        onSubmit={async (data) => {
          await studentsApi.update(getToken, Number(id), data)
          await refetch()
          return {}
        }}
      />

      {/* QR after TOTP reset */}
      {qrResult && (
        <StudentForm
          open={true}
          onOpenChange={(v) => { if (!v) setQrResult(null) }}
          mode="create"
          onSubmit={async () => qrResult}
        />
      )}
    </div>
  )
}
