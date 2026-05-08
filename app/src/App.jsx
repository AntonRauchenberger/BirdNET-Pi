import { useState } from "react";
import "./css/root.css";
import Navbar from "./components/Navbar";
import Sync from "./tabs/sync";

function App() {
    const [activeTab, setActiveTab] = useState("SYNC");

    const renderActiveTab = () => {
        switch (activeTab) {
            case "SYNC":
                return <Sync />;
            default:
                return <div>Tab not found</div>;
        }
    };

    return (
        <div className="app-shell">
            <main className="app-content" role="main">
                {renderActiveTab()}
            </main>
            <Navbar activeTab={activeTab} onTabChange={setActiveTab} />
        </div>
    );
}

export default App;
