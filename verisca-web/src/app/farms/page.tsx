"use client";

import { useState } from "react";
import { Plus, MapPin, Sprout, Tractor } from "lucide-react";

export default function FarmsPage() {
    // Mock Data for now (Replace with API fetch later)
    const [farms, setFarms] = useState([
        { id: 1, name: "Sunset Valley Farms", location: "Mashonaland West", ha: 120, fields: 4 },
        { id: 2, name: "Green Acres Estate", location: "Manicaland", ha: 450, fields: 12 },
    ]);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Farms & Fields</h1>
                    <p className="mt-1 text-sm text-gray-500">Manage farm profiles and field definitions.</p>
                </div>
                <button className="btn-primary">
                    <Plus className="mr-2 h-4 w-4" />
                    Add Farm
                </button>
            </div>

            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {farms.map((farm) => (
                    <div key={farm.id} className="bg-white rounded-xl shadow-sm ring-1 ring-gray-900/5 overflow-hidden hover:shadow-md transition-shadow">
                        <div className="p-6">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary/10 text-secondary-dark">
                                        <Tractor className="h-6 w-6" />
                                    </div>
                                    <h3 className="text-lg font-semibold text-gray-900">{farm.name}</h3>
                                </div>
                            </div>

                            <div className="mt-6 flex items-center gap-4 text-sm text-gray-500">
                                <div className="flex items-center gap-1">
                                    <MapPin className="h-4 w-4" />
                                    {farm.location}
                                </div>
                                <div className="flex items-center gap-1">
                                    <Sprout className="h-4 w-4" />
                                    {farm.ha} ha
                                </div>
                            </div>
                        </div>

                        <div className="bg-gray-50 px-6 py-3 border-t border-gray-100 flex items-center justify-between">
                            <span className="text-sm font-medium text-gray-600">{farm.fields} Fields Configured</span>
                            <button className="text-sm font-semibold text-primary hover:text-primary-light">
                                View Details
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
