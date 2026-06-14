import React, { useState } from "react";
import { registerUser } from "../src/api";

export const RegisterForm: React.FC = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage(null);
    setError(null);

    try {
      const user = await registerUser(email, password, displayName);
      setSuccessMessage(`Registered as ${user.display_name}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Registration failed");
    }
  };

  return (
    <form onSubmit={submit}>
      <div style={{ marginBottom: "8px" }}>
        <label>
          Email: <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        </label>
      </div>
      <div style={{ marginBottom: "8px" }}>
        <label>
          Password: <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
        </label>
      </div>
      <div style={{ marginBottom: "8px" }}>
        <label>
          Display name:{" "}
          <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} required />
        </label>
      </div>
      <button type="submit">Register</button>
      {successMessage && <div>{successMessage}</div>}
      {error && <div style={{ color: "red" }}>{error}</div>}
    </form>
  );
};
