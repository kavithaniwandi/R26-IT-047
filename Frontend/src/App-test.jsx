import { useEffect } from "react";

function App() {
  useEffect(() => {
    console.log("App component mounted");
  }, []);

  return (
    <div style={{ padding: '20px', backgroundColor: 'lightblue' }}>
      <h1>Test App</h1>
      <p>If you can see this, React is working!</p>
    </div>
  );
}

export default App;
