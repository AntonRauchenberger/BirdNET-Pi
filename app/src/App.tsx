import { useState } from "react";
import "./css/root.css";
import Navbar from "./components/Navbar";
import Sync from "./tabs/sync";
import Map from "./tabs/map";
import Settings from "./tabs/settings";

function App() {
    const [activeTab, setActiveTab] = useState("MAP");

    const renderActiveTab = () => {
        switch (activeTab) {
            case "SYNC":
                return <Sync />;
            case "MAP":
                return <Map />;
            case "SETTINGS":
                return <Settings />;
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
