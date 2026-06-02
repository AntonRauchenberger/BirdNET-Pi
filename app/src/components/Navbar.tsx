import { MapPin, Bird, Settings, RefreshCw, Gauge } from "lucide-react";

const Navbar = (props: {
    activeTab: string;
    onTabChange: (tab: string) => void;
}) => {
    const tabs = ["SYNC", "BIRDS", "MAP", "BENCH", "SETTINGS"];

    const renderIcon = (tab: string) => {
        switch (tab) {
            case "SYNC":
                return <RefreshCw size={24} aria-hidden="true" />;
            case "BIRDS":
                return <Bird size={24} aria-hidden="true" />;
            case "MAP":
                return <MapPin size={24} aria-hidden="true" />;
            case "SETTINGS":
                return <Settings size={24} aria-hidden="true" />;
            case "BENCH":
                return <Gauge size={24} aria-hidden="true" />;
            default:
                return null;
        }
    };

    return (
        <nav className="bottom-nav" role="tablist">
            {tabs.map((tab) => {
                const isActive = props.activeTab === tab;

                return (
                    <button
                        key={tab}
                        type="button"
                        className={`tab-button${isActive ? " active" : ""}`}
                        role="tab"
                        aria-selected={isActive}
                        aria-current={isActive ? "page" : undefined}
                        onClick={() => props.onTabChange(tab)}
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
