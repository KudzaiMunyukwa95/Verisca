"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader2, Save } from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";

export default function CreateClaimPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [farms, setFarms] = useState<any[]>([]); // Should type properly
    const [selectedFarm, setSelectedFarm] = useState("");

    // Form State
    const [formData, setFormData] = useState({
        farm_id: "",
        field_id: "", // In real app, fetch fields when farm is selected
        peril_type: "Hail",
        date_of_loss: new Date().toISOString().split('T')[0],
        assessor_id: "", // We might want to list assessors too
    });

    // Mock fetching farms (In real app, call API)
    useEffect(() => {
        // api.get('/farms').then(...)
        // For prototype, we'll assume manual entry or mock
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            // 1. Create Claim via API
            // const res = await api.post('/claims', formData);

            // Mock success for now since we don't have full backend data
            console.log("Submitting claim:", formData);
            await new Promise(r => setTimeout(r, 1000)); // Simulate delay

            router.push("/dashboard");
        } catch (error) {
            console.error("Failed to create claim", error);
            alert("Failed to create claim");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto space-y-6">
            <div className="flex items-center gap-4">
                <Link
                    href="/dashboard"
                    className="p-2 rounded-full hover:bg-gray-100 text-gray-500"
                >
                    <ArrowLeft className="h-5 w-5" />
                </Link>
                <h1 className="text-2xl font-bold text-gray-900">Create New Claim</h1>
            </div>

            <div className="bg-white rounded-xl shadow-sm ring-1 ring-gray-900/5 p-8">
                <form onSubmit={handleSubmit} className="space-y-6">

                    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                        {/* Farm Selection (Mock) */}
                        <div className="col-span-2">
                            <label className="block text-sm font-medium text-gray-700">Farm Name</label>
                            <input
                                type="text"
                                required
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm py-2 px-3 border"
                                placeholder="e.g. Sunset Valley Farm"
                            // In real app this is a select dropdown
                            />
                        </div>

                        {/* Field Selection */}
                        <div className="col-span-2 sm:col-span-1">
                            <label className="block text-sm font-medium text-gray-700">Field Name/ID</label>
                            <input
                                type="text"
                                required
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm py-2 px-3 border"
                                placeholder="e.g. Field A-1"
                            />
                        </div>

                        {/* Peril Type */}
                        <div className="col-span-2 sm:col-span-1">
                            <label className="block text-sm font-medium text-gray-700">Peril Type</label>
                            <select
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm py-2 px-3 border bg-white"
                                value={formData.peril_type}
                                onChange={(e) => setFormData({ ...formData, peril_type: e.target.value })}
                            >
                                <option value="Hail">Hail</option>
                                <option value="Drought">Drought</option>
                                <option value="Fire">Fire</option>
                                <option value="Frost">Frost</option>
                            </select>
                        </div>

                        {/* Date of Loss */}
                        <div className="col-span-2">
                            <label className="block text-sm font-medium text-gray-700">Date of Loss</label>
                            <input
                                type="date"
                                required
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm py-2 px-3 border"
                                value={formData.date_of_loss}
                                onChange={(e) => setFormData({ ...formData, date_of_loss: e.target.value })}
                            />
                        </div>

                        {/* Assessor Assignment */}
                        <div className="col-span-2">
                            <label className="block text-sm font-medium text-gray-700">Assign Assessor (Email)</label>
                            <input
                                type="email"
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm py-2 px-3 border"
                                placeholder="assessor@verisca.com"
                                onChange={(e) => setFormData({ ...formData, assessor_id: e.target.value })}
                            />
                            <p className="mt-1 text-xs text-gray-500">
                                Enter the email of the assessor to assign instantly.
                            </p>
                        </div>
                    </div>

                    <div className="pt-4 flex justify-end gap-3">
                        <Link
                            href="/dashboard"
                            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                        >
                            Cancel
                        </Link>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary-light disabled:opacity-50"
                        >
                            {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                            Create Claim
                        </button>
                    </div>

                </form>
            </div>
        </div>
    );
}
