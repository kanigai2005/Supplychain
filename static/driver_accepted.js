document.addEventListener('DOMContentLoaded', () => {
    const DRIVER_ID = 1;
    const container = document.getElementById('groups-container');

    function formatStatus(status) {
        if (status === 'delivery_complete') return 'Delivery Complete!';
        return status.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
    }

    function getActionForStatus(order) {
        switch (order.status) {
            case 'accepted':
                return `<button onclick="updateOrderStatus(${order.id}, 'out_for_delivery')">Mark as Out for Delivery</button>`;
            case 'out_for_delivery':
                return `<button onclick="updateOrderStatus(${order.id}, 'delivery_complete')">Mark as Delivery Reached</button>`;
            case 'delivery_complete':
                return `<p style="color: green; font-weight: bold;">✔ Order Fulfilled</p>`;
            default: return '';
        }
    }

    async function fetchAcceptedOrders() {
        const response = await fetch(`/api/driver/orders/accepted/${DRIVER_ID}`);
        const groupedOrders = await response.json();

        if (!container) { return; }

        if (Object.keys(groupedOrders).length === 0) {
            container.innerHTML = '<p>You have not accepted any orders yet.</p>';
            return;
        }

        container.innerHTML = '';

        for (const address in groupedOrders) {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'address-group';
            
            let orderCardsHtml = '';

            groupedOrders[address].forEach(order => {
                const typeTag = order.delivery_type === 'door' ? '<span class="tag tag-door">DOOR</span>' : '<span class="tag tag-common">HUB</span>';

                orderCardsHtml += `
                    <div class="order-card">
                        <h4>To: ${order.vendor_name} ${typeTag}</h4>
                        <div class="details">
                            <p><strong>Status:</strong> ${formatStatus(order.status)}</p>
                            <p><strong>Allotted Time:</strong> ${order.delivery_time}</p>
                        </div>
                        <div class="actions">${getActionForStatus(order)}</div>
                    </div>
                `;
            });
            
            // NOTE: The total earnings header has been removed.
            groupDiv.innerHTML = `
                <h2>Stop: ${address}</h2>
                ${orderCardsHtml}
            `;
            container.appendChild(groupDiv);
        }
    }

    window.updateOrderStatus = async (orderId, newStatus) => {
        const response = await fetch(`/api/driver/orders/update_status/${orderId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        if (response.ok) { fetchAcceptedOrders(); }
        else { alert('Error updating status.'); }
    };

    fetchAcceptedOrders();
});