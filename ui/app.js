let selectedGroupId = null;
let participants = [];

function showMessage(message, type = "success") {
    const messageElement = document.getElementById("message");

    messageElement.textContent = message;
    messageElement.className = type;
}

async function apiRequest(baseUrl, path, options, serviceName) {
    let response;

    try {
        response = await fetch(`${baseUrl}${path}`, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...options.headers
            }
        });
    } catch (error) {
        throw new Error(
            `${serviceName} is starting up or temporarily unavailable. Please try again in a moment.`
        );
    }

    let data = {};

    try {
        const responseText = await response.text();
        data = responseText ? JSON.parse(responseText) : {};
    } catch (error) {
        data = {};
    }

    if (!response.ok) {
        if ([502, 503, 504].includes(response.status)) {
            throw new Error(
                `${serviceName} is starting up or temporarily unavailable. Please try again in a moment.`
            );
        }

        throw new Error(
            data.error || `${serviceName} request failed (HTTP ${response.status})`
        );
    }

    return data;
}

async function expenseRequest(path, options = {}) {
    return apiRequest(
        API_CONFIG.expenseService,
        path,
        options,
        "Expense Service"
    );
}

async function settlementRequest(path, options = {}) {
    return apiRequest(
        API_CONFIG.settlementService,
        path,
        options,
        "Settlement Service"
    );
}

async function loadGroups() {
    try {
        const groups = await expenseRequest("/api/groups");

        const groupsList = document.getElementById("groups-list");
        groupsList.innerHTML = "";

        if (groups.length === 0) {
            groupsList.textContent = "No groups created yet.";
            return;
        }

        groups.forEach(group => {
            const button = document.createElement("button");
            button.textContent = group.name;
            button.type = "button";

            button.addEventListener("click", () => {
                selectGroup(group.id, group.name);
            });

            groupsList.appendChild(button);
        });
    } catch (error) {
        showMessage(error.message, "error");
    }
}

async function selectGroup(groupId, groupName) {
    selectedGroupId = groupId;

    document.getElementById("group-dashboard").hidden = false;
    document.getElementById("selected-group-name").textContent = groupName;

    await loadParticipants();
    await loadExpenses();
    await loadBalances();
}

async function loadParticipants() {
    try {
        participants = await expenseRequest(
            `/api/groups/${selectedGroupId}/participants`
        );

        const list = document.getElementById("participants-list");
        list.innerHTML = "";

        const payerSelect = document.getElementById("expense-payer");
        const settlementPayer = document.getElementById("settlement-payer");
        const settlementReceiver = document.getElementById("settlement-receiver");
        const shares = document.getElementById("expense-shares");

        payerSelect.innerHTML = '<option value="">Who paid?</option>';
        settlementPayer.innerHTML = '<option value="">Who pays?</option>';
        settlementReceiver.innerHTML = '<option value="">Who receives?</option>';
        shares.innerHTML = "";

        participants.forEach(participant => {
            const item = document.createElement("li");
            item.textContent = participant.name;
            list.appendChild(item);

            [payerSelect, settlementPayer, settlementReceiver].forEach(select => {
                const option = document.createElement("option");
                option.value = participant.id;
                option.textContent = participant.name;
                select.appendChild(option);
            });

            const label = document.createElement("label");
            const checkbox = document.createElement("input");

            checkbox.type = "checkbox";
            checkbox.value = participant.id;
            checkbox.name = "shared-participants";

            label.appendChild(checkbox);
            label.appendChild(document.createTextNode(participant.name));
            shares.appendChild(label);
        });
    } catch (error) {
        showMessage(error.message, "error");
    }
}

async function loadExpenses() {
    try {
        const snapshot = await expenseRequest(
            `/api/groups/${selectedGroupId}/snapshot`
        );

        const list = document.getElementById("expenses-list");
        list.innerHTML = "";

        if (snapshot.expenses.length === 0) {
            list.textContent = "No expenses recorded yet.";
            return;
        }

        snapshot.expenses.forEach(expense => {
            const item = document.createElement("p");
            item.textContent =
                `${expense.description} — €${Number(expense.amount).toFixed(2)} ` +
                `(Paid by ${expense.paid_by_name})`;

            list.appendChild(item);
        });
    } catch (error) {
        showMessage(error.message, "error");
    }
}

