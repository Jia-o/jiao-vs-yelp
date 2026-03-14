import sqlite3
import os

# Database setup
con = sqlite3.connect("restaurants.db")
cur = con.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS restaurants (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT NOT NULL, 
        cuisine TEXT, 
        my_rating REAL, 
        public_rating REAL
    )
""")

def auto_update_report():
    rows = cur.execute("""
        SELECT id, name, cuisine, my_rating, public_rating, 
        (my_rating - public_rating) as diff 
        FROM restaurants 
        ORDER BY my_rating DESC
    """).fetchall()

    table_rows = ""
    for r_id, name, cuisine, my_r, pub_r, diff in rows:
        color = "green" if diff >= 0 else "pink"
        table_rows += f"""
            <tr>
                <td>{r_id}</td><td>{name}</td><td>{cuisine}</td>
                <td>{my_r:.1f}</td><td>{pub_r:.1f}</td>
                <td style="color:{color}">{diff:+.2f}</td>
            </tr>
        """

    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background-color: #E8DAF0; padding: 20px; color: #4a3b52; }}
            h2 {{ color: #A7ABDE; }}
            input {{ padding: 10px; width: 100%; margin-bottom: 20px; border: 2px solid #C8CEEE; border-radius: 8px; }}
            table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            th {{ background-color: #A7ABDE; padding: 15px; cursor: pointer; text-align: left; transition: 0.3s; }}
            th:hover {{ background-color: #858ac9; }}
            td {{ padding: 12px; border-bottom: 1px solid #F3E4F5; }}
        </style>
    </head>
    <body>
        <h2>Restaurant Ratings</h2>
        <input type="text" id="searchInput" onkeyup="filterTable()" placeholder="Search...">
        <table id="resTable">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">ID</th>
                    <th onclick="sortTable(1)">Name</th>
                    <th onclick="sortTable(2)">Cuisine</th>
                    <th onclick="sortTable(3)">My Rating</th>
                    <th onclick="sortTable(4)">Public</th>
                    <th onclick="sortTable(5)">Diff</th>
                </tr>
            </thead>
            <tbody>{table_rows}</tbody>
        </table>

        <script>
            function filterTable() {{
                let filter = document.getElementById("searchInput").value.toUpperCase();
                let rows = document.getElementById("resTable").tBodies[0].rows;
                for (let row of rows) {{
                    row.style.display = row.innerText.toUpperCase().includes(filter) ? "" : "none";
                }}
            }}

            function sortTable(n) {{
                let table = document.getElementById("resTable");
                let tbody = table.tBodies[0];
                let rows = Array.from(tbody.rows);
                let th = table.tHead.rows[0].cells[n];
                
                // Toggle logic: Default to 'asc' if not currently 'asc'
                let dir = (th.getAttribute('data-sort') === 'asc') ? 'desc' : 'asc';
                
                // Reset other headers
                Array.from(table.tHead.rows[0].cells).forEach(cell => {{
                    cell.setAttribute('data-sort', '');
                    cell.innerText = cell.innerText.replace(' ▲', '').replace(' ▼', '');
                }});

                th.setAttribute('data-sort', dir);
                th.innerText += (dir === 'asc' ? ' ▲' : ' ▼');

                rows.sort((a, b) => {{
                    let valA = a.cells[n].innerText;
                    let valB = b.cells[n].innerText;
                    
                    // Numeric vs Text comparison
                    let comp = (n === 0 || n > 2) ? (parseFloat(valA) - parseFloat(valB)) : valA.localeCompare(valB);
                    return (dir === 'asc') ? comp : -comp;
                }});

                rows.forEach(row => tbody.appendChild(row));
            }}
        </script>
    </body>
    </html>
    """

    with open("display.html", "w") as f:
        f.write(html_content)
    print("✅ display.html updated with ID and improved sorting.")


def list_restaurants():
    rows = cur.execute("SELECT id, name, cuisine, my_rating, public_rating FROM restaurants").fetchall()
    print("\n--- CURRENT RESTAURANTS ---")
    for r in rows: 
        print(f"ID {r[0]}: {r[1]} | {r[2]} | Mine: {r[3]} | Public: {r[4]}")

def get_valid_rating(prompt, default=None):
    """Helper to ensure ratings are between 1 and 5."""
    while True:
        value = input(prompt)
        
        # Handle the update scenario where user might press enter for the default
        if default is not None and value == "":
            return default
            
        try:
            val = float(value)
            if 1.0 <= val <= 5.0:
                return val
            else:
                print("⚠️ Rating must be between 1.0 and 5.0.")
        except ValueError:
            print("⚠️ Invalid input. Please enter a number.")

def add_restaurant():
    name = input("Name: ")
    cuisine = input("Cuisine: ")
    my_r = get_valid_rating("My Rating (1-5): ")
    pub_r = get_valid_rating("Public Rating (1-5): ")
    
    cur.execute("INSERT INTO restaurants (name, cuisine, my_rating, public_rating) VALUES (?, ?, ?, ?)", 
                (name, cuisine, my_r, pub_r))
    con.commit()
    auto_update_report()
    print("✅ Restaurant added.")

def update_restaurant():
    list_restaurants()
    target_id = input("\nEnter the ID of the restaurant to update: ")
    
    restaurant = cur.execute("SELECT name, cuisine, my_rating, public_rating FROM restaurants WHERE id = ?", (target_id,)).fetchone()
    
    if not restaurant:
        print("❌ ID not found.")
        return

    print("(Leave blank to keep existing value)")
    new_name = input(f"New Name [{restaurant[0]}]: ") or restaurant[0]
    new_cuisine = input(f"New Cuisine [{restaurant[1]}]: ") or restaurant[1]
    
    # Use the helper for ratings with defaults
    new_my = get_valid_rating(f"New My Rating [{restaurant[2]}]: ", default=restaurant[2])
    new_pub = get_valid_rating(f"New Public Rating [{restaurant[3]}]: ", default=restaurant[3])
    
    cur.execute("""
        UPDATE restaurants 
        SET name = ?, cuisine = ?, my_rating = ?, public_rating = ? 
        WHERE id = ?
    """, (new_name, new_cuisine, new_my, new_pub, target_id))
    
    con.commit()
    auto_update_report()
    print("✅ Update successful.")

def delete_restaurant():
    list_restaurants()
    target_id = input("\nEnter the ID to DELETE: ")
    
    # Delete the target
    cur.execute("DELETE FROM restaurants WHERE id = ?", (target_id,))
    
    # Shift IDs down for all entries with an ID greater than the one deleted
    cur.execute("UPDATE restaurants SET id = id - 1 WHERE id > ?", (target_id,))
    
    # Reset the sqlite sequence so new entries don't conflict
    cur.execute("UPDATE sqlite_sequence SET seq = (SELECT MAX(id) FROM restaurants) WHERE name='restaurants'")
    
    con.commit()
    auto_update_report()
    print(f"✅ Entry {target_id} removed and IDs re-indexed.")

# MAIN MENU
while True:
    print("\nWhat would you like to do?")
    print("1. Add a new restaurant")
    print("2. Update an existing restaurant")
    print("3. Delete a restaurant")
    print("4. Exit")
    
    choice = input("Select an option (1-4): ")
    
    if choice == "1": add_restaurant()
    elif choice == "2": update_restaurant()
    elif choice == "3": delete_restaurant()
    elif choice == "4": 
        print("Goodbye!")
        break
    else:
        print("Invalid choice, please try again.")