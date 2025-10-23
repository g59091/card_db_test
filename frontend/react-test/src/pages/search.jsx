
import "../styles/search.css";
import { use, useState } from "react";

export default function Search() {
    const [cardName, setCardName] = useState("");
    const [message, setMessage] = useState("");
    const [result, setResult] = useState(null);
    const [inInventory, setInInventory] = useState(false);
    const [error, setError] = useState("");

    const handleSearch = async (e) => {
        e.preventDefault();
        setMessage("");
        setResult(null);
        //console.log(cardName);
        try {
             const res = await fetch("/search", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    //"User-Agent": "CardVault/1.0",
                    //"Accept": "application/json;q=0.9,*/*;q=0.8",
                },
                body: JSON.stringify({ card_name: cardName }),
            });
            //console.log(res);

            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                //console.log(data);
                throw new Error(data.error || "Card not found");
            }

            const data = await res.json();

            //console.log(data);
            setResult(data.result);
            setInInventory(data.in_inv_flag || false);
            setMessage(data.message || "");

        } catch (err) {
            setError(err.message);
        }
    };

    const handleAdd = async (card_id, condition) => {
        try {
            const response = await fetch("/add", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ card_id, condition }),
            });

           if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.error || "Failed to add card");
            }

            setInInventory(true);
            setMessage("Card added to your inventory!");
        } catch (err) {
            setMessage(err.message);
        }
    };

    const handleRemove = async (card_id) => {
        try {
            const response = await fetch("/remove", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ card_id }),
            });

            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.error || "Failed to remove card");
            }

            setInInventory(false);
            setMessage("Card removed from your inventory.");
        } catch (err) {
            setMessage(err.message);
        }
    };

    return ( 
        <div>
            <h1>CardVault Search</h1>
            <p>
                <a href="/inventory">View My Inventory</a>
            </p>
            <form onSubmit={handleSearch}>
                <input
                    type="text"
                    placeholder="Enter card name"
                    value={cardName}
                    onChange={(e) => 
                    setCardName(e.target.value)}
                    required
                />
                <button type="submit">Search</button>
            </form>

            {message && <p><strong>{message}</strong></p>}

            {result && (
                <div>
                    <h2>{result.name}</h2>
                    <img
                        src={result.image_url}
                        alt={result.name}
                        width="250"
                        style={{ border: "1px solid #ccc", marginTop: "1rem" }}
                    />
                    <p><strong>Type:</strong> {result.type}</p>
                    <p><strong>Rarity:</strong> {result.rarity}</p>
                    <p><strong>Mana Cost:</strong> {result.mana_cost}</p>
                    <p><strong>Rules:</strong> {result.rules_text}</p>

                    {!inInventory && (
                        <form
                            onSubmit={(e) => {
                                e.preventDefault();
                                const condition = e.target.condition.value;
                                handleAdd(result.card_id, condition);
                            }}
                        >
                            <label htmlFor="condition">Condition:</label>{" "}
                            <select name="condition" defaultValue="Near Mint">
                                <option value="Near Mint">Near Mint</option>
                                <option value="Lightly Played">Lightly Played</option>
                                <option value="Moderately Played">Moderately Played</option>
                                <option value="Heavily Played">Heavily Played</option>
                            </select>{" "}
                            <button type="submit">Add to My Inventory</button>
                        </form>
                    )}

                    {inInventory && (
                        <form
                            onSubmit={(e) => {
                                e.preventDefault();
                                handleRemove(result.card_id);
                            }}
                            style={{ marginTop: "10px" }}
                        >
                            <button type="submit">Remove from Inventory</button>
                        </form>
                    )}
                </div>
            )}

        </div>
    );
}