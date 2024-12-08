function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        let cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

$(document).ready(function () {
    var currentUrl = window.location.pathname;
    var ticketId = currentUrl.match(/\/tickets\/(\d+)\//);
    console.log(ticketId);
    var socket = new WebSocket(`ws://localhost:8000/ws/ticket_message/${ticketId[1]}/`);

    socket.onopen = function(event) {
        console.log("WebSocket подключен");
    };

    socket.onerror = function(error) {
        console.error("WebSocket ошибка:", error);
    };

    socket.onclose = function(event) {
        console.log("WebSocket закрыт");
    };
    socket.onmessage = function(event) {
        var data = JSON.parse(event.data);
        console.log('Получено сообщение от сервера:', data);
        updateTicketMessages(data);
    };

    function updateTicketMessages(newMessage) {
        const messageHtml = `<li>${newMessage}</li>`;
        $(".ticket-bodies ul").append(messageHtml);
    }

    if (ticketId) {
        ticketId = ticketId[1];
        $('title').text('Ticket ID: ' + ticketId);

        var csrfToken = getCookie('csrftoken'); 
        $.ajaxSetup({
            headers: {
                'X-CSRFToken': csrfToken
            }
        });
        $.ajax({
            url: `/api/v1/tickets/${ticketId}/`,
            method: "GET",
            success: function (data) {
                const ticketHtml = `
                    <div class="ticket-container">
                        <div class="ticket-header">Обращение #${data.id}: ${data.subject}</div>
                        <div>Email: ${data.email}</div>
                        <div>Статус: ${data.status}</div>
                        <div>Создан: ${new Date(data.created_at).toLocaleString()}</div>
                        <div class="ticket-bodies">
                            <h4>Сообщения:</h4>
                            <ul>
                                ${data.bodies.map(body => `<li>${body}</li>`).join("")}
                            </ul>
                        </div>
                    </div>
                `;
                $("#tickets-list").append(ticketHtml);
                if (data.status == "closed") {
                    $(".ticket-response").remove();
                };
                $("#status-select").val(data.status);
            },
            error: function (xhr) {
                console.error(`Ошибка загрузки обращения с ID ${ticketId}:`, xhr.responseText);
            }
        });
        $("#send-message-btn").click(function () {
            var message = $("#message-input").val();
            if (message.trim() === "") {
                alert("Сообщение не может быть пустым!");
                return;
            }
            $.ajax({
                url: "/api/v1/tickets/response/",
                method: "POST",
                data: JSON.stringify({
                    message: message,
                    ticket_id: ticketId
                }),
                contentType: "application/json",
                success: function (response) {
                    alert("Сообщение успешно отправлено!");
                    // Очистить поле ввода
                    $("#message-input").val("");
                },
                error: function (xhr) {
                    console.error("Ошибка при отправке сообщения:", xhr.responseText);
                    alert("Произошла ошибка при отправке сообщения.");
                }
            });
        });

        $("#status-select").change(function () {
            var newStatus = $(this).val();
            $.ajax({
                url: `/api/v1/tickets/${ticketId}/`,
                method: "PATCH",
                data: JSON.stringify({
                    status: newStatus
                }),
                contentType: "application/json",
                success: function (response) {
                    alert("Статус обращения успешно обновлен!");
                    if (newStatus == "closed") {
                        $(".ticket-response").remove();
                    };
                },
                error: function (xhr) {
                    console.error("Ошибка при обновлении статуса обращения:", xhr.responseText);
                    alert("Произошла ошибка при обновлении статуса.");
                }
            });
        });
    } else {
        console.log('Ticket ID not found in the URL');
    }
});