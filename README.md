# 🚀 Supply Chain Control Tower

A production-ready **Supply Chain Management Dashboard** built with **Streamlit** to replace Excel-based workflows for SMEs.

---

## 🌐 Live Demo
👉 (Add your Streamlit link here after deployment)

---

## 📦 Features

### 📊 Dashboard
- Real-time KPIs:
  - Total Inventory
  - Active Orders
  - Delayed Shipments
  - Vendor Score
- Interactive charts using Plotly

### 📦 Inventory Management
- Add / Edit / Delete products
- Fields:
  - Product Name
  - SKU
  - Quantity
  - Warehouse
- Low stock alerts

### 📑 Order Management
- Create, update, delete orders
- Status tracking:
  - Pending
  - Processing
  - Completed

### 🚚 Shipment Tracking
- Track shipment lifecycle:
  - Pending → Dispatched → In Transit → Delivered
- Highlight delayed shipments

### 🤝 Vendor Management
- Store vendor details
- Track performance score

### 🧠 AI Features
- Demand forecasting (Moving Average)
- Smart reorder suggestions

### 📁 Data Handling
- JSON-based storage
- Download data as CSV

### 🔁 Undo / Redo
- Basic undo/redo system for inventory & orders

---

## 🎨 UI/UX Highlights
- Dark & Light mode support
- Clean SaaS dashboard design
- Responsive layout
- Smooth hover effects
- High contrast (no visibility issues)

---

## 🛠️ Tech Stack

- Python
- Streamlit
- Plotly
- JSON (data storage)

---

## 📂 Project Structure
├── main.py
├── inventory.py
├── orders.py
├── shipments.py
├── vendors.py
├── utils.py
├── data.json
├── requirements.txt
└── README.md 

---

## ⚙️ Installation

```bash
git clone https://github.com/YOUR_USERNAME/supply-chain-control-tower.git
cd supply-chain-control-tower
pip install -r requirements.txt
streamlit run main.py


🧑‍💻 Author

Tanay Shrivastava

📌 Notes
Built as a real-world SaaS-style project
Designed for scalability and clean UI
No external APIs required
⭐ If you like this project

Give it a star ⭐ on GitHub!
