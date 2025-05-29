document.addEventListener('DOMContentLoaded', () => {
    const TOKEN = localStorage.getItem('authToken'); // Retrieve token

    // Views
    const initialView = document.getElementById('initial-view');
    const checklistSelectionView = document.getElementById('checklist-selection-view');
    const pastChecklistsView = document.getElementById('past-checklists-view');

    // Buttons for view switching
    const dailyBtn = document.getElementById('loadDailyBtn');
    const weeklyBtn = document.getElementById('loadWeeklyBtn');
    const monthlyBtn = document.getElementById('loadMonthlyBtn');
    const viewPastChecklistsBtn = document.getElementById('viewPastChecklistsBtn');
    
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
    const closeBtn = itemHistoryModal.querySelector('.close-btn'); 
    if(closeBtn) closeBtn.onclick = () => itemHistoryModal.style.display = 'none';


    function switchToView(viewToShow) {
        initialView.style.display = 'none';
        checklistSelectionView.style.display = 'none';
        pastChecklistsView.style.display = 'none';
        
        // Hide specific parts of checklistSelectionView if not actively choosing template/filling one
        templateSelectionArea.style.display = 'none';
        currentChecklistArea.innerHTML = '';
        submitChecklistBtn.style.display = 'none';

        viewToShow.style.display = 'block';
    }

    async function fetchChecklistTemplates(type) {
        switchToView(checklistSelectionView);
        templateSelectionArea.style.display = 'block'; // Show this part of the view
        currentChecklistArea.innerHTML = ''; 
        submitChecklistBtn.style.display = 'none';
        selectedChecklistTypeSpan.textContent = type.charAt(0).toUpperCase() + type.slice(1);
        templateListUl.innerHTML = '<li>Loading templates...</li>';

        if (!TOKEN) {
            templateListUl.innerHTML = '<li>Please log in to load checklists. (No token found)</li>';
            console.warn('No auth token found.');
            return;
        }

        try {
            const response = await fetch('/api/checklist-templates', {
                headers: { 'x-access-token': TOKEN }
            });
            if (!response.ok) throw new Error((await response.json()).message || 'Failed to fetch templates');
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
        templateSelectionArea.style.display = 'none'; // Hide template list
        currentChecklistArea.innerHTML = '<p>Loading checklist...</p>'; // Show checklist area
        submitChecklistBtn.style.display = 'block';
        submitChecklistBtn.dataset.templateId = templateId;

        try {
            const response = await fetch(`/api/checklist-templates/${templateId}`, {
                headers: { 'x-access-token': TOKEN }
            });
            if (!response.ok) throw new Error((await response.json()).message || 'Failed to fetch template details');
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
                    // The highlighting is done via CSS based on class, label::after adds text
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
        try {
            const response = await fetch(`/api/equipment/${equipmentId}/history`, {
                headers: { 'x-access-token': TOKEN }
            });
            if (!response.ok) return null; 
            const data = await response.json();
            if (data.history && data.history.length > 0) {
                const lastItem = data.history[0]; 
                if (lastItem.status === 'broken' || lastItem.status === 'missing' || lastItem.status === 'needs_repair') {
                    return lastItem; // Return the problematic record
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

        try {
            const response = await fetch(`/api/equipment/${equipmentId}/history`, {
                headers: { 'x-access-token': TOKEN }
            });
            if (!response.ok) throw new Error((await response.json()).message || 'Failed to fetch history');
            const data = await response.json();
            
            if (data.history && data.history.length > 0) {
                historyItemListUl.innerHTML = '';
                data.history.forEach(rec => {
                    const li = document.createElement('li');
                    li.textContent = `${new Date(rec.checked_at).toLocaleString()}: ${rec.status} - ${rec.description_from_check || ''} (Notes: ${rec.notes || 'N/A'})`;
                    if (rec.status === 'broken' || rec.status === 'missing' || rec.status === 'needs_repair') {
                        li.classList.add(`status-${rec.status}`);
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

        const templateId = submitChecklistBtn.dataset.templateId;
        const itemsData = [];
        const itemElements = form.querySelectorAll('.checklist-item');
        let allItemsValid = true;

        itemElements.forEach((itemEl, index) => {
            if (!allItemsValid) return; // Skip further processing if one item is already invalid

            const statusSelect = itemEl.querySelector(`select[name="item_status_${index}"]`);
            const notesTextarea = itemEl.querySelector(`textarea[name="item_notes_${index}"]`);
            const labelElement = itemEl.querySelector('label');
            let originalItemDescription = labelElement.textContent;
            // Clean up the description from added elements like "(View History)" or "(Recent Issue Reported!)"
            if (labelElement.childNodes.length > 1) { // More than just text means other elements (like the history link)
                 originalItemDescription = Array.from(labelElement.childNodes).find(node => node.nodeType === Node.TEXT_NODE)?.textContent.trim() || originalItemDescription;
            }
            
            if (!statusSelect.value) {
                alert(`Please select a status for: "${originalItemDescription}"`);
                statusSelect.focus();
                allItemsValid = false;
            }

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
            notes: "" // Placeholder for overall checklist notes if needed in future
        };

        try {
            submitChecklistBtn.disabled = true;
            submitChecklistBtn.textContent = 'Submitting...';
            const response = await fetch('/api/checklists', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-access-token': TOKEN
                },
                body: JSON.stringify(checklistPayload)
            });

            if (!response.ok) {
                const errorResult = await response.json();
                throw new Error(errorResult.message || 'Failed to submit checklist');
            }
            
            const result = await response.json();
            alert('Checklist submitted successfully! ID: ' + result.id);
            currentChecklistArea.innerHTML = ''; // Clear the form
            submitChecklistBtn.style.display = 'none';
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

        if (!TOKEN) {
            pastChecklistsListUl.innerHTML = '<li>Please log in to view past checklists.</li>';
            return;
        }

        try {
            const response = await fetch('/api/checklists', {
                headers: { 'x-access-token': TOKEN }
            });
            if (!response.ok) throw new Error((await response.json()).message || 'Failed to fetch past checklists');
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
        try {
            const response = await fetch(`/api/checklists/${checklistId}`, {
                headers: { 'x-access-token': TOKEN }
            });
            if (!response.ok) throw new Error((await response.json()).message || 'Failed to fetch checklist details');
            const chk = await response.json();

            let detailHtml = `<h4>Details for Checklist ID: ${chk.id}</h4>`;
            detailHtml += `<p><strong>Template:</strong> ${chk.template_name}</p>`;
            detailHtml += `<p><strong>Completed:</strong> ${new Date(chk.completed_at).toLocaleString()}</p>`;
            if(chk.notes) detailHtml += `<p><strong>Overall Notes:</strong> ${chk.notes}</p>`;
            detailHtml += '<h5>Items:</h5>';
            
            chk.items.forEach(item => {
                detailHtml += `<div class="item-detail">`;
                detailHtml += `<p><strong>Item:</strong> ${item.item_description_from_template}`;
                if(item.equipment_name) detailHtml += ` (Equipment: ${item.equipment_name})`;
                detailHtml += `</p>`;
                detailHtml += `<p><strong>Status:</strong> ${item.status}</p>`;
                if (item.notes) detailHtml += `<p><strong>Notes:</strong> ${item.notes}</p>`;
                detailHtml += `</div>`;
            });
            pastChecklistDetailArea.innerHTML = detailHtml;

        } catch (error) {
            console.error('Error fetching past checklist details:', error);
            pastChecklistDetailArea.innerHTML = `<p>Error: ${error.message}</p>`;
        }
    }

    // Event Listeners
    dailyBtn.addEventListener('click', () => fetchChecklistTemplates('daily'));
    weeklyBtn.addEventListener('click', () => fetchChecklistTemplates('weekly'));
    monthlyBtn.addEventListener('click', () => fetchChecklistTemplates('monthly'));
    submitChecklistBtn.addEventListener('click', handleSubmitChecklist);
    viewPastChecklistsBtn.addEventListener('click', loadPastChecklists);
    
    // Initial state
    if (!TOKEN) {
        initialView.innerHTML = '<h2>Welcome!</h2><p>Please log in to access checklists. (Login UI not yet implemented - manually set authToken in localStorage for now)</p>';
        // Potentially disable buttons that require login
        dailyBtn.disabled = true;
        weeklyBtn.disabled = true;
        monthlyBtn.disabled = true;
        viewPastChecklistsBtn.disabled = true;
    }
    switchToView(initialView); // Always start at initial view
});
