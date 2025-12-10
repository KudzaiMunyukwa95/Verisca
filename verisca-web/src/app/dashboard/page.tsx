"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Loader2, MapPin, Calendar, User } from "lucide-react";
import clsx from "clsx";
import api from "@/lib/api";

interface Claim {
    id: string;
    claim_number: string;
    status: string;
    peril_type: string;
    date_of_loss: string;
    field_name?: string;
    farm_name?: string;
    assessor_name?: string;
}

export default function DashboardPage() {
    const [claims, setClaims] = useState<Claim[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchClaims();
    }, []);

    const fetchClaims = async () => {
        try {
            // Fetching claims from backend (Assuming /claims endpoint exists and returns list)
            const response = await api.get("/claims/");
            setClaims(response.data);
        } catch (error) {
            console.error("Failed to fetch claims:", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex h-96 items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
                    <p className="mt-1 text-sm text-gray-500">
                        Overview of all active claims and assessments.
                    </p>
                </div>
                <Link
                    href="/claims/create"
                    className="flex items-center rounded-lg bg-secondary px-4 py-2 text-sm font-semibold text-primary transition-colors hover:bg-secondary-dark hover:text-white shadow-sm"
                >
                    <Plus className="mr-2 h-4 w-4" />
                    Create New Claim
                </Link>
            </div>

            {/* Stats Cards (Mockup) */}
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-900/5">
                    <p className="text-sm font-medium text-gray-500">Total Claims</p>
                    <p className="mt-2 text-3xl font-bold text-gray-900">{claims.length}</p>
                </div>
                <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-900/5">
                    <p className="text-sm font-medium text-gray-500">Pending Assessment</p>
                    <p className="mt-2 text-3xl font-bold text-orange-600">
                        {claims.filter(c => c.status === 'pending').length}
                    </p>
                </div>
                <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-900/5">
                    <p className="text-sm font-medium text-gray-500">Completed</p>
                    <p className="mt-2 text-3xl font-bold text-green-600">
                        {claims.filter(c => c.status === 'completed').length}
                    </p>
                </div>
            </div>

            {/* Claims List */}
            <div className="rounded-xl bg-white shadow-sm ring-1 ring-gray-900/5 overflow-hidden">
                <div className="border-b border-gray-200 px-6 py-4">
                    <h3 className="font-semibold text-gray-900">Recent Claims</h3>
                </div>

                {claims.length === 0 ? (
                    <div className="p-12 text-center text-gray-500">
                        No claims found. Create one to get started.
                    </div>
                ) : (
                    <ul role="list" className="divide-y divide-gray-100">
                        {claims.map((claim) => (
                            <li key={claim.id} className="relative flex justify-between gap-x-6 px-6 py-5 hover:bg-gray-50 transition-colors">
                                <div className="flex min-w-0 gap-x-4">
                                    <div className="min-w-0 flex-auto">
                                        <p className="text-sm font-semibold leading-6 text-gray-900">
                                            <Link href={`/claims/${claim.id}`} className="focus:outline-none">
                                                <span className="absolute inset-x-0 -top-px bottom-0" />
                                                Claim #{claim.claim_number}
                                            </Link>
                                        </p>
                                        <div className="mt-1 flex items-center text-xs leading-5 text-gray-500">
                                            <MapPin className="mr-1 h-3 w-3" />
                                            {claim.farm_name || 'Unknown Farm'} - {claim.field_name || 'Field 1'}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex shrink-0 items-center gap-x-4">
                                    <div className="hidden sm:flex sm:flex-col sm:items-end">
                                        <p className="text-sm leading-6 text-gray-900 flex items-center">
                                            <User className="h-3 w-3 mr-1 text-gray-400" /> {claim.assessor_name || 'Unassigned'}
                                        </p>
                                        <p className="mt-1 text-xs leading-5 text-gray-500 flex items-center">
                                            <Calendar className="h-3 w-3 mr-1" />
                                            Loss Date: {new Date(claim.date_of_loss).toLocaleDateString()}
                                        </p>
                                    </div>
                                    <span className={clsx(
                                        "inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset",
                                        claim.status === 'completed' ? "bg-green-50 text-green-700 ring-green-600/20" :
                                            claim.status === 'in_progress' ? "bg-blue-50 text-blue-700 ring-blue-600/20" :
                                                "bg-yellow-50 text-yellow-800 ring-yellow-600/20"
                                    )}>
                                        {claim.status || 'Pending'}
                                    </span>
                                    <svg className="h-5 w-5 flex-none text-gray-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                        <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
                                    </svg>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}
