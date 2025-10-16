// Minimal React component that mirrors the Python TaskService logic.
import { useMemo } from "react";

const App = () => {
  const tasks = useMemo(
    () => [
      { name: "Wire CLI into project automation", completed: true },
      { name: "Demonstrate mixed language support", completed: false },
    ],
    []
  );

  return (
    <main>
      <h1>Sample cross-stack project</h1>
      <ul>
        {tasks.map((task) => (
          <li key={task.name}>
            <span>{task.name}</span>
            <strong>{task.completed ? " ✅" : " ⏳"}</strong>
          </li>
        ))}
      </ul>
    </main>
  );
};

export default App;
