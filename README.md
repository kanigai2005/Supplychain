# 📦 Supply-Chain: A Logistics Pooling App

**Tutedude Web Development Hackathon 1.0 Project**  
🔗 [Live Application](https://supplychain-ry30.onrender.com) • 📁 [GitHub Repository](https://github.com/kanigai2005/Supplychain.git)

---

## 📌 Overview

**Supply-Chain** is a logistics pooling platform designed to streamline raw material sourcing for street food vendors. Built with a focus on **time and cost efficiency**, the app enables vendors within a neighborhood to **collaborate on deliveries**, forming a pooled "Supply Chain" that is fulfilled by a single delivery driver. This model significantly reduces transport expenses and eliminates the need for vendors to leave their stalls during peak business hours.

---

## 🧩 The Problem

Street vendors often face a hidden, yet critical cost:  
- 🚶 **Leaving their stalls for 2+ hours** to visit wholesale markets results in lost income.  
- 🚚 **Hiring personal transport** is expensive and often inefficient for small-scale vendors.

These barriers limit operational efficiency, impact profitability, and reduce access to affordable raw materials.

---

## 💡 The Solution

**Supply-Chain** bridges this gap by offering a **community-based delivery pooling system**:
- Vendors submit pickup requests.
- The app identifies nearby vendors with similar needs and creates a **grouped delivery chain**.
- A verified delivery driver accepts the chain, picks up all requested items in one optimized trip, and delivers them:
  - To a **common "Lane Hub"** (low-cost option).
  - Or directly to each vendor's stall (premium delivery option).

---

## ⚙️ Key Features

### 🧑‍🍳 Vendor Module
- Simple registration and stall location setup.
- "Request Pickup" form (Item, Quantity, Supplier/Market).
- Auto-suggested participation in existing chains to reduce cost.
- Order status updates.
- Delivery type selection:
  - 🏠 **Premium Door Delivery** (extra fee).
  - 🏬 **Lane Hub Delivery** (base fee).

### 🚚 Driver Module
- Secure driver registration and login.
- View and accept active delivery chains.
- Consolidated view of pickup points and drop-off locations.
- Status updates per drop-off.

---

## 🛠 Tech Stack

| Layer      | Technology           |
|------------|----------------------|
| **Backend** | Flask (Python)       |
| **Database** | SQLite              |
| **Frontend** | HTML, CSS, JavaScript |
| **Hosting** | Render.com           |

---

## 🔄 Workflow Summary

1. **Vendor** submits a pickup request via the web app.
2. App identifies and suggests joining nearby vendor chains.
3. **Driver** accepts a chain and begins the pickup run.
4. Items are picked up from the wholesale market.
5. Deliveries are completed either at a **common hub** or directly to vendors.
6. All users track status updates.


