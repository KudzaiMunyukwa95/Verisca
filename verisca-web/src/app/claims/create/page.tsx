"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader2, Save, MapPin, Calendar, CloudLightning, User } from "lucide-react";
import Link from "next/link";
import clsx from "clsx";
import api from "@/lib/api";

export default function CreateClaimPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);

    // Simplified Form State (1-Step)
    const [formData, setFormData] = useState({
        farm_name: "",
        crop_type: "Maize",
        variety: "",

        peril_type: "Hail",
        date_of_loss: new Date().toISOString().split('T')[0], // Mapped to 'Notification Date' in UI
        loss_description: "",

        assessor_email: "",
        priority: "Normal",
        notes: ""
    });

    const updateForm = (key: string, value: string) => {
        setFormData(prev => ({ ...prev, [key]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            console.log("Submitting Simplified Claim:", formData);
            // API expects date_of_loss, we send the notification date value there
            await api.post('/claims/', formData);
            alert("Claim created successfully!");
            router.push("/dashboard");
        } catch (error: any) {
            console.error("Failed to create claim", error);
            const msg = error.response?.data?.detail ? JSON.stringify(error.response.data.detail) : error.message;
            alert(`Failed to create claim: ${msg}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="mx-auto max-w-4xl space-y-8">

            {/* Header */}
            <div className="flex items-center justify-between border-b border-gray-200 pb-6">
                <div className="flex items-center gap-4">
                    <Link href="/dashboard" className="p-2 rounded-full hover:bg-gray-100 text-gray-500 transition-colors">
                        <ArrowLeft className="h-5 w-5" />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">New Claim Case</h1>
                        <p className="text-sm text-gray-500">Initiate a new assessment request (Single Step).</p>
                    </div>
                </div>
            </div>

            {/* Form Card */}
            <div className="bg-white rounded-xl shadow-lg ring-1 ring-gray-900/5 overflow-hidden">
                <div className="p-8">
                    <form onSubmit={handleSubmit} className="space-y-8">

                        {/* Section 1: Location & Crop */}
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-4">
                                <MapPin className="h-5 w-5 text-secondary" />
                                Location & Crop
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="col-span-2">
                                    <label className="label">Farm Name / Policy Holder</label>
                                    <input placeholder="Search farm or enter name..." className="input" autoFocus
                                        value={formData.farm_name} onChange={e => updateForm("farm_name", e.target.value)} required />
                                </div>
                                <div>
                                    <label className="label">Crop Type</label>
                                    <select className="input" value={formData.crop_type} onChange={e => updateForm("crop_type", e.target.value)}>
                                        <option>Maize</option>
                                        <option>Wheat</option>
                                        <option>Soybeans</option>
                                        <option>Tobacco</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="label">Variety (Optional)</label>
                                    <input placeholder="e.g. SC 727" className="input"
                                        value={formData.variety} onChange={e => updateForm("variety", e.target.value)} />
                                </div>
                            </div>
                        </div>

                        <hr className="border-gray-100" />

                        {/* Section 2: Notification & Loss */}
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-4">
                                <CloudLightning className="h-5 w-5 text-secondary" />
                                Notification Details
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label className="label">Peril Type</label>
                                    <select className="input" value={formData.peril_type} onChange={e => updateForm("peril_type", e.target.value)}>
                                        <option>Hail</option>
                                        <option>Drought</option>
                                        <option>Flood</option>
                                        <option>Fire</option>
                                        <option>Frost</option>
                                        <option>Wind</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="label">Date of Notification</label>
                                    <input type="date" className="input" required
                                        value={formData.date_of_loss} onChange={e => updateForm("date_of_loss", e.target.value)} />
                                    <p className="mt-1 text-xs text-gray-400">Date the insurer was notified.</p>
                                </div>
                                <div className="col-span-2">
                                    <label className="label">Description of Event</label>
                                    <textarea className="input h-24 resize-none" placeholder="Describe the weather event..."
                                        value={formData.loss_description} onChange={e => updateForm("loss_description", e.target.value)} />
                                </div>
                            </div>
                        </div>

                        <hr className="border-gray-100" />

                        {/* Section 3: Assignment */}
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-4">
                                <User className="h-5 w-5 text-secondary" />
                                Resource Assignment
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label className="label">Assign Assessor</label>
                                    <div className="mt-1 flex rounded-md shadow-sm">
                                        <span className="inline-flex items-center rounded-l-md border border-r-0 border-gray-300 bg-gray-50 px-3 text-gray-500 sm:text-sm">@</span>
                                        <input type="email" placeholder="assessor.email@verisca.com" className="input rounded-l-none"
                                            value={formData.assessor_email} onChange={e => updateForm("assessor_email", e.target.value)} />
                                    </div>
                                </div>
                                <div>
                                    <label className="label">Priority Level</label>
                                    <select className="input" value={formData.priority} onChange={e => updateForm("priority", e.target.value)}>
                                        <option>Low</option>
                                        <option>Normal</option>
                                        <option>High</option>
                                        <option>Critical</option>
                                    </select>
                                </div>
                                <div className="col-span-2">
                                    <label className="label">Instructions / Notes</label>
                                    <textarea className="input h-24" placeholder="Specific instructions for the assessor..."
                                        value={formData.notes} onChange={e => updateForm("notes", e.target.value)} />
                                </div>
                            </div>
                        </div>

                        {/* Footer Controls */}
                        <div className="mt-8 flex items-center justify-end border-t border-gray-100 pt-6">
                            <button type="submit" disabled={loading} className="btn-primary w-full md:w-auto">
                                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                Create Case
                                <Save className="ml-2 h-4 w-4" />
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
