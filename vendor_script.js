document.addEventListener('DOMContentLoaded', function () {
    // --- Get all view sections ---
    const dashboardView = document.getElementById('dashboard-view');
    const requestFormView = document.getElementById('request-form-view');
    const statusView = document.getElementById('status-view');

    // --- Get all buttons and interactive elements ---
    const showRequestFormBtn = document.getElementById('show-request-form-btn');
    const backToDashboardBtn1 = document.getElementById('back-to-dashboard-btn1');
    const backToDashboardBtn2 = document.getElementById('back-to-dashboard-btn2');
    const addItemBtn = document.getElementById('add-item-btn');
    const newRequestForm = document.getElementById('new-request-form');
    const activeRequestsList = document.getElementById('active-requests-list');
    const pastRequestsList = document.getElementById('past-requests-list');
    const itemsContainer = document.getElementById('items-container');

    // --- Get delivery option elements ---
    const deliveryTypeRadios = document.querySelectorAll('input[name="delivery-type"]');
    const hubAddressGroup = document.getElementById('hub-address-group');
    const doorAddressGroup = document.getElementById('door-address-group');
    const hubAddressInput = document.getElementById('hub-address');
    const doorAddressInput = document.getElementById('door-address');

    // --- Helper function to switch views ---
    function showView(viewToShow) {
        dashboardView.classList.add('hidden');
        requestFormView.classList.add('hidden');
        statusView.classList.add('hidden');
        viewToShow.classList.remove('hidden');
    }

    // --- NEW: A robust function to completely reset the form to its original state ---
    function resetRequestForm() {
        // 1. Clear all input values
        newRequestForm.reset();

        // 2. Remove all dynamically added item rows, keeping only the first one
        while (itemsContainer.children.length > 1) {
            itemsContainer.removeChild(itemsContainer.lastChild);
        }

        // 3. Reset the delivery options to the default state
        hubAddressGroup.classList.remove('hidden');
        hubAddressInput.required = true;
        doorAddressGroup.classList.add('hidden');
        doorAddressInput.required = false;
        // Ensure the radio button is also visually reset
        document.querySelector('input[value="Lane Hub"]').checked = true;
    }


    // --- Function to load all requests from the server ---
    async function loadAllRequests() {
        const response = await fetch('/api/requests');
        const requests = await response.json();
        activeRequestsList.innerHTML = '';
        pastRequestsList.innerHTML = '';
        requests.forEach(req => {
            const requestLi = document.createElement('li');
            requestLi.dataset.requestId = req.request_id_str;
            requestLi.innerHTML = `<span>Request #${req.request_id_str} (${req.status})</span><a href="#" class="view-details-link">View Details</a>`;
            if (req.status.toLowerCase().includes('delivered')) {
                pastRequestsList.appendChild(requestLi);
            } else {
                activeRequestsList.appendChild(requestLi);
            }
        });
    }

    // --- Event Listeners for Navigation ---
    showRequestFormBtn.addEventListener('click', () => {
        resetRequestForm(); // Reset the form every time it's shown
        showView(requestFormView);
    });

    // UPDATED: When canceling, also reset the form completely
    backToDashboardBtn1.addEventListener('click', () => {
        resetRequestForm();
        showView(dashboardView);
    });

    backToDashboardBtn2.addEventListener('click', () => { showView(dashboardView); });

    // --- Event Listener for "View Details" links ---
    document.querySelector('main').addEventListener('click', async function(e) {
        if (e.target.classList.contains('view-details-link')) {
            e.preventDefault();
            const requestId = e.target.closest('li').dataset.requestId;
            await populateAndShowStatusView(requestId);
        }
    });
    
    // --- Logic for the New Request Form ---
    addItemBtn.addEventListener('click', () => {
        const newItemDiv = document.createElement('div');
        newItemDiv.classList.add('form-item-group');
        newItemDiv.innerHTML = `<input type="text" class="item-name" placeholder="Item Name" required><input type="text" class="item-quantity" placeholder="Quantity" required>`;
        itemsContainer.appendChild(newItemDiv);
    });

    // --- Logic for Delivery Options (This is now the single source of truth) ---
    deliveryTypeRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.value === 'Lane Hub') {
                hubAddressGroup.classList.remove('hidden');
                hubAddressInput.required = true;
                doorAddressGroup.classList.add('hidden');
                doorAddressInput.required = false;
            } else {
                hubAddressGroup.classList.add('hidden');
                hubAddressInput.required = false;
                doorAddressGroup.classList.remove('hidden');
                doorAddressInput.required = true;
            }
        });
    });

    // --- Form Submission Logic ---
    newRequestForm.addEventListener('submit', async (e) => {
        e.preventDefault(); 
        
        const items = [];
        document.querySelectorAll('#items-container .form-item-group').forEach(itemGroup => {
            const name = itemGroup.querySelector('.item-name').value;
            const quantity = itemGroup.querySelector('.item-quantity').value;
            if (name && quantity) items.push(`${name} - ${quantity}`);
        });

        const selectedDeliveryType = document.querySelector('input[name="delivery-type"]:checked').value;
        let deliveryAddress = (selectedDeliveryType === 'Lane Hub') 
            ? hubAddressInput.value
            : doorAddressInput.value;

        const requestData = {
            supplier: document.getElementById('supplier-name').value,
            items: items,
            delivery: { type: selectedDeliveryType, address: deliveryAddress }
        };

        const response = await fetch('/api/requests', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });

        if (response.ok) {
            await loadAllRequests();
            showView(dashboardView);
            // No need to call reset here, as it's handled when the form is shown next
        } else {
            alert('Failed to create request. Please try again.');
        }
    });

    // --- Status View Logic ---
    async function populateAndShowStatusView(requestId) {
        const response = await fetch(`/api/requests/${requestId}`);
        if (!response.ok) {
            alert('Could not fetch request details.');
            return;
        }
        const data = await response.json();
        
        document.getElementById('status-request-id').textContent = `Status for Request #${data.request_id_str}`;
        document.getElementById('status-supplier').textContent = data.supplier_name;
        document.getElementById('status-delivery-address').textContent = `${data.delivery_type}: ${data.delivery_address}`;
        
        const statusItemsList = document.getElementById('status-items-list');
        statusItemsList.innerHTML = '';
        data.items.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            statusItemsList.appendChild(li);
        });
        const statusTimelineList = document.getElementById('status-timeline-list');
        statusTimelineList.innerHTML = `<li class="completed">Request Received</li><li>Pending Assignment to Driver</li>`;
        showView(statusView);
    }

    // --- Initial State ---
    loadAllRequests(); 
    showView(dashboardView);
});