"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, MapPin, Calendar, User, CloudLightning, FileText, Loader2 } from "lucide-react";
import clsx from "clsx";
import api from "@/lib/api";

export default function ClaimDetailPage() {
    const params = useParams();
    const router = useRouter();
    const [claim, setClaim] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (params.id) {
            fetchClaim(params.id as string);
        }
    }, [params.id]);

    const fetchClaim = async (id: string) => {
        try {
            const response = await api.get(`/claims/${id}`);
            setClaim(response.data);
        } catch (error) {
            console.error("Failed to fetch claim", error);
            // alert("Failed to load claim details.");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        if (!confirm("Are you sure you want to delete this claim? This action cannot be undone.")) return;

        try {
            await api.delete(`/claims/${params.id}`);
            router.push("/dashboard");
        } catch (error) {
            console.error("Failed to delete claim", error);
            alert("Failed to delete claim.");
        }
    };

    if (loading) {
        return (
            <div className="flex h-96 items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (!claim) {
        return (
            <div className="flex flex-col items-center justify-center h-64 space-y-4">
                <p className="text-gray-500">Claim not found.</p>
                <Link href="/dashboard" className="text-primary hover:underline">
                    Back to Dashboard
                </Link>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Link href="/dashboard" className="p-2 rounded-full hover:bg-gray-100 text-gray-500 transition-colors">
                        <ArrowLeft className="h-5 w-5" />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Claim {claim.claim_number}</h1>
                        <p className="text-sm text-gray-500">View details and assessment status.</p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <span className={clsx(
                        "inline-flex items-center rounded-md px-3 py-1 text-sm font-medium ring-1 ring-inset",
                        claim.status === 'completed' ? "bg-green-50 text-green-700 ring-green-600/20" :
                            claim.status === 'in_progress' ? "bg-blue-50 text-blue-700 ring-blue-600/20" :
                                "bg-yellow-50 text-yellow-800 ring-yellow-600/20"
                    )}>
                        {claim.status}
                    </span>
                    <button
                        onClick={handleDelete}
                        className="rounded-md bg-white px-3 py-2 text-sm font-semibold text-red-600 shadow-sm ring-1 ring-inset ring-red-300 hover:bg-red-50"
                    >
                        Delete
                    </button>
                </div>
            </div>

            {/* Info Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                {/* Location & Assessor */}
                <div className="bg-white rounded-xl shadow-sm ring-1 ring-gray-900/5 p-6 space-y-6">
                    <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                        <MapPin className="h-5 w-5 text-gray-400" /> Location & Assignment
                    </h3>
                    <div className="space-y-4">
                        <div>
                            <p className="text-xs font-medium text-gray-500 uppercase">Farm / Policy Holder</p>
                            <p className="text-base text-gray-900">{claim.farm_name || "Unknown Farm"}</p>
                        </div>
                        <div>
                            <p className="text-xs font-medium text-gray-500 uppercase">Field Identifier</p>
                            <p className="text-base text-gray-900">{claim.field_name || "Unknown Field"}</p>
                        </div>
                        <div>
                            <p className="text-xs font-medium text-gray-500 uppercase">Assigned Assessor</p>
                            <p className="text-base text-gray-900 flex items-center gap-2">
                                <User className="h-4 w-4 text-gray-400" />
                                {claim.assessor_name || "Unassigned"}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Loss Details */}
                <div className="bg-white rounded-xl shadow-sm ring-1 ring-gray-900/5 p-6 space-y-6">
                    <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                        <CloudLightning className="h-5 w-5 text-gray-400" /> Loss Details
                    </h3>
                    <div className="space-y-4">
                        <div>
                            <p className="text-xs font-medium text-gray-500 uppercase">Peril Type</p>
                            <p className="text-base text-gray-900">{claim.peril_type}</p>
                        </div>
                        <div>
                            <p className="text-xs font-medium text-gray-500 uppercase">Date of Loss</p>
                            <p className="text-base text-gray-900">{new Date(claim.date_of_loss).toLocaleDateString()}</p>
                        </div>
                        <div>
                            <p className="text-xs font-medium text-gray-500 uppercase">Description</p>
                            <p className="text-sm text-gray-600 italic">
                                "{claim.loss_description || "No description provided."}"
                            </p>
                        </div>
                    </div>
                </div>

            </div>

            {/* Assessment History Mockup */}
            <div className="bg-white rounded-xl shadow-sm ring-1 ring-gray-900/5 p-6">
                <h3 className="font-semibold text-gray-900 flex items-center gap-2 mb-4">
                    <FileText className="h-5 w-5 text-gray-400" /> Assessment History
                </h3>
                <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg border border-dashed border-gray-200">
                    No assessments submitted yet.
                </div>
            </div>

        </div>
    );
}
