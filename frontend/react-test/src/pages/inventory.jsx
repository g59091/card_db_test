import "../styles/inventory.css";

export default function Inventory({ inventory }) {
    return (
        <div>
            <div className="nav">
                <a href="/">Back to Search</a>
            </div>

            <h1>My Inventory</h1>

            {inventory && inventory.length > 0 ? (
                <div className="card-container">
                    {inventory.map((card, index) => (
                        <div className="card-box" key={index}>
                            <img src="{card.image_url}" alt="{card.name}"/>
                            <div className="card-info">
                                <strong>{card.name}</strong><br />
                                Quantity: {card.quantity}<br />
                                Condition: {card.card_condition}
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <p>You don't have any cards in your inventory yet.</p>
            )}
        </div>
    );
}