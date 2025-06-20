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
        let subjectOptions = '<option value="" selected disabled>Select Subject</option>';
        if (window.subjectNames && window.subjectNames.length > 0) {
            window.subjectNames.forEach(function(name) {
                subjectOptions += `<option value="${name}">${name}</option>`;
            });
        }
        td.innerHTML = `
            <div class="space-y-2">
                <select class="w-full p-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white subject-select">
                    ${subjectOptions}
                </select>
                <select class="w-full p-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white faculty-select">
                    <option value="" selected disabled>Select Faculty</option>
                </select>
            </div>
        `;
        row.insertBefore(td, row.lastElementChild);
        attachSubjectFacultyListeners(td);
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
    let classroomOptions = '';
    if (window.classroomNames && window.classroomNames.length > 0) {
        window.classroomNames.forEach(function(name) {
            classroomOptions += `<option value="${name}">${name}</option>`;
        });
    }
    firstCell.innerHTML = `
        <select class="w-full p-2 border border-gray-200 rounded-lg bg-white focus:ring-2 focus:ring-blue-400 font-semibold text-gray-700">
            ${classroomOptions}
        </select>
    `;
    row.appendChild(firstCell);
    for (let i = 0; i < colCount; i++) {
        const td = document.createElement('td');
        td.className = 'p-2 sm:p-4 text-center bg-blue-50 min-w-[160px]';
        let subjectOptions = '<option value="" selected disabled>Select Subject</option>';
        if (window.subjectNames && window.subjectNames.length > 0) {
            window.subjectNames.forEach(function(name) {
                subjectOptions += `<option value="${name}">${name}</option>`;
            });
        }
        td.innerHTML = `
            <div class="space-y-2">
                <select class="w-full p-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white subject-select">
                    ${subjectOptions}
                </select>
                <select class="w-full p-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white faculty-select">
                    <option value="" selected disabled>Select Faculty</option>
                </select>
            </div>
        `;
        row.appendChild(td);
        attachSubjectFacultyListeners(td);
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
    document.getElementById('saveTimetableBtn').addEventListener('click', function(event) {
        event.preventDefault();
        this.disabled = true;
        const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
        let entries = [];
        days.forEach(day => {
            const headRow = document.querySelector(`#timetable-head-${day} tr`);
            const timeInputs = headRow.querySelectorAll('input[type="time"]');
            const rows = document.querySelectorAll(`#timetable-body-${day} tr`);
            rows.forEach((row, rowIndex) => {
                const cells = row.querySelectorAll('td');
                const classroomSelect = cells[0].querySelector('select');
                const classroom = classroomSelect ? classroomSelect.value : '';
                for (let i = 1; i < cells.length - 1; i++) {
                    const subjectSelect = cells[i].querySelector('.subject-select');
                    const facultySelect = cells[i].querySelector('.faculty-select');
                    const subject = subjectSelect ? subjectSelect.value : '';
                    const faculty_ssid = facultySelect ? facultySelect.value : '';
                    const faculty_name = facultySelect ? (facultySelect.selectedOptions[0]?.text || '') : '';
                    const start_time = timeInputs[(i-1)*2] ? timeInputs[(i-1)*2].value : '';
                    const end_time = timeInputs[(i-1)*2+1] ? timeInputs[(i-1)*2+1].value : '';
                    if (subject && faculty_ssid) {
                        entries.push({
                            day: day,
                            classroom: classroom,
                            start_time: start_time,
                            end_time: end_time,
                            subject: subject,
                            faculty_ssid: faculty_ssid,
                            faculty_name: faculty_name,
                            cell_row: rowIndex,
                            cell_col: i - 1
                        });
                    }
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
            this.disabled = false;
        }).bind(this);
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
        }, 300);
    });
}

let subjectOptions = '';
if (window.subjectNames && window.subjectNames.length > 0) {
    window.subjectNames.forEach(function(name) {
        subjectOptions += `<option value="${name}">${name}</option>`;
    });
}

window.removeSubject = function(subject) {
    if (!confirm('Are you sure you want to remove this subject?')) return;
    fetch(window.removeSubjectUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': window.csrfToken
        },
        body: JSON.stringify({subject: subject})
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Subject removed!');
            location.reload(); // Or update the table dynamically
        } else {
            alert('Error: ' + data.message);
        }
    });
};

function getFacultyOptionsForSubject(subject) {
    let options = '<option value="" selected disabled>Select Faculty</option>';
    if (window.subjectFacultyList && subject) {
        window.subjectFacultyList.forEach(function(sf) {
            if (sf.subject === subject) {
                options += `<option value="${sf.faculty_ssid}">${sf.faculty_name}</option>`;
            }
        });
    }
    return options;
}

// Update faculty dropdown when subject changes
function attachSubjectFacultyListeners(row) {
    const selects = row.querySelectorAll('select');
    if (selects.length < 2) return;
    const subjectSelect = selects[0];
    const facultySelect = selects[1];
    // Initially disable faculty select
    facultySelect.disabled = true;
    subjectSelect.addEventListener('change', function() {
        if (subjectSelect.value) {
            facultySelect.innerHTML = getFacultyOptionsForSubject(subjectSelect.value);
            facultySelect.disabled = false;
        } else {
            facultySelect.innerHTML = '<option value="" selected disabled>Select Faculty</option>';
            facultySelect.disabled = true;
        }
    });
}

// Attach listeners to initial static rows on page load
window.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('#timetable-body-Monday, #timetable-body-Tuesday, #timetable-body-Wednesday, #timetable-body-Thursday, #timetable-body-Friday, #timetable-body-Saturday, #timetable-body-Sunday').forEach(function(tbody) {
        tbody.querySelectorAll('tr').forEach(function(row) {
            row.querySelectorAll('td').forEach(function(td) {
                attachSubjectFacultyListeners(td);
            });
        });
    });
});