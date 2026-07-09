/*
   Smart Advertisement Slot Allocation System - main.js
   Manages Theme Toggle, Drag-Drop Uploads, Allocations, and Table Pagination/Search/Sort
*/

// --- Theme Management ---
function initTheme() {
    const themeToggler = document.getElementById('themeToggler');
    if (!themeToggler) return;
    
    const htmlEl = document.documentElement;
    const themeText = document.getElementById('themeToggleText');
    
    // Read persisted theme or default to system/dark
    const savedTheme = localStorage.getItem('theme') || 'dark';
    htmlEl.setAttribute('data-bs-theme', savedTheme);
    updateThemeButton(savedTheme, themeText);
    
    themeToggler.addEventListener('click', () => {
        const currentTheme = htmlEl.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        htmlEl.setAttribute('data-bs-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeButton(newTheme, themeText);
    });
}

function updateThemeButton(theme, buttonTextEl) {
    if (theme === 'dark') {
        buttonTextEl.textContent = 'Light Mode';
    } else {
        buttonTextEl.textContent = 'Dark Mode';
    }
}

// --- Loading Spinner Overlay ---
function showLoader() {
    const loader = document.getElementById('loadingOverlay');
    if (loader) loader.classList.remove('d-none');
}

function hideLoader() {
    const loader = document.getElementById('loadingOverlay');
    if (loader) loader.classList.add('d-none');
}

// --- Drag and Drop File Upload ---
function initUploadPage() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('datasetFile');
    const uploadStatus = document.getElementById('uploadStatus');
    const statusMessage = document.getElementById('statusMessage');
    const btnRunAllocation = document.getElementById('btnRunAllocation');
    
    if (!dropzone) return;
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // Highlight drop zone
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.add('dragover'), false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.remove('dragover'), false);
    });
    
    // Handle dropped files
    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });
    
    // Handle browsing files
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });
    
    function handleFiles(files) {
        if (files.length === 0) return;
        const file = files[0];
        
        // Show status loading
        uploadStatus.classList.remove('d-none');
        statusMessage.className = "alert alert-info d-flex align-items-center gap-2 border border-info border-opacity-25 glass-card";
        statusMessage.innerHTML = `<div class="spinner-border spinner-border-sm text-info"></div><span>Uploading and validating: ${file.name}...</span>`;
        
        const formData = new FormData();
        formData.append('file', file);
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(res => {
            if (res.status === 200) {
                statusMessage.className = "alert alert-success d-flex align-items-center gap-2 border border-success border-opacity-25 glass-card";
                statusMessage.innerHTML = `<i class="bi bi-check-circle-fill text-success"></i><span><b>Success!</b> ${res.body.message} Found ${res.body.stats.total_ads} records.</span>`;
                
                // Refresh page after delay to update the Flask UI context
                setTimeout(() => {
                    window.location.reload();
                }, 1200);
            } else {
                statusMessage.className = "alert alert-danger d-flex align-items-center gap-2 border border-danger border-opacity-25 glass-card";
                statusMessage.innerHTML = `<i class="bi bi-exclamation-triangle-fill text-danger"></i><span><b>Upload Failed:</b> ${res.body.message}</span>`;
            }
        })
        .catch(err => {
            statusMessage.className = "alert alert-danger d-flex align-items-center gap-2 border border-danger border-opacity-25 glass-card";
            statusMessage.innerHTML = `<i class="bi bi-x-circle-fill text-danger"></i><span>Network error. Failed to send file.</span>`;
            console.error(err);
        });
    }
    
    // Run allocation triggers
    if (btnRunAllocation) {
        btnRunAllocation.addEventListener('click', () => {
            const form = document.getElementById('allocateForm');
            if (!form) return;
            
            const formData = new FormData(form);
            showLoader();
            
            fetch('/allocate', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json().then(data => ({ status: response.status, body: data })))
            .then(res => {
                hideLoader();
                if (res.status === 200 && res.body.success) {
                    window.location.href = res.body.redirect;
                } else {
                    alert("Error: " + (res.body.message || "Failed to execute optimization."));
                }
            })
            .catch(err => {
                hideLoader();
                alert("Network error: Failed to trigger optimization.");
                console.error(err);
            });
        });
    }
}

