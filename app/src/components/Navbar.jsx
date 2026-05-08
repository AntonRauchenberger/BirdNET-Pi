import { MapPin, Bird, Settings, RefreshCw } from "lucide-react";

const Navbar = ({ activeTab, onTabChange }) => {
    const tabs = ["SYNC", "BIRDS", "MAP", "SETTINGS"];

    const renderIcon = (tab) => {
        switch (tab) {
            case "SYNC":
                return <RefreshCw size={24} aria-hidden="true" />;
            case "BIRDS":
                return <Bird size={24} aria-hidden="true" />;
            case "MAP":
                return <MapPin size={24} aria-hidden="true" />;
            case "SETTINGS":
                return <Settings size={24} aria-hidden="true" />;
            default:
                return null;
        }
    };

    return (
        <nav className="bottom-nav" aria-label="Hauptnavigation" role="tablist">
            {tabs.map((tab) => {
                const isActive = activeTab === tab;

                return (
                    <button
                        key={tab}
                        type="button"
                        className={`tab-button${isActive ? " active" : ""}`}
                        role="tab"
                        aria-selected={isActive}
                        aria-current={isActive ? "page" : undefined}
                        onClick={() => onTabChange(tab)}
                    >
                        {renderIcon(tab)}
                        <span>{tab}</span>
                    </button>
                );
            })}
        </nav>
    );
};

export default Navbar;
