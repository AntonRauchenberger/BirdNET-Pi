type SwitchProps = {
    checked: boolean;
    onChange?: (checked: boolean) => void;
    disabled?: boolean;
    ariaLabel?: string;
};

const Switch = ({
    checked,
    onChange,
    disabled = false,
    ariaLabel = "Toggle setting",
}: SwitchProps) => {
    const handleToggle = () => {
        if (!disabled) {
            onChange?.(!checked);
        }
    };

    const trackStyle = {
        width: "3.35rem",
        height: "1.9rem",
        border: "none",
        borderRadius: "999px",
        padding: "0.2rem",
        display: "flex",
        alignItems: "center",
        cursor: disabled ? "not-allowed" : "pointer",
        background: checked
            ? "var(--gradiant-clay)"
            : "color-mix(in oklab, var(--black-forest) 14%, var(--cornsilk))",
        boxShadow: checked
            ? "0 6px 18px rgba(188, 108, 37, 0.32)"
            : "inset 0 0 0 1px rgba(40, 54, 24, 0.15)",
        transition:
            "background-color 300ms cubic-bezier(0.16, 1, 0.3, 1), box-shadow 280ms cubic-bezier(0.16, 1, 0.3, 1), opacity 200ms ease",
        opacity: disabled ? 0.5 : 1,
    } as const;

    const thumbStyle = {
        width: "1.5rem",
        height: "1.5rem",
        borderRadius: "50%",
        backgroundColor: "var(--card)",
        boxShadow: checked
            ? "0 2px 8px rgba(188, 108, 37, 0.35)"
            : "0 2px 8px rgba(40, 54, 24, 0.22)",
        transform: checked ? "translateX(1.45rem)" : "translateX(0)",
        willChange: "transform",
        transition:
            "transform 300ms cubic-bezier(0.16, 1, 0.3, 1), box-shadow 280ms cubic-bezier(0.16, 1, 0.3, 1)",
    } as const;

    return (
        <button
            type="button"
            role="switch"
            aria-checked={checked}
            aria-label={ariaLabel}
            onClick={handleToggle}
            disabled={disabled}
            style={trackStyle}
        >
            <span aria-hidden="true" style={thumbStyle} />
        </button>
    );
};

export default Switch;
