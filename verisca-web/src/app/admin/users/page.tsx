"use client";

import { useState, useEffect } from "react";
import { Plus, User, Shield, Mail, Loader2, Save, RefreshCw, AlertCircle, Copy } from "lucide-react";
import api from "@/lib/api";

export default function UserManagementPage() {
    const [users, setUsers] = useState<any[]>([]);
    const [isCreating, setIsCreating] = useState(false);
    const [loading, setLoading] = useState(false);
    const [fetching, setFetching] = useState(true);

    const [newUser, setNewUser] = useState({
        email: "",
        password: "",
        full_name: "",
        role_id: "" // UUID Required
    });

    // Fetch users on mount to 1) Confirm Connection and 2) Find Role IDs
    const fetchUsers = async () => {
        setFetching(true);
        try {
            const res = await api.get('/users/?limit=100');
            setUsers(res.data);
        } catch (error) {
            console.error("Failed to fetch users", error);
        } finally {
            setFetching(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleCreateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const names = newUser.full_name.split(' ');
            // Match schema: UserCreate
            const payload = {
                email: newUser.email,
                username: newUser.email, // Use email as username
                password: newUser.password,
                first_name: names[0],
                last_name: names.slice(1).join(' ') || '',
                role_id: newUser.role_id,
                is_active: true
            };

            await api.post('/users/', payload);

            alert("User created successfully!");
            setIsCreating(false);
            setNewUser({ email: "", password: "", full_name: "", role_id: "" });
            fetchUsers(); // Refresh list to show new user
        } catch (error: any) {
            console.error("Failed to create user", error);
            const msg = error.response?.data?.detail ? JSON.stringify(error.response.data.detail) : error.message;
            alert(`Failed: ${msg}`);
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

            {/* Connection Status & Role Helper */}
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
                <div>
                    <h4 className="font-semibold text-blue-900">Database Connection Status: {fetching ? 'Checking...' : (users.length > 0 ? 'Connected ✅' : 'No Data / Error ❌')}</h4>
                    <p className="text-sm text-blue-700 mt-1">
                        To create a user, we need a valid <strong>Role UUID</strong>.
                        Below is the list of existing users - please copy a <code>role_id</code> from a similar user (Insurer/Assessor) and paste it into the form.
                    </p>
                </div>
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
                        <div className="md:col-span-2">
                            <label className="label">Role ID (UUID)</label>
                            <div className="flex gap-2">
                                <input className="input font-mono text-sm" placeholder="Paste Role UUID here (e.g. 524e94...)" required
                                    value={newUser.role_id} onChange={e => setNewUser({ ...newUser, role_id: e.target.value })} />
                            </div>
                            <p className="text-xs text-gray-500 mt-1">Copy this from the "Role ID" column in the table below.</p>
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

            {/* User List Table */}
            <div className="bg-white rounded-xl shadow-sm ring-1 ring-gray-900/5 overflow-hidden">
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
                    <h3 className="text-lg font-medium text-gray-900">System Users ({users.length})</h3>
                    <button onClick={fetchUsers} className="p-2 hover:bg-gray-100 rounded-full text-gray-500" title="Refresh List">
                        <RefreshCw className={`h-5 w-5 ${fetching ? 'animate-spin' : ''}`} />
                    </button>
                </div>

                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role ID (Copy This)</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {users.map((user) => (
                                <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center">
                                            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold mr-3">
                                                {(user.first_name?.[0] || user.email?.[0] || 'U').toUpperCase()}
                                            </div>
                                            <div>
                                                <div className="text-sm font-medium text-gray-900">{user.first_name} {user.last_name}</div>
                                                <div className="text-sm text-gray-500">{user.email}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <button
                                            className="group flex items-center gap-2 rounded-md bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-600 font-mono hover:bg-primary/10 hover:text-primary transition-all active:scale-95"
                                            onClick={() => {
                                                navigator.clipboard.writeText(user.role_id);
                                                // Optional: Show toast
                                                setNewUser(prev => ({ ...prev, role_id: user.role_id }));
                                                if (!isCreating) setIsCreating(true);
                                            }}
                                            title="Click to copy Role ID to clipboard"
                                        >
                                            {user.role_id.substring(0, 8)}...{user.role_id.substring(user.role_id.length - 4)}
                                            <Copy className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                                        </button>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5 ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                            {user.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                            {!fetching && users.length === 0 && (
                                <tr>
                                    <td colSpan={3} className="px-6 py-12 text-center text-gray-500">
                                        <Shield className="mx-auto h-12 w-12 text-gray-300" />
                                        <h3 className="mt-2 text-sm font-semibold text-gray-900">No users found</h3>
                                        <p className="mt-1 text-sm text-gray-500">Get started by creating a new user.</p>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
