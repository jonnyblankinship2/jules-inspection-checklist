document.addEventListener('DOMContentLoaded', () => {
    // Views
    const initialView = document.getElementById('initial-view');
    const checklistSelectionView = document.getElementById('checklist-selection-view');
    const pastChecklistsView = document.getElementById('past-checklists-view');

    // Buttons for view switching
    const loadDailyBtn = document.getElementById('loadDailyBtn');
    const loadWeeklyBtn = document.getElementById('loadWeeklyBtn');
    const loadMonthlyBtn = document.getElementById('loadMonthlyBtn');
    const viewPastChecklistsBtn = document.getElementById('viewPastChecklistsBtn');
    
    // Auth form containers and buttons
    const loginFormContainer = document.getElementById('login-form-container');
    const registerFormContainer = document.getElementById('register-form-container');
    const showRegisterFormBtn = document.getElementById('show-register-form-btn');
    const showLoginFormBtn = document.getElementById('show-login-form-btn');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const loginMessageDiv = document.getElementById('login-message');
    const registerMessageDiv = document.getElementById('register-message');
    const userStatusDiv = document.getElementById('user-status');
    const loggedInUsernameSpan = document.getElementById('loggedInUsername');
    const logoutBtn = document.getElementById('logoutBtn');

    // Checklist Selection View elements
    const templateSelectionArea = document.getElementById('template-selection-area');
    const selectedChecklistTypeSpan = document.getElementById('selected-checklist-type');
    const templateListUl = document.getElementById('template-list');
    const currentChecklistArea = document.getElementById('current-checklist-area');
    const submitChecklistBtn = document.getElementById('submit-checklist-btn');

    // Past Checklists View elements
    const pastChecklistsListUl = document.getElementById('past-checklists-list');
    const pastChecklistDetailArea = document.getElementById('past-checklist-detail-area');

    // Item History Modal elements
    const itemHistoryModal = document.getElementById('item-history-modal');
    const historyItemNameSpan = document.getElementById('history-item-name');
    const historyItemListUl = document.getElementById('history-item-list');
    const closeModalBtn = itemHistoryModal.querySelector('.close-btn'); 
    if(closeModalBtn) closeModalBtn.onclick = () => itemHistoryModal.style.display = 'none';

    function displayAuthMessage(element, message, isSuccess) {
        element.textContent = message;
        element.className = 'auth-message'; // Reset class
        if (isSuccess) {
            element.classList.add('success');
        } else {
            element.classList.add('error');
        }
    }

    // Function to update UI based on login state
    function updateLoginState() {
        const token = localStorage.getItem('authToken');
        const username = localStorage.getItem('username');

        if (token && username) {
            // Logged in state
            userStatusDiv.style.display = 'block';
            loggedInUsernameSpan.textContent = username;
            
            // Hide auth forms, show main content access
            loginFormContainer.style.display = 'none';
            registerFormContainer.style.display = 'none';
            
            loadDailyBtn.style.display = 'inline-block';
            loadWeeklyBtn.style.display = 'inline-block';
            loadMonthlyBtn.style.display = 'inline-block';
            viewPastChecklistsBtn.style.display = 'inline-block';

            // If initialView was showing login/register, clear it and show welcome.
            // Otherwise, keep the current view (checklist or past checklists)
            if (initialView.style.display === 'block' || initialView.style.display === '') {
                 initialView.innerHTML = '<h2>Welcome!</h2><p>Select an action from the navigation above.</p>';
                 switchToView(initialView); 
            }

        } else {
            // Logged out state
            switchToView(initialView); // Ensure initialView is the active one
            initialView.innerHTML = ''; // Clear previous content (like welcome message)
            initialView.appendChild(loginFormContainer); // Add login form back
            initialView.appendChild(registerFormContainer); // Add register form back (hidden by default)
            loginFormContainer.style.display = 'block'; // Show login form
            registerFormContainer.style.display = 'none'; // Hide register form

            userStatusDiv.style.display = 'none';
            loggedInUsernameSpan.textContent = '';
            
            loadDailyBtn.style.display = 'none';
            loadWeeklyBtn.style.display = 'none';
            loadMonthlyBtn.style.display = 'none';
            viewPastChecklistsBtn.style.display = 'none';

            // Clear content areas
            currentChecklistArea.innerHTML = '';
            templateListUl.innerHTML = '';
            pastChecklistsListUl.innerHTML = '';
            pastChecklistDetailArea.innerHTML = '';
            selectedChecklistTypeSpan.textContent = '';
            submitChecklistBtn.style.display = 'none';
        }
    }

    function switchToView(viewToShow) {
        initialView.style.display = 'none';
        checklistSelectionView.style.display = 'none';
        pastChecklistsView.style.display = 'none';
        
        viewToShow.style.display = 'block';

        // If switching away from checklist selection, ensure its sub-parts are reset if necessary
        if (viewToShow !== checklistSelectionView) {
            templateSelectionArea.style.display = 'none';
            currentChecklistArea.innerHTML = '';
            submitChecklistBtn.style.display = 'none';
        }
    }
    
    showRegisterFormBtn.addEventListener('click', () => {
        loginFormContainer.style.display = 'none';
        registerFormContainer.style.display = 'block';
        loginMessageDiv.textContent = '';
        registerMessageDiv.textContent = '';
    });

    showLoginFormBtn.addEventListener('click', () => {
        registerFormContainer.style.display = 'none';
        loginFormContainer.style.display = 'block';
        loginMessageDiv.textContent = '';
        registerMessageDiv.textContent = '';
    });

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = loginForm.username.value;
        const password = loginForm.password.value;
        displayAuthMessage(loginMessageDiv, "Logging in...", false); // Temp message

        if (!username || !password) {
            displayAuthMessage(loginMessageDiv, "Username and password are required.", false);
            return;
        }

        try {
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await response.json();
            if (response.ok) {
                localStorage.setItem('authToken', data.token);
                localStorage.setItem('username', data.username);
                displayAuthMessage(loginMessageDiv, 'Login successful!', true);
                updateLoginState();
                // switchToView(initialView); // updateLoginState will handle switching to initial view with welcome message
            } else {
                localStorage.removeItem('authToken');
                localStorage.removeItem('username');
                throw new Error(data.message || 'Login failed');
            }
        } catch (error) {
            console.error('Login error:', error);
            displayAuthMessage(loginMessageDiv, error.message, false);
            updateLoginState(); // Ensure UI reflects logged-out state if login fails
        }
    });

    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = registerForm.username.value;
        const password = registerForm.password.value;
        displayAuthMessage(registerMessageDiv, "Registering...", false);

        if (!username || !password) {
            displayAuthMessage(registerMessageDiv, "Username and password are required.", false);
            return;
        }

        try {
            const response = await fetch('/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await response.json();
            if (response.ok) {
                displayAuthMessage(registerMessageDiv, 'Registration successful! Please log in.', true);
                registerForm.reset();
                // Switch to login form
                registerFormContainer.style.display = 'none';
                loginFormContainer.style.display = 'block';
                loginForm.username.focus();
            } else {
                throw new Error(data.message || 'Registration failed');
            }
        } catch (error) {
            console.error('Registration error:', error);
            displayAuthMessage(registerMessageDiv, error.message, false);
        }
    });

    logoutBtn.addEventListener('click', async () => {
        const currentToken = localStorage.getItem('authToken'); // Get token for API call
        // No need to check if !currentToken here, as logoutBtn should only be visible if logged in.
        // If it were, it implies a UI state inconsistency.

        try {
            // Attempt server-side logout if applicable (e.g., for session invalidation if using Flask-Login sessions heavily)
            // For JWT, it's mainly client-side, but good practice to hit a logout endpoint if it exists.
            const response = await fetch('/auth/logout', {
                method: 'POST', // Ensure this matches your backend route
                headers: {
                    'Content-Type': 'application/json',
                    'x-access-token': currentToken // If your /auth/logout is token_protected
                }
            });
            // We don't strictly need to wait for the response to clear local storage for JWT
            // but it's good to check if the server acknowledged it.
            if (!response.ok) {
                const errorData = await response.json();
                console.warn('Server logout issue:', errorData.message);
            }
        } catch (error) {
            console.error('Error during server logout:', error);
        } finally {
            // Always clear local storage and update UI regardless of server response
            localStorage.removeItem('authToken');
            localStorage.removeItem('username');
            
            // Clear content areas
            currentChecklistArea.innerHTML = '';
            templateListUl.innerHTML = '';
            pastChecklistsListUl.innerHTML = '';
            pastChecklistDetailArea.innerHTML = '';
            selectedChecklistTypeSpan.textContent = '';
            loginMessageDiv.textContent = '';
            registerMessageDiv.textContent = '';
            
            updateLoginState(); // This will switch to the initial login view
            alert("Logged out successfully.");
        }
    });

    async function fetchChecklistTemplates(type) {
        switchToView(checklistSelectionView);
        templateSelectionArea.style.display = 'block'; // Make sure this part of the view is visible
        currentChecklistArea.innerHTML = ''; 
        submitChecklistBtn.style.display = 'none';
        selectedChecklistTypeSpan.textContent = type.charAt(0).toUpperCase() + type.slice(1);
        templateListUl.innerHTML = '<li>Loading templates...</li>';
        
        const currentToken = localStorage.getItem('authToken');
        if (!currentToken) {
            templateListUl.innerHTML = '<li>Please log in to load checklists.</li>';
            console.warn('No auth token found for fetchChecklistTemplates.');
            // updateLoginState(); // Could also call this to force UI to login state
            return;
        }

        try {
            const response = await fetch('/api/checklist-templates', { 
                headers: {
                    'Content-Type': 'application/json',
                    'x-access-token': currentToken 
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                if (response.status === 401) { // Token expired or invalid
                    alert(errorData.message || "Session expired. Please log in again.");
                    logoutBtn.click(); // Simulate logout to reset UI
                }
                throw new Error(errorData.message || `Error fetching templates: ${response.statusText}`);
            }
            
            const data = await response.json();
            const filteredTemplates = data.checklist_templates.filter(t => t.type.toLowerCase() === type.toLowerCase());

            if (filteredTemplates.length === 0) {
                templateListUl.innerHTML = `<li>No '${type}' templates found.</li>`;
                return;
            }

            templateListUl.innerHTML = ''; 
            filteredTemplates.forEach(template => {
                const li = document.createElement('li');
                li.textContent = template.name;
                li.dataset.templateId = template.id;
                li.addEventListener('click', () => loadChecklistForTemplate(template.id, template.name));
                templateListUl.appendChild(li);
            });

        } catch (error) {
            console.error('Error fetching checklist templates:', error);
            templateListUl.innerHTML = `<li>Error: ${error.message}</li>`;
        }
    }

    async function loadChecklistForTemplate(templateId, templateName) {
        // checklistSelectionView is already active
        templateSelectionArea.style.display = 'none'; 
        currentChecklistArea.innerHTML = '<p>Loading checklist...</p>';
        submitChecklistBtn.style.display = 'block';
        submitChecklistBtn.dataset.templateId = templateId;
        const currentToken = localStorage.getItem('authToken');

        if (!currentToken) {
            currentChecklistArea.innerHTML = '<p>Please log in to load a checklist.</p>';
            submitChecklistBtn.style.display = 'none';
            console.warn('No auth token found for loadChecklistForTemplate.');
            return;
        }

        try {
            const response = await fetch(`/api/checklist-templates/${templateId}`, {
                headers: {
                    'Content-Type': 'application/json',
                    'x-access-token': currentToken
                }
            });
            if (!response.ok) {
                const errorData = await response.json();
                 if (response.status === 401) {
                    alert(errorData.message || "Session expired. Please log in again.");
                    logoutBtn.click();
                }
                throw new Error(errorData.message || `Error fetching template details: ${response.statusText}`);
            }
            const template = await response.json();
            
            await renderChecklist(template);

        } catch (error) {
            console.error('Error loading checklist:', error);
            currentChecklistArea.innerHTML = `<p>Error loading checklist: ${error.message}</p>`;
            submitChecklistBtn.style.display = 'none';
        }
    }

    async function renderChecklist(template) {
        currentChecklistArea.innerHTML = ''; 
        const form = document.createElement('form');
        form.id = 'active-checklist-form';
           
        const title = document.createElement('h3');
        title.textContent = template.name;
        form.appendChild(title);

        if (template.description) {
            const desc = document.createElement('p');
            desc.textContent = template.description;
            form.appendChild(desc);
        }

        for (const [index, item] of template.items.entries()) {
            const itemDiv = document.createElement('div');
            itemDiv.classList.add('checklist-item');
            itemDiv.dataset.templateItemId = item.id; 
            itemDiv.dataset.equipmentId = item.equipment_id || '';

            const label = document.createElement('label');
            label.setAttribute('for', `item-status-${index}`);
            label.textContent = item.item_description;
            itemDiv.appendChild(label);

            if (item.equipment_id) {
                const historyLink = document.createElement('a');
                historyLink.href = '#';
                historyLink.textContent = ' (View History)';
                historyLink.style.fontSize = '0.8em';
                historyLink.style.marginLeft = '5px';
                historyLink.onclick = (e) => {
                    e.preventDefault();
                    showItemHistory(item.equipment_id, item.item_description);
                };
                label.appendChild(historyLink);
                
                const recentIssue = await checkRecentEquipmentIssues(item.equipment_id);
                if (recentIssue) {
                    itemDiv.classList.add('recent-issue-highlight');
                }
            }

            const statusSelect = document.createElement('select');
            statusSelect.id = `item-status-${index}`;
            statusSelect.name = `item_status_${index}`;
            statusSelect.required = true; 
            const statuses = ['Checked', 'Broken', 'Missing', 'Needs Repair', 'N/A'];
            let selected = false;
            statuses.forEach(s => {
                const option = document.createElement('option');
                option.value = s.toLowerCase().replace(/ /g, '_'); 
                option.textContent = s;
                if (item.expected_status && s.toLowerCase() === item.expected_status.toLowerCase()){
                    option.selected = true;
                    selected = true;
                }
                statusSelect.appendChild(option);
            });
            if (!selected) { 
                 const defaultOption = document.createElement('option');
                 defaultOption.value = ""; 
                 defaultOption.textContent = "-- Select Status --";
                 defaultOption.selected = true;
                 defaultOption.disabled = true; 
                 statusSelect.insertBefore(defaultOption, statusSelect.firstChild);
            }

            itemDiv.appendChild(statusSelect);

            const notesLabel = document.createElement('label');
            notesLabel.htmlFor = `item_notes_${index}`;
            notesLabel.textContent = 'Notes:';
            notesLabel.style.display = 'block';
            notesLabel.style.marginTop = '5px';
            const notesTextarea = document.createElement('textarea');
            notesTextarea.id = `item_notes_${index}`;
            notesTextarea.name = `item_notes_${index}`;
            notesTextarea.rows = 2;
            
            itemDiv.appendChild(notesLabel);
            itemDiv.appendChild(notesTextarea);
            form.appendChild(itemDiv);
        }
        currentChecklistArea.appendChild(form);
    }

    async function checkRecentEquipmentIssues(equipmentId) {
        if (!equipmentId) return null;
        const currentToken = localStorage.getItem('authToken');
        if (!currentToken) return null; // No token, can't fetch

        try {
            const response = await fetch(`/api/equipment/${equipmentId}/history`, {
                headers: { 'x-access-token': currentToken }
            });
            if (!response.ok) {
                if (response.status === 401) logoutBtn.click(); // Token issue
                return null; 
            }
            const data = await response.json();
            if (data.history && data.history.length > 0) {
                const lastItem = data.history[0]; 
                if (lastItem.status === 'broken' || lastItem.status === 'missing' || lastItem.status === 'needs_repair') {
                    return lastItem;
                }
            }
        } catch (error) {
            console.warn('Could not fetch recent equipment history:', error);
        }
        return null;
    }

    async function showItemHistory(equipmentId, itemName) {
        historyItemNameSpan.textContent = itemName || `Equipment ID: ${equipmentId}`;
        historyItemListUl.innerHTML = '<li>Loading history...</li>';
        itemHistoryModal.style.display = 'block';
        const currentToken = localStorage.getItem('authToken');

        if (!currentToken) {
            historyItemListUl.innerHTML = '<li>Authentication token not found. Please log in.</li>';
            return;
        }

        try {
            const response = await fetch(`/api/equipment/${equipmentId}/history`, {
                headers: { 'x-access-token': currentToken }
            });
            if (!response.ok) {
                const errorData = await response.json();
                if (response.status === 401) {
                    alert(errorData.message || "Session expired. Please log in again.");
                    logoutBtn.click();
                }
                throw new Error(errorData.message || 'Failed to fetch history');
            }
            const data = await response.json();
            
            if (data.history && data.history.length > 0) {
                historyItemListUl.innerHTML = '';
                data.history.forEach(rec => {
                    const li = document.createElement('li');
                    li.textContent = `${new Date(rec.checked_at).toLocaleString()}: ${rec.status} - ${rec.description_from_check || ''} (Notes: ${rec.notes || 'N/A'})`;
                    if (rec.status === 'broken' || rec.status === 'missing' || rec.status === 'needs_repair') {
                        li.classList.add(`status-${rec.status.replace(' ', '_')}`);
                    }
                    historyItemListUl.appendChild(li);
                });
            } else {
                historyItemListUl.innerHTML = '<li>No history found for this item.</li>';
            }
        } catch (error) {
            console.error('Error fetching item history:', error);
            historyItemListUl.innerHTML = `<li>Error: ${error.message}</li>`;
        }
    }

    async function handleSubmitChecklist() {
        const form = document.getElementById('active-checklist-form');
        if (!form) return;
        
        const currentToken = localStorage.getItem('authToken');
        if (!currentToken) {
            alert('Please log in to submit checklists.');
            updateLoginState(); // Go to login
            return;
        }

        const templateId = submitChecklistBtn.dataset.templateId;
        const itemsData = [];
        const itemElements = form.querySelectorAll('.checklist-item');
        let allItemsValid = true;

        itemElements.forEach((itemEl, index) => {
            if (!allItemsValid) return; 

            const statusSelect = itemEl.querySelector(`select[name="item_status_${index}"]`);
            const notesTextarea = itemEl.querySelector(`textarea[name="item_notes_${index}"]`);
            const labelElement = itemEl.querySelector('label');
            
            let originalItemDescription = "";
            // Iterate through child nodes to find the first text node for description
            for (let node of labelElement.childNodes) {
                if (node.nodeType === Node.TEXT_NODE && node.textContent.trim() !== "") {
                    originalItemDescription = node.textContent.trim();
                    break;
                }
            }
            if (!originalItemDescription) { // Fallback if text node not found directly
                originalItemDescription = labelElement.textContent.split('(')[0].trim();
            }


            if (!statusSelect.value) { 
                alert(`Please select a status for: "${originalItemDescription}"`);
                statusSelect.focus();
                allItemsValid = false;
            }
            
            if (!allItemsValid) return;


            itemsData.push({
                equipment_id: itemEl.dataset.equipmentId ? parseInt(itemEl.dataset.equipmentId) : null, 
                item_description_from_template: originalItemDescription, 
                status: statusSelect.value,
                notes: notesTextarea.value.trim()
            });
        });

        if (!allItemsValid) return; 

        const checklistPayload = {
            checklist_template_id: parseInt(templateId),
            items: itemsData,
            notes: "" // Add a general notes field for the checklist if needed
        };

        try {
            submitChecklistBtn.disabled = true;
            submitChecklistBtn.textContent = 'Submitting...';
            const response = await fetch('/api/checklists', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-access-token': currentToken
                },
                body: JSON.stringify(checklistPayload)
            });

            if (!response.ok) {
                const errorResult = await response.json();
                if (response.status === 401) {
                    alert(errorResult.message || "Session expired. Please log in again.");
                    logoutBtn.click();
                }
                throw new Error(errorResult.message || 'Failed to submit checklist');
            }
            
            const result = await response.json();
            alert('Checklist submitted successfully! ID: ' + result.id);
            currentChecklistArea.innerHTML = ''; 
            submitChecklistBtn.style.display = 'none';
            templateSelectionArea.style.display = 'none'; 
            switchToView(initialView); 
        } catch (error) {
            console.error('Error submitting checklist:', error);
            alert(`Error: ${error.message}`);
        } finally {
            submitChecklistBtn.disabled = false;
            submitChecklistBtn.textContent = 'Submit Checklist';
        }
    }

    async function loadPastChecklists() {
        switchToView(pastChecklistsView);
        pastChecklistsListUl.innerHTML = '<li>Loading past checklists...</li>';
        pastChecklistDetailArea.innerHTML = ''; 
        const currentToken = localStorage.getItem('authToken');

        if (!currentToken) {
            pastChecklistsListUl.innerHTML = '<li>Please log in to view past checklists.</li>';
            // updateLoginState(); // redirect to login
            return;
        }

        try {
            const response = await fetch('/api/checklists', {
                headers: { 'x-access-token': currentToken }
            });
            if (!response.ok) {
                const errorData = await response.json();
                if (response.status === 401) {
                    alert(errorData.message || "Session expired. Please log in again.");
                    logoutBtn.click();
                }
                throw new Error(errorData.message || 'Failed to fetch past checklists');
            }
            const data = await response.json();

            if (data.checklists && data.checklists.length > 0) {
                pastChecklistsListUl.innerHTML = '';
                data.checklists.forEach(chk => {
                    const li = document.createElement('li');
                    li.textContent = `Checklist ID: ${chk.id} - ${chk.template_name} (Completed: ${new Date(chk.completed_at).toLocaleDateString()})`;
                    li.dataset.checklistId = chk.id;
                    li.addEventListener('click', (event) => {
                        pastChecklistsListUl.querySelectorAll('li').forEach(item => item.classList.remove('active'));
                        event.currentTarget.classList.add('active');
                        loadPastChecklistDetail(chk.id);
                    });
                    pastChecklistsListUl.appendChild(li);
                });
            } else {
                pastChecklistsListUl.innerHTML = '<li>No past checklists found.</li>';
            }
        } catch (error) {
            console.error('Error fetching past checklists:', error);
            pastChecklistsListUl.innerHTML = `<li>Error: ${error.message}</li>`;
        }
    }

    async function loadPastChecklistDetail(checklistId) {
        pastChecklistDetailArea.innerHTML = '<p>Loading details...</p>';
        const currentToken = localStorage.getItem('authToken');
        if (!currentToken) {
             pastChecklistDetailArea.innerHTML = '<p>Authentication error. Please log in.</p>';
             // updateLoginState();
             return;
        }
        try {
            const response = await fetch(`/api/checklists/${checklistId}`, {
                headers: { 'x-access-token': currentToken }
            });
            if (!response.ok) {
                const errorData = await response.json();
                if (response.status === 401) {
                    alert(errorData.message || "Session expired. Please log in again.");
                    logoutBtn.click();
                } else if (response.status === 403) { // Unauthorized to view this specific checklist
                     pastChecklistDetailArea.innerHTML = `<p>Error: ${errorData.message}</p>`;
                     return;
                }
                throw new Error(errorData.message || 'Failed to fetch checklist details');
            }
            const chk = await response.json();

            let detailHtml = `<h4>Details for Checklist ID: ${chk.id}</h4>`;
            detailHtml += `<p><strong>Template:</strong> ${chk.template_name}</p>`;
            detailHtml += `<p><strong>Completed:</strong> ${new Date(chk.completed_at).toLocaleString()}</p>`;
            if(chk.notes) detailHtml += `<p><strong>Overall Notes:</strong> ${chk.notes}</p>`;
            detailHtml += '<h5>Items:</h5>';
            
            if (chk.items && chk.items.length > 0) {
                chk.items.forEach(item => {
                    detailHtml += `<div class="item-detail">`;
                    detailHtml += `<p><strong>Item:</strong> ${item.item_description_from_template}`;
                    if(item.equipment_name) detailHtml += ` (Equipment: ${item.equipment_name})`;
                    detailHtml += `</p>`;
                    detailHtml += `<p><strong>Status:</strong> ${item.status}</p>`;
                    if (item.notes) detailHtml += `<p><strong>Notes:</strong> ${item.notes}</p>`;
                    detailHtml += `</div>`;
                });
            } else {
                detailHtml += '<p>No items found for this checklist.</p>';
            }
            pastChecklistDetailArea.innerHTML = detailHtml;

        } catch (error) {
            console.error('Error fetching past checklist details:', error);
            pastChecklistDetailArea.innerHTML = `<p>Error: ${error.message}</p>`;
        }
    }

    // Event Listeners
    loadDailyBtn.addEventListener('click', () => fetchChecklistTemplates('daily'));
    loadWeeklyBtn.addEventListener('click', () => fetchChecklistTemplates('weekly'));
    loadMonthlyBtn.addEventListener('click', () => fetchChecklistTemplates('monthly'));
    viewPastChecklistsBtn.addEventListener('click', loadPastChecklists);
    submitChecklistBtn.addEventListener('click', handleSubmitChecklist);
    
    // Initial UI setup
    updateLoginState(); 
});
