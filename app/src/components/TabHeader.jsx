const TabHeader = ({ tab, title, subTitle }) => {
    const styles = {
        wrapper: {
            textAlign: "left",
            display: "flex",
            flexDirection: "column",
            gap: "5px",
            position: "relative",
            zIndex: "1",
        },
        tab: {
            fontWeight: "500",
        },
        title: {
            fontSize: "30px",
            fontWeight: "600",
            color: "black",
        },
        subTitle: {
            opacity: "0.7",
            fontSize: "17px",
        },
    };

    return (
        <header>
            <div style={styles.wrapper}>
                <div style={styles.tab}>{tab}</div>
                <div style={styles.title}>{title}</div>
                {subTitle && subTitle.trim() !== "" && (
                    <div style={styles.subTitle}>{subTitle}</div>
                )}
            </div>
        </header>
    );
};

export default TabHeader;
