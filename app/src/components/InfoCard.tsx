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
        text: {
            opacity: 0.9,
            fontWeight: "600",
        }
    }

    return (
        <div style={styles.infoCard}>
            <span style={styles.text}>
                {props.text}
            </span>
        </div>
    );
}

export default InfoCard;