"use client";

import { useState } from "react";
import { Plus, User, Shield, Mail, Loader2, Save } from "lucide-react";
import api from "@/lib/api";

export default function UserManagementPage() {
    const [users, setUsers] = useState<any[]>([]); // In real app, fetch from API
    const [isCreating, setIsCreating] = useState(false);
    const [loading, setLoading] = useState(false);

    const [newUser, setNewUser] = useState({
        email: "",
        password: "",
        full_name: "",
        role: "assessor" // surveyor, admin, insurer
    });

    const handleCreateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            // This endpoint depends on backend implementation. 
            // Usually POST /auth/register or POST /users
            await api.post('/auth/register', {
                email: newUser.email,
                password: newUser.password,
                full_name: newUser.full_name,
                role: newUser.role
            });

            alert("User created successfully!");
            setIsCreating(false);
            setNewUser({ email: "", password: "", full_name: "", role: "assessor" });
            // Fetch users again
        } catch (error) {
            console.error("Failed to create user", error);
            alert("Failed to create user. Ensure you are an Admin.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
                    <p className="mt-1 text-sm text-gray-500">Create and manage Insurers and Assessors.</p>
                </div>
                <button
                    onClick={() => setIsCreating(!isCreating)}
                    className="btn-primary"
                >
                    <Plus className="mr-2 h-4 w-4" />
                    Create New User
                </button>
            </div>

            {/* Create User Form */}
            {isCreating && (
                <div className="bg-white rounded-xl shadow-lg ring-1 ring-gray-900/5 p-6 animate-in slide-in-from-top-4">
                    <h3 className="text-lg font-semibold mb-4">New User Details</h3>
                    <form onSubmit={handleCreateUser} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="label">Full Name</label>
                            <input className="input" placeholder="John Doe" required
                                value={newUser.full_name} onChange={e => setNewUser({ ...newUser, full_name: e.target.value })} />
                        </div>
                        <div>
                            <label className="label">Email Address</label>
                            <input type="email" className="input" placeholder="john@verisca.com" required
                                value={newUser.email} onChange={e => setNewUser({ ...newUser, email: e.target.value })} />
                        </div>
                        <div>
                            <label className="label">Role</label>
                            <select className="input" value={newUser.role} onChange={e => setNewUser({ ...newUser, role: e.target.value })}>
                                <option value="assessor">Assessor (Mobile User)</option>
                                <option value="insurer">Insurer (Portal User)</option>
                                <option value="surveyor">Surveyor</option>
                                <option value="admin">System Admin</option>
                            </select>
                        </div>
                        <div>
                            <label className="label">Temporary Password</label>
                            <input type="text" className="input" placeholder="Secret123!" required
                                value={newUser.password} onChange={e => setNewUser({ ...newUser, password: e.target.value })} />
                        </div>
                        <div className="md:col-span-2 flex justify-end gap-3 mt-4">
                            <button type="button" onClick={() => setIsCreating(false)} className="btn-secondary">Cancel</button>
                            <button type="submit" disabled={loading} className="btn-primary">
                                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                Create User
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* User List Placeholder */}
            <div className="bg-white rounded-xl shadow-sm ring-1 ring-gray-900/5 overflow-hidden">
                <div className="p-12 text-center text-gray-500">
                    <Shield className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                    <h3 className="text-lg font-medium text-gray-900">System Users</h3>
                    <p>User list will appear here once connected to the backend.</p>
                </div>
            </div>
        </div>
    );
}
