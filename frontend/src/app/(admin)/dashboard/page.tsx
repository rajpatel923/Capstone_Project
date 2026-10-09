"use client"

import { Users, UserCheck, Server, Unlock } from "lucide-react"
import { StatsCard } from "@/components/dashboard/stats-card"
import { EventsTable } from "@/components/dashboard/events-table"
import { useStudents } from "@/hooks/use-students"
import { useDevices } from "@/hooks/use-devices"
import { useEvents } from "@/hooks/use-events"

export default function DashboardPage() {
  const { data: studentsData, isLoading: studentsLoading } = useStudents()
  const { data: devices, isLoading: devicesLoading } = useDevices()
  const { items: events, isLoading: eventsLoading } = useEvents()

  const totalStudents = studentsData?.items.length ?? 0
  const activeStudents = studentsData?.items.filter((s) => s.active).length ?? 0
  const totalDevices = devices.length
  const onlineDevices = devices.filter((d) => d.online).length

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold">Overview</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          FRZR BURN system status at a glance
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatsCard
          title="Total Students"
          value={totalStudents}
          icon={Users}
          loading={studentsLoading}
        />
        <StatsCard
          title="Active Students"
          value={activeStudents}
          icon={UserCheck}
          loading={studentsLoading}
        />
        <StatsCard
          title="Devices"
          value={totalDevices}
          icon={Server}
          loading={devicesLoading}
        />
        <StatsCard
          title="Online Now"
          value={onlineDevices}
          subtitle={`of ${totalDevices} devices`}
          icon={Unlock}
          loading={devicesLoading}
        />
      </div>

      {/* Recent events */}
      <div>
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          Recent Unlock Events
        </h2>
        <div className="rounded-lg border bg-white">
          <div className="p-4">
            <EventsTable
              events={events.slice(0, 10)}
              loading={eventsLoading}
              hasMore={false}
              onResultFilter={() => {}}
              onLoadMore={() => {}}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
