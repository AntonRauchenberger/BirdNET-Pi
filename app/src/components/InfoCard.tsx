const InfoCard = (props: {
    text: string
}) => {
    const styles = {
        infoCard: {
            background: "var(--card)",
            padding: "13px",
            borderRadius: "20px",
            textAlign: "left" as const,
            fontSize: "12px",
            border: "var(--card-border)",
            width: "100%",
        },
    }

    return (
        <div style={styles.infoCard}>
            <span style={{ opacity: 0.6 }}>
                {props.text}
            </span>
        </div>
    );
}

export default InfoCard;