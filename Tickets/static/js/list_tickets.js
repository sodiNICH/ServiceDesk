function loadTickets() {
    const status = $('#status').val();
    const ordering = $('#ordering').val();
    let url = '/api/v1/tickets/';
    if (status) url += `?status=${status}&`;
    if (ordering) url += `?ordering=${ordering}`;

    $.ajax({
        url: url,
        type: 'GET',
        success: function (data) {
            const tbody = $('#tickets-list');
            tbody.empty();

            if (data.length === 0) {
                tbody.append('<tr><td colspan="4">Нет обращения</td></tr>');
                return;
            }

            data.forEach(ticket => {
                console.log(ticket)
                tbody.append(`
                    <tr id="ticket-${ticket.id}">
                        <td>${ticket.email}</td>
                        <td><a href="/tickets/${ticket.id}/">${ticket.subject}</a></td>
                        <td>${ticket.status}</td>
                        <td>${new Date(ticket.created_at).toLocaleString()}</td>
                    </tr>
                `);
            });
        },
        error: function () {
            alert('Ошибка при загрузке обращений.');
        }
    });
}

$(document).ready(function () {
    loadTickets();
    var socket = new WebSocket('ws://localhost:8000/ws/ticket_list/');
    socket.onopen = function(event) {
        console.log("WebSocket подключен");
    };
    socket.onmessage = function(event) {
        var data = JSON.parse(event.data);
        console.log('Получено сообщение от сервера:', data);
        updateTicketList(data);
    };
    socket.onerror = function(error) {
        console.error("WebSocket ошибка:", error);
    };
    socket.onclose = function(event) {
        console.log("WebSocket закрыт");
    };
    $('#filter-btn').on('click', loadTickets);
});

function updateTicketList(ticketData) {
    const tbody = $('#tickets-list');
    const existingTicket = $(`#ticket-${ticketData.id}`);

    $('#tickets-list tr:contains("Нет обращения")').remove();
    if (existingTicket.length > 0) {
        existingTicket.replaceWith(`
            <tr id="ticket-${ticketData.id}">
                <td>${ticketData.email}</td>
                <td><a href="/tickets/${ticketData.id}/">${ticketData.subject}</a></td>
                <td>${ticketData.status}</td>
                <td>${new Date(ticketData.created_at).toLocaleString()}</td>
            </tr>
        `);
    } else {
        console.log(ticketData.created_at)
        tbody.append(`
            <tr id="ticket-${ticketData.id}">
                <td>${ticketData.email}</td>
                <td><a href="/tickets/${ticketData.id}/">${ticketData.subject}</a></td>
                <td>${ticketData.status}</td>
                <td>${new Date(ticketData.created_at).toLocaleString()}</td>
            </tr>
        `);
    }
}