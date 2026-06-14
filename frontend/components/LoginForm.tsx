import React, { useState } from "react";
import { loginUser } from "../src/api";

type Props = {
  onLogin: (user: { id: number; email: string; display_name: string }) => void;
};

export const LoginForm: React.FC<Props> = ({ onLogin }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await loginUser(email, password);
      onLogin(user);
    } catch {
      setError("Invalid email or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={submit} style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        style={{ padding: "6px 8px" }}
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        style={{ padding: "6px 8px" }}
      />
      <button type="submit" disabled={loading} style={{ padding: "6px 12px" }}>
        {loading ? "Logging in…" : "Log in"}
      </button>
      {error && <span style={{ color: "red" }}>{error}</span>}
    </form>
  );
};
