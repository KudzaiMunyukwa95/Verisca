"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, Loader2, Save, MapPin, Calendar, CloudLightning, User } from "lucide-react";
import Link from "next/link";
import clsx from "clsx";
import api from "@/lib/api";

// Enterprise Wizard Steps
const STEPS = [
    { id: 1, name: "Location & Crop", icon: MapPin },
    { id: 2, name: "Loss Details", icon: CloudLightning },
    { id: 3, name: "Assignment", icon: User },
];

export default function CreateClaimPage() {
    const router = useRouter();
    const [currentStep, setCurrentStep] = useState(1);
    const [loading, setLoading] = useState(false);

    // Comprehensive Form State
    const [formData, setFormData] = useState({
        // Step 1
        farm_name: "",
        field_name: "",
        crop_type: "Maize",
        variety: "",
        planting_date: "",

        // Step 2
        peril_type: "Hail",
        date_of_loss: new Date().toISOString().split('T')[0],
        loss_description: "",
        estimated_damage: "",

        // Step 3
        assessor_email: "",
        priority: "Normal",
        notes: ""
    });

    const updateForm = (key: string, value: string) => {
        setFormData(prev => ({ ...prev, [key]: value }));
    };

    const nextStep = () => {
        if (currentStep < 3) setCurrentStep(c => c + 1);
    };

    const prevStep = () => {
        if (currentStep > 1) setCurrentStep(c => c - 1);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (currentStep < 3) {
            nextStep();
            return;
        }

        setLoading(true);

        try {
            console.log("Submitting Enterprise Claim:", formData);
            // await api.post('/claims', formData);
            await new Promise(r => setTimeout(r, 1500)); // Simulate robust processing
            router.push("/dashboard");
        } catch (error) {
            console.error("Failed to create claim", error);
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
                        <p className="text-sm text-gray-500">Enter details to initiate a new assessment request.</p>
                    </div>
                </div>
            </div>

            {/* Wizard Progress Bar */}
            <div className="relative">
                <div className="absolute top-1/2 left-0 w-full h-1 bg-gray-200 -translate-y-1/2 rounded-full" />
                <div className="absolute top-1/2 left-0 h-1 bg-primary -translate-y-1/2 rounded-full transition-all duration-500" style={{ width: `${((currentStep - 1) / 2) * 100}%` }} />

                <div className="relative flex justify-between">
                    {STEPS.map((step) => {
                        const isActive = currentStep >= step.id;
                        const isCurrent = currentStep === step.id;
                        return (
                            <div key={step.id} className="flex flex-col items-center bg-gray-50 px-2 z-10">
                                <div className={clsx(
                                    "flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all duration-300",
                                    isActive ? "border-primary bg-primary text-white" : "border-gray-300 bg-white text-gray-400"
                                )}>
                                    <step.icon className="h-5 w-5" />
                                </div>
                                <span className={clsx(
                                    "mt-2 text-xs font-medium uppercase tracking-wider",
                                    isCurrent ? "text-primary" : "text-gray-500"
                                )}>
                                    {step.name}
                                </span>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Form Card */}
            <div className="bg-white rounded-xl shadow-lg ring-1 ring-gray-900/5 overflow-hidden">
                <div className="p-8">
                    <form onSubmit={handleSubmit}>

                        {/* --- Step 1: Location & Crop --- */}
                        {currentStep === 1 && (
                            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
                                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                                    <MapPin className="h-5 w-5 text-secondary" />
                                    Location & Crop Information
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="col-span-2">
                                        <label className="label">Farm Name / Policy Holder</label>
                                        <input placeholder="Search farm or enter name..." className="input" autoFocus
                                            value={formData.farm_name} onChange={e => updateForm("farm_name", e.target.value)} required />
                                    </div>
                                    <div>
                                        <label className="label">Field Identifier</label>
                                        <input placeholder="e.g. Block A-4" className="input"
                                            value={formData.field_name} onChange={e => updateForm("field_name", e.target.value)} required />
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
                                    <div>
                                        <label className="label">Planting Date</label>
                                        <input type="date" className="input"
                                            value={formData.planting_date} onChange={e => updateForm("planting_date", e.target.value)} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* --- Step 2: Loss Details --- */}
                        {currentStep === 2 && (
                            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
                                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                                    <CloudLightning className="h-5 w-5 text-secondary" />
                                    Loss Information
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
                                        <label className="label">Date of Loss</label>
                                        <input type="date" className="input" required
                                            value={formData.date_of_loss} onChange={e => updateForm("date_of_loss", e.target.value)} />
                                    </div>
                                    <div className="col-span-2">
                                        <label className="label">Description of Event</label>
                                        <textarea className="input h-32 resize-none" placeholder="Describe the weather event and initial damage observations..."
                                            value={formData.loss_description} onChange={e => updateForm("loss_description", e.target.value)} />
                                    </div>
                                    <div>
                                        <label className="label">Est. Damage % (Optional)</label>
                                        <input type="number" placeholder="0-100" className="input" max="100" min="0"
                                            value={formData.estimated_damage} onChange={e => updateForm("estimated_damage", e.target.value)} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* --- Step 3: Assignment --- */}
                        {currentStep === 3 && (
                            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
                                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                                    <User className="h-5 w-5 text-secondary" />
                                    Resource Assignment
                                </h3>
                                <div className="grid grid-cols-1 gap-6">
                                    <div>
                                        <label className="label">Assign Assessor</label>
                                        <div className="mt-1 flex rounded-md shadow-sm">
                                            <span className="inline-flex items-center rounded-l-md border border-r-0 border-gray-300 bg-gray-50 px-3 text-gray-500 sm:text-sm">@</span>
                                            <input type="email" placeholder="assessor.email@verisca.com" className="input rounded-l-none" required
                                                value={formData.assessor_email} onChange={e => updateForm("assessor_email", e.target.value)} />
                                        </div>
                                        <p className="mt-1 text-xs text-gray-500">The assessor will be notified immediately via the mobile app.</p>
                                    </div>

                                    <div>
                                        <label className="label">Priority Level</label>
                                        <div className="mt-2 flex gap-4">
                                            {["Low", "Normal", "High", "Critical"].map(p => (
                                                <label key={p} className={clsx(
                                                    "flex-1 cursor-pointer rounded-lg border p-4 text-center text-sm font-medium transition-all hover:bg-gray-50",
                                                    formData.priority === p ? "border-primary bg-primary/5 text-primary ring-1 ring-primary" : "border-gray-200 text-gray-600"
                                                )}>
                                                    <input type="radio" name="priority" className="sr-only" value={p} checked={formData.priority === p} onChange={() => updateForm("priority", p)} />
                                                    {p}
                                                </label>
                                            ))}
                                        </div>
                                    </div>

                                    <div>
                                        <label className="label">Instructions / Notes</label>
                                        <textarea className="input h-24" placeholder="Any specific instructions for the assessor..."
                                            value={formData.notes} onChange={e => updateForm("notes", e.target.value)} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Footer Controls */}
                        <div className="mt-8 flex items-center justify-between border-t border-gray-100 pt-6">
                            {currentStep > 1 ? (
                                <button type="button" onClick={prevStep} className="btn-secondary">
                                    Back
                                </button>
                            ) : (<div></div>)}

                            <button type="submit" disabled={loading} className="btn-primary">
                                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                {currentStep === 3 ? "Create Case" : "Next Step"}
                                {currentStep < 3 && <ArrowRight className="ml-2 h-4 w-4" />}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}