// Algorithm selector layout active state switching
function selectAlgo(algoVal) {
    const cards = document.querySelectorAll('.algo-card');
    cards.forEach(card => card.classList.remove('active'));
    
    const radio = document.getElementById(`algo_${algoVal}`);
    if (radio) {
        radio.checked = true;
        radio.closest('.algo-card').classList.add('active');
    }
}

// --- Interactive Data Table (Search, Sort, Filters, Paginate) ---
let tableState = {
    originalData: [],
    filteredData: [],
    currentPage: 1,
    pageSize: 25,
    sortColumn: 'AdvertisementID',
    sortAscending: true
};

function initAllocationTable(data) {
    tableState.originalData = data;
    tableState.filteredData = [...data];
    
    // Register listeners
    const searchInput = document.getElementById('tableSearch');
    const filterStatus = document.getElementById('filterStatus');
    const filterSlot = document.getElementById('filterSlot');
    const pageSizeSelect = document.getElementById('pageSize');
    
    if (searchInput) searchInput.addEventListener('input', applyFilters);
    if (filterStatus) filterStatus.addEventListener('change', applyFilters);
    if (filterSlot) filterSlot.addEventListener('change', applyFilters);
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener('change', function() {
            tableState.pageSize = parseInt(this.value);
            tableState.currentPage = 1;
            renderTable();
        });
    }
    
    // Register sort click headers
    document.querySelectorAll('.sortable').forEach(header => {
        header.addEventListener('click', function() {
            const col = this.getAttribute('data-sort');
            if (tableState.sortColumn === col) {
                tableState.sortAscending = !tableState.sortAscending;
            } else {
                tableState.sortColumn = col;
                tableState.sortAscending = true;
            }
            
            // Update sort symbols UI
            document.querySelectorAll('.sortable i').forEach(icon => {
                icon.className = "bi bi-arrow-down-up ms-1 small text-muted";
            });
            const activeIcon = this.querySelector('i');
            activeIcon.className = tableState.sortAscending ? "bi bi-arrow-up ms-1 small text-primary" : "bi bi-arrow-down ms-1 small text-primary";
            
            applySorting();
            renderTable();
        });
    });
    
    // Initial display
    applySorting();
    renderTable();
}

function applyFilters() {
    const q = document.getElementById('tableSearch').value.toLowerCase().trim();
    const statusVal = document.getElementById('filterStatus').value;
    const slotVal = document.getElementById('filterSlot').value;
    
    tableState.filteredData = tableState.originalData.filter(ad => {
        const matchesSearch = ad.AdvertisementID.toLowerCase().includes(q) || 
                              ad.PreferredSlot.toLowerCase().includes(q) ||
                              ad.AllocatedSlot.toLowerCase().includes(q);
                              
        const matchesStatus = statusVal === 'ALL' || ad.Status === statusVal;
        const matchesSlot = slotVal === 'ALL' || ad.PreferredSlot === slotVal;
        
        return matchesSearch && matchesStatus && matchesSlot;
    });
    
    tableState.currentPage = 1;
    applySorting();
    renderTable();
}

function applySorting() {
    const col = tableState.sortColumn;
    const isAsc = tableState.sortAscending;
    
    tableState.filteredData.sort((a, b) => {
        let valA = a[col];
        let valB = b[col];
        
        // Handle numeric conversion
        if (['Duration', 'Budget', 'Priority'].includes(col)) {
            valA = parseFloat(valA);
            valB = parseFloat(valB);
        } else {
            valA = String(valA).toLowerCase();
            valB = String(valB).toLowerCase();
        }
        
        if (valA < valB) return isAsc ? -1 : 1;
        if (valA > valB) return isAsc ? 1 : -1;
        return 0;
    });
}

