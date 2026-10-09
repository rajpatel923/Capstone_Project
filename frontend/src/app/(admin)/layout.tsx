import { currentUser } from "@clerk/nextjs/server"
import { redirect } from "next/navigation"
import { Sidebar } from "@/components/dashboard/sidebar"

export default async function AdminLayout({ children }: LayoutProps<"/">) {
  const user = await currentUser()

  if (!user) {
    redirect("/sign-in")
  }

  if ((user.publicMetadata as { role?: string }).role !== "admin") {
    redirect("/sign-in?error=not-admin")
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-zinc-50 p-6">{children}</main>
    </div>
  )
}
