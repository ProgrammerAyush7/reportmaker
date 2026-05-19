document.addEventListener("DOMContentLoaded", () => {

    // category expand

    document.querySelectorAll(".category-toggle").forEach(toggle => {
        toggle.addEventListener("change", () => {
            const tests = toggle.closest(".category-block")
                .querySelector(".category-tests");

            tests.style.display = toggle.checked ? "block" : "none";
        });
    });

    // test expand

    document.querySelectorAll(".test-toggle").forEach(toggle => {
        toggle.addEventListener("change", () => {

            const row = toggle.closest(".test-row");

            const input = row.querySelector(".test-input");
            const subtests = row.querySelector(".subtests");

            if (input) {
                input.style.display = toggle.checked ? "block" : "none";
            }

            if (subtests) {
                subtests.style.display = toggle.checked ? "block" : "none";
            }
        });
    });

    // --------------------------------------------------
    // PREFILL EDIT DATA
    // --------------------------------------------------

    if (window.EDIT_DATA && window.EDIT_DATA.patient) {

        const patient = window.EDIT_DATA.patient;
        const tests = window.EDIT_DATA.tests;

        // patient details

        const nameParts = patient.name.split(" ");

        const possiblePrefix = nameParts[0];

        const prefixes = [
            "Mr",
            "Mrs",
            "Miss",
            "Master",
            "Dr",
            "Adv"
        ];

        if (prefixes.includes(possiblePrefix)) {
            document.getElementById("prefix").value = possiblePrefix;
            document.getElementById("patient_name").value =
                nameParts.slice(1).join(" ");
        } else {
            document.getElementById("patient_name").value = patient.name;
        }

        document.getElementById("age").value = patient.age || "";
        document.getElementById("referred_by").value =
            patient.referred_by || "";

        document.querySelector(
            `input[name="sex"][value="${patient.sex}"]`
        ).checked = true;

        // date

        if (patient.date) {

            const [day, month, year] = patient.date.split("-");

            document.getElementById("date").value =
                `${year}-${month}-${day}`;
        }

        // tests

        document.querySelectorAll(".test-row").forEach(row => {

            const sr = row.dataset.sr;

            if (!(sr in tests)) return;

            const toggle = row.querySelector(".test-toggle");

            toggle.checked = true;

            const input = row.querySelector(".test-input");
            const subtests = row.querySelectorAll(".subtest-input");

            if (input) {
                input.style.display = "block";
                input.value = tests[sr];
            }

            if (subtests.length > 0) {

                const values = tests[sr].split(",");

                row.querySelector(".subtests").style.display = "block";

                subtests.forEach((s, index) => {
                    s.value = values[index] || "";
                });
            }

            // expand category

            const categoryBlock = row.closest(".category-block");

            const categoryToggle =
                categoryBlock.querySelector(".category-toggle");

            categoryToggle.checked = true;

            categoryBlock.querySelector(".category-tests")
                .style.display = "block";
        });
    }

    // submit

    document
        .getElementById("generate-btn")
        .addEventListener("click", async () => {

            const prefix = document.getElementById("prefix").value;
            const name = document.getElementById("patient_name").value.trim();

            const rawDate = document.getElementById("date").value;

            let formattedDate = "";

            if (rawDate) {
                const [year, month, day] = rawDate.split("-");
                formattedDate = `${day}-${month}-${year}`;
            }

            const patient_data = {
                name: prefix ? `${prefix} ${name}` : name,
                age: document.getElementById("age").value.trim(),
                sex: document.querySelector("input[name='sex']:checked").value,
                date: formattedDate,
                referred_by: document.getElementById("referred_by").value.trim()
            };

            const tests = {};

            document.querySelectorAll(".test-row").forEach(row => {

                const checked = row.querySelector(".test-toggle").checked;

                if (!checked) return;

                const sr_no = row.dataset.sr;

                const input = row.querySelector(".test-input");
                const subtests = row.querySelectorAll(".subtest-input");

                if (input) {
                    tests[sr_no] = input.value.trim();
                }

                if (subtests.length > 0) {
                    const values = [];

                    subtests.forEach(s => {
                        values.push(s.value.trim());
                    });

                    tests[sr_no] = values.join(",");
                }
            });

            const payload = {
                patient: patient_data,
                tests: tests,
                edit_mode: false
            };

            if (window.EDIT_DATA && window.EDIT_DATA.patient) {
                payload.edit_mode = true;
                payload.patient.id = window.EDIT_DATA.patient.id;
            }

            await fetch("/submit-report", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            window.location.href = "/";
        });
});