async function loadBalances() {
    try {
        const result = await settlementRequest(
            `/api/groups/${selectedGroupId}/balances`
        );

        const list = document.getElementById("balances-list");
        list.innerHTML = "";

        result.balances.forEach(balance => {
            const participant = participants.find(
                person => person.id === balance.participant_id
            );

            const item = document.createElement("p");
            const name = participant ? participant.name : "Unknown";

            item.textContent =
                `${name}: €${Number(balance.balance).toFixed(2)}`;

            list.appendChild(item);
        });
    } catch (error) {
        showMessage(error.message, "error");
    }
}

document.addEventListener("DOMContentLoaded", loadGroups);

document.getElementById("group-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const name = document.getElementById("group-name").value.trim();

    if (!name) {
        showMessage("Please enter a group name.", "error");
        return;
    }

    try {
        const group = await expenseRequest("/api/groups", {
            method: "POST",
            body: JSON.stringify({ name })
        });

        document.getElementById("group-form").reset();

        showMessage("Group created successfully!");
        await loadGroups();
        await selectGroup(group.id, group.name);

    } catch (error) {
        showMessage(error.message, "error");
    }
});

document.getElementById("participant-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const name = document.getElementById("participant-name").value.trim();

    if (!name) {
        showMessage("Please enter a participant name.", "error");
        return;
    }

    if (!selectedGroupId) {
        showMessage("Please select a group first.", "error");
        return;
    }

    try {
        await expenseRequest(
            `/api/groups/${selectedGroupId}/participants`,
            {
                method: "POST",
                body: JSON.stringify({ name })
            }
        );

        document.getElementById("participant-form").reset();

        showMessage("Participant added successfully!");

        await loadParticipants();
        await loadBalances();

    } catch (error) {
        showMessage(error.message, "error");
    }
});

document.getElementById("expense-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!selectedGroupId) {
        showMessage("Please select a group first.", "error");
        return;
    }

    const description = document.getElementById("expense-description").value.trim();
    const amount = Number(document.getElementById("expense-amount").value);
    const paidById = Number(document.getElementById("expense-payer").value);
    const category = document.getElementById("expense-category").value.trim();

    const sharedParticipants = Array.from(
        document.querySelectorAll(
            'input[name="shared-participants"]:checked'
        )
    ).map(checkbox => Number(checkbox.value));

    if (!description || !category || !paidById || amount <= 0 || sharedParticipants.length === 0) {
        showMessage("Please complete all expense fields and select participants.", "error");
        return;
    }

    try {
        await expenseRequest(
            `/api/groups/${selectedGroupId}/expenses`,
            {
                method: "POST",
                body: JSON.stringify({
                    description,
                    amount,
                    paid_by_id: paidById,
                    category,
                    shared_participants: sharedParticipants
                })
            }
        );

        document.getElementById("expense-form").reset();

        showMessage("Expense added successfully!");

        await loadExpenses();
        await loadBalances();

    } catch (error) {
        showMessage(error.message, "error");
    }
});

document.getElementById("settlement-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!selectedGroupId) {
        showMessage("Please select a group first.", "error");
        return;
    }

    const payerId = Number(document.getElementById("settlement-payer").value);
    const receiverId = Number(document.getElementById("settlement-receiver").value);
    const amount = Number(document.getElementById("settlement-amount").value);

    if (!payerId || !receiverId || amount <= 0) {
        showMessage("Please complete all settlement fields.", "error");
        return;
    }

    if (payerId === receiverId) {
        showMessage("A participant cannot pay themselves.", "error");
        return;
    }

    try {
        await settlementRequest(
            `/api/groups/${selectedGroupId}/settlements`,
            {
                method: "POST",
                body: JSON.stringify({
                    payer_id: payerId,
                    receiver_id: receiverId,
                    amount
                })
            }
        );

        document.getElementById("settlement-form").reset();

        showMessage("Settlement recorded successfully!");

        await loadBalances();

    } catch (error) {
        showMessage(error.message, "error");
    }
});
