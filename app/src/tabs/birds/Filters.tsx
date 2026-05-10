import {
    Search,
    ArrowDownAZ,
    ArrowUpAZ,
    ArrowUp10,
    ArrowDown10,
} from "lucide-react";

type SortState = null | "asc" | "desc";

const cycleSort = (current: SortState): SortState => {
    if (current === null) return "asc";
    if (current === "asc") return "desc";
    return null;
};

const Filters = (props: {
    filter: {
        searchInput: string;
        alphabeticSort: SortState;
        confidenceSort: SortState;
    };
    setFilter: React.Dispatch<
        React.SetStateAction<{
            searchInput: string;
            alphabeticSort: SortState;
            confidenceSort: SortState;
        }>
    >;
}) => {
    const switchAlphabeticSort = () => {
        props.setFilter({
            ...props.filter,
            alphabeticSort: cycleSort(props.filter.alphabeticSort),
        });
    };

    const switchConfidenceSort = () => {
        props.setFilter({
            ...props.filter,
            confidenceSort: cycleSort(props.filter.confidenceSort),
        });
    };

    const styles = {
        inputWrapper: {
            display: "flex",
            width: "100%",
            alignItems: "center",
        },
        inputIcon: {
            background: "var(--card)",
            padding: "10.5px 0px 10.5px 12px",
            borderTopLeftRadius: "30px",
            borderBottomLeftRadius: "30px",
            borderLeft: "var(--card-border)",
            borderTop: "var(--card-border)",
            borderBottom: "var(--card-border)",
        },
        inputField: {
            background: "var(--card)",
            border: "none",
            padding: "14px",
            borderTop: "var(--card-border)",
            borderRight: "var(--card-border)",
            borderBottom: "var(--card-border)",
            borderTopRightRadius: "30px",
            borderBottomRightRadius: "30px",
            width: "100%",
            color: "black",
            fontSize: "17px",
            outline: "none",
        },
        filterIconsWrapper: {
            display: "flex",
            gap: "10px",
            marginTop: "10px",
        },
        filterIconActive: {
            backgroundColor: "var(--black-forest)",
            color: "var(--card)",
            height: "38px",
            width: "38px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            borderRadius: "50%",
        },
        filterIconPassive: {
            backgroundColor: "var(--seccondary)",
            color: "var(--black-forest)",
            height: "38px",
            width: "38px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            borderRadius: "50%",
        },
    };

    return (
        <div style={{ marginTop: "20px" }}>
            <div style={styles.inputWrapper}>
                <div style={styles.inputIcon}>
                    <Search
                        size={22}
                        style={{
                            opacity: "0.7",
                            transform: "translateY(2px)",
                        }}
                    />
                </div>
                <input
                    style={styles.inputField}
                    value={props.filter.searchInput}
                    onChange={(e) =>
                        props.setFilter({
                            ...props.filter,
                            searchInput: e.target.value,
                        })
                    }
                    placeholder="Search species..."
                />
            </div>

            <div style={styles.filterIconsWrapper}>
                <div
                    onClick={switchAlphabeticSort}
                    style={
                        props.filter.alphabeticSort !== null
                            ? styles.filterIconActive
                            : styles.filterIconPassive
                    }
                >
                    {props.filter.alphabeticSort === "asc" ? (
                        <ArrowUpAZ size={22} />
                    ) : (
                        <ArrowDownAZ size={22} />
                    )}
                </div>
                <div
                    onClick={switchConfidenceSort}
                    style={
                        props.filter.confidenceSort !== null
                            ? styles.filterIconActive
                            : styles.filterIconPassive
                    }
                >
                    {props.filter.confidenceSort === "asc" ? (
                        <ArrowUp10 size={22} />
                    ) : (
                        <ArrowDown10 size={22} />
                    )}
                </div>
            </div>
        </div>
    );
};

export default Filters;
