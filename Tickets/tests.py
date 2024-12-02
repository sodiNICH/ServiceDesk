from django.test import TestCase
from Tickets.models import Tickets

class TicketsAPITestCase(TestCase):

    def setUp(self):
        self.ticket_1 = Tickets.objects.create(
            id_mails=[1, 2, 3],
            email="test1@example.com",
            subject="Issue 1",
            bodies=["Problem description 1", "Additional details"],
            messages_id=["msg1", "msg2"],
            status="new",
            created_at="2024-12-02 09:23:04",
            updated_at="2024-12-02 09:23:04",
        )

        self.ticket_2 = Tickets.objects.create(
            id_mails=[4, 5, 6],
            email="test2@example.com",
            subject="Issue 2",
            bodies=["Problem description 2"],
            messages_id=["msg3"],
            status="in_process",
            created_at="2024-12-02 10:00:00",
            updated_at="2024-12-02 10:00:00",
        )

    def test_ticket_creation(self):
        ticket = Tickets.objects.get(id=self.ticket_1.id)
        self.assertEqual(ticket.email, "test1@example.com")
        self.assertEqual(ticket.subject, "Issue 1")
        self.assertEqual(ticket.status, "new")
        self.assertEqual(ticket.id_mails, [1, 2, 3])
        self.assertEqual(ticket.bodies, ["Problem description 1", "Additional details"])
        self.assertEqual(ticket.messages_id, ["msg1", "msg2"])

    def test_ticket_update_status(self):
        ticket = Tickets.objects.get(id=self.ticket_1.id)
        ticket.status = "closed"
        ticket.save()

        updated_ticket = Tickets.objects.get(id=self.ticket_1.id)
        self.assertEqual(updated_ticket.status, "closed")

    def test_ticket_invalid_status_update(self):
        ticket = Tickets.objects.get(id=self.ticket_1.id)
        ticket.status = "invalid_status"
        with self.assertRaises(ValueError):
            ticket.save()

    def test_ticket_empty_email(self):
        ticket = Tickets.objects.create(
            id_mails=[7, 8],
            email="",
            subject="Issue 3",
            bodies=["Problem description 3"],
            messages_id=["msg4"],
            status="new",
            created_at="2024-12-02 11:00:00",
            updated_at="2024-12-02 11:00:00",
        )
        self.assertEqual(ticket.email, "")

    def test_ticket_with_multiple_messages(self):
        ticket = Tickets.objects.get(id=self.ticket_1.id)
        self.assertIn("msg1", ticket.messages_id)
        self.assertIn("msg2", ticket.messages_id)

    def test_ticket_creation_with_bodies(self):
        ticket = Tickets.objects.get(id=self.ticket_1.id)
        self.assertEqual(len(ticket.bodies), 2)
        self.assertEqual(ticket.bodies[0], "Problem description 1")
        self.assertEqual(ticket.bodies[1], "Additional details")

    def test_ticket_with_status_choices(self):
        ticket_new = Tickets.objects.create(
            id_mails=[9, 10],
            email="test3@example.com",
            subject="Issue 4",
            bodies=["Problem description 4"],
            messages_id=["msg5"],
            status="new",
            created_at="2024-12-02 12:00:00",
            updated_at="2024-12-02 12:00:00",
        )
        ticket_in_process = Tickets.objects.create(
            id_mails=[11, 12],
            email="test4@example.com",
            subject="Issue 5",
            bodies=["Problem description 5"],
            messages_id=["msg6"],
            status="in_process",
            created_at="2024-12-02 13:00:00",
            updated_at="2024-12-02 13:00:00",
        )
        ticket_closed = Tickets.objects.create(
            id_mails=[13, 14],
            email="test5@example.com",
            subject="Issue 6",
            bodies=["Problem description 6"],
            messages_id=["msg7"],
            status="closed",
            created_at="2024-12-02 14:00:00",
            updated_at="2024-12-02 14:00:00",
        )

        self.assertEqual(ticket_new.status, "new")
        self.assertEqual(ticket_in_process.status, "in_process")
        self.assertEqual(ticket_closed.status, "closed")

    def test_ticket_creation_with_null_values(self):
        ticket = Tickets.objects.create(
            id_mails=[],
            email=None,
            subject="Issue 7",
            bodies=[],
            messages_id=[],
            status="new",
            created_at="2024-12-02 15:00:00",
            updated_at="2024-12-02 15:00:00",
        )

        self.assertIsNone(ticket.email)
        self.assertEqual(ticket.id_mails, [])
        self.assertEqual(ticket.bodies, [])
        self.assertEqual(ticket.messages_id, [])
