// Helper to show/hide popup
window.showPopup = function() {
    document.getElementById('subjectPopup').classList.remove('hidden');
}
window.closePopup = function() {
    document.getElementById('subjectPopup').classList.add('hidden');
}
window.addSubject = function() {
    window.showPopup();
}

// Add/remove columns
window.addColumn = function(day) {
    const headRow = document.querySelector(`#timetable-head-${day} tr`);
    const bodyRows = document.querySelectorAll(`#timetable-body-${day} tr`);
    const newHead = document.createElement('th');
    newHead.className = 'p-2 sm:p-4 text-center text-blue-800 font-semibold border-b border-gray-200 min-w-[160px]';
    newHead.innerHTML = `
        <div class="flex flex-col sm:flex-row items-center sm:space-x-2 space-y-1 sm:space-y-0">
            <input type="time" class="w-full sm:w-1/2 p-2 border border-gray-200 rounded-lg bg-white focus:ring-2 focus:ring-blue-400">
            <span class="hidden sm:inline text-gray-500">to</span>
            <input type="time" class="w-full sm:w-1/2 p-2 border border-gray-200 rounded-lg bg-white focus:ring-2 focus:ring-blue-400">
        </div>
    `;
    headRow.insertBefore(newHead, headRow.lastElementChild);
    bodyRows.forEach(row => {
        const td = document.createElement('td');
        td.className = 'p-2 sm:p-4 text-center bg-blue-50 min-w-[160px]';
        td.innerHTML = `
            <div class="space-y-2">
                <select class="w-full p-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white">
                    <option>Subject A</option>
                    <option>Subject B</option>
                    <option>Subject C</option>
                </select>
                <select class="w-full p-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white">
                    <option>1</option>
                    <option>2</option>
                    <option>3</option>
                </select>
            </div>
        `;
        row.insertBefore(td, row.lastElementChild);
    });
}
window.removeColumn = function(day) {
    const headRow = document.querySelector(`#timetable-head-${day} tr`);
    const bodyRows = document.querySelectorAll(`#timetable-body-${day} tr`);
    if (headRow.children.length > 3) {
        headRow.removeChild(headRow.children[headRow.children.length - 2]);
        bodyRows.forEach(row => {
            row.removeChild(row.children[row.children.length - 2]);
        });
    }
}
window.addRow = function(day) {
    const tbody = document.getElementById(`timetable-body-${day}`);
    const colCount = document.querySelector(`#timetable-head-${day} tr`).children.length - 2;
    const row = document.createElement('tr');
    row.className = 'hover:bg-gray-50 transition-colors duration-200';
    const firstCell = document.createElement('td');
    firstCell.className = 'p-2 sm:p-4 text-center bg-blue-50 min-w-[120px]';
    firstCell.innerHTML = `
        <select class="w-full p-2 border border-gray-200 rounded-lg bg-white focus:ring-2 focus:ring-blue-400 font-semibold text-gray-700">
            <option value="Session 1">Session 1</option>
            <option value="Session 2">Session 2</option>
            <option value="Session 3">Session 3</option>
        </select>
    `;
    row.appendChild(firstCell);
    for (let i = 0; i < colCount; i++) {
        const td = document.createElement('td');
        td.className = 'p-2 sm:p-4 text-center bg-blue-50 min-w-[160px]';
        td.innerHTML = `
            <div class="space-y-2">
                <select class="w-full p-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white">
                    <option>Subject A</option>
                    <option>Subject B</option>
                    <option>Subject C</option>
                </select>
                <select class="w-full p-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white">
                    <option>1</option>
                    <option>2</option>
                    <option>3</option>
                </select>
            </div>
        `;
        row.appendChild(td);
    }
    const controlCell = document.createElement('td');
    controlCell.className = 'bg-blue-50';
    row.appendChild(controlCell);
    tbody.appendChild(row);
}
window.removeRow = function(day) {
    const tbody = document.getElementById(`timetable-body-${day}`);
    if (tbody.children.length > 1) {
        tbody.removeChild(tbody.lastElementChild);
    }
}

// Save timetable
if (document.getElementById('saveTimetableBtn')) {
    document.getElementById('saveTimetableBtn').addEventListener('click', function() {
        const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
        let entries = [];
        days.forEach(day => {
            const rows = document.querySelectorAll(`#timetable-body-${day} tr`);
            rows.forEach(row => {
                const session = row.querySelector('select').value;
                const cells = row.querySelectorAll('td');
                for (let i = 1; i < cells.length - 1; i++) { // skip first and last cell
                    const timeInputs = document.querySelectorAll(`#timetable-head-${day} input[type="time"]`);
                    const start_time = timeInputs[(i-1)*2].value;
                    const end_time = timeInputs[(i-1)*2+1].value;
                    const selects = cells[i].querySelectorAll('select');
                    const subject = selects[0].value;
                    const faculty_ssid = selects[1].value;
                    entries.push({
                        day,
                        session,
                        start_time,
                        end_time,
                        subject,
                        faculty_ssid,
                        faculty_name: "" // You can fetch this if needed
                    });
                }
            });
        });
        fetch(window.saveTimetableUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": window.csrfToken
            },
            body: JSON.stringify({entries})
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                alert("Timetable saved!");
            } else {
                alert("Error saving timetable: " + data.message);
            }
        });
    });
}

// Subject form submit
if (document.getElementById('subjectForm')) {
    document.getElementById('subjectForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const subject = document.getElementById('subjectName').value.trim();
        const faculty_ssid = document.getElementById('facultySsid').value.trim();
        const faculty_name = document.getElementById('facultyName').value.trim();
        if (!subject || !faculty_ssid) {
            alert('Subject and Faculty SSID are required.');
            return;
        }
        fetch(window.saveSubjectFacultyUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": window.csrfToken
            },
            body: JSON.stringify({
                subject: subject,
                faculty_ssid: faculty_ssid,
                faculty_name: faculty_name
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                alert("Subject saved!");
                window.closePopup();
                // Optionally, refresh the subject/faculty table here
            } else {
                alert("Error: " + data.message);
            }
        })
        .catch(err => {
            alert("Error: " + err);
        });
    });
}

// Live faculty name fetch
if (document.getElementById('facultySsid')) {
    let facultySsidTimeout = null;
    document.getElementById('facultySsid').addEventListener('input', function() {
        const ssid = this.value.trim();
        clearTimeout(facultySsidTimeout);
        if (!ssid) {
            document.getElementById('facultyName').value = "";
            return;
        }
        facultySsidTimeout = setTimeout(() => {
            fetch(window.getFacultyNameBySsidUrl + '?ssid=' + encodeURIComponent(ssid))
                .then(response => response.json())
                .then(data => {
                    if (data.status === "success") {
                        document.getElementById('facultyName').value = data.faculty_name;
                    } else {
                        document.getElementById('facultyName').value = "";
                    }
                });
        }, 300); // 300ms debounce
    });
}