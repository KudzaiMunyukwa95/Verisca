"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, FilePlus, Users, LogOut, Sprout } from "lucide-react";
import clsx from "clsx";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const pathname = usePathname();
    const router = useRouter();

    const handleLogout = () => {
        localStorage.removeItem("verisca_token");
        localStorage.removeItem("verisca_user");
        router.push("/");
    };

    const navItems = [
        { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
        { name: "New Claim", href: "/claims/create", icon: FilePlus },
        { name: "Farms & Fields", href: "/farms", icon: Sprout },
        { name: "User Management", href: "/admin/users", icon: Users },
    ];

    return (
        <div className="flex min-h-screen bg-gray-50">
            {/* Sidebar */}
            <aside className="fixed inset-y-0 left-0 z-50 w-64 bg-primary text-white shadow-lg">
                {/* Logo Area */}
                <div className="flex h-20 items-center justify-center border-b border-primary-light px-6">
                    <img src="/logo.png" alt="Yieldera Logo" className="h-12 w-auto object-contain" />
                </div>

                {/* Navigation */}
                <nav className="flex-1 space-y-1 px-3 py-6">
                    {navItems.map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                className={clsx(
                                    "flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                                    isActive
                                        ? "bg-primary-light text-white shadow-sm"
                                        : "text-gray-300 hover:bg-primary-light/50 hover:text-white"
                                )}
                            >
                                <item.icon className="mr-3 h-5 w-5 flex-shrink-0" />
                                {item.name}
                            </Link>
                        );
                    })}
                </nav>

                {/* Footer / Logout */}
                <div className="border-t border-primary-light p-4">
                    <button
                        onClick={handleLogout}
                        className="flex w-full items-center rounded-lg px-3 py-2 text-sm font-medium text-gray-300 transition-colors hover:bg-red-500/10 hover:text-red-400"
                    >
                        <LogOut className="mr-3 h-5 w-5" />
                        Sign Out
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="ml-64 flex-1 p-8">
                <div className="mx-auto max-w-7xl">
                    {children}
                </div>
            </main>
        </div>
    );
}
