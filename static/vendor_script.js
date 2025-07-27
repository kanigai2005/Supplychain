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
    const deliveryTypeRadios = document.querySelectorAll('input[name="delivery-type"]');
    const hubAddressGroup = document.getElementById('hub-address-group');
    const doorAddressGroup = document.getElementById('door-address-group');
    const hubAddressInput = document.getElementById('hub-address');
    const doorAddressInput = document.getElementById('door-address');

    // --- Helper function to switch views ---
    function showView(viewToShow) {
        if (!dashboardView || !requestFormView || !statusView) {
            console.error("One or more view containers are missing from the HTML.");
            return;
        }
        dashboardView.classList.add('hidden');
        requestFormView.classList.add('hidden');
        statusView.classList.add('hidden');
        viewToShow.classList.remove('hidden');
    }

    // --- Function to completely reset the form to its original state ---
    function resetRequestForm() {
        if (!newRequestForm) return;
        newRequestForm.reset();
        if (itemsContainer) {
            while (itemsContainer.children.length > 1) {
                itemsContainer.removeChild(itemsContainer.lastChild);
            }
        }
        // Also reset the delivery options visibility
        if (hubAddressGroup && doorAddressGroup) {
            hubAddressGroup.classList.remove('hidden');
            hubAddressInput.required = true;
            doorAddressGroup.classList.add('hidden');
            doorAddressInput.required = false;
            document.querySelector('input[value="Lane Hub"]').checked = true;
        }
    }

    // --- Function to load all requests from the server ---
    async function loadAllRequests() {
        const response = await fetch('/api/vendor/requests');
        if (!response.ok) {
            console.error("Failed to fetch vendor requests.");
            activeRequestsList.innerHTML = '<li>Error loading requests.</li>';
            return;
        }
        const requests = await response.json();
        
        activeRequestsList.innerHTML = '';
        pastRequestsList.innerHTML = '';

        requests.forEach(req => {
            const requestLi = document.createElement('li');
            requestLi.dataset.requestId = req.id;
            requestLi.innerHTML = `<span>Request #${req.id} (${req.status})</span><a href="#" class="view-details-link">View Details</a>`;
            if (req.status.toLowerCase() === 'completed') {
                pastRequestsList.appendChild(requestLi);
            } else {
                activeRequestsList.appendChild(requestLi);
            }
        });
    }

    // --- Event Listeners for Navigation ---
    if (showRequestFormBtn) {
        showRequestFormBtn.addEventListener('click', () => {
            resetRequestForm();
            showView(requestFormView);
        });
    }

    if (backToDashboardBtn1) backToDashboardBtn1.addEventListener('click', () => showView(dashboardView));
    if (backToDashboardBtn2) backToDashboardBtn2.addEventListener('click', () => showView(dashboardView));

    // --- Event Listener for "View Details" links ---
    document.querySelector('main').addEventListener('click', async function(e) {
        if (e.target.classList.contains('view-details-link')) {
            e.preventDefault();
            const requestId = e.target.closest('li').dataset.requestId;
            if (requestId) await populateAndShowStatusView(requestId);
        }
    });
    
    // --- Logic for the New Request Form ---
    if (addItemBtn) {
        addItemBtn.addEventListener('click', () => {
            const newItemDiv = document.createElement('div');
            newItemDiv.classList.add('form-item-group');
            newItemDiv.innerHTML = `<input type="text" class="item-name" placeholder="Item Name" required><input type="text" class="item-quantity" placeholder="Quantity (e.g., 25kg)" required>`;
            itemsContainer.appendChild(newItemDiv);
        });
    }

    // --- Logic for toggling delivery address input fields ---
    if (deliveryTypeRadios) {
        deliveryTypeRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                const isHub = radio.value === 'Lane Hub';
                hubAddressGroup.classList.toggle('hidden', !isHub);
                hubAddressInput.required = isHub;
                doorAddressGroup.classList.toggle('hidden', isHub);
                doorAddressInput.required = !isHub;
            });
        });
    }

    // --- Form Submission Logic ---
    if (newRequestForm) {
        newRequestForm.addEventListener('submit', async (e) => {
            e.preventDefault(); 
            
            const items = [];
            document.querySelectorAll('#items-container .form-item-group').forEach(itemGroup => {
                const name = itemGroup.querySelector('.item-name').value;
                const quantity = itemGroup.querySelector('.item-quantity').value;
                if (name && quantity) items.push(`${name} - ${quantity}`);
            });

            // THIS IS THE CORRECTED DATA COLLECTION
            const selectedDeliveryType = document.querySelector('input[name="delivery-type"]:checked').value;
            const deliveryAddress = (selectedDeliveryType === 'Lane Hub') ? hubAddressInput.value : doorAddressInput.value;

            const requestData = {
                items: items,
                delivery_type: selectedDeliveryType,
                delivery_address: deliveryAddress
            };

            const response = await fetch('/api/vendor/requests', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });

            if (response.ok) {
                await loadAllRequests();
                showView(dashboardView);
            } else {
                alert('Failed to create request. Please try again.');
            }
        });
    }

    // --- Status View Logic ---
    async function populateAndShowStatusView(requestId) {
        const response = await fetch(`/api/vendor/requests/${requestId}`);
        if (!response.ok) {
            alert('Could not fetch request details.');
            return;
        }
        const data = await response.json();
        
        document.getElementById('status-request-id').textContent = `Status for Request #${data.id}`;
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
        statusTimelineList.innerHTML = `<li class="completed">Request Sent (${data.status})</li>`;
        showView(statusView);
    }

    // --- Initial State ---
    loadAllRequests(); 
    showView(dashboardView);
});