import { use, useState } from "react";

export default function Register() {
    const [username, setUserName] = useState("");
    const [password, setPassword] = useState("");
    const [email, setEmail] = useState("");
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        try {
            const res = await fetch("/register", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ username, email, password }),
            });

            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.error || "Registration failed");
            }

            const data = await res.json();
            console.log("Registration success:", data);

            window.location.href = "/login";

        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div>
            <h1>Create a CardVault Account</h1>
            <form onSubmit={handleSubmit}>
                <label>Username:</label><br />
                <input
                    type="text"
                    value={username}
                    onChange={(t) => setUserName(t.target.value)} 
                    required
                /><br /><br />
                <label>Email:</label><br />
                <input
                    type="text"
                    value={email}
                    onChange={(t) => setEmail(t.target.value)} 
                    required
                /><br /><br />
                <label>Password:</label><br />
                <input
                    type="text"
                    value={password}
                    onChange={(t) => setPassword(t.target.value)} 
                    required
                /><br /><br />

                <button type="submit">Register</button>
            </form>
            <p>Already have an account? <a href="/login">Login here</a></p>

            {error && ( 
                <p style={{color:"red"}}><strong>{ error }</strong></p>
            )}
        </div>
    );
}