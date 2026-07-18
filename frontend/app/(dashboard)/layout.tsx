import { AppHeader } from "@/components/app-shell/app-header";
import { AppSidebar } from "@/components/app-shell/app-sidebar";
import { CommandMenu } from "@/components/app-shell/command-menu";
import { MobileNavigation } from "@/components/app-shell/mobile-navigation";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-background flex min-h-svh w-full">
      <AppSidebar />
      <MobileNavigation />
      <div className="flex min-w-0 flex-1 flex-col">
        <AppHeader />
        <main id="main-content" tabIndex={-1} className="flex-1 outline-none">
          <div className="mx-auto w-full max-w-7xl px-4 py-6 md:px-6">{children}</div>
        </main>
      </div>
      <CommandMenu />
    </div>
  );
}
