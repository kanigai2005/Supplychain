document.addEventListener('DOMContentLoaded', () => {
    const DRIVER_ID = 1;
    const container = document.getElementById('orders-container');

    async function fetchAvailableOrders() {
        const response = await fetch('/api/orders/available');
        const orders = await response.json();

        if (!container) { return; }

        if (orders.length === 0) {
            container.innerHTML = '<p>No available orders at the moment.</p>';
            return;
        }

        container.innerHTML = '';
        orders.forEach(order => {
            const card = document.createElement('div');
            card.className = 'order-card';
            card.id = `order-${order.id}`;

            const quickTag = order.is_quick ? '<span class="tag tag-quick">QUICK</span>' : '';
            const typeTag = order.delivery_type === 'door' 
                ? '<span class="tag tag-door">DOOR DELIVERY</span>' 
                : '<span class="tag tag-common">COMMON HUB</span>';
            
            // NOTE: All price/fee display has been removed.
            card.innerHTML = `
                <h3>Order for: ${order.vendor_name}</h3>
                <div class="details">
                    <p><strong>Pickup:</strong> ${order.pickup_address}</p>
                    <p><strong>Deliver To:</strong> ${order.delivery_address}</p>
                </div>
                <div class="tags">${quickTag}${typeTag}</div>
                <div class="actions">
                    <input type="text" id="time-${order.id}" placeholder="e.g., 2:00 PM today">
                    <button onclick="acceptOrder(${order.id})">Accept</button>
                </div>
            `;
            container.appendChild(card);
        });
    }

    window.acceptOrder = async (orderId) => {
        const timeInput = document.getElementById(`time-${orderId}`);
        const deliveryTime = timeInput.value.trim();

        if (!deliveryTime) {
            alert('Please allot a delivery time.');
            return;
        }
        
        const response = await fetch(`/api/orders/accept/${orderId}/${DRIVER_ID}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ delivery_time: deliveryTime })
        });

        if (response.ok) {
            alert('Order accepted successfully!');
            document.getElementById(`order-${orderId}`).remove();
        } else {
            const result = await response.json();
            alert(`Error: ${result.error}`);
        }
    };

    fetchAvailableOrders();
});