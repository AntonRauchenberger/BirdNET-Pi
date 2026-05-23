import { ChevronLeft } from "lucide-react";
import { useEffect } from "react";
import { ReactNode } from "react";

const SubPage = (props: {
    subPageVisible: boolean;
    closeSubPage: () => void;
    activeSubPage: ReactNode;
    setSubPageVisible: (visible: boolean) => void;
    headerElement?: ReactNode;
}) => {

    useEffect(() => {
        const animationFrame = window.requestAnimationFrame(() => {
            props.setSubPageVisible(true);
        });

        return () => {
            window.cancelAnimationFrame(animationFrame);
        };
    }, [props.setSubPageVisible]);

    useEffect(() => {
        const previousBodyOverflow = document.body.style.overflow;
        const previousBodyTouchAction = document.body.style.touchAction;

        document.body.style.overflow = "hidden";
        document.body.style.touchAction = "none";

        return () => {
            document.body.style.overflow = previousBodyOverflow;
            document.body.style.touchAction = previousBodyTouchAction;
        };
    }, []);

    const styles = {
        subPageOverlay: {
            position: "fixed" as const,
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 20,
            transform: props.subPageVisible ? "translateX(0%)" : "translateX(100%)",
            transition: "transform 280ms ease-in-out",
            display: "flex",
            flexDirection: "column" as const,
            height: "100dvh",
            background: "var(--cornsilk)",
            width: "100vw",
            overflow: "hidden",
            overscrollBehavior: "none" as const,
            touchAction: "pan-y",
        },
        subPageHeader: {
            display: "flex",
            alignItems: "center",
            gap: "10px",
            padding: "1rem 1.25rem",
            justifyContent: "space-between",
            boxShadow: "var(--shadow-soft)",
            background: "var(--gradiant-leaf)",
            color: "var(--card)",
        },
        backButton: {
            border: "none",
            background: "transparent",
            color: "inherit",
            display: "flex",
            alignItems: "center",
            gap: "2px",
            fontWeight: 600,
            fontSize: "19px",
            cursor: "pointer",
            padding: "2px 0",
        },
        subPageBody: {
            padding: "1rem 1.25rem",
            flex: 1,
            overflowY: "auto" as const,
            overflowX: "hidden" as const,
            overscrollBehavior: "contain" as const,
            WebkitOverflowScrolling: "touch" as const,
            paddingTop: "0"
        },
    }

    return (
        <div style={styles.subPageOverlay}>
            <div style={styles.subPageHeader}>
                <button
                    type="button"
                    onClick={props.closeSubPage}
                    style={styles.backButton}
                    aria-label="Go back to Settings"
                >
                    <ChevronLeft size={20} />
                    Back
                </button>
                {props.headerElement}
            </div>

            <div style={styles.subPageBody}>
                {props.activeSubPage}
            </div>
        </div>
    )
}

export default SubPage