function renderTable() {
    const tbody = document.getElementById('tableBody');
    const tableInfo = document.getElementById('tableInfo');
    const pagination = document.getElementById('tablePagination');
    
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    const len = tableState.filteredData.length;
    const startIdx = (tableState.currentPage - 1) * tableState.pageSize;
    const endIdx = Math.min(startIdx + tableState.pageSize, len);
    
    const pageData = tableState.filteredData.slice(startIdx, endIdx);
    
    if (pageData.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-secondary"><i class="bi bi-folder-x me-1"></i> No campaign records match the current filters.</td></tr>`;
        tableInfo.textContent = `Showing 0 to 0 of 0 entries`;
        pagination.innerHTML = '';
        return;
    }
    
    pageData.forEach(ad => {
        const isAllocated = ad.Status === 'Allocated';
        const badgeClass = isAllocated ? 'status-badge-allocated' : 'status-badge-rejected';
        const budgetFmt = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(ad.Budget);
        
        const intervalStr = isAllocated ? `${ad.AllocatedStartTime} - ${ad.AllocatedEndTime}` : '<span class="text-muted">N/A</span>';
        const allocatedSlotStr = isAllocated ? `<span class="badge bg-primary bg-opacity-10 text-primary py-1 px-2 border border-primary border-opacity-10">${ad.AllocatedSlot}</span>` : '<span class="text-muted">None</span>';
        
        const tr = document.createElement('tr');
        if (isAllocated) tr.className = 'table-active-row';
        
        tr.innerHTML = `
            <td class="fw-bold">${ad.AdvertisementID}</td>
            <td>${ad.Duration} mins</td>
            <td class="fw-bold text-success">${budgetFmt}</td>
            <td><span class="badge bg-secondary bg-opacity-20 text-main py-1 px-2 rounded">${ad.Priority}</span></td>
            <td>${ad.PreferredSlot}</td>
            <td>${allocatedSlotStr}</td>
            <td class="font-monospace">${intervalStr}</td>
            <td><span class="badge ${badgeClass} py-1.5 px-3 rounded-pill fw-semibold">${ad.Status}</span></td>
        `;
        tbody.appendChild(tr);
    });
    
    // Update table info text
    tableInfo.textContent = `Showing ${startIdx + 1} to ${endIdx} of ${len} entries`;
    
    // Draw pagination controls
    pagination.innerHTML = '';
    const totalPages = Math.ceil(len / tableState.pageSize);
    
    if (totalPages <= 1) return;
    
    // Previous button
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${tableState.currentPage === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<a class="page-link" href="#" aria-label="Previous"><i class="bi bi-chevron-left"></i></a>`;
    prevLi.addEventListener('click', (e) => {
        e.preventDefault();
        if (tableState.currentPage > 1) {
            tableState.currentPage--;
            renderTable();
        }
    });
    pagination.appendChild(prevLi);
    
    // Page index buttons
    const maxVisiblePages = 5;
    let startPage = Math.max(1, tableState.currentPage - 2);
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage < maxVisiblePages - 1) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    for (let p = startPage; p <= endPage; p++) {
        const pageLi = document.createElement('li');
        pageLi.className = `page-item ${tableState.currentPage === p ? 'active' : ''}`;
        pageLi.innerHTML = `<a class="page-link" href="#">${p}</a>`;
        pageLi.addEventListener('click', (e) => {
            e.preventDefault();
            tableState.currentPage = p;
            renderTable();
        });
        pagination.appendChild(pageLi);
    }
    
    // Next button
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${tableState.currentPage === totalPages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#" aria-label="Next"><i class="bi bi-chevron-right"></i></a>`;
    nextLi.addEventListener('click', (e) => {
        e.preventDefault();
        if (tableState.currentPage < totalPages) {
            tableState.currentPage++;
            renderTable();
        }
    });
    pagination.appendChild(nextLi);
}

// --- Deterministic Sample Dataset Generation ---
function generateSampleDataset() {
    const slots = ['Morning', 'Afternoon', 'Evening', 'PrimeTime'];
    let csvContent = "AdvertisementID,Duration,Budget,Priority,PreferredSlot\n";
    
    // Generate 50 items
    for (let i = 1; i <= 50; i++) {
        const adId = `AD${String(i).padStart(3, '0')}`;
        const duration = [15, 20, 30, 40, 45, 60][(i * 11) % 6];
        const priority = (i % 10) + 1; // 1 to 10
        const budget = duration * 180 + priority * 400 - (i % 3) * 150;
        const slot = slots[i % slots.length];
        
        csvContent += `${adId},${duration},${budget},${priority},${slot}\n`;
    }
    
    // Trigger browser local download
    const blob = new Blob([csvContent], { type: 'text/plain;charset=utf-8;' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", "sample_standard_dataset.txt");
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Global bootstrap initializing
document.addEventListener("DOMContentLoaded", () => {
    initTheme();
});
