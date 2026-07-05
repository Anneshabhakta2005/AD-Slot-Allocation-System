
# Smart Advertisement Slot Allocation System

An advanced, production-quality media optimization tool that schedules advertisements across TV channels or digital platforms to maximize total campaign revenue while satisfying slot capacities, priority requirements, and budget constraints.

This application is built as a modular Flask project with a modern, glassmorphic dark-mode default user interface using Vanilla CSS and JavaScript, backed by Python optimization algorithms.

---

## Table of Contents
1. [Core Features](#core-features)
2. [Supported Algorithms](#supported-algorithms)
3. [Folder Structure](#folder-structure)
4. [Installation & Setup](#installation--setup)
5. [Running the Application](#running-the-application)
6. [Testing the Codebase](#testing-the-codebase)
7. [Dataset Format Specifications](#dataset-format-specifications)
8. [Future Enhancements](#future-enhancements)

---

## Core Features
*   **Drag-and-Drop File Upload:** Seamless drag-drop zone with instant CSV/TXT column parsing and input validation.
*   **Dynamic Visual Timeline:** A custom horizontal scheduling block timeline showing exactly how slot capacities (180/240 mins) are packed with color-coded ads.
*   **Interactive Results Table:** Global text search, column sorting, pagination controls, and row counts.
*   **Strategy Comparison Benchmarks:** Side-by-side performance table showing execution runtime (in ms), scheduled ad counts, unused time, and optimized revenue for all algorithms.
*   **Visual Charts Dashboard:** Chart.js canvas renderings mapping slot revenues (Bar), yields (Pie), cumulative revenue curves (Line), and priority distribution (Dual Bar).
*   **Report Exports:** Download full schedules as CSV or print complete vector PDF reports containing statistics, tables, and graphs.
*   **Dual Styling Themes:** Translucent glass cards and styling transitions supporting Dark Mode (default) and Light Mode.

---

## Supported Algorithms

### 1. Greedy Scheduling
*   **Execution Time:** $O(N \log N)$
*   **Sorting Criteria:** Sorts campaigns in descending order by `Priority`, then by `Budget`, and finally in ascending order by `Duration` (to fit smaller items).
*   **Concept:** Fast heuristic scheduling that works by allocating the highest-valued campaign that can fit within the remaining slot time. Useful for large datasets.

### 2. 0/1 Knapsack Dynamic Programming
*   **Execution Time:** $O(N \times W)$ where $W$ is the slot capacity (180 or 240 minutes).
*   **Optimization Goal:** Maximizes total budget revenue.
*   **Concept:** Maps slot capacities to weights and budgets to values. Guarantees the absolute mathematical optimal schedule combination for each slot.

### 3. Weighted Interval Scheduling (Bonus)
*   **Execution Time:** $O(N \log N)$
*   **Conflict Resolution:** Schedules campaigns that specify fixed start and end times (`StartTime`, `EndTime`) using dynamic programming on compatibility arrays.
*   **Concept:** Computes non-overlapping intervals yielding maximum budgets. Includes a hash-based generator for datasets missing explicit time boundaries.

---

## Folder Structure

```
AD Slot Allocation System/
│
├── app.py                      # Flask Server and Application routing
├── requirements.txt            # Package dependencies
├── README.md                   # System documentation
│
├── algorithms/                 # Backend algorithmic logic
│   ├── __init__.py
│   ├── parser.py               # Dataset CSV parser and input validator
│   ├── greedy.py               # Greedy scheduling logic
│   ├── knapsack.py             # 0/1 Knapsack dynamic programming solver
│   ├── interval.py             # Weighted Interval Scheduling solver
│   ├── allocator.py            # Orchestrator & benchmarking wrapper
│   └── utils.py                # Math helpers & ReportLab PDF generator
│
├── templates/                  # Jinja2 HTML pages
│   ├── base.html               # Base layout, navbar, sidebar, theme controls
│   ├── index.html              # Upload page & strategy selectors
│   ├── result.html             # Timelines & paginated schedules
│   ├── dashboard.html          # Stats cards & Chart.js dashboards
│   ├── about.html              # Computational complexity details
│   └── help.html               # FAQ page & sample templates
│
├── static/                     # Assets & client logic
│   ├── css/
│   │   └── style.css           # Glassmorphism, animations, theme stylesheet
│   └── js/
│       ├── main.js             # File drop handlers, tables, theme controls
│       └── charts.js           # Chart.js graphs mapping
│
├── tests/                      # Automated test suite
│   └── test_algorithms.py      # Core parser & scheduling tests
│
└── uploads/                    # Temporary caching directory for JSON/TXT datasets
```

---

## Installation & Setup

### Prerequisites
*   Python 3.11 or higher
*   pip package manager

### Installation Steps
1. Navigate to the project root directory:
   ```bash
   cd "AD Slot Allocation System"
   ```
2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Application

1. Spin up the Flask development server:
   ```bash
   python app.py
   ```
2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```
3. Test using the testing tools on the main page to download sample standard or interval-based files.

---

## Testing the Codebase

Run the automated unittest suite to verify backend routines:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## Dataset Format Specifications

The uploaded dataset must be a comma-separated `.txt` file containing the following columns:

### 1. Standard Dataset (Greedy & Knapsack)
```csv
AdvertisementID,Duration,Budget,Priority,PreferredSlot
AD001,30,5000,8,Morning
AD002,45,8500,9,PrimeTime
AD003,60,12000,7,Evening
AD004,20,3500,5,Morning
```

### 2. Interval-based Dataset (Weighted Interval Scheduling)
```csv
AdvertisementID,Duration,Budget,Priority,PreferredSlot,StartTime,EndTime
AD001,30,5000,8,Morning,09:00,09:30
AD002,45,8500,9,PrimeTime,21:00,21:45
AD003,60,12000,7,Evening,17:00,18:00
```
*Note: Valid slot names are `Morning` (180m), `Afternoon` (180m), `Evening` (240m), and `PrimeTime` (180m).*

---

## Future Enhancements
1. **Multi-Channel Scheduling:** Expand slot allocation to support multiple television channels simultaneously, mapping to the Multiple Knapsack Problem.
2. **Ad Exclusion Rules:** Enforce constraints preventing competing brands (e.g. Coca-Cola and Pepsi) from scheduling ads inside the same slot.
3. **Database Persistence:** Integrate SQLAlchemy to save schedules, compare historical campaigns, and support multi-user accounts.
