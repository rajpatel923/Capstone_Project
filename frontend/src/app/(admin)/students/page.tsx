"use client"

import { useState } from "react"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { StudentTable } from "@/components/dashboard/student-table"
import { StudentForm } from "@/components/dashboard/student-form"
import { useStudents } from "@/hooks/use-students"
import { toast } from "sonner"
import type { StudentResponse } from "@/types/api"

export default function StudentsPage() {
  const { data, isLoading, createStudent, updateStudent, toggleActive, resetTotp } = useStudents()
  const [formOpen, setFormOpen] = useState(false)
  const [editStudent, setEditStudent] = useState<StudentResponse | undefined>()

  const handleEdit = (student: StudentResponse) => {
    setEditStudent(student)
    setFormOpen(true)
  }

  const handleFormClose = (v: boolean) => {
    if (!v) setEditStudent(undefined)
    setFormOpen(v)
  }

  const handleResetTotp = async (student: StudentResponse) => {
    try {
      const result = await resetTotp(student.id)
      // Show QR via a re-use of the student form in QR-only mode
      // Simplest UX: open form with provisioning_uri pre-set
      // We trigger this via a custom state
      setPendingQr(result.provisioning_uri)
    } catch (err) {
      toast.error((err as Error).message)
    }
  }

  const [pendingQr, setPendingQr] = useState<string | null>(null)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Students</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {data?.items.length ?? 0} students enrolled
          </p>
        </div>
        <Button onClick={() => { setEditStudent(undefined); setFormOpen(true) }}>
          <Plus className="mr-2 size-4" />
          New Student
        </Button>
      </div>

      <div className="rounded-lg border bg-white">
        <StudentTable
          students={data?.items ?? []}
          loading={isLoading}
          onEdit={handleEdit}
          onToggleActive={(s) => toggleActive(s.id, !s.active)}
          onResetTotp={handleResetTotp}
        />
      </div>

      {/* Create/Edit form */}
      <StudentForm
        open={formOpen}
        onOpenChange={handleFormClose}
        mode={editStudent ? "edit" : "create"}
        student={editStudent}
        onSubmit={(data) =>
          editStudent
            ? updateStudent(editStudent.id, data).then(() => ({}))
            : createStudent(data)
        }
      />

      {/* QR display after TOTP reset */}
      {pendingQr && (
        <StudentForm
          open={pendingQr !== null}
          onOpenChange={(v) => { if (!v) setPendingQr(null) }}
          mode="create"
          onSubmit={async () => ({ provisioning_uri: pendingQr! })}
        />
      )}
    </div>
  )
}
