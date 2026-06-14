import React, { useState } from "react";
import { postTip } from "../src/api";

type Props = {
  matchId: number;
};

export const TipForm: React.FC<Props> = ({ matchId }) => {
  const [value, setValue] = useState("1");
  const [status, setStatus] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("Saving...");
    try {
      await postTip(matchId, value);
      setStatus("Saved");
    } catch {
      setStatus("Error");
    }
  };

  return (
    <form onSubmit={submit} style={{ marginTop: "4px" }}>
      <label>
        Your tip (1/X/2):{" "}
        <input value={value} onChange={(e) => setValue(e.target.value.toUpperCase())} maxLength={1} />
      </label>
      <button type="submit" style={{ marginLeft: "8px" }}>
        Save
      </button>
      {status && <span style={{ marginLeft: "8px" }}>{status}</span>}
    </form>
  );
};
