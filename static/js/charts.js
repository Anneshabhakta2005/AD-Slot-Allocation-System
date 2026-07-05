/*
   Smart Advertisement Slot Allocation System - charts.js
   Initializes and updates all Dashboard Chart.js graphs
*/

function initDashboardCharts(stats, comparisons, activeAlgo) {
    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    
    // Theme colors matching style.css variables
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';
    const textColor = isDark ? '#94a3b8' : '#475569';
    const accentColor = '#6366f1';
    
    // Retrieve colors
    const colorsList = ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e'];
    
    // --- 1. Revenue by Slot (Bar Chart) ---
    const ctxRevenue = document.getElementById('chartRevenueSlot');
    if (ctxRevenue) {
        // Fetch active slot revenues from stats or calculate
        const slots = ['Morning', 'Afternoon', 'Evening', 'PrimeTime'];
        
        // We calculate revenues for the active algorithm
        const activeComparisons = comparisons[activeAlgo.toLowerCase()];
        
        // Calculate revenues from rawAdsData defined globally
        const revenues = [0, 0, 0, 0];
        rawAdsData.forEach(ad => {
            if (ad.Status === 'Allocated') {
                const sIdx = slots.indexOf(ad.AllocatedSlot);
                if (sIdx !== -1) {
                    revenues[sIdx] += ad.Budget;
                }
            }
        });
        
        new Chart(ctxRevenue, {
            type: 'bar',
            data: {
                labels: slots,
                datasets: [{
                    label: 'Revenue ($)',
                    data: revenues,
                    backgroundColor: colorsList,
                    borderRadius: 8,
                    borderWidth: 0,
                    barThickness: 32
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `$${context.raw.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: textColor }
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: {
                            color: textColor,
                            callback: function(value) { return '$' + value; }
                        }
                    }
                }
            }
        });
    }
    
    // --- 2. Allocation Yield Ratio (Pie Chart) ---
    const ctxRatio = document.getElementById('chartAllocatedRatio');
    if (ctxRatio) {
        new Chart(ctxRatio, {
            type: 'pie',
            data: {
                labels: ['Allocated', 'Rejected'],
                datasets: [{
                    data: [stats.allocated_count, stats.rejected_count],
                    backgroundColor: ['#10b981', '#ef4444'],
                    borderColor: isDark ? '#111428' : '#ffffff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: textColor, padding: 15 }
                    }
                }
            }
        });
    }
    
    // --- 3. Cumulative Revenue Growth Curve (Line Graph) ---
    const ctxGrowth = document.getElementById('chartRevenueGrowth');
    if (ctxGrowth) {
        // Filter and sort allocated ads chronologically
        const slotsOrder = { 'Morning': 1, 'Afternoon': 2, 'Evening': 3, 'PrimeTime': 4 };
        
        const allocatedAds = rawAdsData
            .filter(ad => ad.Status === 'Allocated')
            .sort((a, b) => {
                const orderA = slotsOrder[a.AllocatedSlot] || 0;
                const orderB = slotsOrder[b.AllocatedSlot] || 0;
                if (orderA !== orderB) return orderA - orderB;
                
                // Compare start times
                return String(a.AllocatedStartTime).localeCompare(String(b.AllocatedStartTime));
            });
            
        // Build cumulative values
        let runningSum = 0;
        const labels = ['Start'];
        const growthData = [0];
        
        allocatedAds.forEach((ad, index) => {
            runningSum += ad.Budget;
            labels.push(`${ad.AdvertisementID} (${ad.AllocatedSlot})`);
            growthData.push(runningSum);
        });
        
        new Chart(ctxGrowth, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Cumulative Revenue ($)',
                    data: growthData,
                    borderColor: accentColor,
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: true,
                    tension: 0.25,
                    borderWidth: 3,
                    pointRadius: growthData.length > 50 ? 0 : 3,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Total: $${context.raw.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: growthData.length < 30, // Hide x-axis labels if too many items
                        grid: { display: false },
                        ticks: { color: textColor }
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: {
                            color: textColor,
                            callback: function(value) { return '$' + value; }
                        }
                    }
                }
            }
        });
    }
    
    // --- 4. Priority Distribution (Dual-Bar Chart) ---
    const ctxPriority = document.getElementById('chartPriorityDist');
    if (ctxPriority) {
        // Collect allocated vs rejected ads count per priority level (1 to 10)
        const priorities = Array.from({ length: 10 }, (_, i) => i + 1);
        const allocatedCounts = Array(10).fill(0);
        const rejectedCounts = Array(10).fill(0);
        
        rawAdsData.forEach(ad => {
            const pIdx = ad.Priority - 1;
            if (pIdx >= 0 && pIdx < 10) {
                if (ad.Status === 'Allocated') {
                    allocatedCounts[pIdx]++;
                } else {
                    rejectedCounts[pIdx]++;
                }
            }
        });
        
        new Chart(ctxPriority, {
            type: 'bar',
            data: {
                labels: priorities,
                datasets: [
                    {
                        label: 'Allocated Ads',
                        data: allocatedCounts,
                        backgroundColor: '#10b981',
                        borderRadius: 4
                    },
                    {
                        label: 'Rejected Ads',
                        data: rejectedCounts,
                        backgroundColor: '#ef4444',
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: textColor }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: textColor },
                        title: { display: true, text: 'Campaign Priority Level', color: textColor }
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: { color: textColor, stepSize: 1 }
                    }
                }
            }
        });
    }
}
