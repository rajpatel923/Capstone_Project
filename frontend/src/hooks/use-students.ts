"use client"

import { useState, useEffect, useCallback } from "react"
import { useAuth } from "@clerk/nextjs"
import { toast } from "sonner"
import { studentsApi } from "@/lib/api/students"
import type {
  StudentListResponse,
  StudentCreate,
  StudentUpdate,
  StudentEnrollResponse,
  BulkEnrollRow,
  BulkEnrollResponse,
} from "@/types/api"
import { APIError } from "@/lib/api/client"

export function useStudents() {
  const { getToken } = useAuth()
  const [data, setData] = useState<StudentListResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<APIError | null>(null)

  const fetch = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await studentsApi.list(getToken)
      setData(result)
    } catch (e) {
      setError(e as APIError)
    } finally {
      setIsLoading(false)
    }
  }, [getToken])

  useEffect(() => {
    fetch()
  }, [fetch])

  const createStudent = async (body: StudentCreate): Promise<StudentEnrollResponse> => {
    const result = await studentsApi.create(getToken, body)
    toast.success(`Student ${result.full_name} enrolled`)
    await fetch()
    return result
  }

  const updateStudent = async (id: number, body: StudentUpdate) => {
    const result = await studentsApi.update(getToken, id, body)
    toast.success("Student updated")
    await fetch()
    return result
  }

  const toggleActive = async (id: number, active: boolean) => {
    const result = await studentsApi.update(getToken, id, { active })
    toast.success(active ? "Student activated" : "Student deactivated")
    await fetch()
    return result
  }

  const resetTotp = async (id: number): Promise<StudentEnrollResponse> => {
    const result = await studentsApi.resetTotp(getToken, id)
    toast.success("TOTP secret reset")
    return result
  }

  const deleteStudent = async (id: number) => {
    await studentsApi.delete(getToken, id)
    toast.success("Student deleted")
    await fetch()
  }

  const bulkEnroll = async (students: BulkEnrollRow[]): Promise<BulkEnrollResponse> => {
    const result = await studentsApi.bulkEnroll(getToken, students)
    if (result.enrolled_count > 0) {
      toast.success(`Enrolled ${result.enrolled_count} student${result.enrolled_count === 1 ? "" : "s"}`)
      await fetch()
    }
    return result
  }

  return { data, isLoading, error, createStudent, updateStudent, toggleActive, resetTotp, deleteStudent, bulkEnroll, refetch: fetch }
}
