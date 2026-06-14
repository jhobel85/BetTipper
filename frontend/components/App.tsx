import React, { useState } from "react";
import { Leaderboard } from "./Leaderboard";
import { MatchList } from "./MatchList";
import { LoginForm } from "./LoginForm";

type User = { id: number; email: string; display_name: string };

const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto", padding: "16px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <h1 style={{ margin: 0 }}>MS 2026 Tipper</h1>
        {user ? (
          <span>
            👤 {user.display_name}{" "}
            <button onClick={() => setUser(null)} style={{ marginLeft: "8px" }}>Log out</button>
          </span>
        ) : null}
      </div>

      {!user ? (
        <>
          <h2>Log in</h2>
          <LoginForm onLogin={setUser} />
          <details style={{ marginTop: "16px", background: "#f5f5f5", padding: "8px 12px", borderRadius: "4px" }}>
            <summary style={{ cursor: "pointer" }}>ℹ️ No account yet? How to register</summary>
            <p>Use the API docs at <a href="http://localhost:8000/docs" target="_blank">http://localhost:8000/docs</a> → <code>POST /api/v1/auth/register</code></p>
            <pre style={{ background: "#eee", padding: "8px", overflowX: "auto" }}>{`curl -X POST http://localhost:8000/api/v1/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{"email":"you@example.com","password":"secret","display_name":"Your Name"}'`}</pre>
          </details>
        </>
      ) : (
        <>
          <MatchList />
          <hr />
          <h2>Leaderboard</h2>
          <Leaderboard />
        </>
      )}
    </div>
  );
};

export default App;
