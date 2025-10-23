import { use, useState } from "react";

export default function Login() {
    const [username, setUserName] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        try {
            const res = await fetch("/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ username, password }),
            });

            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.error || "Login failed");
            }

            const data = await res.json();
            console.log("Login success:", data);

            window.location.href = "/";

        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div>
            <h1>Login to CardVault</h1>
            <form onSubmit={handleSubmit}>
                <label>Username:</label><br />
                <input
                    type="text"
                    value={username}
                    onChange={(t) => setUserName(t.target.value)} 
                    required
                /><br /><br />
                <label>Password:</label><br />
                <input
                    type="text"
                    value={password}
                    onChange={(t) => setPassword(t.target.value)} 
                    required
                /><br /><br />

                <button type="submit">Login</button>
            </form>
            <p>Don't have an account? <a href="/register">Register here</a></p>

            {error && ( 
                <p style={{color:"red"}}><strong>{ error }</strong></p>
            )}
        </div>
    );
}